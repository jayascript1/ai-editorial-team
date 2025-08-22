const AgentGrid = () => {
  const agents = [
    {
      name: 'Research Analyst',
      description: 'Deep research and insights',
      icon: (
        <svg className="w-8 h-8 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
        </svg>
      ),
      color: 'from-blue-500 to-cyan-500',
      bgColor: 'from-blue-500/20 to-cyan-500/20'
    },
    {
      name: 'Article Writer',
      description: 'Compelling content creation',
      icon: (
        <svg className="w-8 h-8 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z" />
        </svg>
      ),
      color: 'from-emerald-500 to-green-500',
      bgColor: 'from-emerald-500/20 to-green-500/20'
    },
    {
      name: 'Editor',
      description: 'Polish and refinement',
      icon: (
        <svg className="w-8 h-8 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 21h10a2 2 0 002-2V9.414a1 1 0 00-.293-.707l-5.414-5.414A1 1 0 0012.586 3H7a2 2 0 00-2 2v14a2 2 0 002 2z" />
        </svg>
      ),
      color: 'from-purple-500 to-violet-500',
      bgColor: 'from-purple-500/20 to-violet-500/20'
    },
    {
      name: 'Social Media Strategist',
      description: 'Engaging social content',
      icon: (
        <svg className="w-8 h-8 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 8h10M7 12h4m1 8l-4-4H5a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v8a2 2 0 01-2 2h-3l-4 4z" />
        </svg>
      ),
      color: 'from-orange-500 to-amber-500',
      bgColor: 'from-orange-500/20 to-amber-500/20'
    }
  ]

  return (
    <div className="mb-20">
      <div className="text-center mb-16 animate-fade-in">
        <h2 className="text-4xl font-bold text-white mb-6">Meet Your AI Team</h2>
        <p className="text-xl text-slate-300 max-w-3xl mx-auto leading-relaxed">
          Our specialized AI agents work together to transform your ideas into polished, engaging content.
        </p>
      </div>
      
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-8">
        {agents.map((agent, index) => (
          <div key={index} className="group relative animate-fade-in" style={{animationDelay: `${0.1 * index}s`}}>
            <div className={`absolute inset-0 bg-gradient-to-br ${agent.bgColor} rounded-3xl blur-xl opacity-0 group-hover:opacity-100 transition-all duration-700`}></div>
            <div className="relative bg-white/10 backdrop-blur-xl rounded-3xl border border-white/20 p-8 text-center group-hover:scale-105 transition-all duration-500 hover:shadow-2xl hover:border-white/40 hover:bg-white/20">
              <div className={`w-20 h-20 bg-gradient-to-br ${agent.color} rounded-2xl flex items-center justify-center mx-auto mb-6 group-hover:shadow-lg transition-all duration-500 transform group-hover:scale-110 group-hover:animate-pulse-slow`}>
                {agent.icon}
              </div>
              <h3 className="text-xl font-bold text-white mb-3 group-hover:text-transparent group-hover:bg-gradient-to-r group-hover:from-blue-400 group-hover:to-purple-400 group-hover:bg-clip-text transition-all duration-500">{agent.name}</h3>
              <p className="text-slate-300 leading-relaxed group-hover:text-slate-200 transition-colors duration-300">{agent.description}</p>
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}

export default AgentGrid
