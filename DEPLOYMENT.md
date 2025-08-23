# AI Editorial Team - Vercel Deployment Guide

## Current Deployment Status

### ✅ Frontend Deployment
The frontend (React app) can be deployed to Vercel successfully.

### ⚠️ Backend Challenge
The backend API with CrewAI dependencies is too large for Vercel's serverless function limits (250MB unzipped). This is common with AI/ML applications that have heavy dependencies.

## Deployment Strategy

### Option 1: Frontend-Only Deployment (Recommended for Demo)
Deploy only the frontend to Vercel for demonstration purposes:

```bash
# Deploy frontend only
vercel --yes
```

The frontend will be available at: `https://ai-editorial-team-[hash].vercel.app`

### Option 2: Hybrid Deployment (Recommended for Production)

1. **Frontend on Vercel**: Deploy the React frontend to Vercel
2. **Backend on Railway/Render**: Deploy the Flask backend to a platform that supports longer-running processes

#### Backend Deployment Options:

**Railway.app**:
```bash
# Install Railway CLI
npm install -g @railway/cli

# Login and deploy backend
railway login
cd backend
railway init
railway up
```

**Render.com**:
1. Connect your GitHub repository
2. Create a new Web Service
3. Set build command: `cd backend && pip install -r requirements.txt`
4. Set start command: `cd backend && python app.py`

### Option 3: Full Docker Deployment
Use Docker containers for both frontend and backend:

```dockerfile
# Dockerfile for backend
FROM python:3.10-slim
WORKDIR /app
COPY backend/requirements.txt .
RUN pip install -r requirements.txt
COPY backend/ .
EXPOSE 5001
CMD [\"python\", \"app.py\"]
```

## Environment Variables

For any deployment platform, set these environment variables:

```bash
OPENAI_API_KEY=your_openai_api_key_here
OPENAI_MODEL=gpt-4o-mini
```

## Current Deployment

The frontend is currently deployed to Vercel. To use it with a separate backend:

1. Update the API URL in `frontend/src/api/aiService.js`
2. Deploy the backend to Railway, Render, or another platform
3. Update CORS settings in the backend to allow your Vercel domain

## Next Steps

1. **For Demo**: Use the current Vercel frontend deployment
2. **For Production**: Deploy backend separately and update API URLs
3. **For Full Features**: Set up environment variables on the backend platform

## URLs

- **Frontend**: Will be provided after deployment
- **Backend**: Deploy separately to Railway/Render
- **Repository**: GitHub repository for continuous deployment

## Support

For issues with:
- Vercel deployment: Check Vercel dashboard
- Backend deployment: Use Railway or Render documentation
- Environment variables: Ensure OpenAI API key is properly set