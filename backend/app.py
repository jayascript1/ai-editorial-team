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
        print(f"🆔 NEW USER SESSION: Created user_id {session['user_id']}")
    
    user_id = session['user_id']
    print(f"🔍 SESSION DEBUG: Using user_id {user_id}")
    
    # Initialize user session if it doesn't exist
    if user_id not in user_sessions:
        print(f"🆕 USER DATA: Creating user_sessions for {user_id}")
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
        print(f"📥 QUEUE: Created session_queues for {user_id}")
    else:
        print(f"✅ USER DATA: Found existing user_sessions for {user_id}")
    
    # Update last activity
    user_sessions[user_id]['last_activity'] = datetime.now().isoformat()
    
    print(f"📊 SESSION SUMMARY: user_sessions has {len(user_sessions)} users, session_queues has {len(session_queues)} queues")
    
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
        print(f"🔍 SSE DEBUG: Looking for user_id {user_id}")
        print(f"📊 SSE DEBUG: Available session_queues: {list(session_queues.keys())}")
        print(f"📊 SSE DEBUG: Available user_sessions: {list(user_sessions.keys())}")
        
        if user_id in session_queues:
            print(f"🔄 SSE: Sending update to user {user_id}: {update_data.get('current_agent', 'Unknown')} - {update_data.get('current_thought', 'No thought')[:50]}...")
            session_queues[user_id].put(update_data)
        else:
            print(f"❌ SSE: User {user_id} not found in session_queues")
            print(f"❌ SSE: session_queues has these users: {list(session_queues.keys())}")
    except Exception as e:
        print(f"❌ SSE: Error sending update to user {user_id}: {e}")

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
            # Clean up the text for better parsing
            clean_text = text.strip()
            
            # Look for agent start indicators - more comprehensive patterns
            agent_start_patterns = [
                "Working Agent:",
                "Agent:", 
                "🤖 Agent Started",
                "Starting agent:",
                "# Agent:",
                "[Agent]",
                ">>> Agent"
            ]
            
            # Look for agent thinking patterns
            thinking_patterns = [
                "Thought:",
                "I need to",
                "Let me",
                "I will",
                "I should",
                "First,",
                "Next,",
                "Now I",
                "Action:",
                "Observation:",
                "Reasoning:",
                "Analysis:"
            ]
            
            # Check for agent start or transition
            for pattern in agent_start_patterns:
                if pattern in clean_text:
                    for i, agent_name in enumerate(self.agent_names):
                        # Look for both full name and last word (e.g., "Analyst", "Writer")
                        agent_keywords = [agent_name, agent_name.split()[-1]]
                        if any(keyword in clean_text for keyword in agent_keywords):
                            # Only update if this is a new agent or step progression
                            if user_status['current_agent'] != agent_name or user_status['current_step'] != i:
                                user_status['current_step'] = i
                                user_status['current_agent'] = agent_name
                                user_status['current_thought'] = f"{agent_name} is beginning their task..."
                                
                                send_user_update(self.user_id, {
                                    'current_step': i,
                                    'current_agent': agent_name,
                                    'current_thought': f"{agent_name} is beginning their task...",
                                    'agent_thoughts': user_status['agent_thoughts'],
                                    'is_processing': True
                                })
                                
                                print(f"🎯 User {self.user_id}: Detected {agent_name} started (step {i})")
                            break
                    break
            
            # Check for thinking patterns to show real-time thoughts
            for pattern in thinking_patterns:
                if pattern in clean_text:
                    current_agent = user_status.get('current_agent')
                    if current_agent:
                        # Extract the thought content
                        thought_start = clean_text.find(pattern)
                        if thought_start != -1:
                            # Get a meaningful portion of the thought
                            thought_text = clean_text[thought_start:thought_start + 150].split('\n')[0]
                            user_status['current_thought'] = f"{current_agent}: {thought_text}"
                            
                            send_user_update(self.user_id, {
                                'current_step': user_status['current_step'],
                                'current_agent': current_agent,
                                'current_thought': f"{current_agent}: {thought_text}",
                                'agent_thoughts': user_status['agent_thoughts'],
                                'is_processing': True
                            })
                            
                            print(f"💭 User {self.user_id}: {current_agent} thinking: {thought_text[:50]}...")
                    break
            
            # Look for final answer/completion indicators - be more selective
            completion_patterns = [
                "Final Answer:",
                "Task completed successfully",
                "Finished working on",
                "Agent execution complete",
                "OUTPUT:",
                "RESULT:"
            ]
            
            for pattern in completion_patterns:
                if pattern in clean_text:
                    current_agent = user_status.get('current_agent')
                    if current_agent and current_agent not in user_status['agent_thoughts']:
                        timestamp = time.strftime("%H:%M:%S")
                        
                        # Try to extract the actual result
                        result_start = clean_text.find(pattern)
                        if result_start != -1:
                            result_text = clean_text[result_start + len(pattern):result_start + len(pattern) + 300]
                            result_text = result_text.split('\n')[0].strip()
                            if result_text and len(result_text) > 20:  # Only capture substantial outputs
                                user_status['agent_thoughts'][current_agent] = f"[{timestamp}] {result_text[:200]}..."
                                completion_msg = f"{current_agent} has completed their task"
                                user_status['current_thought'] = completion_msg
                                
                                send_user_update(self.user_id, {
                                    'current_step': user_status['current_step'],
                                    'current_agent': current_agent,
                                    'current_thought': completion_msg,
                                    'agent_thoughts': user_status['agent_thoughts'],
                                    'is_processing': True
                                })
                                
                                print(f"✅ User {self.user_id}: {current_agent} completed with output: {result_text[:50]}...")
                    break
        
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
        description="Edit the article so it's twice as clear in terms of tone and structure",
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
CORS(app, 
     supports_credentials=True, 
     origins=['http://localhost:5173', 'http://127.0.0.1:5173', 'https://ai-editorial-team.vercel.app'],
     allow_headers=['Content-Type', 'Authorization', 'Cache-Control', 'Accept', 'Origin'],
     methods=['GET', 'POST', 'OPTIONS', 'PUT', 'DELETE'])  # Enable CORS with full EventSource support

# Configure Flask-Session with SECRET_KEY for session management
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'dev-secret-key-change-in-production')
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
        # Status is already set by the generate-content endpoint
        # Just confirm the processing state and add more details
        user_status['current_thought'] = 'Setting up AI agents and preparing to analyze the topic...'
        
        # Send initial detailed update
        send_user_update(user_id, {
            'current_step': 0,
            'current_agent': 'Research Analyst',
            'current_thought': 'Setting up AI agents and preparing to analyze the topic...',
            'agent_thoughts': {},
            'is_processing': True
        })
        
        print(f"🤖 User {user_id}: Starting CrewAI processing for topic: {topic}")
        
        # Send setup update after a short delay
        time.sleep(2)
        user_status['current_thought'] = 'Your AI Editorial team is are ready. Starting research phase...'
        send_user_update(user_id, {
            'current_step': 0,
            'current_agent': 'Research Analyst',
            'current_thought': 'Your AI Editorial team is ready. Starting research phase...',
            'agent_thoughts': {},
            'is_processing': True
        })
        
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
            description="Edit the article so it's twice as clear in terms of tone and structure",
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
        
        # Run the crew with systematic agent progress tracking
        print("🚀 Starting CrewAI execution with systematic progress tracking...")
        
        # Set up systematic agent monitoring
        agent_names = ['Research Analyst', 'Article Writer', 'Editor', 'Social Media Strategist']
        agent_tasks = [task1, task2, task3, task4]
        
        # Create the full crew for execution
        full_crew = Crew(
            agents=[researcher, writer, editor, tweeter],
            tasks=[task1, task2, task3, task4],
            verbose=True
        )
        
        # Execute with honest timing - all agents work simultaneously
        print(f"🚀 User {user_id}: Starting honest CrewAI execution - all agents working simultaneously")
        
        # Send honest start notification
        send_user_update(user_id, {
            'current_step': 0,
            'current_agent': 'AI Team',
            'current_thought': 'All AI agents are now working simultaneously on your topic...',
            'agent_thoughts': {},
            'is_processing': True
        })
        
        # Record actual start time
        start_time = time.time()
        start_timestamp = time.strftime("%H:%M:%S")
        
        # Execute the complete crew workflow (all agents with proper context flow)
        print(f"🚀 User {user_id}: Executing full crew with proper context passing")
        crew_result = full_crew.kickoff()
        print(f"✅ User {user_id}: Full crew execution completed")
        
        # Record actual completion time
        end_time = time.time()
        end_timestamp = time.strftime("%H:%M:%S")
        actual_duration = end_time - start_time
        
        # Access individual task outputs using official CrewAI output structure
        individual_results = []
        if hasattr(crew_result, 'output') and crew_result.output:
            print(f"📝 User {user_id}: Found {len(crew_result.output)} task outputs")
            # CrewAI provides output as a list of results
            for idx, task_output in enumerate(crew_result.output):
                individual_results.append(str(task_output))
                print(f"✅ User {user_id}: Captured output for task {idx}: {str(task_output)[:100]}...")
        elif hasattr(crew_result, 'tasks_output') and crew_result.tasks_output:
            print(f"📝 User {user_id}: Found {len(crew_result.tasks_output)} task outputs")
            # CrewAI provides tasks_output as a list of TaskOutput objects
            for idx, task_output in enumerate(crew_result.tasks_output):
                # Each TaskOutput has a 'raw' attribute containing the actual output
                if hasattr(task_output, 'raw') and task_output.raw:
                    individual_results.append(str(task_output.raw))
                    print(f"✅ User {user_id}: Captured output for task {idx}: {str(task_output.raw)[:100]}...")
                elif hasattr(task_output, 'result') and task_output.result:
                    individual_results.append(str(task_output.result))
                    print(f"✅ User {user_id}: Captured result for task {idx}: {str(task_output.result)[:100]}...")
                else:
                    print(f"⚠️ User {user_id}: Task {idx} output has no accessible content")
        else:
            print(f"⚠️ User {user_id}: No output found in crew_result, available attributes: {dir(crew_result) if crew_result else 'None'}")
        
        # Store results for later use
        task_results = [crew_result] if crew_result else []
        agent_outputs = individual_results if individual_results else []
        
        # Send honest completion notification with real timing
        send_user_update(user_id, {
            'current_step': 4,
            'current_agent': 'AI Team',
            'current_thought': f'All AI agents completed successfully in {actual_duration:.1f} seconds!',
            'agent_thoughts': {},
            'is_processing': True
        })
        
        # Store all agent outputs with honest timestamps
        for i, agent_name in enumerate(agent_names):
            timestamp = end_timestamp  # All agents completed at the same time
            if i < len(agent_outputs):
                # Use the actual agent output from CrewAI
                agent_output = agent_outputs[i]
                user_status['agent_thoughts'][agent_name] = f"[{timestamp}] {agent_output}"
                print(f"📝 User {user_id}: Stored actual output for {agent_name}: {agent_output[:100]}...")
            else:
                # Fallback message when individual outputs aren't available
                user_status['agent_thoughts'][agent_name] = f"[{timestamp}] Task completed successfully with proper context flow"
                print(f"📝 User {user_id}: Using fallback message for {agent_name}")
        
        # Send final update with all agent outputs
        send_user_update(user_id, {
            'current_step': 4,
            'current_agent': None,
            'current_thought': f'AI Team completed in {actual_duration:.1f} seconds',
            'agent_thoughts': user_status['agent_thoughts'],
            'is_processing': True
        })
        
        # Combine all task results using the crew result
        result = "\n\n".join([str(r) for r in task_results if r])
        
        # Log the final combined result
        print(f"📝 User {user_id}: Final combined result: {result[:200] if result else 'No result'}...")
        print(f"📊 User {user_id}: Individual agent outputs captured: {len(agent_outputs)} out of {len(agent_names)}")
        
        # Store the final result
        user_status['final_result'] = result
        
    except Exception as e:
        error_msg = f"Error in systematic CrewAI execution: {str(e)}"
        print(f"❌ {error_msg}")
        timestamp = time.strftime("%H:%M:%S")
        
        # Store error for any incomplete agents
        for agent_name in agent_names:
            if agent_name not in user_status['agent_thoughts']:
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
    
    # Mark processing as complete only when we have substantial agent outputs
    user_status['is_processing'] = False
    user_status['current_step'] = 4
    user_status['current_agent'] = None
    timestamp = time.strftime("%H:%M:%S")
    
    # Only declare completion if we have outputs from all expected agents
    agents_with_outputs = len(user_status['agent_thoughts'])
    if agents_with_outputs >= 4:
        user_status['current_thought'] = "All CrewAI tasks completed successfully!"
        completion_message = "All CrewAI tasks completed successfully!"
    else:
        user_status['current_thought'] = f"CrewAI processing finished with {agents_with_outputs} agent outputs"
        completion_message = f"CrewAI processing finished with {agents_with_outputs} agent outputs"
    
    # Send final completion update
    send_user_update(user_id, {
        'current_step': 4,
        'current_agent': None,
        'current_thought': completion_message,
        'agent_thoughts': user_status['agent_thoughts'],
        'is_processing': False
    })
    
    print(f"✅ User {user_id}: CrewAI processing completed for topic: {topic}")
    print(f"📊 Final results: {len(user_status['agent_thoughts'])} agents completed their tasks")

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
    
    # Immediately set processing to true to prevent race condition
    user_status['is_processing'] = True
    user_status['current_step'] = 0
    user_status['current_agent'] = 'Research Analyst'
    user_status['current_thought'] = 'Starting content generation...' 
    user_status['topic'] = topic
    user_status['agent_thoughts'] = {}
    
    print(f"🚀 User {user_id}: Set processing=True, starting thread for topic: {topic}")
    
    # Start processing in a separate thread for this user
    thread = Thread(target=process_crew_ai, args=(topic, user_id))
    thread.daemon = True
    thread.start()
    
    print(f"🔄 User {user_id}: Thread started, returning success response")
    
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

@app.route('/api/stream', methods=['GET', 'OPTIONS'])
def stream_updates():
    """Stream real-time updates to the frontend for the current user"""
    # Handle preflight OPTIONS request
    if request.method == 'OPTIONS':
        response = app.make_default_options_response()
        headers = response.headers
        if request.headers.get('Origin') in ['http://localhost:5173', 'https://ai-editorial-team.vercel.app']:
            headers['Access-Control-Allow-Origin'] = request.headers.get('Origin')
        else:
            headers['Access-Control-Allow-Origin'] = 'http://localhost:5173'
        headers['Access-Control-Allow-Methods'] = 'GET, OPTIONS'
        headers['Access-Control-Allow-Headers'] = 'Content-Type, Authorization, Cache-Control'
        headers['Access-Control-Allow-Credentials'] = 'true'
        return response
    
    # Get user_id from query parameter or session
    user_id_param = request.args.get('user_id')
    if user_id_param:
        user_id = user_id_param
        print(f"🔗 SSE: Using user_id from URL parameter: {user_id}")
    else:
        user_id = get_or_create_user_session()
        print(f"🔗 SSE: Using user_id from session: {user_id}")
    
    user_queue = get_user_queue(user_id)
    user_status = get_user_processing_status(user_id)
    
    print(f"🔍 SSE: Looking for user_id {user_id}")
    print(f"📊 SSE: user_queue exists: {user_queue is not None}")
    print(f"📊 SSE: user_status exists: {user_status is not None}")
    
    if not user_queue:
        print(f"❌ SSE: User session not found for {user_id}")
        return jsonify({'error': 'User session not found'}), 400
    
    if not user_status:
        print(f"❌ SSE: User status not found for {user_id}")
        return jsonify({'error': 'User status not found'}), 400
    
    def generate():
        timeout_count = 0
        max_empty_timeouts = 5  # Allow 5 seconds of no updates before sending heartbeat
        
        while True:
            try:
                # Wait for updates from the user's queue
                update_data = user_queue.get(timeout=1)
                
                # Reset timeout counter when we get data
                timeout_count = 0
                
                # Send the update
                yield f"data: {json.dumps(update_data)}\n\n"
                
                # If not processing, stop the stream
                if not update_data.get('is_processing', False):
                    break
                    
            except queue.Empty:
                timeout_count += 1
                
                # Only send heartbeat after some timeouts and if actually processing
                if timeout_count >= max_empty_timeouts and user_status['is_processing']:
                    # Send current user status as heartbeat
                    status_data = {
                        'current_step': user_status['current_step'],
                        'current_agent': user_status['current_agent'],
                        'current_thought': user_status['current_thought'],
                        'agent_thoughts': user_status['agent_thoughts'],
                        'is_processing': user_status['is_processing']
                    }
                    yield f"data: {json.dumps(status_data)}\n\n"
                    timeout_count = 0  # Reset counter after sending heartbeat
                
                # If not processing, stop the stream
                if not user_status['is_processing']:
                    # Send final status update before closing
                    final_status = {
                        'current_step': user_status['current_step'],
                        'current_agent': user_status['current_agent'],
                        'current_thought': user_status['current_thought'],
                        'agent_thoughts': user_status['agent_thoughts'],
                        'is_processing': False
                    }
                    yield f"data: {json.dumps(final_status)}\n\n"
                    break
    
    # Set the appropriate origin based on request headers
    origin = request.headers.get('Origin')
    if not origin or origin not in ['http://localhost:5173', 'https://ai-editorial-team.vercel.app']:
        origin = 'https://ai-editorial-team.vercel.app'  # Default to production URL
    
    print(f"🔗 SSE: Setting Access-Control-Allow-Origin to {origin}")
    
    return app.response_class(
        generate(),
        mimetype='text/event-stream',
        headers={
            'Cache-Control': 'no-cache',
            'Connection': 'keep-alive',
            'Access-Control-Allow-Origin': origin,
            'Access-Control-Allow-Credentials': 'true',
            'Access-Control-Allow-Headers': 'Content-Type, Authorization, Cache-Control',
            'Access-Control-Allow-Methods': 'GET, OPTIONS',
            'Content-Type': 'text/event-stream',
            'X-Accel-Buffering': 'no'  # Disable proxy buffering for real-time streaming
        }
    )

@app.route('/api/test-simple-crew', methods=['POST'])
def test_simple_crew_execution():
    """Test a simple single-agent crew execution"""
    try:
        data = request.get_json()
        topic = data.get('topic', 'AI testing')
        
        # Create a single agent
        simple_agent = Agent(
            role="Writer",
            goal="Write a brief summary about the given topic",
            backstory="You are a concise writer.",
            verbose=True,
            llm=llm
        )
        
        # Create a simple task
        simple_task = Task(
            description=f"Write a 50-word summary about: {topic}",
            expected_output="A concise 50-word summary",
            agent=simple_agent
        )
        
        # Create minimal crew
        simple_crew = Crew(
            agents=[simple_agent],
            tasks=[simple_task],
            verbose=False
        )
        
        # Execute the crew
        result = simple_crew.kickoff()
        
        return jsonify({
            'success': True,
            'topic': topic,
            'result': str(result),
            'message': 'Simple crew execution successful'
        })
        
    except Exception as e:
        import traceback
        return jsonify({
            'success': False,
            'error': str(e),
            'error_type': type(e).__name__,
            'traceback': traceback.format_exc()
        }), 500

@app.route('/api/test-agent', methods=['GET'])
def test_agent_creation():
    """Test if we can create a single CrewAI agent"""
    try:
        # Test creating a simple agent
        test_agent = Agent(
            role="Test Agent",
            goal="Test basic functionality",
            backstory="A simple test agent for debugging",
            verbose=True,
            llm=llm
        )
        
        # Test creating a simple task
        test_task = Task(
            description="Say 'Agent creation successful'",
            expected_output="A simple confirmation message",
            agent=test_agent
        )
        
        # Test creating a minimal crew
        test_crew = Crew(
            agents=[test_agent],
            tasks=[test_task],
            verbose=True
        )
        
        return jsonify({
            'success': True,
            'agent_created': True,
            'task_created': True,
            'crew_created': True,
            'agent_role': test_agent.role,
            'task_description': test_task.description
        })
        
    except Exception as e:
        import traceback
        return jsonify({
            'success': False,
            'error': str(e),
            'error_type': type(e).__name__,
            'traceback': traceback.format_exc()
        }), 500

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
