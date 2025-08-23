import { useEffect, useState } from 'react'

const ProcessFlow = ({ currentStep = 0, isProcessing = false, currentAgent = null, currentThought = null, agentThoughts = {} }) => {
  // Add state to prevent flashing and ensure minimum display time
  const [showProcessing, setShowProcessing] = useState(false)
  const [hasStartedProcessing, setHasStartedProcessing] = useState(false)
  const [workflowActive, setWorkflowActive] = useState(false)
  
  // Debug logging
  console.log('🔍 ProcessFlow props:', { currentStep, isProcessing, currentAgent, currentThought, agentThoughts })
  
  // Use useEffect to log when props change
  useEffect(() => {
    console.log('🔄 ProcessFlow props updated:', { currentStep, isProcessing, currentAgent, currentThought, agentThoughts })
  }, [currentStep, isProcessing, currentAgent, currentThought, agentThoughts])
  
  // Manage processing display state to prevent flashing and maintain workflow visibility
  useEffect(() => {
    if (isProcessing) {
      setShowProcessing(true)
      setHasStartedProcessing(true)
      setWorkflowActive(true)
      console.log('🚀 ProcessFlow: Workflow activated, keeping timeline visible')
    } else if (hasStartedProcessing) {
      // Only hide after processing stops AND we have outputs from all 4 agents
      const hasAllOutputs = Object.keys(agentThoughts).length === 4
      const isWorkflowComplete = !isProcessing && hasAllOutputs
      
      console.log('🔄 ProcessFlow: Processing stopped, checking completion status:', {
        isProcessing,
        agentOutputCount: Object.keys(agentThoughts).length,
        hasAllOutputs,
        isWorkflowComplete
      })
      
      if (isWorkflowComplete) {
        // Keep showing for a minimum time even after all processing completes
        const timer = setTimeout(() => {
          console.log('✅ ProcessFlow: Hiding workflow display after completion period')
          setShowProcessing(false)
          setWorkflowActive(false)
        }, 5000) // Show for 5 seconds after complete workflow finishes
        
        return () => clearTimeout(timer)
      }
      // If workflow is not complete, keep everything visible
    }
  }, [isProcessing, hasStartedProcessing, agentThoughts])
  
  // Track when any agent activity happens to maintain display
  useEffect(() => {
    // Keep workflow active if:
    // 1. We have a current agent working
    // 2. We have agent outputs but haven't reached final completion (< 4 agents)
    // 3. Processing is happening
    const shouldStayActive = currentAgent || 
                           (Object.keys(agentThoughts).length > 0 && Object.keys(agentThoughts).length < 4) ||
                           isProcessing
    
    if (shouldStayActive && hasStartedProcessing) {
      setWorkflowActive(true)
      console.log('🔄 ProcessFlow: Agent activity detected, maintaining workflow visibility:', {
        currentAgent,
        agentOutputCount: Object.keys(agentThoughts).length,
        isProcessing
      })
    }
  }, [currentAgent, agentThoughts, isProcessing, hasStartedProcessing])
  
  const steps = [
    { name: 'Research', description: 'Deep analysis and insights', icon: '🔍', agent: 'Research Analyst' },
    { name: 'Writing', description: 'Content creation', icon: '✍️', agent: 'Article Writer' },
    { name: 'Editing', description: 'Polish and refine', icon: '📝', agent: 'Editor' },
    { name: 'Social Media', description: 'Engaging content', icon: '📱', agent: 'Social Media Strategist' }
  ]

  return (
    <div className="mb-20">
      <div className="text-center mb-16 animate-fade-in">
        <h2 className="text-4xl font-bold text-white mb-6">How It Works</h2>
        <p className="text-xl text-slate-300 max-w-3xl mx-auto leading-relaxed">
          Our AI team follows a proven workflow to deliver high-quality content.
        </p>
        

      </div>
      
      <div className="max-w-5xl mx-auto">
        <div className="relative">
          {/* Connection line */}
          <div className="absolute top-10 left-0 right-0 h-0.5 bg-gradient-to-r from-blue-500/30 via-purple-500/30 to-emerald-500/30 hidden md:block animate-pulse-slow"></div>
          
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6 md:gap-8 lg:gap-12">
            {steps.map((step, index) => {
              // Enhanced agent status logic for accurate representation
              const hasAgentOutput = agentThoughts[step.agent] !== undefined
              const isCurrentlyActive = currentAgent === step.agent && isProcessing
              const isCompleted = hasAgentOutput && !isCurrentlyActive
              const isInProgress = index <= currentStep && (isProcessing || workflowActive) && !isCompleted
              const isPending = index > currentStep && !hasAgentOutput
              
              // Improved visual state logic
              const displayState = isCurrentlyActive ? 'active' : 
                                  isCompleted ? 'completed' : 
                                  isInProgress ? 'started' : 'pending'
              
              const agentThought = agentThoughts[step.agent] || null
              
              // Enhanced debug logging
              console.log(`🎨 ${step.agent} - State: ${displayState}, hasOutput: ${hasAgentOutput}, currentAgent: ${currentAgent}, step: ${index}/${currentStep}`);
              
              return (
                <div key={index} className="relative text-center group animate-fade-in" style={{animationDelay: `${0.2 * index}s`}}>
                  {/* Step circle */}
                  <div className={`relative z-10 w-16 h-16 md:w-20 md:h-20 mx-auto mb-4 md:mb-6 rounded-2xl flex items-center justify-center text-2xl md:text-3xl transition-all duration-700 ${
                    displayState === 'active'
                      ? 'bg-gradient-to-br from-blue-500 to-purple-600 text-white shadow-2xl scale-110 animate-glow' 
                      : displayState === 'completed'
                      ? 'bg-gradient-to-br from-emerald-500 to-green-500 text-white shadow-xl scale-105' 
                      : displayState === 'started'
                      ? 'bg-gradient-to-br from-yellow-500 to-orange-500 text-white shadow-lg'
                      : 'bg-white/10 backdrop-blur-sm border border-white/20 text-slate-400 group-hover:border-white/40 group-hover:bg-white/20'
                  }`}>
                    {displayState === 'active' && (
                      <div className="absolute inset-0 rounded-2xl bg-gradient-to-br from-blue-500 to-purple-600 animate-ping opacity-75"></div>
                    )}
                    {displayState === 'completed' ? '✓' : 
                     displayState === 'active' ? step.icon : 
                     displayState === 'started' ? '⏳' : 
                     step.icon}
                  </div>
                  
                  {/* Step info */}
                  <div className="space-y-2 md:space-y-3">
                    <h3 className={`font-bold text-lg md:text-xl transition-all duration-500 ${
                      displayState === 'active' ? 'text-blue-400 scale-110' : 
                      displayState === 'completed' ? 'text-emerald-400' : 
                      'text-slate-300 group-hover:text-white'
                    }`}>
                      {step.name}
                    </h3>
                    <p className="text-sm md:text-base text-slate-400 leading-relaxed group-hover:text-slate-300 transition-colors duration-300">{step.description}</p>
                    
                    {/* Agent name with enhanced styling */}
                    <div className="space-y-2">
                      <p className={`text-xs md:text-sm font-medium transition-all duration-300 ${
                        displayState === 'active' ? 'text-blue-400' : 
                        displayState === 'completed' ? 'text-emerald-400' : 
                        'text-slate-500'
                      }`}>
                        {step.agent}
                      </p>
                      
                      {/* Enhanced Agent status indicator with improved logic */}
                      {(workflowActive || showProcessing || isProcessing) && (
                        <div className="flex items-center justify-center space-x-1 md:space-x-2">
                          {displayState === 'active' && (
                            <>
                              <div className="w-1.5 h-1.5 md:w-2 md:h-2 bg-blue-400 rounded-full animate-agent-working"></div>
                              <span className="text-xs text-blue-400 font-medium">🟢 Working</span>
                            </>
                          )}
                          {displayState === 'completed' && (
                            <>
                              <div className="w-1.5 h-1.5 md:w-2 md:h-2 bg-emerald-400 rounded-full animate-agent-complete"></div>
                              <span className="text-xs text-emerald-400 font-medium">Finished</span>
                            </>
                          )}
                          {displayState === 'started' && (
                            <>
                              <div className="w-1.5 h-1.5 md:w-2 md:h-2 bg-yellow-400 rounded-full animate-pulse"></div>
                              <span className="text-xs text-yellow-400 font-medium">⏳ Started</span>
                            </>
                          )}
                          {displayState === 'pending' && (
                            <>
                              <div className="w-1.5 h-1.5 md:w-2 md:h-2 bg-slate-500 rounded-full"></div>
                              <span className="text-xs text-slate-500 font-medium">⏸️ Waiting</span>
                            </>
                          )}
                        </div>
                      )}
                    </div>
                </div>
                
                {/* Enhanced status display */}
                  {(workflowActive || showProcessing || isProcessing) && (
                    <div className="mt-4 animate-fade-in">
                      {displayState === 'active' && (
                        <div className="space-y-3">
                          {/* Current thought display with ENHANCED visibility */}
                          {currentAgent === step.agent && currentThought && (
                            <div className="bg-gradient-to-r from-blue-500/30 to-purple-500/30 backdrop-blur-sm rounded-xl p-3 md:p-4 border-2 border-blue-400/70 shadow-2xl animate-pulse-slow">
                              <div className="flex items-start space-x-2 md:space-x-3">
                                <span className="text-blue-200 text-lg md:text-xl animate-bounce">💭</span>
                                <div className="flex-1">
                                  <p className="text-xs md:text-sm text-blue-100 leading-relaxed text-left font-bold">
                                    {currentThought}
                                  </p>
                                  <div className="flex items-center justify-between mt-2">
                                    <p className="text-xs text-blue-300 font-semibold">🤖 {currentAgent} working...</p>
                                    <p className="text-xs text-blue-400 font-medium">
                                      {new Date().toLocaleTimeString()}
                                    </p>
                                  </div>
                                </div>
                              </div>
                            </div>
                          )}
                          
                          {/* Enhanced animated progress indicator */}
                          <div className="flex items-center justify-center space-x-3 text-blue-400">
                            <div className="flex space-x-1">
                              <div className="w-2 h-2 md:w-3 md:h-3 bg-blue-400 rounded-full animate-bounce"></div>
                              <div className="w-2 h-2 md:w-3 md:h-3 bg-blue-400 rounded-full animate-bounce" style={{animationDelay: '0.1s'}}></div>
                              <div className="w-2 h-2 md:w-3 md:h-3 bg-blue-400 rounded-full animate-bounce" style={{animationDelay: '0.2s'}}></div>
                            </div>
                            <span className="text-xs md:text-sm font-bold animate-pulse">PROCESSING</span>
                          </div>
                        </div>
                      )}
                    </div>
                  )}
                </div>
              )
            })}
          </div>
        </div>
        
        {/* Agent Outputs Summary - Show ONLY after ALL agents are complete */}
        {Object.keys(agentThoughts).length === 4 && !isProcessing && (
          <div className="mt-16 animate-fade-in">
            <div className="max-w-6xl mx-auto px-4">
              <div className="text-center mb-8 animate-fade-in">
                <div className="inline-flex items-center space-x-3 mb-4">
                  <div className="w-4 h-4 bg-emerald-400 rounded-full animate-bounce"></div>
                  <h3 className="text-2xl md:text-3xl font-bold text-emerald-400">
                    🎉 All Agents Completed Successfully!
                  </h3>
                  <div className="w-4 h-4 bg-emerald-400 rounded-full animate-bounce" style={{animationDelay: '0.2s'}}></div>
                </div>
                <p className="text-slate-300">Your AI editorial team has finished creating content. Review the outputs below:</p>
              </div>
              <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                {Object.entries(agentThoughts).map(([agent, output]) => {
                  const outputText = output.split('] ')[1] || output;
                  const timestamp = output.split('] ')[0]?.replace('[', '') || '';
                  
                  return (
                    <div key={agent} className="bg-slate-800/50 backdrop-blur-sm rounded-xl p-4 md:p-6 border border-slate-600/30 hover:border-slate-500/50 transition-all duration-300 animate-fade-in">
                      <div className="flex items-center space-x-3 mb-4">
                        <span className="text-xl md:text-2xl">🤖</span>
                        <h4 className="font-bold text-slate-200 text-lg md:text-xl">{agent}</h4>
                        <div className="ml-auto">
                          <div className="w-2 h-2 bg-emerald-400 rounded-full"></div>
                        </div>
                      </div>
                      <div className="text-sm md:text-base text-slate-300 leading-relaxed whitespace-pre-wrap break-words">
                        {outputText}
                      </div>
                      {timestamp && (
                        <p className="text-xs text-slate-500 mt-3 font-medium">
                          Completed at: {timestamp}
                        </p>
                      )}
                    </div>
                  );
                })}
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}

export default ProcessFlow
