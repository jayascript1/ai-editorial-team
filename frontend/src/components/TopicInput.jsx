import { useState } from 'react'

const TopicInput = ({ onSubmit, disabled }) => {
  const [topic, setTopic] = useState('How AI is transforming creative industries')

  const handleSubmit = (e) => {
    e.preventDefault()
    if (topic.trim() && !disabled) {
      onSubmit(topic.trim())
    }
  }

  return (
    <div className="relative">
      <div className="absolute inset-0 bg-gradient-to-r from-blue-500/20 to-purple-600/20 rounded-3xl blur-xl"></div>
      <div className="relative bg-white/10 backdrop-blur-xl rounded-3xl border border-white/20 p-8 shadow-2xl max-w-2xl mx-auto">
        <div className="text-center mb-8">
          <h2 className="text-3xl font-bold text-white mb-3">Choose Your Topic</h2>
          <p className="text-slate-300 text-lg">Enter any topic and watch our AI team create amazing content</p>
        </div>
        
        <form onSubmit={handleSubmit} className="space-y-6">
          <div>
            <label htmlFor="topic" className="block text-sm font-semibold text-slate-200 mb-3">
              Topic
            </label>
            <textarea
              id="topic"
              value={topic}
              onChange={(e) => setTopic(e.target.value)}
              disabled={disabled}
              className="w-full px-6 py-4 bg-white/10 backdrop-blur-sm border border-white/20 rounded-2xl text-white placeholder-slate-400 resize-none h-28 focus:outline-none focus:ring-2 focus:ring-blue-400/50 focus:border-blue-400/50 transition-all duration-300"
              placeholder="Enter your topic here..."
              required
            />
          </div>
          
          <button
            type="submit"
            disabled={disabled || !topic.trim()}
            className="w-full bg-gradient-to-r from-blue-500 to-purple-600 hover:from-blue-600 hover:to-purple-700 text-white font-semibold py-4 px-8 rounded-2xl transition-all duration-300 transform hover:scale-105 hover:shadow-2xl disabled:opacity-50 disabled:cursor-not-allowed disabled:transform-none disabled:shadow-none"
          >
            {disabled ? (
              <div className="flex items-center justify-center space-x-3">
                <div className="w-5 h-5 border-2 border-white border-t-transparent rounded-full animate-spin"></div>
                <span>Processing...</span>
              </div>
            ) : (
              'Generate Content'
            )}
          </button>
        </form>
        
        <div className="mt-6 text-center">
          <p className="text-sm text-slate-400">
            Our AI team will research, write, edit, and create social media content for your topic.
          </p>
        </div>
      </div>
    </div>
  )
}

export default TopicInput
