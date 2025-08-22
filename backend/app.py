from flask import Flask, request, jsonify
from flask_cors import CORS
import os
import sys
import asyncio
from threading import Thread
import time
import json
import queue

# Add the parent directory to the path to import main.py
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import your existing CrewAI code
from langchain_openai import ChatOpenAI
from dotenv import load_dotenv

# Import CrewAI after environment setup
from crewai import Agent, Task, Crew

# Load environment variables
load_dotenv()
os.environ["OPENAI_API_KEY"] = os.getenv("OPENAI_API_KEY")

# Create a custom LLM class that forces temperature to 1 and removes unsupported parameters
class FixedTemperatureLLM(ChatOpenAI):
    def __init__(self, **kwargs):
        # Force temperature to 1 for gpt-4o-mini compatibility
        kwargs['temperature'] = 1
        
        # Remove unsupported parameters for gpt-4o-mini
        kwargs.pop('stop', None)
        kwargs.pop('max_tokens', None)
        kwargs.pop('top_p', None)
        kwargs.pop('frequency_penalty', None)
        kwargs.pop('presence_penalty', None)
        
        super().__init__(**kwargs)
    
    def _get_invocation_params(self, **kwargs):
        """Override to remove unsupported parameters from all calls"""
        params = super()._get_invocation_params(**kwargs)
        
        # Remove unsupported parameters that might be passed by CrewAI
        params.pop('stop', None)
        params.pop('max_tokens', None)
        params.pop('top_p', None)
        params.pop('frequency_penalty', None)
        params.pop('presence_penalty', None)
        
        return params
    
    def invoke(self, messages, **kwargs):
        """Override invoke to filter parameters"""
        # Remove unsupported parameters
        kwargs.pop('stop', None)
        kwargs.pop('max_tokens', None)
        kwargs.pop('top_p', None)
        kwargs.pop('frequency_penalty', None)
        kwargs.pop('presence_penalty', None)
        
        return super().invoke(messages, **kwargs)
    
    def ainvoke(self, messages, **kwargs):
        """Override ainvoke to filter parameters"""
        # Remove unsupported parameters
        kwargs.pop('stop', None)
        kwargs.pop('max_tokens', None)
        kwargs.pop('top_p', None)
        kwargs.pop('frequency_penalty', None)
        kwargs.pop('presence_penalty', None)
        
        return super().ainvoke(messages, **kwargs)
    
    def _call(self, messages, stop=None, **kwargs):
        """Override _call to filter parameters (older LangChain interface)"""
        # Remove unsupported parameters
        kwargs.pop('stop', None)
        kwargs.pop('max_tokens', None)
        kwargs.pop('top_p', None)
        kwargs.pop('frequency_penalty', None)
        kwargs.pop('presence_penalty', None)
        
        return super()._call(messages, **kwargs)
    
    def _acall(self, messages, stop=None, **kwargs):
        """Override _acall to filter parameters (older LangChain interface)"""
        # Remove unsupported parameters
        kwargs.pop('stop', None)
        kwargs.pop('max_tokens', None)
        kwargs.pop('top_p', None)
        kwargs.pop('frequency_penalty', None)
        kwargs.pop('presence_penalty', None)
        
        return super()._acall(messages, **kwargs)
    
    def _generate(self, messages, stop=None, **kwargs):
        """Override _generate to filter parameters (core generation method)"""
        # Remove unsupported parameters
        kwargs.pop('stop', None)
        kwargs.pop('max_tokens', None)
        kwargs.pop('top_p', None)
        kwargs.pop('frequency_penalty', None)
        kwargs.pop('presence_penalty', None)
        
        return super()._generate(messages, **kwargs)

# Define the LLM with model from environment variable
model_name = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
api_key = os.getenv("OPENAI_API_KEY")

print(f"🔧 Using model: {model_name}")
print(f"🔧 API key set: {'Yes' if api_key else 'No'}")

# Force model to gpt-4o-mini if not set
if not model_name or model_name == "gpt-5-nano":
    model_name = "gpt-4o-mini"
    print(f"🔧 Forcing model to: {model_name}")

llm = FixedTemperatureLLM(
    model=model_name,
    api_key=api_key
)

# Create a safe task execution wrapper
def safe_task_execute(task, *args, **kwargs):
    """Wrapper to safely execute tasks without unsupported parameters"""
    try:
        # Remove any unsupported parameters that might be passed
        kwargs.pop('stop', None)
        kwargs.pop('max_tokens', None)
        kwargs.pop('top_p', None)
        kwargs.pop('frequency_penalty', None)
        kwargs.pop('presence_penalty', None)
        
        # Execute the task with the safe LLM
        response = task.agent.llm.invoke(
            messages=[{"role": "user", "content": task.description}],
            **kwargs
        )
        
        # Extract the content from AIMessage or other response types
        if hasattr(response, 'content'):
            return response.content
        elif isinstance(response, str):
            return response
        elif hasattr(response, 'message'):
            return response.message.content
        else:
            return str(response)
            
    except Exception as e:
        print(f"Error in safe task execution: {e}")
        raise e

# Global queue for real-time updates
update_queue = queue.Queue()

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

def process_crew_ai(topic):
    """Process the CrewAI workflow in a separate thread"""
    global processing_status
    
    try:
        processing_status['is_processing'] = True
        processing_status['topic'] = topic
        processing_status['current_step'] = 0
        processing_status['error'] = None
        processing_status['agent_thoughts'] = {}
        processing_status['current_agent'] = None
        processing_status['current_thought'] = None
        
        # Send initial update
        send_update({
            'current_step': 0,
            'current_agent': 'Research Analyst',
            'current_thought': 'Initializing CrewAI workflow...',
            'agent_thoughts': {},
            'is_processing': True
        })
        
        # Update processing status
        processing_status['current_step'] = 0
        processing_status['current_agent'] = 'Research Analyst'
        processing_status['current_thought'] = 'Initializing CrewAI workflow...'
        
        print(f"🤖 Starting CrewAI processing for topic: {topic}")
        
        # Create custom agents that capture their thoughts
        print(f"🔧 Creating Research Analyst with LLM: {type(llm).__name__} - {getattr(llm, 'model', 'Unknown')}")
        researcher = Agent(
            role="Research Analyst",
            goal="Research a given topic deeply and provide clear findings",
            backstory="You're a seasoned researcher known for producing accurate and concise insights.",
            verbose=True,
            llm=llm
        )

        print(f"🔧 Creating Article Writer with LLM: {type(llm).__name__} - {getattr(llm, 'model', 'Unknown')}")
        writer = Agent(
            role="Article Writer",
            goal="Write a short, compelling article based on the research",
            backstory="You're a skilled writer who turns insights into engaging prose.",
            verbose=True,
            llm=llm
        )

        print(f"🔧 Creating Editor with LLM: {type(llm).__name__} - {getattr(llm, 'model', 'Unknown')}")
        editor = Agent(
            role="Editor",
            goal="Polish the article for tone, flow, and clarity",
            backstory="You're a language expert who makes content shine.",
            verbose=True,
            llm=llm
        )

        print(f"🔧 Creating Social Media Strategist with LLM: {type(llm).__name__} - {getattr(llm, 'model', 'Unknown')}")
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
        
        # Execute tasks one by one to capture real progress
        previous_output = None
        
        for i, task in enumerate([task1, task2, task3, task4]):
            processing_status['current_step'] = i
            processing_status['current_agent'] = task.agent.role
            timestamp = time.strftime("%H:%M:%S")
            current_thought = f"Starting {task.agent.role} task..."
            processing_status['current_thought'] = current_thought
            
            # Send update for current step
            send_update({
                'current_step': i,
                'current_agent': task.agent.role,
                'current_thought': current_thought,
                'agent_thoughts': processing_status['agent_thoughts'],
                'is_processing': True
            })
            
            print(f"🎯 Executing task {i+1}: {task.agent.role}")
            
            # Update task description to include previous agent's output
            if previous_output and i > 0:
                # For writing, editing, and social media tasks, include the previous output
                if i == 1:  # Writing task
                    task.description = f"Write a 400-word article based on this research: {previous_output}"
                elif i == 2:  # Editing task
                    task.description = f"Edit this article for tone, clarity, and structure: {previous_output}"
                elif i == 3:  # Social media task
                    task.description = f"Summarise this article into a tweet (max 280 characters): {previous_output}"
            
            # Execute the task
            try:
                # Send thinking update
                thinking_thought = f"{task.agent.role} is analyzing and working..."
                processing_status['current_thought'] = thinking_thought
                send_update({
                    'current_step': i,
                    'current_agent': task.agent.role,
                    'current_thought': thinking_thought,
                    'agent_thoughts': processing_status['agent_thoughts'],
                    'is_processing': True
                })
                
                # Debug: Check what LLM the agent is using
                print(f"🔍 {task.agent.role} using LLM: {type(task.agent.llm).__name__}")
                print(f"🔍 LLM model: {getattr(task.agent.llm, 'model', 'Unknown')}")
                
                # Use safe task execution to avoid parameter issues
                try:
                    result = safe_task_execute(task)
                except Exception as e:
                    # Fallback to direct LLM call if task execution fails
                    print(f"Task execution failed, trying direct LLM call: {e}")
                    response = task.agent.llm.invoke(
                        messages=[{"role": "user", "content": task.description}]
                    )
                    
                    # Extract the content from AIMessage or other response types
                    if hasattr(response, 'content'):
                        result = response.content
                    elif isinstance(response, str):
                        result = response
                    elif hasattr(response, 'message'):
                        result = response.message.content
                    else:
                        result = str(response)
                timestamp = time.strftime("%H:%M:%S")
                
                # Store the actual output from the agent
                agent_output = f"[{timestamp}] {result}"
                processing_status['agent_thoughts'][task.agent.role] = agent_output
                processing_status['current_thought'] = f"{task.agent.role} completed successfully"
                
                # Send completion update
                send_update({
                    'current_step': i,
                    'current_agent': task.agent.role,
                    'current_thought': f"{task.agent.role} completed successfully",
                    'agent_thoughts': processing_status['agent_thoughts'],
                    'is_processing': True
                })
                
                # Store this output for the next agent
                previous_output = result
                
                print(f"✅ {task.agent.role} completed: {result[:100]}...")
                
                # Brief pause to show completion
                time.sleep(1)
                
            except Exception as e:
                error_msg = f"Error in {task.agent.role} task: {str(e)}"
                print(f"❌ {error_msg}")
                processing_status['agent_thoughts'][task.agent.role] = f"[{timestamp}] Error: {error_msg}"
                processing_status['current_thought'] = f"Error: {error_msg}"
                
                # Send error update
                send_update({
                    'current_step': i,
                    'current_agent': task.agent.role,
                    'current_thought': f"Error: {error_msg}",
                    'agent_thoughts': processing_status['agent_thoughts'],
                    'is_processing': True
                })
                
                time.sleep(1)
        
        # Get the final crew result
        print("📝 Getting final crew result...")
        raw_result = crew.kickoff()
        
        # Log the final crew result for debugging
        print(f"📝 Final CrewAI result: {raw_result[:500]}...")
        
        # Store the final result in processing status for reference
        processing_status['final_result'] = raw_result
        
        # Mark processing as complete
        processing_status['is_processing'] = False
        processing_status['current_step'] = 4
        processing_status['current_agent'] = None
        timestamp = time.strftime("%H:%M:%S")
        processing_status['current_thought'] = f"All CrewAI tasks completed successfully!"
        
        # Send final completion update
        send_update({
            'current_step': 4,
            'current_agent': None,
            'current_thought': "All CrewAI tasks completed successfully!",
            'agent_thoughts': processing_status['agent_thoughts'],
            'is_processing': False
        })
        
        print(f"✅ CrewAI processing completed for topic: {topic}")
        print(f"📊 Final results: {len(processing_status['agent_thoughts'])} agents completed their tasks")
        
    except Exception as e:
        error_msg = f"Error in CrewAI processing: {str(e)}"
        print(f"❌ {error_msg}")
        processing_status['error'] = error_msg
        processing_status['is_processing'] = False
        processing_status['current_agent'] = None
        timestamp = time.strftime("%H:%M:%S")
        processing_status['current_thought'] = f'Error: {error_msg}'
        
        # Send error update
        send_update({
            'current_step': processing_status['current_step'],
            'current_agent': None,
            'current_thought': f"Error: {error_msg}",
            'agent_thoughts': processing_status['agent_thoughts'],
            'is_processing': False
        })

@app.route('/api/generate-content', methods=['POST'])
def generate_content():
    """Start the AI content generation process"""
    global processing_status
    
    if processing_status['is_processing']:
        return jsonify({'error': 'Already processing a request'}), 400
    
    data = request.get_json()
    topic = data.get('topic', 'How AI is transforming creative industries')
    
    if not topic:
        return jsonify({'error': 'Topic is required'}), 400
    
    # Reset status
    processing_status['error'] = None
    
    # Start processing in a separate thread
    thread = Thread(target=process_crew_ai, args=(topic,))
    thread.daemon = True
    thread.start()
    
    return jsonify({
        'message': 'Content generation started',
        'topic': topic
    })

@app.route('/api/status', methods=['GET'])
def get_status():
    """Get the current processing status"""
    return jsonify(processing_status)

@app.route('/api/stream', methods=['GET'])
def stream_updates():
    """Stream real-time updates to the frontend"""
    def generate():
        while True:
            try:
                # Wait for updates from the queue
                update_data = update_queue.get(timeout=1)
                
                # Send the update
                yield f"data: {json.dumps(update_data)}\n\n"
                
                # If not processing, stop the stream
                if not update_data.get('is_processing', False):
                    break
                    
            except queue.Empty:
                # Send current status as heartbeat
                status_data = {
                    'current_step': processing_status['current_step'],
                    'current_agent': processing_status['current_agent'],
                    'current_thought': processing_status['current_thought'],
                    'agent_thoughts': processing_status['agent_thoughts'],
                    'is_processing': processing_status['is_processing']
                }
                yield f"data: {json.dumps(status_data)}\n\n"
                
                # If not processing, stop the stream
                if not processing_status['is_processing']:
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

@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({'status': 'healthy', 'message': 'AI Editorial Team API is running'})

@app.route('/api/debug', methods=['GET'])
def debug_status():
    """Debug endpoint to check current processing status"""
    return jsonify({
        'processing_status': processing_status,
        'current_time': time.time(),
        'is_processing': processing_status['is_processing']
    })

@app.route('/api/test-process', methods=['GET'])
def test_process():
    """Test endpoint to manually trigger processing for debugging"""
    global processing_status
    
    if processing_status['is_processing']:
        return jsonify({'error': 'Already processing'})
    
    # Start a test process
    thread = Thread(target=process_crew_ai, args=('Test Topic',))
    thread.daemon = True
    thread.start()
    
    return jsonify({'message': 'Test process started'})

if __name__ == '__main__':
    print("🚀 Starting AI Editorial Team Backend...")
    print("📝 This backend integrates with your existing CrewAI Python code")
    print("🌐 API endpoints available at http://localhost:5001")
    print("🔗 Frontend should be running at http://localhost:5173")
    
    app.run(debug=True, host='0.0.0.0', port=5001)
