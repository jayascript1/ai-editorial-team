import { useState, useEffect, useRef } from 'react'
import Header from './components/Header'
import TopicInput from './components/TopicInput'
import AgentGrid from './components/AgentGrid'
import ProcessFlow from './components/ProcessFlow'
import { aiService } from './api/aiService'

function App() {
  const [topic, setTopic] = useState('How AI is transforming creative industries')
  const [isProcessing, setIsProcessing] = useState(false)
  const [userId, setUserId] = useState(null) // Add userId state

  const [currentStep, setCurrentStep] = useState(0)
  const [error, setError] = useState(null)
  const [currentAgent, setCurrentAgent] = useState(null)
  const [currentThought, setCurrentThought] = useState(null)
  const [agentThoughts, setAgentThoughts] = useState({})

  const eventSourceRef = useRef(null)

  // Handle Server-Sent Events for real-time updates
  useEffect(() => {
    // Test API connection when app loads
    const testConnection = async () => {
      console.log('🧪 Testing API connection on app load...');
      const isConnected = await aiService.testConnection();
      if (!isConnected) {
        console.error('❌ API connection failed on app load');
        setError('Unable to connect to AI service. Please check your connection and try again.');
      } else {
        console.log('✅ API connection successful on app load');
        setError(null);
      }
    };
    
    testConnection();
  }, []);

  useEffect(() => {
    if (isProcessing && userId) {
      console.log('🔴 Creating EventSource connection with userId:', userId)
      
      // Create EventSource URL using the same base URL logic as aiService
      const baseUrl = window.location.hostname === 'localhost' ? 'http://localhost:5001' : 'https://ai-editorial-team.onrender.com'
      const streamUrl = `${baseUrl}/api/stream?user_id=${userId}`
      console.log('📡 EventSource URL:', streamUrl)
      
      // Create EventSource directly
      eventSourceRef.current = new EventSource(streamUrl)
      
      if (eventSourceRef.current) {
        eventSourceRef.current.onopen = () => {
          console.log('✅ EventSource connected successfully')
        }
        
        eventSourceRef.current.onmessage = (event) => {
          try {
            const data = JSON.parse(event.data)
            console.log('🔴 Received SSE data:', data)  // Debug log
            
            if (data.current_step !== undefined) {
              console.log('📊 Updating current step:', data.current_step)
              setCurrentStep(data.current_step)
            }
            
            if (data.current_agent !== undefined) {
              console.log('🤖 Updating current agent:', data.current_agent)
              setCurrentAgent(data.current_agent)
            }
            
            if (data.current_thought !== undefined) {
              console.log('💭 Updating current thought:', data.current_thought)
              setCurrentThought(data.current_thought)
            }
            
            if (data.agent_thoughts !== undefined) {
              console.log('🧠 Updating agent thoughts:', data.agent_thoughts)
              setAgentThoughts(data.agent_thoughts)
            }
            
            if (!data.is_processing) {
              console.log('✅ Processing completed, keeping display visible for a moment...')
              // Keep the display visible for a few seconds before hiding
              setTimeout(() => {
                console.log('✅ Now hiding processing display')
                setIsProcessing(false)
                eventSourceRef.current?.close()
              }, 3000) // Keep visible for 3 seconds after completion
            }
          } catch (err) {
            console.error('Error parsing SSE data:', err)
          }
        }
        
        eventSourceRef.current.onerror = (error) => {
          console.error('EventSource error:', error)
          eventSourceRef.current?.close()
        }
      } else {
        console.error('Failed to create EventSource')
        setError('Failed to establish real-time connection')
        setIsProcessing(false)
      }
    }
    
    return () => {
      if (eventSourceRef.current) {
        eventSourceRef.current.close()
      }
    }
  }, [isProcessing, userId])

  const handleTopicSubmit = async (newTopic) => {
    console.log('🚀 Starting topic submission:', newTopic)
    setTopic(newTopic)
    setCurrentStep(0)
    setError(null)
    setCurrentAgent(null)
    setCurrentThought(null)
    setAgentThoughts({})
    
    try {
      const result = await aiService.generateContent(newTopic)
      
      if (!result.success) {
        throw new Error(result.error || 'Failed to start content generation')
      }
      
      console.log('Content generation started successfully')
      
      // Store the userId and THEN set processing to true
      if (result.user_id) {
        console.log('🏷️ Setting userId and starting processing:', result.user_id)
        setUserId(result.user_id)
        setIsProcessing(true)
        console.log('🔄 Set isProcessing to TRUE')
      } else {
        throw new Error('No user_id received from server')
      }
      
    } catch (err) {
      console.error('❌ Error starting content generation:', err)
      console.log('🔄 Setting isProcessing to FALSE due to error')
      setError(err.message)
      setIsProcessing(false)
    }
  }

  const resetProcess = () => {
    setCurrentStep(0)
    setIsProcessing(false)
    setError(null)
    setCurrentAgent(null)
    setCurrentThought(null)
    setAgentThoughts({})
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900 relative overflow-hidden">
      {/* Background Elements */}
      <div className="absolute inset-0 overflow-hidden">
        <div className="absolute -top-40 -right-40 w-80 h-80 bg-gradient-to-br from-blue-500/20 to-purple-600/20 rounded-full blur-3xl animate-float"></div>
        <div className="absolute -bottom-40 -left-40 w-80 h-80 bg-gradient-to-tr from-emerald-500/20 to-cyan-600/20 rounded-full blur-3xl animate-float" style={{animationDelay: '2s'}}></div>
        <div className="absolute top-1/2 left-1/2 transform -translate-x-1/2 -translate-y-1/2 w-96 h-96 bg-gradient-to-r from-violet-500/10 to-fuchsia-600/10 rounded-full blur-3xl animate-float" style={{animationDelay: '4s'}}></div>
      </div>
      
      <Header />
      
      <main className="relative z-10 container mx-auto px-6 py-16 max-w-6xl">
        <div className="text-center mb-20 animate-fade-in">
          <div className="inline-flex items-center justify-center w-20 h-20 bg-gradient-to-br from-blue-500 to-purple-600 rounded-2xl mb-8 shadow-2xl animate-glow">
            <svg className="w-10 h-10 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z" />
            </svg>
          </div>
          <h1 className="text-6xl font-bold text-white mb-6 bg-gradient-to-r from-blue-400 via-purple-400 to-emerald-400 bg-clip-text text-transparent leading-tight animate-slide-up">
            AI Editorial Team
          </h1>
          <p className="text-xl text-slate-300 max-w-2xl mx-auto leading-relaxed animate-slide-up" style={{animationDelay: '0.2s'}}>
            Transform any topic into polished content with our AI-powered research, writing, editing, and social media team.
          </p>
        </div>

        {/* Meet Your AI Team - moved above topic input */}
        <div className="mb-16 animate-fade-in" style={{animationDelay: '0.4s'}}>
          <AgentGrid 
            currentStep={currentStep}
            isProcessing={isProcessing}
            currentAgent={currentAgent}
            agentThoughts={agentThoughts}
          />
        </div>

        <div className="animate-scale-in" style={{animationDelay: '0.6s'}}>
          <TopicInput onSubmit={handleTopicSubmit} disabled={isProcessing} />
        </div>
        
        {/* Error Display */}
        {error && (
          <div className="mt-8 max-w-2xl mx-auto">
            <div className="bg-red-500/20 backdrop-blur-xl rounded-2xl border border-red-500/30 p-6 text-center">
              <h3 className="text-xl font-bold text-red-400 mb-2">Error</h3>
              <p className="text-red-300">{error}</p>
              <button
                onClick={resetProcess}
                className="mt-4 bg-red-500 hover:bg-red-600 text-white font-semibold py-2 px-6 rounded-xl transition-all duration-300"
              >
                Try Again
              </button>
            </div>
          </div>
        )}
        

        
        {/* Always show ProcessFlow */}
        <div className="mt-24 animate-fade-in" style={{animationDelay: '0.8s'}}>
          <ProcessFlow 
            currentStep={currentStep} 
            isProcessing={isProcessing}
            currentAgent={currentAgent}
            currentThought={currentThought}
            agentThoughts={agentThoughts}
          />
        </div>


      </main>
    </div>
  )
}

export default App
