# Sailor - Production Deployment Guide

This guide covers deploying Sailor to production with all security best practices implemented.

## 📋 Prerequisites

- Docker & Docker Compose installed
- Domain name with DNS configured
- SSL/TLS certificate (Let's Encrypt recommended)
- Redis instance (for rate limiting across multiple workers)
- Reverse proxy (Nginx recommended)

## 🔒 Security Checklist

Before deploying to production, ensure:

- [x] All P0 security fixes applied (v2.0.0+)
- [ ] SECRET_KEY set to secure random value
- [ ] CORS_ORIGINS configured for your domain(s)
- [ ] Rate limiting storage configured (Redis)
- [ ] HTTPS enforced
- [ ] API keys secured in environment variables
- [ ] Firewall rules configured
- [ ] Log aggregation set up
- [ ] Monitoring and alerts configured

## 🚀 Quick Start

### 1. Environment Configuration

Create `/home/user/sailor/backend/.env` (DO NOT commit this file):

```bash
# CRITICAL: Generate a secure SECRET_KEY
# Run: python -c 'import secrets; print(secrets.token_hex(32))'
SECRET_KEY=<your-64-character-hex-secret>

# Set to production
FLASK_ENV=production

# Configure allowed CORS origins (comma-separated)
CORS_ORIGINS=https://yourdomain.com,https://app.yourdomain.com

# Rate limiting with Redis (recommended for production)
RATE_LIMIT_STORAGE_URI=redis://redis:6379/0

# OAuth Configuration (optional)
GOOGLE_CLIENT_ID=your-client-id
GOOGLE_CLIENT_SECRET=your-client-secret

# Error Tracking with Sentry (optional but recommended)
SENTRY_DSN=https://your-public-key@o123456.ingest.sentry.io/7654321
SENTRY_TRACES_SAMPLE_RATE=0.1
SENTRY_RELEASE=sailor@2.0.0

# Prometheus Metrics (enabled by default)
ENABLE_METRICS=true
```

### 2. Docker Compose Production Setup

Create `docker-compose.prod.yml`:

```yaml
version: '3.8'

services:
  # Redis for rate limiting and caching
  redis:
    image: redis:7-alpine
    restart: unless-stopped
    command: redis-server --appendonly yes
    volumes:
      - redis-data:/data
    networks:
      - sailor-net
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 10s
      timeout: 3s
      retries: 3

  # Backend API
  backend:
    build:
      context: ./backend
      dockerfile: Dockerfile
    restart: unless-stopped
    ports:
      - "127.0.0.1:5000:5000"  # Bind to localhost only
    environment:
      - FLASK_ENV=production
      - SECRET_KEY=${SECRET_KEY}
      - CORS_ORIGINS=${CORS_ORIGINS}
      - RATE_LIMIT_STORAGE_URI=redis://redis:6379/0
      - OPENAI_API_KEY=${OPENAI_API_KEY:-}
      - ANTHROPIC_API_KEY=${ANTHROPIC_API_KEY:-}
      - SENTRY_DSN=${SENTRY_DSN:-}
      - SENTRY_TRACES_SAMPLE_RATE=${SENTRY_TRACES_SAMPLE_RATE:-0.1}
      - SENTRY_RELEASE=${SENTRY_RELEASE:-sailor@2.0.0}
      - ENABLE_METRICS=${ENABLE_METRICS:-true}
    env_file:
      - backend/.env
    depends_on:
      redis:
        condition: service_healthy
      mcp:
        condition: service_healthy
    networks:
      - sailor-net
    deploy:
      resources:
        limits:
          cpus: '1'
          memory: 1G
        reservations:
          cpus: '0.25'
          memory: 256M
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:5000/api/health"]
      interval: 30s
      timeout: 5s
      retries: 3
      start_period: 10s

  # MCP Server
  mcp:
    build:
      context: .
      dockerfile: Dockerfile.mcp-http
    restart: unless-stopped
    ports:
      - "127.0.0.1:8000:8000"  # Bind to localhost only
    environment:
      - SAILOR_LOG_LEVEL=INFO
      - PYTHONUNBUFFERED=1
    volumes:
      - ./output:/home/sailor/output
    networks:
      - sailor-net
    deploy:
      resources:
        limits:
          cpus: '2'
          memory: 2G
        reservations:
          cpus: '0.5'
          memory: 512M
    healthcheck:
      test: ["CMD", "python", "-c", "import socket; s=socket.socket(); s.connect(('localhost', 8000)); s.close()"]
      interval: 30s
      timeout: 5s
      retries: 3
      start_period: 15s

networks:
  sailor-net:
    driver: bridge

volumes:
  redis-data:
    driver: local
```

### 3. Nginx Reverse Proxy Configuration

Create `/etc/nginx/sites-available/sailor`:

```nginx
# Rate limiting zones
limit_req_zone $binary_remote_addr zone=api_limit:10m rate=10r/s;
limit_req_zone $binary_remote_addr zone=general_limit:10m rate=100r/m;

# Upstream servers
upstream sailor_backend {
    server 127.0.0.1:5000 fail_timeout=5s max_fails=3;
}

upstream sailor_mcp {
    server 127.0.0.1:8000 fail_timeout=5s max_fails=3;
}

server {
    listen 80;
    server_name yourdomain.com;

    # Redirect HTTP to HTTPS
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name yourdomain.com;

    # SSL Configuration
    ssl_certificate /etc/letsencrypt/live/yourdomain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/yourdomain.com/privkey.pem;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers 'ECDHE-ECDSA-AES128-GCM-SHA256:ECDHE-RSA-AES128-GCM-SHA256';
    ssl_prefer_server_ciphers on;
    ssl_session_cache shared:SSL:10m;
    ssl_session_timeout 10m;

    # Security Headers (defense in depth with Talisman)
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header Referrer-Policy "strict-origin-when-cross-origin" always;
    add_header Permissions-Policy "geolocation=(), camera=(), microphone=()" always;

    # Logs
    access_log /var/log/nginx/sailor_access.log;
    error_log /var/log/nginx/sailor_error.log;

    # Root location
    location / {
        limit_req zone=general_limit burst=20 nodelay;
        proxy_pass http://sailor_backend;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;

        # Timeouts
        proxy_connect_timeout 10s;
        proxy_send_timeout 30s;
        proxy_read_timeout 30s;
    }

    # API endpoints with stricter rate limiting
    location /api/generate-mermaid {
        limit_req zone=api_limit burst=5 nodelay;
        proxy_pass http://sailor_backend;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;

        # Longer timeout for AI generation
        proxy_read_timeout 90s;
    }

    # Health checks (no rate limiting)
    location /api/health {
        proxy_pass http://sailor_backend;
        access_log off;
    }

    # MCP Server (internal only, optional)
    location /mcp/ {
        # Restrict to internal network only
        allow 10.0.0.0/8;
        allow 172.16.0.0/12;
        allow 192.168.0.0/16;
        deny all;

        proxy_pass http://sailor_mcp/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    }

    # Static files
    location /static/ {
        alias /var/www/sailor/static/;
        expires 1y;
        add_header Cache-Control "public, immutable";
    }
}
```

Enable the site:
```bash
sudo ln -s /etc/nginx/sites-available/sailor /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

### 4. Deploy with Docker Compose

```bash
# Generate SECRET_KEY
python -c 'import secrets; print(f"SECRET_KEY={secrets.token_hex(32)}")' >> backend/.env

# Edit backend/.env and set other required variables

# Build and start services
docker-compose -f docker-compose.prod.yml up -d --build

# Check logs
docker-compose -f docker-compose.prod.yml logs -f

# Verify health
curl https://yourdomain.com/api/health
curl https://yourdomain.com/api/health/detailed
```

## 📊 Monitoring

### Health Check Endpoints

| Endpoint | Purpose | Expected Response |
|----------|---------|-------------------|
| `/api/health` | Basic health | 200 OK |
| `/api/health/detailed` | Detailed checks | 200 OK (with details) |
| `/api/health/live` | Liveness probe | 200 OK |
| `/api/health/ready` | Readiness probe | 200 OK |

### Sentry Error Tracking

Sailor integrates with Sentry for production error tracking and performance monitoring.

#### Setup

1. **Create a Sentry project** at https://sentry.io/
2. **Get your DSN** from the project settings
3. **Add to environment variables** in `backend/.env`:

```bash
# Sentry Configuration
SENTRY_DSN=https://your-public-key@o123456.ingest.sentry.io/7654321
SENTRY_TRACES_SAMPLE_RATE=0.1
SENTRY_RELEASE=sailor@2.0.0
```

4. **Restart the backend** service

#### Features

- **Automatic error capture**: All unhandled exceptions are sent to Sentry
- **Performance traces**: 10% of requests are traced (configurable)
- **Sensitive data filtering**: API keys, passwords, and tokens are automatically filtered
- **Environment tracking**: Errors tagged with production/development environment
- **Release tracking**: Track errors by deployment version

#### Verification

```bash
# Trigger a test error (in development)
curl -X POST https://yourdomain.com/api/test-error

# Check Sentry dashboard for the error
```

### Prometheus Metrics

Sailor exposes Prometheus-compatible metrics at the `/metrics` endpoint.

#### Metrics Available

| Metric | Type | Description | Labels |
|--------|------|-------------|--------|
| `flask_http_request_total` | Counter | Total HTTP requests | method, status, endpoint |
| `flask_http_request_duration_seconds` | Histogram | Request duration | method, endpoint |
| `sailor_ai_api_calls_total` | Counter | AI API calls | provider, status |
| `sailor_ai_api_duration_seconds` | Histogram | AI API call duration | provider |
| `sailor_mermaid_generation_requests_total` | Counter | Mermaid generation requests | status |

#### Setup with Docker Compose

Add Prometheus and Grafana to your `docker-compose.prod.yml`:

```yaml
  # Prometheus
  prometheus:
    image: prom/prometheus:latest
    restart: unless-stopped
    ports:
      - "127.0.0.1:9090:9090"  # Bind to localhost only
    volumes:
      - ./monitoring/prometheus.yml:/etc/prometheus/prometheus.yml:ro
      - ./monitoring/prometheus-alerts.yml:/etc/prometheus/alerts/alerts.yml:ro
      - prometheus-data:/prometheus
    command:
      - '--config.file=/etc/prometheus/prometheus.yml'
      - '--storage.tsdb.path=/prometheus'
      - '--web.console.libraries=/usr/share/prometheus/console_libraries'
      - '--web.console.templates=/usr/share/prometheus/consoles'
    networks:
      - sailor-net
    depends_on:
      - backend

  # Grafana
  grafana:
    image: grafana/grafana:latest
    restart: unless-stopped
    ports:
      - "127.0.0.1:3000:3000"  # Bind to localhost only
    environment:
      - GF_SECURITY_ADMIN_PASSWORD=${GRAFANA_ADMIN_PASSWORD:-admin}
      - GF_USERS_ALLOW_SIGN_UP=false
      - GF_SERVER_ROOT_URL=https://yourdomain.com/grafana
    volumes:
      - ./monitoring/grafana-dashboard.json:/etc/grafana/provisioning/dashboards/sailor.json:ro
      - grafana-data:/var/lib/grafana
    networks:
      - sailor-net
    depends_on:
      - prometheus

volumes:
  prometheus-data:
    driver: local
  grafana-data:
    driver: local
```

#### Configuration Files

The monitoring configuration files are located in `/monitoring`:

- `prometheus.yml` - Prometheus scrape configuration
- `prometheus-alerts.yml` - Alert rules for critical conditions
- `grafana-dashboard.json` - Pre-built dashboard with 9 panels

#### Nginx Reverse Proxy for Grafana

Add to your Nginx configuration:

```nginx
    # Grafana (protected)
    location /grafana/ {
        # Restrict to VPN or trusted IPs
        allow 10.0.0.0/8;
        allow YOUR_IP_ADDRESS;
        deny all;

        proxy_pass http://127.0.0.1:3000/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # Prometheus (internal only)
    location /prometheus/ {
        allow 127.0.0.1;
        deny all;

        proxy_pass http://127.0.0.1:9090/;
    }
```

#### Import Grafana Dashboard

1. Access Grafana at `https://yourdomain.com/grafana`
2. Login (default: admin/admin)
3. Navigate to **Dashboards → Import**
4. Upload `monitoring/grafana-dashboard.json`
5. Select Prometheus data source
6. Click **Import**

#### Alert Rules Configured

The `prometheus-alerts.yml` includes these production alerts:

- **HighErrorRate**: >5% error rate for 5 minutes
- **EndpointDown**: Service unavailable for 1 minute
- **SlowResponseTime**: p95 >30s for 5 minutes
- **HighAIAPIErrorRate**: >10% AI API errors for 5 minutes
- **RateLimitHighUsage**: Approaching rate limits
- **HighMemoryUsage**: >90% memory for 5 minutes
- **LowDiskSpace**: <10% disk space

Configure Alertmanager to receive notifications via email, Slack, or PagerDuty.

#### Disable Metrics (Optional)

To disable metrics collection:

```bash
# In backend/.env
ENABLE_METRICS=false
```

### Log Aggregation

Ship logs to centralized logging:

```yaml
# Add to docker-compose.prod.yml
logging:
  driver: "json-file"
  options:
    max-size: "10m"
    max-file: "3"
    labels: "service"
```

Or use ELK/Loki stack for advanced log analysis.

## 🔧 Maintenance

### Regular Updates

```bash
# Pull latest code
git pull origin main

# Rebuild containers
docker-compose -f docker-compose.prod.yml build

# Rolling update (zero downtime)
docker-compose -f docker-compose.prod.yml up -d --no-deps --build backend

# Verify health
curl https://yourdomain.com/api/health/detailed
```

### Database Backups (if added in future)

```bash
# Backup (when database added)
docker-compose exec postgres pg_dump -U sailor > backup-$(date +%Y%m%d).sql
```

### Log Rotation

Configure logrotate for Nginx and application logs:

```
/var/log/nginx/sailor*.log {
    daily
    rotate 14
    compress
    delaycompress
    notifempty
    sharedscripts
    postrotate
        systemctl reload nginx > /dev/null 2>&1
    endscript
}
```

## 🐛 Troubleshooting

### Service Not Starting

```bash
# Check logs
docker-compose -f docker-compose.prod.yml logs backend
docker-compose -f docker-compose.prod.yml logs mcp

# Check configuration
docker-compose -f docker-compose.prod.yml config

# Verify environment variables
docker-compose -f docker-compose.prod.yml exec backend env
```

### Rate Limiting Issues

```bash
# Check Redis connectivity
docker-compose -f docker-compose.prod.yml exec redis redis-cli ping

# Monitor rate limit hits
docker-compose -f docker-compose.prod.yml logs backend | grep "rate limit"
```

### SSL Certificate Issues

```bash
# Renew Let's Encrypt certificate
sudo certbot renew --nginx

# Test SSL configuration
sudo nginx -t
```

## 🔐 Security Best Practices

1. **Keep secrets out of git**: Use `.env` files (gitignored)
2. **Rotate SECRET_KEY**: Periodically generate new keys
3. **Monitor logs**: Set up alerts for suspicious activity
4. **Update dependencies**: Regularly run `pip list --outdated`
5. **Firewall rules**: Only expose necessary ports (80, 443)
6. **DDoS protection**: Use Cloudflare or similar CDN
7. **Backup configuration**: Store encrypted backups offsite
8. **Incident response**: Have a plan for security incidents

## 📈 Scaling

### Horizontal Scaling

Run multiple backend instances with load balancer:

```yaml
backend:
  deploy:
    replicas: 3
    restart_policy:
      condition: on-failure
```

### Database (when needed)

Add PostgreSQL for persistent storage:

```yaml
postgres:
  image: postgres:16-alpine
  environment:
    POSTGRES_DB: sailor
    POSTGRES_USER: sailor
    POSTGRES_PASSWORD: ${DB_PASSWORD}
  volumes:
    - postgres-data:/var/lib/postgresql/data
```

## 📝 Compliance

### GDPR Considerations

- User API keys are not logged
- Session data can be configured to expire
- No PII stored without consent
- Right to deletion can be implemented

### SOC 2 / ISO 27001

- All security headers implemented
- Encryption in transit (HTTPS)
- Access logging enabled
- Security updates process documented

## 🆘 Support

For production issues:
- Check `/api/health/detailed` endpoint
- Review application logs
- Check Nginx error logs
- Monitor rate limit violations

## 📚 Additional Resources

- [Docker Security Best Practices](https://docs.docker.com/engine/security/)
- [OWASP Top 10](https://owasp.org/www-project-top-ten/)
- [Flask Production Deployment](https://flask.palletsprojects.com/en/3.0.x/deploying/)
- [Nginx Security Headers](https://securityheaders.com/)

---

**Version**: 2.0.0
**Last Updated**: 2025-11-15
**Security Level**: Production-Ready (P0 issues resolved)
