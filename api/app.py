from flask import Flask, request, jsonify
from flask_cors import CORS
import os
import sys
import asyncio
from threading import Thread
import time
import json
import queue
import io
import re

# Import your existing CrewAI code
from langchain_openai import ChatOpenAI
from dotenv import load_dotenv

# Import CrewAI after environment setup
from crewai import Agent, Task, Crew

# Load environment variables
load_dotenv()

# Simple LLM configuration for CrewAI 0.28.0 compatibility
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

# Global queue for real-time updates
update_queue = queue.Queue()

class CrewAIOutputCapture:
    """Captures and parses CrewAI output to track agent progress in real-time"""
    
    def __init__(self, original_stdout, agent_names):
        self.original_stdout = original_stdout
        self.agent_names = agent_names
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
        global processing_status
        
        try:
            # Look for agent start marker
            if "🤖 Agent Started" in text or "Agent:" in text:
                for i, agent_name in enumerate(self.agent_names):
                    if agent_name in text:
                        processing_status['current_step'] = i
                        processing_status['current_agent'] = agent_name
                        processing_status['current_thought'] = f"{agent_name} is working..."
                        
                        send_update({
                            'current_step': i,
                            'current_agent': agent_name,
                            'current_thought': f"{agent_name} is working...",
                            'agent_thoughts': processing_status['agent_thoughts'],
                            'is_processing': True
                        })
                        
                        print(f"🎯 Detected {agent_name} started working")
                        break
            
            # Look for agent completion marker
            elif "✅ Agent Final Answer" in text or "Final Answer:" in text:
                # Get the current agent that just completed
                current_agent = processing_status.get('current_agent')
                if current_agent:
                    timestamp = time.strftime("%H:%M:%S")
                    processing_status['current_thought'] = f"{current_agent} completed successfully!"
                    
                    send_update({
                        'current_step': processing_status['current_step'],
                        'current_agent': current_agent,
                        'current_thought': f"{current_agent} completed successfully!",
                        'agent_thoughts': processing_status['agent_thoughts'],
                        'is_processing': True
                    })
                    
                    print(f"✅ Detected {current_agent} completed work")
        
        except Exception as e:
            print(f"Error parsing CrewAI output: {e}")

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
        print(f"🔧 Creating Research Analyst with LLM: {type(llm).__name__} - {getattr(llm, 'model', 'gpt-4o-mini')}")
        researcher = Agent(
            role="Research Analyst",
            goal="Research a given topic deeply and provide clear findings",
            backstory="You're a seasoned researcher known for producing accurate and concise insights.",
            verbose=True,
            llm=llm
        )

        print(f"🔧 Creating Article Writer with LLM: {type(llm).__name__} - {getattr(llm, 'model', 'gpt-4o-mini')}")
        writer = Agent(
            role="Article Writer",
            goal="Write a short, compelling article based on the research",
            backstory="You're a skilled writer who turns insights into engaging prose.",
            verbose=True,
            llm=llm
        )

        print(f"🔧 Creating Editor with LLM: {type(llm).__name__} - {getattr(llm, 'model', 'gpt-4o-mini')}")
        editor = Agent(
            role="Editor",
            goal="Polish the article for tone, flow, and clarity",
            backstory="You're a language expert who makes content shine.",
            verbose=True,
            llm=llm
        )

        print(f"🔧 Creating Social Media Strategist with LLM: {type(llm).__name__} - {getattr(llm, 'model', 'gpt-4o-mini')}")
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
        output_capture = CrewAIOutputCapture(original_stdout, agent_names)
        
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
                        processing_status['agent_thoughts'][agent_name] = f"[{timestamp}] {task_output}"
                        print(f"✅ {agent_name} output captured: {task_output[:100]}...")
                    else:
                        # Fallback: create a meaningful output based on the task description
                        fallback_output = f"Completed {task.description.lower()} task successfully."
                        processing_status['agent_thoughts'][agent_name] = f"[{timestamp}] {fallback_output}"
                        print(f"📝 {agent_name} fallback output created")
                    
                    # Send update for this agent's completion
                    send_update({
                        'current_step': i,
                        'current_agent': agent_name,
                        'current_thought': f"{agent_name} completed successfully!",
                        'agent_thoughts': processing_status['agent_thoughts'],
                        'is_processing': True
                    })
            
            # Log the final crew result for debugging
            print(f"📝 Final CrewAI result: {result[:500] if isinstance(result, str) else str(result)[:500]}...")
            
            # Store the final result in processing status for reference
            processing_status['final_result'] = result
            
        except Exception as e:
            # Restore stdout first
            sys.stdout = original_stdout
            
            error_msg = f"Error in CrewAI execution: {str(e)}"
            print(f"❌ {error_msg}")
            timestamp = time.strftime("%H:%M:%S")
            
            # Store error for all agents
            for agent_name in agent_names:
                processing_status['agent_thoughts'][agent_name] = f"[{timestamp}] Error: {error_msg}"
            
            # Send error update
            send_update({
                'current_step': processing_status['current_step'],
                'current_agent': None,
                'current_thought': f"Error: {error_msg}",
                'agent_thoughts': processing_status['agent_thoughts'],
                'is_processing': False
            })
            
            # Re-raise the error
            raise e
        
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

# Vercel handler
def handler(request, context):
    return app(request.environ, context)

# For local development
if __name__ == '__main__':
    app.run(debug=True)