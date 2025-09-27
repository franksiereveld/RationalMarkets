# 🚀 Deployment Guide

This guide covers multiple deployment options for the AI Long/Short Investment Club educational platform.

## 📋 **Prerequisites**

### **Required**
- Python 3.11 or higher
- Git for version control
- Basic command line knowledge

### **Optional (for specific deployments)**
- Docker and Docker Compose
- Cloud platform account (Heroku, Vercel, GCP, AWS)
- Domain name for custom hosting

## 🏠 **Local Development**

### **Quick Start**
```bash
# Clone the repository
git clone https://github.com/yourusername/ai-longshort-investment-club.git
cd ai-longshort-investment-club

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Run in demo mode
python app.py
```

Visit `http://localhost:5000` to access the platform.

### **Environment Configuration**
```bash
# Copy environment template
cp .env.example .env

# Edit .env file with your settings (optional for demo mode)
# ALPACA_API_KEY=your_paper_api_key
# ALPACA_SECRET_KEY=your_paper_secret_key
# SWISSQUOTE_CLIENT_ID=your_oauth_client_id
# SWISSQUOTE_CLIENT_SECRET=your_oauth_client_secret
```

## 🐳 **Docker Deployment**

### **Single Container**
```bash
# Build the image
docker build -t ai-longshort-club .

# Run the container
docker run -p 5000:5000 ai-longshort-club
```

### **Docker Compose (Recommended)**
```bash
# Start all services
docker-compose up -d

# View logs
docker-compose logs -f

# Stop services
docker-compose down
```

### **Production with Nginx**
```bash
# Start with nginx reverse proxy
docker-compose --profile production up -d
```

## ☁️ **Cloud Deployment Options**

### **1. Heroku (Easiest)**

#### **One-Click Deploy**
[![Deploy to Heroku](https://www.herokucdn.com/deploy/button.svg)](https://heroku.com/deploy)

#### **Manual Deploy**
```bash
# Install Heroku CLI
# Create Heroku app
heroku create your-app-name

# Set environment variables (optional)
heroku config:set FLASK_ENV=production

# Deploy
git push heroku main

# Open app
heroku open
```

### **2. Vercel (Frontend Focus)**
```bash
# Install Vercel CLI
npm i -g vercel

# Deploy
vercel

# Follow prompts for configuration
```

### **3. Google Cloud Platform**
```bash
# Install gcloud CLI
# Initialize project
gcloud init

# Deploy to App Engine
gcloud app deploy

# View app
gcloud app browse
```

### **4. AWS (Advanced)**

#### **Elastic Beanstalk**
```bash
# Install EB CLI
pip install awsebcli

# Initialize application
eb init

# Create environment
eb create production

# Deploy
eb deploy
```

#### **ECS with Fargate**
```bash
# Build and push to ECR
aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin your-account.dkr.ecr.us-east-1.amazonaws.com

docker build -t ai-longshort-club .
docker tag ai-longshort-club:latest your-account.dkr.ecr.us-east-1.amazonaws.com/ai-longshort-club:latest
docker push your-account.dkr.ecr.us-east-1.amazonaws.com/ai-longshort-club:latest

# Deploy via ECS console or CLI
```

## 🔧 **Configuration Options**

### **Environment Variables**
```bash
# Flask Configuration
FLASK_ENV=production          # production, development
FLASK_DEBUG=0                 # 0 for production, 1 for development
FLASK_HOST=0.0.0.0           # Host to bind to
FLASK_PORT=5000              # Port to run on

# Broker API Keys (Optional - platform works in demo mode)
ALPACA_API_KEY=your_key
ALPACA_SECRET_KEY=your_secret
ALPACA_BASE_URL=https://paper-api.alpaca.markets

SWISSQUOTE_CLIENT_ID=your_client_id
SWISSQUOTE_CLIENT_SECRET=your_client_secret
SWISSQUOTE_BASE_URL=https://api.swissquote.com

# Security
SECRET_KEY=your-secret-key-here
CORS_ORIGINS=https://yourdomain.com

# Logging
LOG_LEVEL=INFO               # DEBUG, INFO, WARNING, ERROR
LOG_FILE=app.log
```

### **Production Checklist**
- [ ] Set `FLASK_ENV=production`
- [ ] Set `FLASK_DEBUG=0`
- [ ] Configure proper `SECRET_KEY`
- [ ] Set up HTTPS/SSL certificates
- [ ] Configure CORS origins
- [ ] Set up monitoring and logging
- [ ] Configure backup strategy
- [ ] Test all broker integrations
- [ ] Verify educational disclaimers

## 🔒 **Security Considerations**

### **API Keys and Secrets**
- Never commit API keys to version control
- Use environment variables or secure secret management
- Rotate keys regularly
- Use paper trading accounts for educational purposes

### **HTTPS and SSL**
```nginx
# Example nginx configuration for SSL
server {
    listen 443 ssl;
    server_name yourdomain.com;
    
    ssl_certificate /path/to/certificate.crt;
    ssl_certificate_key /path/to/private.key;
    
    location / {
        proxy_pass http://localhost:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

### **Firewall and Access Control**
- Restrict access to admin endpoints
- Implement rate limiting
- Use Web Application Firewall (WAF)
- Monitor for suspicious activity

## 📊 **Monitoring and Logging**

### **Application Monitoring**
```python
# Health check endpoint available at /api/health
# Monitor response time and availability
# Set up alerts for downtime
```

### **Log Management**
```bash
# View application logs
tail -f app.log

# Docker logs
docker-compose logs -f ai-longshort-club

# Heroku logs
heroku logs --tail
```

### **Performance Monitoring**
- Monitor response times
- Track API call rates and limits
- Monitor memory and CPU usage
- Set up alerts for errors

## 🔄 **CI/CD Pipeline**

### **GitHub Actions (Included)**
The repository includes a complete CI/CD pipeline:
- Automated testing on push/PR
- Security scanning with bandit and safety
- Docker image building and pushing
- Deployment automation

### **Custom Deployment**
```yaml
# Example deployment step
- name: Deploy to production
  run: |
    # Your deployment commands here
    ssh user@server 'cd /app && git pull && docker-compose up -d'
```

## 🐛 **Troubleshooting**

### **Common Issues**

#### **Port Already in Use**
```bash
# Find process using port 5000
lsof -i :5000

# Kill process
kill -9 <PID>
```

#### **Module Not Found**
```bash
# Ensure virtual environment is activated
source venv/bin/activate

# Reinstall dependencies
pip install -r requirements.txt
```

#### **API Connection Issues**
- Verify API credentials are correct
- Check broker API status pages
- Ensure network connectivity
- Try demo mode first

#### **Docker Issues**
```bash
# Rebuild without cache
docker build --no-cache -t ai-longshort-club .

# Check container logs
docker logs <container_id>

# Clean up Docker resources
docker system prune -a
```

## 📈 **Scaling Considerations**

### **Horizontal Scaling**
- Use load balancer for multiple instances
- Implement session management
- Consider database for user data (if added)
- Use CDN for static assets

### **Performance Optimization**
- Enable gzip compression
- Implement caching strategies
- Optimize API call patterns
- Use connection pooling

## 🔄 **Updates and Maintenance**

### **Regular Updates**
```bash
# Pull latest changes
git pull origin main

# Update dependencies
pip install -r requirements.txt --upgrade

# Restart application
# (method depends on deployment type)
```

### **Backup Strategy**
- Regular code backups via Git
- Configuration backup
- Log file rotation
- Database backups (if applicable)

## 📞 **Support**

### **Getting Help**
- Check the [troubleshooting section](#troubleshooting)
- Review [GitHub Issues](https://github.com/yourusername/ai-longshort-investment-club/issues)
- Consult platform-specific documentation
- Join community discussions

### **Reporting Issues**
When reporting deployment issues, include:
- Deployment method used
- Error messages and logs
- Environment details (OS, Python version, etc.)
- Steps to reproduce the issue

---

**Remember**: This platform is for educational purposes only. Ensure all deployments include appropriate disclaimers and comply with local regulations.

