# AI-Powered IT Helpdesk - Local Development and On-Premise Deployment

## 7. Local Development and On-Premise Hosting on Ubuntu Server 24.04

### 7.1 Overview

This document provides comprehensive instructions for setting up the AI-powered IT helpdesk system on Ubuntu Server 24.04, suitable for:
- **Local Development**: Developers working on the application
- **On-Premise Hosting**: Organizations preferring to host on their own infrastructure
- **Hybrid Deployment**: Development/staging on-premise, production in cloud

**Benefits of Local/On-Premise Deployment:**
- ✅ Full control over data and infrastructure
- ✅ No cloud egress costs
- ✅ Meet strict data residency requirements
- ✅ Lower costs for small to medium deployments
- ✅ No internet dependency for internal operations

**Considerations:**
- ❌ Higher upfront capital expenditure (hardware)
- ❌ Requires in-house DevOps expertise
- ❌ Manual scaling and high availability setup
- ❌ Responsible for security patches and updates
- ❌ Disaster recovery more complex

---

### 7.2 System Requirements

#### 7.2.1 Hardware Requirements

**Minimum (Development/Small Deployment - Up to 500 Users):**
- **CPU**: 4 cores (2.5 GHz+)
- **RAM**: 16 GB
- **Storage**: 100 GB SSD
- **Network**: 100 Mbps

**Recommended (Production - 500-2,000 Users):**
- **CPU**: 8 cores (3.0 GHz+)
- **RAM**: 32 GB
- **Storage**: 500 GB SSD (NVMe preferred)
- **Network**: 1 Gbps

**High Availability (Production - 2,000+ Users):**
- **3 Application Servers**: 8 cores, 16 GB RAM each
- **2 Database Servers**: 8 cores, 32 GB RAM each (Primary + Replica)
- **1 Redis Server**: 4 cores, 8 GB RAM
- **1 Load Balancer**: 4 cores, 8 GB RAM
- **Storage**: 1 TB SSD (RAID 10 for database)
- **Network**: 10 Gbps

#### 7.2.2 Software Requirements

- **Operating System**: Ubuntu Server 24.04 LTS (Noble Numbat)
- **Node.js**: 20.x LTS
- **PostgreSQL**: 15 or 16
- **Redis**: 7.x
- **Nginx**: 1.24+
- **Docker**: 24.x (optional, for containerized setup)
- **Git**: 2.x

---

### 7.3 Initial Server Setup

#### 7.3.1 Update System and Install Basic Tools

```bash
# Update package list and upgrade system
sudo apt update && sudo apt upgrade -y

# Install essential tools
sudo apt install -y \
  curl \
  wget \
  git \
  build-essential \
  software-properties-common \
  apt-transport-https \
  ca-certificates \
  gnupg \
  lsb-release \
  ufw \
  fail2ban \
  unattended-upgrades

# Set timezone
sudo timedatectl set-timezone Asia/Karachi

# Set hostname
sudo hostnamectl set-hostname helpdesk-server
```

#### 7.3.2 Create Application User

```bash
# Create dedicated user for running the application
sudo adduser --system --group --home /opt/helpdesk helpdesk

# Add user to sudoers (for deployment scripts)
sudo usermod -aG sudo helpdesk

# Set password for helpdesk user
sudo passwd helpdesk

# Switch to helpdesk user
sudo su - helpdesk
```

#### 7.3.3 Configure Firewall

```bash
# Enable UFW firewall
sudo ufw --force enable

# Allow SSH (important: do this first!)
sudo ufw allow 22/tcp

# Allow HTTP and HTTPS
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp

# Check firewall status
sudo ufw status verbose
```

---

### 7.4 Install Node.js

```bash
# Install Node.js 20.x LTS using NodeSource repository
curl -fsSL https://deb.nodesource.com/setup_20.x | sudo -E bash -
sudo apt install -y nodejs

# Verify installation
node --version  # Should show v20.x.x
npm --version   # Should show 10.x.x

# Install global npm packages
sudo npm install -g pm2 yarn
```

---

### 7.5 Install and Configure PostgreSQL

#### 7.5.1 Install PostgreSQL 16

```bash
# Add PostgreSQL official repository
sudo apt install -y postgresql-common
sudo /usr/share/postgresql-common/pgdg/apt.postgresql.org.sh

# Install PostgreSQL 16
sudo apt install -y postgresql-16 postgresql-contrib-16

# Verify installation
sudo systemctl status postgresql

# PostgreSQL should be running on port 5432
```

#### 7.5.2 Configure PostgreSQL

```bash
# Switch to postgres user
sudo su - postgres

# Create database and user
psql << EOF
CREATE DATABASE helpdesk;
CREATE USER helpdesk_user WITH PASSWORD 'your_secure_password_here';
GRANT ALL PRIVILEGES ON DATABASE helpdesk TO helpdesk_user;

-- Grant schema privileges
\c helpdesk
GRANT ALL ON SCHEMA public TO helpdesk_user;
ALTER DATABASE helpdesk OWNER TO helpdesk_user;

-- Enable required extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";  -- For text search

-- Install pgvector for semantic search (if needed)
CREATE EXTENSION IF NOT EXISTS vector;
EOF

# Exit postgres user
exit
```

#### 7.5.3 Configure PostgreSQL for Performance

```bash
# Edit postgresql.conf
sudo nano /etc/postgresql/16/main/postgresql.conf

# Recommended settings for 32 GB RAM server:
# max_connections = 200
# shared_buffers = 8GB
# effective_cache_size = 24GB
# maintenance_work_mem = 2GB
# checkpoint_completion_target = 0.9
# wal_buffers = 16MB
# default_statistics_target = 100
# random_page_cost = 1.1  # For SSD
# effective_io_concurrency = 200  # For SSD
# work_mem = 20MB
# min_wal_size = 1GB
# max_wal_size = 4GB

# Configure for remote connections (if needed)
# listen_addresses = '*'

# Edit pg_hba.conf to allow password authentication
sudo nano /etc/postgresql/16/main/pg_hba.conf

# Add this line (adjust IP range as needed):
# host    helpdesk        helpdesk_user   10.0.0.0/8      scram-sha-256
# host    helpdesk        helpdesk_user   192.168.0.0/16  scram-sha-256

# Restart PostgreSQL
sudo systemctl restart postgresql

# Enable PostgreSQL to start on boot
sudo systemctl enable postgresql
```

#### 7.5.4 Install pgvector (Optional, for Semantic Search)

```bash
# Install pgvector extension
sudo apt install -y postgresql-16-pgvector

# Enable in database
sudo su - postgres
psql -d helpdesk << EOF
CREATE EXTENSION IF NOT EXISTS vector;
EOF
exit
```

---

### 7.6 Install and Configure Redis

```bash
# Install Redis 7.x
sudo apt install -y redis-server

# Edit Redis configuration
sudo nano /etc/redis/redis.conf

# Recommended settings:
# maxmemory 4gb
# maxmemory-policy allkeys-lru
# bind 127.0.0.1  # Only local connections (change if Redis on separate server)
# requirepass your_redis_password_here
# appendonly yes  # Enable persistence
# appendfsync everysec

# Restart Redis
sudo systemctl restart redis-server

# Enable Redis to start on boot
sudo systemctl enable redis-server

# Test Redis
redis-cli ping  # Should return PONG

# Test with password
redis-cli
> AUTH your_redis_password_here
> PING
> exit
```

---

### 7.7 Install Nginx (Reverse Proxy)

```bash
# Install Nginx
sudo apt install -y nginx

# Remove default site
sudo rm /etc/nginx/sites-enabled/default

# Create helpdesk site configuration
sudo nano /etc/nginx/sites-available/helpdesk

# Add this configuration:
```

```nginx
# /etc/nginx/sites-available/helpdesk

# Rate limiting zone
limit_req_zone $binary_remote_addr zone=api_limit:10m rate=100r/m;
limit_req_zone $binary_remote_addr zone=login_limit:10m rate=5r/m;

# Upstream backend servers
upstream helpdesk_backend {
    least_conn;  # Load balancing method
    server 127.0.0.1:3000 max_fails=3 fail_timeout=30s;
    # Add more backend servers for high availability:
    # server 127.0.0.1:3001 max_fails=3 fail_timeout=30s;
    # server 127.0.0.1:3002 max_fails=3 fail_timeout=30s;
    keepalive 32;
}

# HTTP server (redirect to HTTPS)
server {
    listen 80;
    listen [::]:80;
    server_name helpdesk.digiskills.pk;

    # Redirect all HTTP to HTTPS
    return 301 https://$server_name$request_uri;
}

# HTTPS server
server {
    listen 443 ssl http2;
    listen [::]:443 ssl http2;
    server_name helpdesk.digiskills.pk;

    # SSL certificates (use Let's Encrypt or your own certs)
    ssl_certificate /etc/ssl/certs/helpdesk.crt;
    ssl_certificate_key /etc/ssl/private/helpdesk.key;

    # SSL configuration
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers 'ECDHE-ECDSA-AES128-GCM-SHA256:ECDHE-RSA-AES128-GCM-SHA256:ECDHE-ECDSA-AES256-GCM-SHA384:ECDHE-RSA-AES256-GCM-SHA384';
    ssl_prefer_server_ciphers on;
    ssl_session_cache shared:SSL:10m;
    ssl_session_timeout 10m;

    # Security headers
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains; preload" always;
    add_header X-Frame-Options "DENY" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header Referrer-Policy "strict-origin-when-cross-origin" always;

    # Max upload size
    client_max_body_size 25M;

    # Logging
    access_log /var/log/nginx/helpdesk_access.log;
    error_log /var/log/nginx/helpdesk_error.log;

    # API endpoints (with rate limiting)
    location /api/ {
        limit_req zone=api_limit burst=20 nodelay;

        proxy_pass http://helpdesk_backend;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_cache_bypass $http_upgrade;

        # Timeouts
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }

    # Login endpoint (strict rate limiting)
    location /api/auth/login {
        limit_req zone=login_limit burst=3 nodelay;

        proxy_pass http://helpdesk_backend;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # WebSocket support
    location /socket.io/ {
        proxy_pass http://helpdesk_backend;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;

        # WebSocket timeouts
        proxy_read_timeout 86400s;
        proxy_send_timeout 86400s;
    }

    # Static files (Next.js)
    location /_next/static/ {
        proxy_pass http://helpdesk_backend;
        proxy_cache_valid 200 365d;
        add_header Cache-Control "public, immutable";
    }

    # Health check endpoint (no rate limiting)
    location /health {
        proxy_pass http://helpdesk_backend;
        access_log off;
    }

    # Root and all other requests
    location / {
        proxy_pass http://helpdesk_backend;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_cache_bypass $http_upgrade;
    }
}
```

```bash
# Enable the site
sudo ln -s /etc/nginx/sites-available/helpdesk /etc/nginx/sites-enabled/

# Test Nginx configuration
sudo nginx -t

# Restart Nginx
sudo systemctl restart nginx

# Enable Nginx to start on boot
sudo systemctl enable nginx
```

---

### 7.8 SSL Certificate Setup

#### 7.8.1 Option 1: Let's Encrypt (Free, Recommended)

```bash
# Install Certbot
sudo apt install -y certbot python3-certbot-nginx

# Obtain certificate (automatic Nginx configuration)
sudo certbot --nginx -d helpdesk.digiskills.pk

# Certbot will automatically:
# - Obtain certificate
# - Update Nginx configuration
# - Set up automatic renewal

# Test renewal
sudo certbot renew --dry-run

# Certificates auto-renew via systemd timer
sudo systemctl list-timers | grep certbot
```

#### 7.8.2 Option 2: Self-Signed Certificate (Development Only)

```bash
# Generate self-signed certificate
sudo mkdir -p /etc/ssl/private
sudo openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
  -keyout /etc/ssl/private/helpdesk.key \
  -out /etc/ssl/certs/helpdesk.crt \
  -subj "/C=PK/ST=Punjab/L=Lahore/O=Digiskills/CN=helpdesk.digiskills.pk"

# Set permissions
sudo chmod 600 /etc/ssl/private/helpdesk.key
sudo chmod 644 /etc/ssl/certs/helpdesk.crt
```

---

### 7.9 Application Deployment

#### 7.9.1 Clone Repository

```bash
# Switch to helpdesk user
sudo su - helpdesk
cd /opt/helpdesk

# Clone repository
git clone https://github.com/your-org/helpdesk-application.git app
cd app

# Or if using SSH:
# git clone git@github.com:your-org/helpdesk-application.git app
```

#### 7.9.2 Configure Environment Variables

```bash
# Create .env file
nano /opt/helpdesk/app/.env

# Add configuration:
```

```bash
# .env file for production

# Node environment
NODE_ENV=production
PORT=3000

# Database
DATABASE_URL=postgresql://helpdesk_user:your_secure_password_here@localhost:5432/helpdesk

# Redis
REDIS_URL=redis://:your_redis_password_here@localhost:6379

# JWT secrets (generate with: openssl rand -base64 32)
JWT_SECRET=your_jwt_secret_here_minimum_32_characters
REFRESH_TOKEN_SECRET=your_refresh_token_secret_here

# Field encryption key (generate with: openssl rand -hex 32)
FIELD_ENCRYPTION_KEY=your_field_encryption_key_64_hex_chars
MFA_ENCRYPTION_KEY=your_mfa_encryption_key_64_hex_chars

# Application URL
APP_URL=https://helpdesk.digiskills.pk
API_URL=https://helpdesk.digiskills.pk/api

# SSO Configuration (Google Workspace)
GOOGLE_CLIENT_ID=your_google_client_id
GOOGLE_CLIENT_SECRET=your_google_client_secret
GOOGLE_CALLBACK_URL=https://helpdesk.digiskills.pk/auth/google/callback

# Or Microsoft Azure AD
# AZURE_CLIENT_ID=your_azure_client_id
# AZURE_CLIENT_SECRET=your_azure_client_secret
# AZURE_TENANT_ID=your_azure_tenant_id

# Email (SMTP)
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=helpdesk@digiskills.pk
SMTP_PASSWORD=your_smtp_password
SMTP_FROM=helpdesk@digiskills.pk

# OpenAI (for AI features)
OPENAI_API_KEY=sk-your-openai-api-key
OPENAI_ORG_ID=org-your-org-id

# Storage (local file system for on-premise)
STORAGE_TYPE=local  # or 's3' for cloud storage
UPLOAD_DIR=/opt/helpdesk/uploads

# Logging
LOG_LEVEL=info
LOG_DIR=/opt/helpdesk/logs

# Security
COOKIE_SECRET=your_cookie_secret_here
SESSION_SECRET=your_session_secret_here

# Rate limiting
RATE_LIMIT_WINDOW_MS=900000  # 15 minutes
RATE_LIMIT_MAX_REQUESTS=100

# Feature flags
ENABLE_AI_CATEGORIZATION=true
ENABLE_SEMANTIC_SEARCH=true
ENABLE_MFA=true
```

```bash
# Set proper permissions
chmod 600 /opt/helpdesk/app/.env
```

#### 7.9.3 Install Dependencies and Build

```bash
cd /opt/helpdesk/app

# Install backend dependencies
npm ci --production

# Generate Prisma client
npx prisma generate

# Run database migrations
npx prisma migrate deploy

# Seed initial data (optional)
npm run seed

# Build application
npm run build

# For Next.js frontend (if separate)
cd frontend
npm ci --production
npm run build
cd ..
```

#### 7.9.4 Create Upload and Log Directories

```bash
# Create directories
sudo mkdir -p /opt/helpdesk/uploads
sudo mkdir -p /opt/helpdesk/logs

# Set ownership
sudo chown -R helpdesk:helpdesk /opt/helpdesk/uploads
sudo chown -R helpdesk:helpdesk /opt/helpdesk/logs

# Set permissions
sudo chmod 755 /opt/helpdesk/uploads
sudo chmod 755 /opt/helpdesk/logs
```

---

### 7.10 Process Management with PM2

#### 7.10.1 Create PM2 Ecosystem File

```bash
# Create PM2 configuration
nano /opt/helpdesk/app/ecosystem.config.js
```

```javascript
// ecosystem.config.js
module.exports = {
  apps: [
    {
      name: 'helpdesk-api',
      script: 'dist/main.js',
      instances: 4,  // Number of instances (use 'max' for all CPU cores)
      exec_mode: 'cluster',
      env: {
        NODE_ENV: 'production',
        PORT: 3000,
      },
      error_file: '/opt/helpdesk/logs/api-error.log',
      out_file: '/opt/helpdesk/logs/api-out.log',
      log_date_format: 'YYYY-MM-DD HH:mm:ss Z',
      merge_logs: true,
      max_memory_restart: '1G',
      autorestart: true,
      watch: false,
      max_restarts: 10,
      min_uptime: '10s',
    },
    {
      name: 'helpdesk-worker-ai',
      script: 'dist/workers/ai-worker.js',
      instances: 2,
      exec_mode: 'cluster',
      env: {
        NODE_ENV: 'production',
        WORKER_TYPE: 'ai',
      },
      error_file: '/opt/helpdesk/logs/worker-ai-error.log',
      out_file: '/opt/helpdesk/logs/worker-ai-out.log',
      max_memory_restart: '512M',
      autorestart: true,
    },
    {
      name: 'helpdesk-worker-email',
      script: 'dist/workers/email-worker.js',
      instances: 1,
      env: {
        NODE_ENV: 'production',
        WORKER_TYPE: 'email',
      },
      error_file: '/opt/helpdesk/logs/worker-email-error.log',
      out_file: '/opt/helpdesk/logs/worker-email-out.log',
      max_memory_restart: '256M',
      autorestart: true,
    },
    {
      name: 'helpdesk-worker-reports',
      script: 'dist/workers/report-worker.js',
      instances: 1,
      env: {
        NODE_ENV: 'production',
        WORKER_TYPE: 'reports',
      },
      error_file: '/opt/helpdesk/logs/worker-reports-error.log',
      out_file: '/opt/helpdesk/logs/worker-reports-out.log',
      max_memory_restart: '512M',
      autorestart: true,
    },
  ],
};
```

#### 7.10.2 Start Application with PM2

```bash
# Start all applications
pm2 start ecosystem.config.js

# Check status
pm2 status

# View logs
pm2 logs

# View specific app logs
pm2 logs helpdesk-api

# Monitor
pm2 monit

# Save PM2 configuration
pm2 save

# Setup PM2 to start on boot
pm2 startup systemd -u helpdesk --hp /opt/helpdesk
# Run the command it outputs (as root)

# View PM2 dashboard (web interface)
pm2 web
```

#### 7.10.3 PM2 Management Commands

```bash
# Restart all apps
pm2 restart all

# Restart specific app
pm2 restart helpdesk-api

# Stop all apps
pm2 stop all

# Delete all apps from PM2
pm2 delete all

# Reload apps with zero downtime
pm2 reload all

# Scale app instances
pm2 scale helpdesk-api 8  # Scale to 8 instances

# View detailed info
pm2 describe helpdesk-api

# Clear logs
pm2 flush
```

---

### 7.11 Monitoring and Logging

#### 7.11.1 Install Monitoring Tools

```bash
# Install htop for process monitoring
sudo apt install -y htop

# Install netdata for comprehensive monitoring
bash <(curl -Ss https://my-netdata.io/kickstart.sh)

# Access Netdata dashboard at http://server-ip:19999

# Secure Netdata with basic auth
sudo apt install -y apache2-utils
sudo htpasswd -c /etc/netdata/htpasswd admin

# Edit Netdata config
sudo nano /etc/netdata/netdata.conf
# Add under [web]:
# bind to = 127.0.0.1
# Then access via Nginx reverse proxy
```

#### 7.11.2 Configure Log Rotation

```bash
# Create logrotate configuration
sudo nano /etc/logrotate.d/helpdesk
```

```bash
# /etc/logrotate.d/helpdesk
/opt/helpdesk/logs/*.log {
    daily
    missingok
    rotate 30
    compress
    delaycompress
    notifempty
    create 0640 helpdesk helpdesk
    sharedscripts
    postrotate
        pm2 reloadLogs
    endscript
}
```

#### 7.11.3 Setup Application Monitoring

```bash
# Install PM2 monitoring (optional, paid service)
pm2 plus

# Or use PM2 open-source monitoring
pm2 install pm2-server-monit
```

---

### 7.12 Backup Configuration

#### 7.12.1 Database Backup Script

```bash
# Create backup script
sudo nano /opt/helpdesk/scripts/backup-database.sh
```

```bash
#!/bin/bash
# /opt/helpdesk/scripts/backup-database.sh

# Configuration
BACKUP_DIR="/opt/helpdesk/backups/database"
DB_NAME="helpdesk"
DB_USER="helpdesk_user"
RETENTION_DAYS=30
DATE=$(date +%Y-%m-%d_%H-%M-%S)
BACKUP_FILE="$BACKUP_DIR/helpdesk_$DATE.sql.gz"

# Create backup directory if not exists
mkdir -p $BACKUP_DIR

# Perform backup
echo "Starting database backup..."
PGPASSWORD="your_secure_password_here" pg_dump -U $DB_USER -h localhost $DB_NAME | gzip > $BACKUP_FILE

# Check if backup was successful
if [ $? -eq 0 ]; then
    echo "Database backup completed: $BACKUP_FILE"

    # Delete backups older than retention period
    find $BACKUP_DIR -name "helpdesk_*.sql.gz" -mtime +$RETENTION_DAYS -delete
    echo "Old backups cleaned up (retention: $RETENTION_DAYS days)"
else
    echo "Database backup failed!"
    exit 1
fi

# Optional: Upload to remote backup server or cloud storage
# rsync -avz $BACKUP_FILE user@backup-server:/backups/helpdesk/
# or
# aws s3 cp $BACKUP_FILE s3://helpdesk-backups/database/
```

```bash
# Make executable
chmod +x /opt/helpdesk/scripts/backup-database.sh

# Test backup
/opt/helpdesk/scripts/backup-database.sh
```

#### 7.12.2 Application Backup Script

```bash
# Create application backup script
sudo nano /opt/helpdesk/scripts/backup-app.sh
```

```bash
#!/bin/bash
# /opt/helpdesk/scripts/backup-app.sh

BACKUP_DIR="/opt/helpdesk/backups/application"
DATE=$(date +%Y-%m-%d_%H-%M-%S)
BACKUP_FILE="$BACKUP_DIR/app_$DATE.tar.gz"

mkdir -p $BACKUP_DIR

echo "Starting application backup..."

# Backup uploads and configuration
tar -czf $BACKUP_FILE \
    /opt/helpdesk/uploads \
    /opt/helpdesk/app/.env \
    /opt/helpdesk/app/ecosystem.config.js

if [ $? -eq 0 ]; then
    echo "Application backup completed: $BACKUP_FILE"

    # Delete backups older than 30 days
    find $BACKUP_DIR -name "app_*.tar.gz" -mtime +30 -delete
else
    echo "Application backup failed!"
    exit 1
fi
```

```bash
# Make executable
chmod +x /opt/helpdesk/scripts/backup-app.sh
```

#### 7.12.3 Schedule Automatic Backups

```bash
# Edit crontab
crontab -e

# Add these lines:
# Daily database backup at 2 AM
0 2 * * * /opt/helpdesk/scripts/backup-database.sh >> /opt/helpdesk/logs/backup.log 2>&1

# Weekly application backup on Sunday at 3 AM
0 3 * * 0 /opt/helpdesk/scripts/backup-app.sh >> /opt/helpdesk/logs/backup.log 2>&1
```

---

### 7.13 Security Hardening

#### 7.13.1 Configure Fail2ban

```bash
# Install fail2ban
sudo apt install -y fail2ban

# Create custom jail for Nginx
sudo nano /etc/fail2ban/jail.d/nginx-helpdesk.conf
```

```ini
[nginx-http-auth]
enabled = true
filter = nginx-http-auth
port = http,https
logpath = /var/log/nginx/helpdesk_error.log
maxretry = 5
bantime = 3600
findtime = 600

[nginx-limit-req]
enabled = true
filter = nginx-limit-req
port = http,https
logpath = /var/log/nginx/helpdesk_error.log
maxretry = 10
bantime = 3600
findtime = 600
```

```bash
# Restart fail2ban
sudo systemctl restart fail2ban

# Check status
sudo fail2ban-client status
```

#### 7.13.2 Configure Automatic Security Updates

```bash
# Configure unattended upgrades
sudo dpkg-reconfigure -plow unattended-upgrades

# Edit configuration
sudo nano /etc/apt/apt.conf.d/50unattended-upgrades

# Ensure these are uncommented:
# Unattended-Upgrade::Automatic-Reboot "true";
# Unattended-Upgrade::Automatic-Reboot-Time "02:00";
```

#### 7.13.3 Harden SSH

```bash
# Edit SSH configuration
sudo nano /etc/ssh/sshd_config

# Recommended settings:
# PermitRootLogin no
# PasswordAuthentication no  # If using SSH keys
# PubkeyAuthentication yes
# Port 2222  # Change default port (optional)
# AllowUsers helpdesk admin  # Restrict users

# Restart SSH
sudo systemctl restart sshd
```

---

### 7.14 Docker-Based Local Development (Alternative)

For developers who prefer containerized setup:

#### 7.14.1 Install Docker and Docker Compose

```bash
# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# Add user to docker group
sudo usermod -aG docker $USER

# Install Docker Compose
sudo apt install -y docker-compose-plugin

# Verify installation
docker --version
docker compose version
```

#### 7.14.2 Create Docker Compose File

```yaml
# docker-compose.yml
version: '3.8'

services:
  # PostgreSQL Database
  postgres:
    image: postgres:16-alpine
    container_name: helpdesk-postgres
    environment:
      POSTGRES_DB: helpdesk
      POSTGRES_USER: helpdesk_user
      POSTGRES_PASSWORD: helpdesk_password
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U helpdesk_user"]
      interval: 10s
      timeout: 5s
      retries: 5

  # Redis Cache
  redis:
    image: redis:7-alpine
    container_name: helpdesk-redis
    command: redis-server --appendonly yes --requirepass redis_password
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 10s
      timeout: 5s
      retries: 5

  # Application Backend
  api:
    build:
      context: .
      dockerfile: Dockerfile
    container_name: helpdesk-api
    depends_on:
      postgres:
        condition: service_healthy
      redis:
        condition: service_healthy
    environment:
      NODE_ENV: development
      DATABASE_URL: postgresql://helpdesk_user:helpdesk_password@postgres:5432/helpdesk
      REDIS_URL: redis://:redis_password@redis:6379
      JWT_SECRET: dev_jwt_secret_change_in_production
      OPENAI_API_KEY: ${OPENAI_API_KEY}
    ports:
      - "3000:3000"
    volumes:
      - ./src:/app/src
      - ./uploads:/app/uploads
      - ./logs:/app/logs
      - node_modules:/app/node_modules
    command: npm run start:dev

  # Workers (AI, Email, Reports)
  worker:
    build:
      context: .
      dockerfile: Dockerfile
    container_name: helpdesk-worker
    depends_on:
      - postgres
      - redis
      - api
    environment:
      NODE_ENV: development
      DATABASE_URL: postgresql://helpdesk_user:helpdesk_password@postgres:5432/helpdesk
      REDIS_URL: redis://:redis_password@redis:6379
      OPENAI_API_KEY: ${OPENAI_API_KEY}
    volumes:
      - ./src:/app/src
      - node_modules:/app/node_modules
    command: npm run worker:dev

  # Nginx Reverse Proxy
  nginx:
    image: nginx:alpine
    container_name: helpdesk-nginx
    depends_on:
      - api
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf:ro
      - ./ssl:/etc/nginx/ssl:ro
    restart: unless-stopped

volumes:
  postgres_data:
  redis_data:
  node_modules:
```

#### 7.14.3 Docker Commands

```bash
# Start all services
docker compose up -d

# View logs
docker compose logs -f

# View specific service logs
docker compose logs -f api

# Stop all services
docker compose down

# Rebuild and start
docker compose up -d --build

# Run database migrations
docker compose exec api npx prisma migrate deploy

# Access database shell
docker compose exec postgres psql -U helpdesk_user -d helpdesk

# Access Redis CLI
docker compose exec redis redis-cli -a redis_password

# Scale workers
docker compose up -d --scale worker=3
```

---

### 7.15 Development Workflow

#### 7.15.1 Local Development Setup

```bash
# Clone repository
git clone https://github.com/your-org/helpdesk-application.git
cd helpdesk-application

# Install dependencies
npm install

# Copy environment template
cp .env.example .env.local

# Edit environment variables
nano .env.local

# Run database migrations
npx prisma migrate dev

# Seed database (optional)
npm run seed

# Start development server (with hot reload)
npm run dev

# In another terminal, start worker processes
npm run worker:dev

# Application runs at http://localhost:3000
```

#### 7.15.2 Code Quality Tools

```bash
# Linting
npm run lint

# Format code
npm run format

# Type checking
npm run type-check

# Run tests
npm run test          # Unit tests
npm run test:e2e      # End-to-end tests
npm run test:cov      # Coverage report
```

---

### 7.16 Comparison: Local vs Cloud Deployment

| Aspect | Local/On-Premise | Cloud (AWS) |
|--------|------------------|-------------|
| **Initial Cost** | High (hardware purchase) | Low (pay-as-you-go) |
| **Operational Cost** | Lower (electricity, maintenance) | Higher (monthly fees) |
| **Scalability** | Manual (hardware purchase) | Automatic (auto-scaling) |
| **High Availability** | Complex (manual setup) | Built-in (multi-AZ) |
| **Disaster Recovery** | Manual (backup scripts) | Managed (RDS, S3 replication) |
| **Maintenance** | Manual updates, patches | Automated patches (managed services) |
| **Security** | Full control, self-managed | Shared responsibility model |
| **Data Control** | Complete ownership | Stored in cloud provider |
| **Internet Dependency** | Optional (local network) | Required |
| **Setup Time** | Longer (manual configuration) | Faster (managed services) |
| **DevOps Expertise** | Required | Moderate (simplified by managed services) |
| **Best For** | Small orgs, strict data requirements | Growing orgs, rapid scaling needs |

**Recommendation:**
- **Start Local**: For MVP and initial deployment (500-1,000 users)
- **Hybrid**: Development/staging local, production in cloud
- **Full Cloud**: When scaling beyond 2,000 users or need global reach

---

### 7.17 Troubleshooting

#### 7.17.1 Common Issues

**Issue: Application won't start**
```bash
# Check PM2 logs
pm2 logs helpdesk-api --lines 100

# Check if port 3000 is already in use
sudo lsof -i :3000

# Check if database is accessible
psql -U helpdesk_user -d helpdesk -h localhost

# Check environment variables
pm2 env 0
```

**Issue: Database connection errors**
```bash
# Check PostgreSQL status
sudo systemctl status postgresql

# Check PostgreSQL logs
sudo tail -f /var/log/postgresql/postgresql-16-main.log

# Test connection
psql -U helpdesk_user -d helpdesk -h localhost -W

# Check pg_hba.conf authentication
sudo cat /etc/postgresql/16/main/pg_hba.conf
```

**Issue: Redis connection errors**
```bash
# Check Redis status
sudo systemctl status redis-server

# Check Redis logs
sudo tail -f /var/log/redis/redis-server.log

# Test connection
redis-cli -a your_redis_password ping
```

**Issue: Nginx 502 Bad Gateway**
```bash
# Check if backend is running
pm2 status

# Check Nginx error logs
sudo tail -f /var/log/nginx/helpdesk_error.log

# Test backend directly
curl http://localhost:3000/health

# Check Nginx configuration
sudo nginx -t
```

**Issue: High memory usage**
```bash
# Check memory usage
free -h
htop

# Check PM2 processes
pm2 status
pm2 monit

# Restart with memory limit
pm2 restart helpdesk-api --max-memory-restart 1G
```

#### 7.17.2 Performance Tuning

```bash
# PostgreSQL query analysis
psql -U helpdesk_user -d helpdesk << EOF
SELECT query, calls, total_time, mean_time
FROM pg_stat_statements
ORDER BY mean_time DESC
LIMIT 10;
EOF

# Check slow queries
sudo tail -f /var/log/postgresql/postgresql-16-main.log | grep "duration"

# Analyze table statistics
psql -U helpdesk_user -d helpdesk << EOF
ANALYZE tickets;
ANALYZE kb_articles;
EOF

# Check index usage
psql -U helpdesk_user -d helpdesk << EOF
SELECT schemaname, tablename, indexname, idx_scan
FROM pg_stat_user_indexes
WHERE idx_scan = 0;
EOF
```

---

## Summary

This comprehensive guide provides everything needed to deploy the AI-powered IT helpdesk on Ubuntu Server 24.04, whether for:
- **Local Development**: Quick setup for developers
- **Small Deployment**: Single server for 500-2,000 users
- **Production On-Premise**: High availability multi-server setup

**Key Components Covered:**
- ✅ Complete system requirements and setup
- ✅ PostgreSQL 16 with performance tuning
- ✅ Redis 7 for caching and queues
- ✅ Nginx reverse proxy with SSL
- ✅ PM2 process management
- ✅ Automated backups and monitoring
- ✅ Security hardening (firewall, fail2ban, SSL)
- ✅ Docker-based development alternative
- ✅ Comprehensive troubleshooting guide

**Next Steps:**
1. Choose deployment method (bare metal or Docker)
2. Follow the installation steps sequentially
3. Configure monitoring and backups
4. Run through the troubleshooting guide to verify setup
5. Consider migrating to cloud (AWS) as the organization grows

With both local and cloud deployment options documented, Digiskills.pk has the flexibility to choose the best approach for their needs and scale appropriately.
