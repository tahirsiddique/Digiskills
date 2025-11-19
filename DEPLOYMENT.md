# Digiskills IT Helpdesk - Deployment Guide

## Quick Start (Recommended for On-Premise)

The easiest way to deploy Digiskills is using Docker Compose, which packages everything you need into containers.

### Prerequisites

- Docker (version 20.10 or higher)
- Docker Compose (version 2.0 or higher)
- 2GB RAM minimum
- 5GB disk space

### Installation Steps

1. **Clone or download the repository:**
```bash
cd /path/to/digiskills
```

2. **Configure environment variables (optional):**
```bash
cp .env.example .env
# Edit .env file with your preferred settings
nano .env
```

3. **Start the application:**
```bash
docker-compose up -d
```

4. **Access the application:**
- **Frontend:** http://localhost (or your server IP)
- **API Documentation:** http://localhost:8000/docs
- **Default admin credentials:**
  - Username: `admin`
  - Password: `admin123`

5. **Change admin password:**
After first login, go to your profile and update the password immediately!

### Stopping the Application

```bash
docker-compose down
```

### Viewing Logs

```bash
# All services
docker-compose logs -f

# Backend only
docker-compose logs -f backend

# Frontend only
docker-compose logs -f frontend
```

## Manual Installation (Without Docker)

### Backend Setup

1. **Install Python 3.11+**

2. **Create virtual environment:**
```bash
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. **Install dependencies:**
```bash
pip install -r requirements.txt
```

4. **Configure environment:**
```bash
cp .env.example .env
# Edit .env with your settings
```

5. **Run the backend:**
```bash
python main.py
```

Backend will be available at http://localhost:8000

### Frontend Setup

1. **Install Node.js 18+**

2. **Install dependencies:**
```bash
cd frontend
npm install
```

3. **Configure API URL (if backend is not on localhost:8000):**
Create `frontend/.env` file:
```
VITE_API_URL=http://your-backend-url:8000
```

4. **Development mode:**
```bash
npm run dev
```

5. **Production build:**
```bash
npm run build
npm run preview
```

## Production Deployment

### Using Docker Compose (Recommended)

1. **Update docker-compose.yml for production:**
- Set strong SECRET_KEY
- Change ADMIN_PASSWORD
- Update CORS_ORIGINS to your domain
- Consider using PostgreSQL instead of SQLite

2. **Use environment file:**
```bash
cp .env.example .env
nano .env
```

Set:
- `SECRET_KEY`: Generate a strong random key
- `ADMIN_PASSWORD`: Strong password
- `ADMIN_EMAIL`: Your admin email

3. **Deploy:**
```bash
docker-compose up -d
```

4. **Setup SSL/HTTPS (recommended):**

Add nginx reverse proxy or use Traefik for automatic SSL with Let's Encrypt.

Example nginx configuration:
```nginx
server {
    listen 80;
    server_name your-domain.com;
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl;
    server_name your-domain.com;

    ssl_certificate /path/to/cert.pem;
    ssl_certificate_key /path/to/key.pem;

    location / {
        proxy_pass http://localhost:80;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

### Using PostgreSQL Database

For production, consider PostgreSQL instead of SQLite:

1. **Add PostgreSQL to docker-compose.yml:**
```yaml
services:
  postgres:
    image: postgres:15
    container_name: digiskills-db
    restart: unless-stopped
    environment:
      POSTGRES_DB: digiskills
      POSTGRES_USER: digiskills
      POSTGRES_PASSWORD: your-secure-password
    volumes:
      - postgres-data:/var/lib/postgresql/data
    networks:
      - digiskills-network

volumes:
  postgres-data:
```

2. **Update backend environment:**
```
DATABASE_URL=postgresql://digiskills:your-secure-password@postgres:5432/digiskills
```

3. **Add psycopg2 to requirements.txt:**
```
psycopg2-binary==2.9.9
```

## Backup and Restore

### SQLite Database

**Backup:**
```bash
docker cp digiskills-backend:/app/digiskills.db ./backup-$(date +%Y%m%d).db
```

**Restore:**
```bash
docker cp ./backup-YYYYMMDD.db digiskills-backend:/app/digiskills.db
docker-compose restart backend
```

### PostgreSQL Database

**Backup:**
```bash
docker exec digiskills-db pg_dump -U digiskills digiskills > backup-$(date +%Y%m%d).sql
```

**Restore:**
```bash
docker exec -i digiskills-db psql -U digiskills digiskills < backup-YYYYMMDD.sql
```

## Monitoring

### Health Checks

- Backend: http://localhost:8000/health
- Check application status: `docker-compose ps`

### Logs

```bash
# View all logs
docker-compose logs

# Follow logs
docker-compose logs -f

# Service-specific logs
docker-compose logs backend
docker-compose logs frontend
```

## Troubleshooting

### Container won't start

```bash
# Check logs
docker-compose logs backend

# Rebuild containers
docker-compose down
docker-compose build --no-cache
docker-compose up -d
```

### Database issues

```bash
# Reset database (WARNING: destroys all data)
docker-compose down
docker volume rm digiskills_backend-data
docker-compose up -d
```

### Permission issues

```bash
# Fix uploads directory permissions
docker exec digiskills-backend chmod -R 755 /app/uploads
```

### API not accessible

Check CORS settings in backend/.env:
```
CORS_ORIGINS=http://localhost,http://your-domain.com
```

## Upgrading

1. **Backup your database**
2. **Pull latest code:**
```bash
git pull origin main
```
3. **Rebuild and restart:**
```bash
docker-compose down
docker-compose build
docker-compose up -d
```

## Security Checklist

- [ ] Changed default admin password
- [ ] Set strong SECRET_KEY
- [ ] Enabled HTTPS/SSL
- [ ] Configured firewall (only ports 80/443 open)
- [ ] Regular database backups
- [ ] Updated CORS_ORIGINS to your domain only
- [ ] Disabled DEBUG mode (DEBUG=false)
- [ ] Using PostgreSQL for production (not SQLite)
- [ ] Regular security updates: `docker-compose pull && docker-compose up -d`

## Performance Tuning

### For 100+ users:

1. Use PostgreSQL instead of SQLite
2. Add Redis for caching
3. Use gunicorn with multiple workers:

Update backend Dockerfile CMD:
```dockerfile
CMD ["gunicorn", "main:app", "-w", "4", "-k", "uvicorn.workers.UvicornWorker", "--bind", "0.0.0.0:8000"]
```

Add to requirements.txt:
```
gunicorn==21.2.0
```

## Support

For issues and questions:
- Check logs: `docker-compose logs`
- Review this deployment guide
- Check application logs in the containers

---

**Default Access:**
- URL: http://localhost (or your server IP)
- Username: admin
- Password: admin123

**Remember to change the default password immediately after first login!**
