# Digiskills IT Helpdesk

A modern, full-featured IT helpdesk system built for on-premise deployment. Manage support tickets, track issues, and streamline your IT support operations.

## Features

### Core Functionality
- **Ticket Management**: Create, track, and resolve support tickets
- **User Authentication**: Secure JWT-based authentication system
- **Role-Based Access Control**: Admin, Technician, and User roles
- **Ticket Prioritization**: Low, Medium, High, and Critical priority levels
- **Ticket Lifecycle**: New → Assigned → In Progress → Resolved → Closed
- **Comment System**: Add comments and internal notes to tickets
- **Category Management**: Organize tickets by category
- **Dashboard**: Real-time overview of ticket statistics

### Phase 2 Features (NEW!)
- **Email Notifications**: Automated emails for ticket creation, assignment, status changes, and comments
- **File Attachments**: Upload and download files to/from tickets (with file type and size validation)
- **Advanced Search**: Full-text search across tickets with multiple filters
- **Ticket Templates**: Pre-defined ticket templates for common issues
- **SLA Tracking**: Automatic SLA policy application with response and resolution time tracking

### User Roles

**Admin**
- Full system access
- User management
- Create/manage categories
- View all tickets
- Assign tickets to technicians

**Technician**
- View and manage assigned tickets
- Update ticket status
- Add internal notes
- Assign tickets to other technicians

**User**
- Create support tickets
- View own tickets
- Add comments to tickets
- Track ticket status

## Technology Stack

**Backend:**
- Python 3.11+
- FastAPI (high-performance web framework)
- SQLAlchemy (ORM)
- SQLite/PostgreSQL (database)
- JWT authentication
- Pydantic (data validation)

**Frontend:**
- React 18
- Vite (build tool)
- React Router (navigation)
- Axios (API client)
- Lucide React (icons)

**Deployment:**
- Docker & Docker Compose
- Nginx (reverse proxy)

## Quick Start

### Using Docker (Recommended)

1. **Prerequisites**: Install Docker and Docker Compose

2. **Start the application:**
```bash
docker-compose up -d
```

3. **Access the application:**
- Open http://localhost in your browser
- Login with default credentials:
  - Username: `admin`
  - Password: `admin123`

4. **Change default password immediately!**

For detailed deployment instructions, see [DEPLOYMENT.md](DEPLOYMENT.md)

## Manual Installation

### Backend

```bash
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env
python main.py
```

### Frontend

```bash
cd frontend
npm install
npm run dev
```

## Project Structure

```
Digiskills/
├── backend/                # Python FastAPI backend
│   ├── routers/           # API route handlers
│   │   ├── auth.py        # Authentication endpoints
│   │   ├── users.py       # User management
│   │   ├── tickets.py     # Ticket operations
│   │   ├── categories.py  # Category management
│   │   └── comments.py    # Comment system
│   ├── models.py          # Database models
│   ├── schemas.py         # Pydantic schemas
│   ├── database.py        # Database configuration
│   ├── auth.py            # Authentication utilities
│   ├── config.py          # Application settings
│   ├── main.py            # FastAPI application
│   ├── requirements.txt   # Python dependencies
│   └── Dockerfile         # Backend Docker image
├── frontend/              # React frontend
│   ├── src/
│   │   ├── api/          # API client
│   │   ├── components/   # React components
│   │   ├── context/      # React context (auth)
│   │   ├── pages/        # Page components
│   │   ├── App.jsx       # Main app component
│   │   └── main.jsx      # Entry point
│   ├── package.json      # Node dependencies
│   ├── vite.config.js    # Vite configuration
│   ├── nginx.conf        # Production nginx config
│   └── Dockerfile        # Frontend Docker image
├── docker-compose.yml     # Docker orchestration
├── DEPLOYMENT.md         # Deployment guide
├── CLAUDE.md            # AI assistant guide
└── README.md            # This file
```

## API Documentation

Once the backend is running, visit:
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## Configuration

### Environment Variables

Copy `.env.example` to `.env` and customize:

```bash
# Security
SECRET_KEY=your-secret-key-here

# Admin User
ADMIN_USERNAME=admin
ADMIN_PASSWORD=your-secure-password
ADMIN_EMAIL=admin@example.com

# Email (optional)
SMTP_ENABLED=false
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your-email@example.com
SMTP_PASSWORD=your-password
```

## Usage Guide

### Creating a Ticket

1. Login to the system
2. Click "New Ticket" button
3. Fill in:
   - Title (brief description)
   - Detailed description
   - Priority level
   - Category (optional)
4. Click "Create Ticket"

### Managing Tickets (Technician/Admin)

1. Go to "Tickets" page
2. Click on a ticket to view details
3. Update status dropdown
4. Assign to technician
5. Add comments or internal notes
6. Mark as resolved when complete

### User Management (Admin Only)

1. Navigate to "Users" page
2. View all system users
3. Update user roles
4. Activate/deactivate accounts

## Security Features

- Password hashing with bcrypt
- JWT token-based authentication
- Role-based access control (RBAC)
- Input validation and sanitization
- CORS protection
- SQL injection prevention
- XSS protection

## Production Deployment

For production deployment:

1. **Use HTTPS**: Setup SSL certificates (Let's Encrypt recommended)
2. **Strong passwords**: Change all default passwords
3. **PostgreSQL**: Use PostgreSQL instead of SQLite
4. **Backups**: Setup regular database backups
5. **Monitoring**: Implement health checks and logging
6. **Updates**: Keep Docker images updated

See [DEPLOYMENT.md](DEPLOYMENT.md) for complete production setup guide.

## Backup and Restore

### Backup Database

```bash
docker cp digiskills-backend:/app/digiskills.db ./backup-$(date +%Y%m%d).db
```

### Restore Database

```bash
docker cp ./backup.db digiskills-backend:/app/digiskills.db
docker-compose restart backend
```

## Troubleshooting

### Application won't start
```bash
docker-compose logs backend
docker-compose logs frontend
```

### Reset everything
```bash
docker-compose down -v
docker-compose up -d
```

### Database issues
Check logs and ensure database volume has correct permissions.

## Development

### Backend Development

```bash
cd backend
source venv/bin/activate
uvicorn main:app --reload
```

### Frontend Development

```bash
cd frontend
npm run dev
```

### Running Tests

```bash
# Backend
cd backend
pytest

# Frontend
cd frontend
npm test
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## Roadmap

### Phase 1: MVP (Complete)
- [x] User authentication
- [x] Ticket CRUD operations
- [x] Status management
- [x] Comment system
- [x] Category management

### Phase 2: Enhancement (Complete)
- [x] Email notifications
- [x] File attachments
- [x] Advanced search
- [x] Ticket templates
- [x] SLA tracking

### Phase 3: Advanced (Future)
- [ ] Knowledge base
- [ ] Reporting and analytics
- [ ] Mobile application
- [ ] Integration APIs
- [ ] AI-powered categorization

## License

This project is provided as-is for internal use and development.

## Support

For deployment help, see [DEPLOYMENT.md](DEPLOYMENT.md)

For development guidance, see [CLAUDE.md](CLAUDE.md)

## Default Credentials

**Warning**: Change these immediately after first deployment!

- Username: `admin`
- Password: `admin123`
- Email: `admin@digiskills.local`

---

**Built with FastAPI + React | Designed for On-Premise Deployment**
