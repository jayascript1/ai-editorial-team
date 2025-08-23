import { useEffect } from 'react'

const ProcessFlow = ({ currentStep = 0, isProcessing = false, currentAgent = null, currentThought = null, agentThoughts = {} }) => {
  // Debug logging
  console.log('🔍 ProcessFlow props:', { currentStep, isProcessing, currentAgent, currentThought, agentThoughts })
  
  // Use useEffect to log when props change
  useEffect(() => {
    console.log('🔄 ProcessFlow props updated:', { currentStep, isProcessing, currentAgent, currentThought, agentThoughts })
  }, [currentStep, isProcessing, currentAgent, currentThought, agentThoughts])
  
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
        
        {/* Current Agent Status Display */}
        {isProcessing && currentAgent && (
          <div className="mt-8 max-w-4xl mx-auto px-4 animate-fade-in">
            <div className="bg-gradient-to-r from-blue-500/20 to-purple-500/20 backdrop-blur-xl rounded-2xl border-2 border-blue-500/30 p-4 md:p-6 shadow-2xl">
              <div className="flex items-center justify-center space-x-2 md:space-x-4 mb-4">
                <div className="w-3 h-3 md:w-4 md:h-4 bg-blue-400 rounded-full animate-pulse"></div>
                <h3 className="text-xl md:text-2xl font-bold text-blue-400 text-center">🤖 {currentAgent}</h3>
                <div className="w-3 h-3 md:w-4 md:h-4 bg-blue-400 rounded-full animate-pulse"></div>
              </div>
              {currentThought && (
                <div className="space-y-3">
                  <p className="text-base md:text-lg text-blue-200 leading-relaxed text-center">
                    {currentThought}
                  </p>
                  <p className="text-xs text-blue-400 text-center">
                    Last updated: {new Date().toLocaleTimeString()}
                  </p>
                  {/* Show current agent's latest output if available */}
                  {agentThoughts[currentAgent] && (
                    <div className="mt-3 p-3 md:p-4 bg-blue-500/10 rounded-lg border border-blue-500/20">
                      <p className="text-xs text-blue-300 font-medium mb-2 text-center">Latest output from {currentAgent}:</p>
                      <p className="text-xs md:text-sm text-blue-200 leading-relaxed text-center">
                        {agentThoughts[currentAgent].split('] ')[1]?.substring(0, 120)}...
                      </p>
                    </div>
                  )}
                </div>
              )}
              <div className="mt-4 w-full bg-blue-500/20 rounded-full h-2 md:h-3">
                <div 
                  className="bg-gradient-to-r from-blue-400 to-purple-500 h-2 md:h-3 rounded-full transition-all duration-1000 ease-out shadow-lg"
                  style={{width: `${((currentStep + 1) / 4) * 100}%`}}
                ></div>
              </div>
              <p className="text-blue-300 text-xs md:text-sm mt-2 text-center">
                Step {currentStep + 1} of 4 • {Math.round(((currentStep + 1) / 4) * 100)}% Complete
              </p>
            </div>
          </div>
        )}
      </div>
      
      <div className="max-w-5xl mx-auto">
        <div className="relative">
          {/* Connection line */}
          <div className="absolute top-10 left-0 right-0 h-0.5 bg-gradient-to-r from-blue-500/30 via-purple-500/30 to-emerald-500/30 hidden md:block animate-pulse-slow"></div>
          
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6 md:gap-8 lg:gap-12">
            {steps.map((step, index) => {
              const isActive = isProcessing && index === currentStep
              const isCompleted = isProcessing && index < currentStep
              const isPending = !isProcessing || index > currentStep
              const isCurrentAgent = currentAgent === step.agent
              const agentThought = agentThoughts[step.agent] || null
              
              // Debug logging for each step
              if (isCurrentAgent) {
                console.log(`🎯 ${step.agent} is current agent with thought: ${currentThought}`)
              }
              if (agentThought) {
                console.log(`💡 ${step.agent} has completed thought: ${agentThought}`)
              }
              
              return (
                <div key={index} className="relative text-center group animate-fade-in" style={{animationDelay: `${0.2 * index}s`}}>
                  {/* Step circle */}
                  <div className={`relative z-10 w-16 h-16 md:w-20 md:h-20 mx-auto mb-4 md:mb-6 rounded-2xl flex items-center justify-center text-2xl md:text-3xl transition-all duration-700 ${
                    isActive 
                      ? 'bg-gradient-to-br from-blue-500 to-purple-600 text-white shadow-2xl scale-110 animate-glow' 
                      : isCompleted 
                      ? 'bg-gradient-to-br from-emerald-500 to-green-500 text-white shadow-xl' 
                      : 'bg-white/10 backdrop-blur-sm border border-white/20 text-slate-400 group-hover:border-white/40 group-hover:bg-white/20'
                  }`}>
                    {isActive && (
                      <div className="absolute inset-0 rounded-2xl bg-gradient-to-br from-blue-500 to-purple-600 animate-ping opacity-75"></div>
                    )}
                    {isCompleted ? '✅' : step.icon}
                  </div>
                  
                  {/* Step info */}
                  <div className="space-y-2 md:space-y-3">
                    <h3 className={`font-bold text-lg md:text-xl transition-all duration-500 ${
                      isActive ? 'text-blue-400 scale-110' : isCompleted ? 'text-emerald-400' : 'text-slate-300 group-hover:text-white'
                    }`}>
                      {step.name}
                    </h3>
                    <p className="text-sm md:text-base text-slate-400 leading-relaxed group-hover:text-slate-300 transition-colors duration-300">{step.description}</p>
                    
                                        {/* Agent name with enhanced styling */}
                    <div className="space-y-2">
                      <p className={`text-xs md:text-sm font-medium transition-all duration-300 ${
                        isCurrentAgent ? 'text-blue-400' : isCompleted ? 'text-emerald-400' : 'text-slate-500'
                      }`}>
                        {step.agent}
                      </p>
                      
                      {/* Agent status indicator */}
                      {isProcessing && (
                        <div className="flex items-center justify-center space-x-1 md:space-x-2">
                          {isCurrentAgent && (
                            <>
                              <div className={`w-1.5 h-1.5 md:w-2 md:h-2 bg-blue-400 rounded-full ${isCurrentAgent ? 'animate-agent-working' : ''}`}></div>
                              <span className="text-xs text-blue-400 font-medium">Working</span>
                            </>
                          )}
                          {isCompleted && (
                            <>
                              <div className="w-1.5 h-1.5 md:w-2 md:h-2 bg-emerald-400 rounded-full animate-agent-complete"></div>
                              <span className="text-xs text-emerald-400 font-medium">Done</span>
                            </>
                          )}
                          {isPending && (
                            <>
                              <div className="w-1.5 h-1.5 md:w-2 md:h-2 bg-slate-500 rounded-full"></div>
                              <span className="text-xs text-slate-500 font-medium">Pending</span>
                            </>
                          )}
                        </div>
                      )}
                    </div>
                </div>
                
                {/* Enhanced status display */}
                  {isProcessing && (
                    <div className="mt-4 animate-fade-in">
                      {isActive && (
                        <div className="space-y-3">
                          {/* Current thought display */}
                          {isCurrentAgent && currentThought && (
                            <div className="bg-blue-500/20 backdrop-blur-sm rounded-xl p-3 md:p-4 border-2 border-blue-500/40 animate-thought-update shadow-lg">
                              <div className="flex items-start space-x-2 md:space-x-3">
                                <span className="text-blue-400 text-base md:text-lg">💭</span>
                                <div className="flex-1">
                                  <p className="text-xs md:text-sm text-blue-200 leading-relaxed text-left font-medium">
                                    {currentThought}
                                  </p>
                                  <p className="text-xs text-blue-400 mt-1">🤖 {currentAgent} is currently thinking...</p>
                                </div>
                              </div>
                            </div>
                          )}
                          

                          
                          {/* Progress indicator */}
                          <div className="flex items-center justify-center space-x-2 text-blue-400">
                            <div className="w-2 h-2 md:w-3 md:h-3 bg-blue-400 rounded-full animate-pulse"></div>
                            <span className="text-xs md:text-sm font-semibold">Processing...</span>
                          </div>
                        </div>
                      )}
                      
                      {isCompleted && (
                        <div className="flex items-center justify-center space-x-2 md:space-x-3 text-emerald-400">
                          <div className="w-3 h-3 md:w-4 md:h-4 bg-emerald-400 rounded-full"></div>
                          <span className="text-xs md:text-sm font-semibold">Complete</span>
                        </div>
                      )}
                      

                    </div>
                  )}
                </div>
              )
            })}
          </div>
        </div>
        
        {/* Agent Outputs Summary - Show during and after processing */}
        {Object.keys(agentThoughts).length > 0 && (
          <div className="mt-16 animate-fade-in">
            <div className="max-w-6xl mx-auto px-4">
              <h3 className="text-2xl md:text-3xl font-bold text-white text-center mb-8">
                🤖 {isProcessing ? 'Agent Outputs' : 'Final Agent Outputs'}
              </h3>
              <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                {Object.entries(agentThoughts).map(([agent, output]) => {
                  const outputText = output.split('] ')[1] || output;
                  const timestamp = output.split('] ')[0]?.replace('[', '') || '';
                  
                  return (
                    <div key={agent} className="bg-slate-800/50 backdrop-blur-sm rounded-xl p-4 md:p-6 border border-slate-600/30 hover:border-slate-500/50 transition-all duration-300 animate-fade-in">
                      <div className="flex items-center space-x-3 mb-4">
                        <span className="text-xl md:text-2xl">🤖</span>
                        <h4 className="font-bold text-slate-200 text-lg md:text-xl">{agent}</h4>
                        {isProcessing && (
                          <div className="ml-auto">
                            <div className="w-2 h-2 bg-emerald-400 rounded-full animate-pulse"></div>
                          </div>
                        )}
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
