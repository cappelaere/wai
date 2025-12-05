# Scholarship Copilot - Deployment Guide

Complete guide for deploying Scholarship Copilot to production.

## Pre-Deployment Checklist

### Local Development Testing
- [ ] Run `validate_setup.py` - all checks pass
- [ ] Backend starts without errors: `python run.py`
- [ ] Frontend loads at http://localhost:3000
- [ ] Health check passes: `curl http://localhost:8000/health`
- [ ] Create a test session and send a query
- [ ] Verify all 4 MCP servers are initialized

### Code Quality
- [ ] No Python syntax errors: `python -m py_compile app/**/*.py`
- [ ] No hardcoded secrets in code
- [ ] All imports are valid
- [ ] Logging is configured appropriately

### Environment Configuration
- [ ] `.env` file with all required variables
- [ ] `ANTHROPIC_API_KEY` is set and valid
- [ ] `ENVIRONMENT=production`
- [ ] `PROCESSOR_OUTPUT_PATH` points to valid data
- [ ] `ALLOWED_ORIGINS` configured for your domain

## Environment Variables Reference

```env
# Server Configuration
FASTAPI_HOST=0.0.0.0
FASTAPI_PORT=8000
ENVIRONMENT=production
DEBUG=false

# Claude API
ANTHROPIC_API_KEY=sk-ant-... (REQUIRED)
CLAUDE_MODEL=claude-opus-4-1
CLAUDE_MAX_TOKENS=2048

# Paths
PROCESSOR_OUTPUT_PATH=/path/to/output
APPLICATION_DATA_PATH=/path/to/data

# Session Configuration
SESSION_TIMEOUT=3600  # 1 hour in seconds
MAX_HISTORY=100

# CORS
ALLOWED_ORIGINS=https://yourdomain.com,https://www.yourdomain.com

# Logging
LOG_LEVEL=INFO
LOG_FILE=/var/log/scholarship-copilot.log
```

## Deployment Options

### Option 1: Docker (Recommended)

#### 1. Create Dockerfile

```dockerfile
FROM python:3.13-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY web/backend/requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY web/backend/app ./app
COPY processor ./processor
COPY output ./output

# Create non-root user
RUN useradd -m -u 1000 appuser && chown -R appuser:appuser /app
USER appuser

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health')"

# Run application
CMD ["python", "-m", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

#### 2. Create docker-compose.yml

```yaml
version: '3.8'

services:
  web:
    build: .
    ports:
      - "8000:8000"
    environment:
      - FASTAPI_HOST=0.0.0.0
      - FASTAPI_PORT=8000
      - ENVIRONMENT=production
      - ANTHROPIC_API_KEY=${ANTHROPIC_API_KEY}
      - CLAUDE_MODEL=claude-opus-4-1
    volumes:
      - ./output:/app/output:ro
      - ./logs:/app/logs
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3

  frontend:
    image: nginx:alpine
    ports:
      - "80:80"
    volumes:
      - ./web/frontend:/usr/share/nginx/html:ro
      - ./nginx.conf:/etc/nginx/nginx.conf:ro
    restart: unless-stopped
```

#### 3. Build and Run

```bash
# Build image
docker build -t scholarship-copilot .

# Run container
docker run -p 8000:8000 \
  -e ANTHROPIC_API_KEY=sk-ant-... \
  -v $(pwd)/output:/app/output:ro \
  -v $(pwd)/logs:/app/logs \
  scholarship-copilot

# Or use docker-compose
docker-compose up -d
```

### Option 2: Systemd Service (Linux)

#### 1. Create Service File

Create `/etc/systemd/system/scholarship-copilot.service`:

```ini
[Unit]
Description=Scholarship Copilot FastAPI Server
After=network.target

[Service]
Type=notify
User=scholarship
WorkingDirectory=/opt/scholarship-copilot
Environment="PATH=/opt/scholarship-copilot/venv/bin"
ExecStart=/opt/scholarship-copilot/venv/bin/python -m uvicorn app.main:app --host 0.0.0.0 --port 8000
ExecReload=/bin/kill -s HUP $MAINPID
KillMode=process
Restart=on-failure
RestartSec=5

[Install]
WantedBy=multi-user.target
```

#### 2. Enable and Start Service

```bash
sudo systemctl daemon-reload
sudo systemctl enable scholarship-copilot
sudo systemctl start scholarship-copilot
sudo systemctl status scholarship-copilot
```

### Option 3: Manual Deployment with Gunicorn

#### 1. Install Gunicorn

```bash
pip install gunicorn
```

#### 2. Create startup script

```bash
#!/bin/bash
cd /opt/scholarship-copilot
source venv/bin/activate
gunicorn \
  --workers 4 \
  --worker-class uvicorn.workers.UvicornWorker \
  --bind 0.0.0.0:8000 \
  --access-logfile /var/log/scholarship-copilot-access.log \
  --error-logfile /var/log/scholarship-copilot-error.log \
  --log-level info \
  app.main:app
```

## Post-Deployment Configuration

### 1. Reverse Proxy (Nginx)

Create `/etc/nginx/sites-available/scholarship-copilot`:

```nginx
upstream scholarship_api {
    server localhost:8000;
}

server {
    listen 80;
    server_name yourdomain.com;

    # Redirect to HTTPS
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name yourdomain.com;

    # SSL Configuration
    ssl_certificate /etc/letsencrypt/live/yourdomain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/yourdomain.com/privkey.pem;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;

    # Security Headers
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-Frame-Options "SAMEORIGIN" always;

    # API Proxy
    location /api/ {
        proxy_pass http://scholarship_api;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_read_timeout 300s;
        proxy_connect_timeout 300s;
    }

    # Health Check Endpoint
    location /health {
        proxy_pass http://scholarship_api;
    }

    # Frontend
    location / {
        root /var/www/scholarship-copilot;
        try_files $uri /index.html;
    }
}
```

Enable site:
```bash
sudo ln -s /etc/nginx/sites-available/scholarship-copilot /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

### 2. SSL/TLS with Let's Encrypt

```bash
sudo apt-get install certbot python3-certbot-nginx
sudo certbot certonly --nginx -d yourdomain.com -d www.yourdomain.com
```

### 3. Monitoring and Logging

#### Configure Logging

Update `app/config.py` for production logging:

```python
LOG_LEVEL = "INFO"
LOG_FILE = "/var/log/scholarship-copilot/app.log"
```

#### Monitor with Systemd

```bash
# View logs
journalctl -u scholarship-copilot -f

# View last 100 lines
journalctl -u scholarship-copilot -n 100
```

#### Configure Log Rotation

Create `/etc/logrotate.d/scholarship-copilot`:

```
/var/log/scholarship-copilot/*.log {
    daily
    rotate 14
    compress
    delaycompress
    notifempty
    create 0640 scholarship scholarship
    sharedscripts
    postrotate
        systemctl reload scholarship-copilot > /dev/null 2>&1 || true
    endscript
}
```

### 4. Database Setup (Recommended for Production)

Replace in-memory session storage with PostgreSQL:

```bash
sudo apt-get install postgresql postgresql-contrib

# Create database
sudo -u postgres createdb scholarship_copilot
sudo -u postgres createuser scholarship -P

# Grant permissions
sudo -u postgres psql -c "GRANT ALL PRIVILEGES ON DATABASE scholarship_copilot TO scholarship;"
```

Update `.env`:
```env
DATABASE_URL=postgresql://scholarship:password@localhost/scholarship_copilot
```

### 5. Backup Strategy

```bash
#!/bin/bash
# Daily backup script
BACKUP_DIR=/backups/scholarship-copilot
mkdir -p $BACKUP_DIR

# Backup processor output
tar -czf $BACKUP_DIR/output-$(date +%Y%m%d).tar.gz output/

# Backup database (if using PostgreSQL)
pg_dump scholarship_copilot | gzip > $BACKUP_DIR/db-$(date +%Y%m%d).sql.gz

# Keep only last 30 days
find $BACKUP_DIR -type f -mtime +30 -delete
```

Add to crontab:
```bash
0 2 * * * /opt/scholarship-copilot/backup.sh
```

## Performance Tuning

### 1. Gunicorn Workers

Calculate optimal workers: `(2 × CPU cores) + 1`

```bash
gunicorn --workers 9 ...  # For 4-core system
```

### 2. Session Cleanup

Automatic cleanup of expired sessions (built-in). Configure timeout in `.env`:
```env
SESSION_TIMEOUT=3600  # Adjust as needed
```

### 3. Database Connection Pooling

If using PostgreSQL, add to `app/config.py`:
```python
SQLALCHEMY_POOL_SIZE = 20
SQLALCHEMY_MAX_OVERFLOW = 0
```

### 4. Rate Limiting

Add rate limiting middleware to `app/main.py`:
```python
from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
```

## Security Hardening

### 1. API Authentication

Add bearer token authentication:
```python
from fastapi import HTTPException, Depends
from fastapi.security import HTTPBearer

security = HTTPBearer()

async def verify_token(credentials = Depends(security)):
    if credentials.credentials != os.getenv("API_TOKEN"):
        raise HTTPException(status_code=401)
    return credentials
```

### 2. Input Validation

- All endpoints use Pydantic for validation (already implemented)
- Validate file uploads (size limits, file types)
- Implement SQL injection prevention (using SQLAlchemy)

### 3. CORS Configuration

Only allow your frontend domain:
```env
ALLOWED_ORIGINS=https://yourdomain.com
```

### 4. Security Headers

Nginx configuration includes:
- HSTS (HTTP Strict Transport Security)
- X-Content-Type-Options: nosniff
- X-Frame-Options: SAMEORIGIN
- Content-Security-Policy

### 5. Regular Updates

```bash
# Update dependencies monthly
pip install --upgrade -r requirements.txt
```

## Monitoring and Alerts

### Health Check

```bash
# Monitor endpoint availability
curl -f https://yourdomain.com/health || alert "Service down"
```

### Application Metrics

Monitor via logs:
```bash
# Check error rate
grep "ERROR" /var/log/scholarship-copilot/app.log | wc -l

# Check response times
grep "ms" /var/log/scholarship-copilot/app.log | tail -10
```

### Alerting Setup

Configure with your monitoring system (e.g., Prometheus, DataDog):
```
- Alert on service down (health check fails)
- Alert on error rate > 5%
- Alert on response time > 5s
- Alert on disk space < 10%
```

## Troubleshooting Production Issues

### Service Won't Start
```bash
# Check logs
journalctl -u scholarship-copilot -n 50

# Check port in use
sudo lsof -i :8000

# Check file permissions
ls -la /opt/scholarship-copilot
```

### High Memory Usage
```bash
# Check memory by process
ps aux | grep python

# Reduce worker count or increase SESSION_TIMEOUT
```

### Database Connection Issues
```bash
# Test database connection
psql -h localhost -U scholarship -d scholarship_copilot

# Check connection string in .env
```

### SSL Certificate Issues
```bash
# Check certificate expiration
ssl-cert-check -c /etc/letsencrypt/live/yourdomain.com/fullchain.pem

# Renew certificate
sudo certbot renew
```

## Rollback Procedure

```bash
# Keep previous version
cp -r /opt/scholarship-copilot /opt/scholarship-copilot.backup

# Rollback if needed
rm -rf /opt/scholarship-copilot
mv /opt/scholarship-copilot.backup /opt/scholarship-copilot
systemctl restart scholarship-copilot
```

## Post-Deployment Testing

### 1. Smoke Tests

```bash
# Health check
curl https://yourdomain.com/health

# Create session
curl -X POST https://yourdomain.com/api/v1/sessions \
  -H "Content-Type: application/json" \
  -d '{"user_id":"test"}'

# Send query
curl -X POST https://yourdomain.com/api/v1/chat \
  -H "Content-Type: application/json" \
  -d '{"query":"test","session_id":"..."}'
```

### 2. Load Testing

```bash
# Using Apache Bench
ab -n 100 -c 10 https://yourdomain.com/health

# Using wrk
wrk -t4 -c100 -d30s https://yourdomain.com/health
```

### 3. Browser Testing

- Open https://yourdomain.com in browser
- Create new session
- Send test queries
- Verify responses display correctly

## Maintenance Schedule

- **Daily**: Review error logs
- **Weekly**: Check disk space and backups
- **Monthly**: Update dependencies, review performance metrics
- **Quarterly**: Security audit, performance tuning
- **Yearly**: Disaster recovery testing

## Support & Documentation

- **API Documentation**: https://yourdomain.com/docs
- **Logs**: `/var/log/scholarship-copilot/`
- **Configuration**: `/opt/scholarship-copilot/.env`
- **Code**: https://github.com/yourusername/scholarships

---

**Last Updated**: November 2024
**Version**: 1.0
**Status**: Production Ready
