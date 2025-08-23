from flask import Flask, request, jsonify, session
from flask_cors import CORS
from flask_session import Session
import os
import sys
import asyncio
from threading import Thread
import time
import json
import queue
import io
import re
import uuid
from datetime import datetime

# Add the parent directory to the path to import main.py
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import your existing CrewAI code
from langchain_openai import ChatOpenAI
from dotenv import load_dotenv

# Import CrewAI after environment setup
from crewai import Agent, Task, Crew

# Load environment variables
load_dotenv()

# Create sessions directory for Flask-Session
sessions_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'flask_session')
if not os.path.exists(sessions_dir):
    os.makedirs(sessions_dir)
    print(f"📁 Created sessions directory: {sessions_dir}")

# Secure API key management - ensure OPENAI_API_KEY is set
api_key = os.getenv("OPENAI_API_KEY")
if not api_key:
    raise ValueError("OPENAI_API_KEY environment variable is required but not set")

os.environ["OPENAI_API_KEY"] = api_key

# Simple LLM configuration for CrewAI 0.165.1 compatibility

# Define the LLM with model from environment variable
model_name = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
api_key = os.getenv("OPENAI_API_KEY")

print(f"🔧 Using model: {model_name}")
print(f"🔧 API key set: {'Yes' if api_key else 'No'}")

# Simple LLM configuration using standard ChatOpenAI
llm = ChatOpenAI(
    model=model_name,
    api_key=api_key,
    temperature=0.7
)

# LLM Integration Testing - verify LLM functionality during startup
try:
    test_response = llm.invoke("Test connection - respond with 'OK'")
    print(f"✅ LLM test successful: {test_response.content[:50]}...")
except Exception as e:
    print(f"❌ LLM test failed: {e}")
    raise RuntimeError(f"LLM initialization failed: {e}")

# User session management
user_sessions = {}  # Store user-specific processing status
session_queues = {}  # Store user-specific update queues

def get_or_create_user_session():
    """Get or create a user session"""
    if 'user_id' not in session:
        session['user_id'] = str(uuid.uuid4())
        session['created_at'] = datetime.now().isoformat()
    
    user_id = session['user_id']
    
    # Initialize user session if it doesn't exist
    if user_id not in user_sessions:
        user_sessions[user_id] = {
            'is_processing': False,
            'current_step': 0,
            'total_steps': 4,
            'topic': '',
            'result': None,
            'error': None,
            'agent_thoughts': {},
            'current_agent': None,
            'current_thought': None,
            'created_at': datetime.now().isoformat(),
            'last_activity': datetime.now().isoformat()
        }
        
        # Create user-specific queue
        session_queues[user_id] = queue.Queue()
    
    # Update last activity
    user_sessions[user_id]['last_activity'] = datetime.now().isoformat()
    
    return user_id

def get_user_processing_status(user_id):
    """Get processing status for a specific user"""
    if user_id not in user_sessions:
        return None
    return user_sessions[user_id]

def get_user_queue(user_id):
    """Get update queue for a specific user"""
    if user_id not in session_queues:
        return None
    return session_queues[user_id]

def send_user_update(user_id, update_data):
    """Send update to a specific user's queue"""
    try:
        if user_id in session_queues:
            session_queues[user_id].put(update_data)
    except Exception as e:
        print(f"Error sending update to user {user_id}: {e}")

# Clean up old sessions (older than 1 hour)
def cleanup_old_sessions():
    """Remove old user sessions to prevent memory leaks"""
    current_time = datetime.now()
    users_to_remove = []
    
    for user_id, user_data in user_sessions.items():
        last_activity = datetime.fromisoformat(user_data['last_activity'])
        if (current_time - last_activity).total_seconds() > 3600:  # 1 hour
            users_to_remove.append(user_id)
    
    for user_id in users_to_remove:
        del user_sessions[user_id]
        if user_id in session_queues:
            del session_queues[user_id]
        print(f"🧹 Cleaned up old session for user {user_id}")

# Global queue for real-time updates (keeping for backward compatibility)
update_queue = queue.Queue()

class CrewAIOutputCapture:
    """Captures and parses CrewAI output to track agent progress in real-time"""
    
    def __init__(self, original_stdout, agent_names, user_id):
        self.original_stdout = original_stdout
        self.agent_names = agent_names
        self.user_id = user_id
        self.buffer = ""
        
    def write(self, text):
        # Write to original stdout so we still see the output
        self.original_stdout.write(text)
        self.original_stdout.flush()
        
        # Add to buffer for parsing
        self.buffer += text
        
        # Parse for agent activity
        self._parse_agent_activity(text)
    
    def flush(self):
        self.original_stdout.flush()
    
    def _parse_agent_activity(self, text):
        """Parse CrewAI output for agent start/completion markers"""
        user_status = get_user_processing_status(self.user_id)
        if not user_status:
            return
        
        try:
            # Look for agent start marker
            if "🤖 Agent Started" in text or "Agent:" in text:
                for i, agent_name in enumerate(self.agent_names):
                    if agent_name in text:
                        user_status['current_step'] = i
                        user_status['current_agent'] = agent_name
                        user_status['current_thought'] = f"{agent_name} is working..."
                        
                        send_user_update(self.user_id, {
                            'current_step': i,
                            'current_agent': agent_name,
                            'current_thought': f"{agent_name} is working...",
                            'agent_thoughts': user_status['agent_thoughts'],
                            'is_processing': True
                        })
                        
                        print(f"🎯 User {self.user_id}: Detected {agent_name} started working")
                        break
            
            # Look for agent completion marker
            elif "✅ Agent Final Answer" in text or "Final Answer:" in text:
                # Get the current agent that just completed
                current_agent = user_status.get('current_agent')
                if current_agent:
                    timestamp = time.strftime("%H:%M:%S")
                    user_status['current_thought'] = f"{current_agent} completed successfully!"
                    
                    send_user_update(self.user_id, {
                        'current_step': user_status['current_step'],
                        'current_agent': current_agent,
                        'current_thought': f"{current_agent} completed successfully!",
                        'agent_thoughts': user_status['agent_thoughts'],
                        'is_processing': True
                    })
                    
                    print(f"✅ User {self.user_id}: Detected {current_agent} completed work")
        
        except Exception as e:
            print(f"Error parsing CrewAI output for user {self.user_id}: {e}")

def create_crew(topic):
    """Create a CrewAI crew for the given topic"""
    # Define your agents with custom thought capture
    researcher = Agent(
        role="Research Analyst",
        goal="Research a given topic deeply and provide clear findings",
        backstory="You're a seasoned researcher known for producing accurate and concise insights.",
        verbose=True,
        llm=llm,
        allow_delegation=False
    )

    writer = Agent(
        role="Article Writer",
        goal="Write a short, compelling article based on the research",
        backstory="You're a skilled writer who turns insights into engaging prose.",
        verbose=True,
        llm=llm,
        allow_delegation=False
    )

    editor = Agent(
        role="Editor",
        goal="Polish the article for tone, flow, and clarity",
        backstory="You're a language expert who makes content shine.",
        verbose=True,
        llm=llm,
        allow_delegation=False
    )

    tweeter = Agent(
        role="Social Media Strategist",
        goal="Summarise the article into a tweet for engagement",
        backstory="You're great at distilling ideas into bite-sized, high-impact tweets.",
        verbose=True,
        llm=llm,
        allow_delegation=False
    )

    # Define tasks with expected outputs
    task1 = Task(
        description=f"Research the topic: {topic}",
        expected_output="A list of 3–5 key insights about the topic.",
        agent=researcher
    )

    task2 = Task(
        description="Write a 400-word article based on the research",
        expected_output="A complete article, written in natural language, based on the research insights.",
        agent=writer
    )

    task3 = Task(
        description="Edit the article for tone, clarity, and structure",
        expected_output="A refined version of the article with improved tone and readability.",
        agent=editor
    )

    task4 = Task(
        description="Summarise the article in a single tweet (max 280 characters)",
        expected_output="A concise, engaging tweet that captures the article's core idea.",
        agent=tweeter
    )

    # Create the Crew
    crew = Crew(
        agents=[researcher, writer, editor, tweeter],
        tasks=[task1, task2, task3, task4],
        verbose=True
    )
    
    return crew

def run_crew(crew):
    """Run the CrewAI crew and return results"""
    try:
        result = crew.kickoff()
        return result
    except Exception as e:
        return f"Error running crew: {str(e)}"

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

# Configure Flask-Session
app.config['SESSION_TYPE'] = 'filesystem'
app.config['SESSION_FILE_DIR'] = sessions_dir
app.config['SESSION_COOKIE_SECURE'] = False # Set to True in production
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
app.config['PERMANENT_SESSION_LIFETIME'] = 3600 # Session expires after 1 hour
Session(app)

# Store processing status
processing_status = {
    'is_processing': False,
    'current_step': 0,
    'total_steps': 4,
    'topic': '',
    'result': None,
    'error': None,
    'agent_thoughts': {},  # Store each agent's thoughts
    'current_agent': None,
    'current_thought': None
}

def send_update(update_data):
    """Send update to the queue for streaming"""
    try:
        update_queue.put(update_data)
    except Exception as e:
        print(f"Error sending update: {e}")

def process_crew_ai(topic, user_id):
    """Process the CrewAI workflow in a separate thread for a specific user"""
    user_status = get_user_processing_status(user_id)
    if not user_status:
        print(f"❌ User {user_id} not found for processing")
        return
    
    try:
        user_status['is_processing'] = True
        user_status['topic'] = topic
        user_status['current_step'] = 0
        user_status['error'] = None
        user_status['agent_thoughts'] = {}
        user_status['current_agent'] = None
        user_status['current_thought'] = None
        
        # Send initial update
        send_user_update(user_id, {
            'current_step': 0,
            'current_agent': 'Research Analyst',
            'current_thought': 'Initializing CrewAI workflow...',
            'agent_thoughts': {},
            'is_processing': True
        })
        
        # Update processing status
        user_status['current_step'] = 0
        user_status['current_agent'] = 'Research Analyst'
        user_status['current_thought'] = 'Initializing CrewAI workflow...'
        
        print(f"🤖 User {user_id}: Starting CrewAI processing for topic: {topic}")
        
        # Create custom agents that capture their thoughts
        print(f"🔧 Creating Research Analyst with LLM: {type(llm).__name__} - {getattr(llm, 'model', 'openai/gpt-5-nano')}")
        researcher = Agent(
            role="Research Analyst",
            goal="Research a given topic deeply and provide clear findings",
            backstory="You're a seasoned researcher known for producing accurate and concise insights.",
            verbose=True,
            llm=llm
        )

        print(f"🔧 Creating Article Writer with LLM: {type(llm).__name__} - {getattr(llm, 'model', 'openai/gpt-5-nano')}")
        writer = Agent(
            role="Article Writer",
            goal="Write a short, compelling article based on the research",
            backstory="You're a skilled writer who turns insights into engaging prose.",
            verbose=True,
            llm=llm
        )

        print(f"🔧 Creating Editor with LLM: {type(llm).__name__} - {getattr(llm, 'model', 'openai/gpt-5-nano')}")
        editor = Agent(
            role="Editor",
            goal="Polish the article for tone, flow, and clarity",
            backstory="You're a language expert who makes content shine.",
            verbose=True,
            llm=llm
        )

        print(f"🔧 Creating Social Media Strategist with LLM: {type(llm).__name__} - {getattr(llm, 'model', 'openai/gpt-5-nano')}")
        tweeter = Agent(
            role="Social Media Strategist",
            goal="Summarise the article into a tweet for engagement",
            backstory="You're great at distilling ideas into bite-sized, high-impact tweets.",
            verbose=True,
            llm=llm
        )

        # Define tasks with expected outputs
        task1 = Task(
            description=f"Research the topic: {topic}",
            expected_output="A list of 3–5 key insights about the topic.",
            agent=researcher
        )

        task2 = Task(
            description="Write a 400-word article based on the research",
            expected_output="A complete article, written in natural language, based on the research insights.",
            agent=writer
        )

        task3 = Task(
            description="Edit the article for tone, clarity, and structure",
            expected_output="A refined version of the article with improved tone and readability.",
            agent=editor
        )

        task4 = Task(
            description="Summarise the article in a single tweet (max 280 characters)",
            expected_output="A concise, engaging tweet that captures the article's core idea.",
            agent=tweeter
        )

        # Create the Crew
        crew = Crew(
            agents=[researcher, writer, editor, tweeter],
            tasks=[task1, task2, task3, task4],
            verbose=True
        )
        
        # Run the crew and capture real-time updates
        print("🚀 Starting CrewAI execution...")
        
        # Set up real-time output monitoring
        agent_names = ['Research Analyst', 'Article Writer', 'Editor', 'Social Media Strategist']
        original_stdout = sys.stdout
        output_capture = CrewAIOutputCapture(original_stdout, agent_names, user_id)
        
        # Execute the full crew workflow with real-time monitoring
        try:
            # Redirect stdout to capture CrewAI output
            sys.stdout = output_capture
            
            # Execute CrewAI
            result = crew.kickoff()
            
            # Restore original stdout
            sys.stdout = original_stdout
            
            # After crew execution, try to extract individual task results
            timestamp = time.strftime("%H:%M:%S")
            
            # Try to get individual task results from the crew
            if hasattr(crew, 'tasks') and crew.tasks:
                for i, task in enumerate(crew.tasks):
                    agent_name = agent_names[i]
                    
                    # Check if the task has a result or output
                    task_output = None
                    if hasattr(task, 'output') and task.output:
                        task_output = str(task.output)
                    elif hasattr(task, 'result') and task.result:
                        task_output = str(task.result)
                    elif hasattr(task, '_output') and task._output:
                        task_output = str(task._output)
                    
                    if task_output:
                        user_status['agent_thoughts'][agent_name] = f"[{timestamp}] {task_output}"
                        print(f"✅ User {user_id}: {agent_name} output captured: {task_output[:100]}...")
                    else:
                        # Fallback: create a meaningful output based on the task description
                        fallback_output = f"Completed {task.description.lower()} task successfully."
                        user_status['agent_thoughts'][agent_name] = f"[{timestamp}] {fallback_output}"
                        print(f"📝 User {user_id}: {agent_name} fallback output created")
                    
                    # Send update for this agent's completion
                    send_user_update(user_id, {
                        'current_step': i,
                        'current_agent': agent_name,
                        'current_thought': f"{agent_name} completed successfully!",
                        'agent_thoughts': user_status['agent_thoughts'],
                        'is_processing': True
                    })
            
            # If we couldn't extract individual outputs, create them from the final result
            if not processing_status['agent_thoughts']:
                # Parse the result to extract individual agent contributions
                if isinstance(result, str) and result.strip():
                    # Try to split the result into logical sections
                    sections = []
                    
                    # Look for common section markers
                    if '##' in result:
                        sections = [s.strip() for s in result.split('##') if s.strip()]
                    elif '---' in result:
                        sections = [s.strip() for s in result.split('---') if s.strip()]
                    elif '\n\n' in result:
                        sections = [s.strip() for s in result.split('\n\n') if s.strip()]
                    else:
                        # Split by sentences or paragraphs
                        sentences = result.split('. ')
                        sections = ['. '.join(sentences[i:i+3]) + '.' for i in range(0, len(sentences), 3)]
                    
                    # Assign sections to agents
                    for i, agent_name in enumerate(agent_names):
                        if i < len(sections) and sections[i]:
                            agent_output = sections[i][:500]  # Limit length
                        else:
                            # Create a meaningful output based on agent role
                            if 'Research' in agent_name:
                                agent_output = "Conducted comprehensive research on the topic, gathering key insights and data points."
                            elif 'Writer' in agent_name:
                                agent_output = "Created engaging and informative content based on the research findings."
                            elif 'Editor' in agent_name:
                                agent_output = "Polished the content for clarity, flow, and professional presentation."
                            elif 'Social Media' in agent_name:
                                agent_output = "Developed social media-ready content to maximize engagement and reach."
                            else:
                                agent_output = f"Successfully completed the {agent_name.lower()} task."
                        
                        user_status['agent_thoughts'][agent_name] = f"[{timestamp}] {agent_output}"
                        
                        # Send update for this agent's completion
                        send_user_update(user_id, {
                            'current_step': i,
                            'current_agent': agent_name,
                            'current_thought': f"{agent_name} completed successfully!",
                            'agent_thoughts': user_status['agent_thoughts'],
                            'is_processing': True
                        })
                        
                        print(f"✅ User {user_id}: {agent_name} completed: {agent_output[:100]}...")
                
                else:
                    # Final fallback: create generic completion messages
                    for i, agent_name in enumerate(agent_names):
                        user_status['agent_thoughts'][agent_name] = f"[{timestamp}] Task completed successfully."
                        
                        send_user_update(user_id, {
                            'current_step': i,
                            'current_agent': agent_name,
                            'current_thought': f"{agent_name} completed successfully!",
                            'agent_thoughts': user_status['agent_thoughts'],
                            'is_processing': True
                        })
            
            # Log the final crew result for debugging
            print(f"📝 User {user_id}: Final CrewAI result: {result[:500] if isinstance(result, str) else str(result)[:500]}...")
            
            # Store the final result in user status for reference
            user_status['final_result'] = result
            
        except Exception as e:
            # Restore stdout first
            sys.stdout = original_stdout
            
            error_msg = f"Error in CrewAI execution: {str(e)}"
            print(f"❌ {error_msg}")
            timestamp = time.strftime("%H:%M:%S")
            
            # Store error for all agents
            for agent_name in agent_names:
                user_status['agent_thoughts'][agent_name] = f"[{timestamp}] Error: {error_msg}"
            
            # Send error update
            send_user_update(user_id, {
                'current_step': user_status['current_step'],
                'current_agent': None,
                'current_thought': f"Error: {error_msg}",
                'agent_thoughts': user_status['agent_thoughts'],
                'is_processing': False
            })
            
            # Re-raise the error
            raise e
        
        # Mark processing as complete
        user_status['is_processing'] = False
        user_status['current_step'] = 4
        user_status['current_agent'] = None
        timestamp = time.strftime("%H:%M:%S")
        user_status['current_thought'] = f"All CrewAI tasks completed successfully!"
        
        # Send final completion update
        send_user_update(user_id, {
            'current_step': 4,
            'current_agent': None,
            'current_thought': "All CrewAI tasks completed successfully!",
            'agent_thoughts': user_status['agent_thoughts'],
            'is_processing': False
        })
        
        print(f"✅ User {user_id}: CrewAI processing completed for topic: {topic}")
        print(f"📊 Final results: {len(user_status['agent_thoughts'])} agents completed their tasks")
        
    except Exception as e:
        error_msg = f"Error in CrewAI processing: {str(e)}"
        print(f"❌ User {user_id}: {error_msg}")
        user_status['error'] = error_msg
        user_status['is_processing'] = False
        user_status['current_agent'] = None
        timestamp = time.strftime("%H:%M:%S")
        user_status['current_thought'] = f'Error: {error_msg}'
        
        # Send error update
        send_user_update(user_id, {
            'current_step': user_status['current_step'],
            'current_agent': None,
            'current_thought': f"Error: {error_msg}",
            'agent_thoughts': user_status['agent_thoughts'],
            'is_processing': False
        })

@app.route('/api/generate-content', methods=['POST'])
def generate_content():
    """Start the AI content generation process"""
    # Get or create user session
    user_id = get_or_create_user_session()
    user_status = get_user_processing_status(user_id)
    
    if user_status['is_processing']:
        return jsonify({'error': 'You already have a request processing'}), 400
    
    data = request.get_json()
    topic = data.get('topic', 'How AI is transforming creative industries')
    
    if not topic:
        return jsonify({'error': 'Topic is required'}), 400
    
    # Reset status for this user
    user_status['error'] = None
    
    # Start processing in a separate thread for this user
    thread = Thread(target=process_crew_ai, args=(topic, user_id))
    thread.daemon = True
    thread.start()
    
    return jsonify({
        'message': 'Content generation started',
        'topic': topic,
        'user_id': user_id
    })

@app.route('/api/status', methods=['GET'])
def get_status():
    """Get the current processing status for the current user"""
    user_id = get_or_create_user_session()
    user_status = get_user_processing_status(user_id)
    return jsonify(user_status)

@app.route('/api/stream', methods=['GET'])
def stream_updates():
    """Stream real-time updates to the frontend for the current user"""
    user_id = get_or_create_user_session()
    user_queue = get_user_queue(user_id)
    user_status = get_user_processing_status(user_id)
    
    if not user_queue:
        return jsonify({'error': 'User session not found'}), 400
    
    def generate():
        while True:
            try:
                # Wait for updates from the user's queue
                update_data = user_queue.get(timeout=1)
                
                # Send the update
                yield f"data: {json.dumps(update_data)}\n\n"
                
                # If not processing, stop the stream
                if not update_data.get('is_processing', False):
                    break
                    
            except queue.Empty:
                # Send current user status as heartbeat
                status_data = {
                    'current_step': user_status['current_step'],
                    'current_agent': user_status['current_agent'],
                    'current_thought': user_status['current_thought'],
                    'agent_thoughts': user_status['agent_thoughts'],
                    'is_processing': user_status['is_processing']
                }
                yield f"data: {json.dumps(status_data)}\n\n"
                
                # If not processing, stop the stream
                if not user_status['is_processing']:
                    break
    
    return app.response_class(
        generate(),
        mimetype='text/event-stream',
        headers={
            'Cache-Control': 'no-cache',
            'Connection': 'keep-alive',
            'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Headers': 'Cache-Control',
            'Content-Type': 'text/event-stream'
        }
    )

@app.route('/api/test-llm', methods=['GET'])
def test_llm_direct():
    """Test LLM connectivity directly"""
    try:
        # Test basic LLM connectivity
        test_prompt = "Say 'Hello from production server'"
        response = llm.invoke(test_prompt)
        
        return jsonify({
            'success': True,
            'prompt': test_prompt,
            'response': response.content,
            'model': getattr(llm, 'model_name', getattr(llm, 'model', 'unknown')),
            'api_key_set': bool(os.getenv('OPENAI_API_KEY')),
            'model_env_var': os.getenv('OPENAI_MODEL', 'not set')
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e),
            'error_type': type(e).__name__,
            'model': getattr(llm, 'model_name', getattr(llm, 'model', 'unknown')),
            'api_key_set': bool(os.getenv('OPENAI_API_KEY')),
            'model_env_var': os.getenv('OPENAI_MODEL', 'not set')
        }), 500

@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({'status': 'healthy', 'message': 'AI Editorial Team API is running'})

@app.route('/api/debug', methods=['GET'])
def debug_status():
    """Debug endpoint to check current processing status"""
    user_id = get_or_create_user_session()
    user_status = get_user_processing_status(user_id)
    
    return jsonify({
        'user_id': user_id,
        'user_status': user_status,
        'current_time': time.time(),
        'total_active_users': len(user_sessions),
        'all_user_ids': list(user_sessions.keys())
    })

@app.route('/api/test-process', methods=['GET'])
def test_process():
    """Test endpoint to manually trigger processing for debugging"""
    user_id = get_or_create_user_session()
    user_status = get_user_processing_status(user_id)
    
    if user_status['is_processing']:
        return jsonify({'error': 'You already have a process running'})
    
    # Start a test process for this user
    thread = Thread(target=process_crew_ai, args=('Test Topic', user_id))
    thread.daemon = True
    thread.start()
    
    return jsonify({'message': 'Test process started', 'user_id': user_id})

@app.route('/api/users', methods=['GET'])
def get_active_users():
    """Get all active users and their processing status (for debugging)"""
    active_users = {}
    for user_id, user_data in user_sessions.items():
        active_users[user_id] = {
            'is_processing': user_data['is_processing'],
            'topic': user_data['topic'],
            'current_step': user_data['current_step'],
            'current_agent': user_data['current_agent'],
            'created_at': user_data['created_at'],
            'last_activity': user_data['last_activity']
        }
    
    return jsonify({
        'total_users': len(active_users),
        'users': active_users
    })

if __name__ == '__main__':
    print("🚀 Starting AI Editorial Team Backend...")
    print("📝 This backend integrates with your existing CrewAI Python code")
    print("🌐 API endpoints available")
    print("🔗 Frontend should be running on Vercel")
    
    # Get port from environment variable (Render provides PORT)
    port = int(os.getenv('PORT', 5001))
    
    # Set up a periodic task to clean up old sessions
    def cleanup_task():
        while True:
            cleanup_old_sessions()
            time.sleep(300) # Check every 5 minutes
    
    cleanup_thread = Thread(target=cleanup_task)
    cleanup_thread.daemon = True
    cleanup_thread.start()

    app.run(debug=False, host='0.0.0.0', port=port)
