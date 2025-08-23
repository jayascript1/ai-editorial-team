# AI Editorial Team - Render Deployment Guide

## 🎯 Overview
This guide will help you deploy your AI Editorial Team backend to Render's free tier.

## 📋 Prerequisites
- GitHub account with your code pushed to a repository
- OpenAI API key
- Render account (free at render.com)

## 🚀 Step-by-Step Deployment

### Step 1: Prepare Your Repository
1. **Push your code to GitHub** (if not already done):
   ```bash
   git add .
   git commit -m "Prepare for Render deployment"
   git push origin main
   ```

### Step 2: Create Render Account
1. Go to [render.com](https://render.com)
2. Sign up with your GitHub account
3. Authorize Render to access your repositories

### Step 3: Deploy Backend to Render

#### 3.1 Create New Web Service
1. Click "New +" → "Web Service"
2. Connect your GitHub repository containing the AI Editorial Team
3. Configure the service:

   **Basic Settings:**
   - **Name**: `ai-editorial-team-backend`
   - **Region**: Oregon (US West)
   - **Branch**: `main`
   - **Root Directory**: `backend`
   - **Runtime**: Python 3

   **Build & Deploy:**
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `python app.py`

#### 3.2 Set Environment Variables
In the Environment section, add these variables:

| Variable Name | Value |
|---------------|-------|
| `OPENAI_API_KEY` | `your_actual_openai_api_key` |
| `OPENAI_MODEL` | `gpt-4o-mini` |
| `FLASK_ENV` | `production` |

**🔒 Security Note**: Never share your OpenAI API key publicly!

### Step 4: Deploy
1. Click "Create Web Service"
2. Wait for the build to complete (5-10 minutes)
3. Your backend will be available at: `https://your-service-name.onrender.com`

### Step 5: Update Frontend Configuration
Once your backend is deployed, update your Vercel frontend to use the new API URL:

1. **Get your Render URL**: Copy the URL from your Render dashboard (e.g., `https://ai-editorial-team-backend.onrender.com`)

2. **Update Frontend Environment Variables**: 
   
   **Option A: Direct Code Update**
   - Edit `frontend/src/api/aiService.js`
   - Replace `https://your-render-backend-url.onrender.com` with your actual Render URL
   
   **Option B: Environment Variables (Recommended)**
   - Update `frontend/.env.production` with your Render URL:
     ```
     VITE_API_URL=https://your-actual-render-url.onrender.com
     ```
   - In Vercel dashboard, add environment variable:
     - Key: `VITE_API_URL`
     - Value: `https://your-actual-render-url.onrender.com`

3. **Redeploy Frontend**: 
   ```bash
   git add .
   git commit -m "Update API URL for Render backend"
   git push origin main
   ```
   Vercel will automatically redeploy with the new configuration.

## 🧪 Testing Your Deployment

### Health Check
Visit `https://your-service-name.onrender.com/api/health` to verify the backend is running.

### Full Test
1. Go to your Vercel frontend URL
2. Enter a topic and click "Generate Content"
3. Watch the real-time progress as AI agents work

## 📊 Render Free Tier Limits
- **750 hours/month** of runtime
- **512 MB RAM**
- **0.1 CPU**
- **Sleeps after 15 minutes** of inactivity
- **Cold start time**: 30-60 seconds when waking up

## 🔧 Troubleshooting

### Common Issues:

**1. Build Fails - Requirements Installation**
- Check that `requirements.txt` is in the `backend` directory
- Verify all dependencies are correctly listed

**2. Service Won't Start**
- Check logs in Render dashboard
- Ensure `OPENAI_API_KEY` is set correctly
- Verify the start command is `python app.py`

**3. API Key Errors**
- Double-check your OpenAI API key is valid
- Ensure you have sufficient OpenAI credits
- Verify the key has the correct permissions

**4. CORS Issues**
- The backend is configured for CORS
- If issues persist, check the Flask-CORS configuration

**5. Cold Start Delays**
- First request after sleep takes 30-60 seconds
- This is normal for Render's free tier
- Consider upgrading to paid tier for production use

### Checking Logs:
1. Go to your Render dashboard
2. Select your service
3. Click "Logs" tab to see real-time output

## 🔗 Final URLs

After successful deployment:
- **Frontend**: `https://ai-editorial-team-[hash].vercel.app`
- **Backend**: `https://your-service-name.onrender.com`
- **API Health Check**: `https://your-service-name.onrender.com/api/health`

## 🎉 You're Done!

Your AI Editorial Team is now fully deployed and accessible worldwide! The frontend on Vercel will communicate with your backend on Render to provide the full AI-powered content generation experience.

## 💡 Next Steps
- Set up custom domains for both services
- Monitor usage and performance
- Consider upgrading to paid tiers for production workloads
- Set up monitoring and alerts for your services