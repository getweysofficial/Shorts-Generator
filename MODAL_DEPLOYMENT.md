# 🚀 Modal Deployment Guide for Shorts Generator

This guide will walk you through deploying your Shorts Generator backend to Modal.

## 📋 Prerequisites

- Modal account (sign up at [modal.com](https://modal.com))
- Modal CLI installed: `pip install modal`
- Modal authentication: `modal token new`

## 🔧 Step 1: Install Modal

```bash
pip install modal
```

Or add to your `pyproject.toml`:

```toml
dependencies = [
    # ... existing dependencies ...
    "modal>=0.64.0",
]
```

## 🔐 Step 2: Create Modal Secrets

Modal uses secrets to store environment variables securely. Create a secret with all your configuration:

```bash
modal secret create shorts-generator-secrets \
  GEMINI_API_KEY=your_gemini_key \
  GROQ_API_KEY=your_groq_key \
  BUCKET_NAME=your_bucket_name \
  AWS_REGION=your_aws_region \
  AWS_ACCESS_KEY=your_aws_access_key \
  AWS_SECRET_KEY=your_aws_secret_key \
  SUPABASE_ANON_KEY=your_supabase_key \
  SENDER_EMAIL_ADDRESS=your_email \
  APP_PASSWORD=your_app_password \
  SENDER_HOST=smtp.gmail.com \
  SENDER_PORT=587
```

**Note:** You can also create secrets via the Modal dashboard at https://modal.com/secrets

## 📁 Step 3: Project Structure

Ensure your project structure looks like this:

```
Shorts-Generator/
├── modal_app.py          # Modal deployment file (new)
├── src/
│   ├── api.py
│   ├── config.py
│   ├── task.py
│   ├── model.py
│   ├── mail_sender.py
│   └── shorts_generator/
│       ├── __init__.py
│       ├── audio_trancriber.py
│       ├── prompt.py
│       ├── shorts_agent.py
│       ├── utils.py
│       └── video_processor.py
└── pyproject.toml
```

## 🚀 Step 4: Deploy to Modal

Deploy your app:

```bash
modal deploy modal_app.py
```

This will:
1. Build the Docker image with all dependencies
2. Upload your code
3. Deploy the FastAPI app as a web endpoint
4. Make the background task function available

## 🌐 Step 5: Get Your API URL

After deployment, Modal will provide you with a URL like:

```
https://your-username--shorts-generator-fastapi-app.modal.run
```

You can also find this in the Modal dashboard.

## 📊 Step 6: Test Your Deployment

```bash
# Test the API docs
curl https://your-username--shorts-generator-fastapi-app.modal.run/docs

# Test a simple endpoint
curl https://your-username--shorts-generator-fastapi-app.modal.run/get-upload-url/?user_id=test&filename=test.mp4
```

## 🔄 Step 7: Update Your Frontend

Update your frontend to use the Modal URL instead of your local/EC2 URL:

```typescript
const API_URL = "https://your-username--shorts-generator-fastapi-app.modal.run"
```

## 🎯 Key Differences from Celery/Redis Setup

### 1. **No Redis Required**
   - Modal handles task queuing internally
   - No need to run Redis server

### 2. **Task Execution**
   - Old: `get_shorts_from_video.delay(...)` (Celery)
   - New: `generate_shorts_task.spawn(...)` (Modal)

### 3. **Task Status**
   - Modal provides task tracking via dashboard
   - You may want to implement a database to track task status
   - Or use Modal's function call tracking

### 4. **Scaling**
   - Modal automatically scales based on demand
   - No need to manage worker processes
   - Scales to zero when not in use

## 📝 Step 8: Monitor Your Deployment

### Modal Dashboard

Visit https://modal.com/apps to see:
- Function invocations
- Logs
- Resource usage
- Errors

### View Logs

```bash
modal app logs shorts-generator
```

## 🔧 Configuration Options

### Adjust Resources

Edit `modal_app.py` to change resource allocation:

```python
@app.function(
    # ... other config ...
    cpu=8,        # More CPUs for faster processing
    memory=16384,  # 16GB RAM for large videos
    gpu="T4",     # Add GPU if needed for ML models
    timeout=7200,  # 2 hour timeout
)
```

### Use GPU (Optional)

If you need GPU acceleration:

```python
@app.function(
    # ... other config ...
    gpu="T4",  # or "A10G", "A100", etc.
)
```

## 🆘 Troubleshooting

### Common Issues

1. **Import Errors**
   - Ensure all imports use absolute paths from `/root/src`
   - Check that `sys.path.insert(0, "/root/src")` is in your functions

2. **File Not Found**
   - Modal functions run in isolated containers
   - Use Modal Volumes for persistent storage
   - Temporary files should use `/tmp` directory

3. **Timeout Errors**
   - Increase `timeout` parameter in function decorator
   - Default is 300 seconds (5 minutes)

4. **Memory Issues**
   - Increase `memory` parameter
   - Consider processing videos in smaller chunks

### View Function Logs

```bash
# View logs for a specific function
modal function logs generate_shorts_task

# View logs for the web app
modal function logs fastapi_app
```

### Debug Locally

You can test Modal functions locally:

```bash
modal run modal_app.py::generate_shorts_task --user-id test --user-email test@test.com --video-url https://... --shorts-time 60 --task-id test-123
```

## 💰 Cost Considerations

Modal pricing:
- **Free tier**: $30/month in compute credits
- **Pay-as-you-go**: Only pay for what you use
- **Scales to zero**: No cost when idle

Compare to EC2:
- EC2: Pay for instance 24/7
- Modal: Pay only when processing videos

## 🔄 Updating Your Deployment

When you make changes:

```bash
# Redeploy
modal deploy modal_app.py

# Or deploy with a specific name
modal deploy modal_app.py --name shorts-generator-v2
```

## 📚 Additional Resources

- [Modal Documentation](https://modal.com/docs)
- [Modal Python SDK](https://modal.com/docs/reference)
- [FastAPI on Modal](https://modal.com/docs/guide/ex/fastapi)
- [Modal Examples](https://modal.com/docs/examples)

## 🎉 Next Steps

1. Set up custom domain (optional)
2. Configure rate limiting
3. Add monitoring/alerting
4. Implement task status tracking in a database
5. Set up CI/CD for automatic deployments

---

**Note:** Remember to keep your secrets secure and never commit them to version control!

