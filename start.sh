#!/bin/bash

echo "🚀 Starting AI Editorial Team..."
echo ""

# Check if .env file exists
if [ ! -f .env ]; then
    echo "⚠️  Warning: .env file not found!"
    echo "   Please create a .env file with your OPENAI_API_KEY"
    echo "   Example: OPENAI_API_KEY=your_key_here"
    echo ""
fi

# Start backend
echo "🐍 Starting Python backend (Flask + CrewAI)..."
cd backend
python3 app.py &
BACKEND_PID=$!
cd ..

# Wait a moment for backend to start
sleep 3

# Start frontend
echo "⚛️  Starting React frontend..."
cd frontend
npm run dev &
FRONTEND_PID=$!
cd ..

echo ""
echo "✅ Services started!"
echo "   Backend: http://localhost:5001"
echo "   Frontend: http://localhost:5173"
echo ""
echo "Press Ctrl+C to stop all services"

# Wait for user to stop
trap "echo ''; echo '🛑 Stopping services...'; kill $BACKEND_PID $FRONTEND_PID; exit" INT
wait
