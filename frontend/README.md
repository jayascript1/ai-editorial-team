# AI Editorial Team - Frontend

A sleek, modern React UI for the AI Editorial Team powered by CrewAI. This frontend provides an elegant interface for generating AI-powered content through research, writing, editing, and social media creation.

## Features

- 🎨 **Modern Design**: Clean, minimal UI built with Tailwind CSS
- 🚀 **Responsive**: Works seamlessly on desktop and mobile devices
- ⚡ **Fast**: Built with Vite for lightning-fast development and builds
- 🔄 **Real-time Updates**: Live progress tracking during AI processing
- 📱 **Social Media Preview**: Twitter-style preview for generated content
- 📋 **Copy to Clipboard**: Easy content copying for all generated materials

## Tech Stack

- **React 18** - Modern React with hooks
- **Vite** - Fast build tool and dev server
- **Tailwind CSS** - Utility-first CSS framework
- **JavaScript (ES6+)** - Modern JavaScript features

## Getting Started

### Prerequisites

- Node.js 16+ 
- npm or yarn

### Installation

1. Install dependencies:
```bash
npm install
```

2. Start the development server:
```bash
npm run dev
```

3. Open your browser and navigate to `http://localhost:5173`

### Building for Production

```bash
npm run build
```

The built files will be in the `dist` folder.

## Project Structure

```
src/
├── components/          # React components
│   ├── Header.jsx      # Navigation header
│   ├── TopicInput.jsx  # Topic input form
│   ├── AgentGrid.jsx   # AI agents showcase
│   ├── ProcessFlow.jsx # Workflow visualization
│   └── Results.jsx     # Results display
├── api/                # API services
│   └── aiService.js    # AI service integration
├── App.jsx             # Main application component
├── main.jsx            # Application entry point
└── index.css           # Tailwind CSS and custom styles
```

## Components

### Header
Navigation header with branding and menu items.

### TopicInput
Form for entering topics to generate content about.

### AgentGrid
Showcase of the four AI agents (Research, Writing, Editing, Social Media).

### ProcessFlow
Visual representation of the AI workflow with real-time progress tracking.

### Results
Display of generated content with copy-to-clipboard functionality.

## Customization

### Colors
The color scheme can be customized in `tailwind.config.js` under the `primary` color palette.

### Animations
Custom animations are defined in the Tailwind config and can be modified or extended.

### Styling
Component-specific styles are defined in `src/index.css` using Tailwind's `@layer components`.

## Integration with Python Backend

The frontend is designed to work with your Python CrewAI program. To integrate:

1. Create API endpoints in your Python backend
2. Update the `aiService.js` file to make actual API calls
3. Handle real-time updates through WebSocket or polling

Example API integration:
```javascript
const response = await fetch('/api/generate-content', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({ topic })
})
```

## Development

### Adding New Components
1. Create the component file in `src/components/`
2. Import and use in `App.jsx`
3. Follow the existing component patterns

### Styling
- Use Tailwind CSS utility classes
- Add custom styles in `src/index.css` using `@layer components`
- Maintain consistency with the existing design system

### State Management
The app uses React's built-in state management with hooks. For larger applications, consider adding Redux or Zustand.

## Browser Support

- Chrome 90+
- Firefox 88+
- Safari 14+
- Edge 90+

## License

This project is part of the AI Editorial Team application.

## Contributing

1. Follow the existing code style
2. Use meaningful component and variable names
3. Add comments for complex logic
4. Test on multiple devices and browsers
