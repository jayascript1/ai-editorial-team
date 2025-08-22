# AI Editorial Team - Backend

A Flask API backend that integrates with your existing CrewAI Python code to provide a RESTful interface for the AI Editorial Team frontend.

## Features

- 🚀 **Flask API**: Fast, lightweight Python web framework
- 🔗 **CORS Support**: Cross-origin resource sharing enabled
- 🧵 **Async Processing**: Background processing for AI tasks
- 📊 **Status Tracking**: Real-time progress monitoring
- 🔌 **CrewAI Integration**: Seamless integration with your existing Python code

## Setup

### Prerequisites

- Python 3.8+
- pip
- Your existing CrewAI environment

### Installation

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Set up your environment variables:
```bash
cp .env.example .env
# Edit .env with your OpenAI API key
```

3. Run the backend:
```bash
python app.py
```

The API will be available at `http://localhost:5000`

## API Endpoints

### POST /api/generate-content
Start the AI content generation process.

**Request Body:**
```json
{
  "topic": "Your topic here"
}
```

**Response:**
```json
{
  "message": "Content generation started",
  "topic": "Your topic here"
}
```

### GET /api/status
Get the current processing status.

**Response:**
```json
{
  "is_processing": true,
  "current_step": 1,
  "total_steps": 4,
  "topic": "Your topic",
  "result": null
}
```

### GET /api/results
Get the generated content results.

**Response:**
```json
{
  "research": "Research insights...",
  "article": "Article content...",
  "edited": "Edited version...",
  "tweet": "Social media post..."
}
```

### GET /api/health
Health check endpoint.

**Response:**
```json
{
  "status": "healthy",
  "message": "AI Editorial Team API is running"
}
```

## Integration with CrewAI

The backend is designed to work with your existing `main.py` file. To integrate:

1. **Modify the import**: Update the import statement in `app.py` to match your file structure
2. **Call your functions**: Replace the simulated processing with actual calls to your CrewAI functions
3. **Handle results**: Parse the CrewAI output and format it for the frontend

Example integration:
```python
# In process_crew_ai function
crew = create_crew(topic)  # Your existing function
result = run_crew(crew)    # Your existing function

# Parse and format the result for the frontend
processing_status['result'] = parse_crew_result(result)
```

## Development

### Running in Development Mode
```bash
python app.py
```

### Running with Gunicorn (Production)
```bash
gunicorn -w 4 -b 0.0.0.0:5000 app:app
```

### Environment Variables
- `OPENAI_API_KEY`: Your OpenAI API key
- `FLASK_ENV`: Set to 'development' for debug mode

## Error Handling

The backend includes comprehensive error handling:
- Invalid requests
- Processing conflicts
- CrewAI errors
- Network issues

## Security

- CORS enabled for frontend integration
- Input validation
- Error message sanitization

## Monitoring

The backend provides real-time status updates:
- Processing state
- Current step
- Error messages
- Completion status

## Troubleshooting

### Common Issues

1. **Import Errors**: Check your file paths and CrewAI installation
2. **API Key Issues**: Verify your OpenAI API key in the environment
3. **CORS Errors**: Ensure the frontend URL is allowed in CORS settings

### Debug Mode

Enable debug mode for detailed error messages:
```python
app.run(debug=True)
```

## License

This project is part of the AI Editorial Team application.
