"""Main FastAPI application."""
import os
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session

from config import settings
from database import engine, init_db, SessionLocal
from models import User, Category, UserRole, SLAPolicy, SLAPriority
from auth import get_password_hash
from routers import auth, users, tickets, categories, comments, templates, sla, attachments


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events."""
    # Startup
    print("🚀 Starting Digiskills IT Helpdesk...")

    # Initialize database
    print("📊 Initializing database...")
    init_db()

    # Create default data
    db = SessionLocal()
    try:
        # Create admin user if not exists
        admin = db.query(User).filter(User.username == settings.ADMIN_USERNAME).first()
        if not admin:
            print("👤 Creating default admin user...")
            admin = User(
                username=settings.ADMIN_USERNAME,
                email=settings.ADMIN_EMAIL,
                password_hash=get_password_hash(settings.ADMIN_PASSWORD),
                first_name="System",
                last_name="Administrator",
                role=UserRole.ADMIN,
                is_active=True
            )
            db.add(admin)
            db.commit()
            print(f"✅ Admin user created: {settings.ADMIN_USERNAME}")

        # Create default categories
        if db.query(Category).count() == 0:
            print("📁 Creating default categories...")
            default_categories = [
                Category(name="Hardware", description="Hardware-related issues"),
                Category(name="Software", description="Software and application issues"),
                Category(name="Network", description="Network connectivity issues"),
                Category(name="Account", description="User account and access issues"),
                Category(name="Other", description="Other issues"),
            ]
            db.add_all(default_categories)
            db.commit()
            print("✅ Default categories created")

        # Create default SLA policies
        if db.query(SLAPolicy).count() == 0:
            print("⏱️  Creating default SLA policies...")
            default_sla_policies = [
                SLAPolicy(
                    name="Low Priority SLA",
                    description="SLA for low priority tickets",
                    priority=SLAPriority.LOW,
                    response_time_hours=24.0,
                    resolution_time_hours=120.0,
                    is_active=True
                ),
                SLAPolicy(
                    name="Medium Priority SLA",
                    description="SLA for medium priority tickets",
                    priority=SLAPriority.MEDIUM,
                    response_time_hours=8.0,
                    resolution_time_hours=48.0,
                    is_active=True
                ),
                SLAPolicy(
                    name="High Priority SLA",
                    description="SLA for high priority tickets",
                    priority=SLAPriority.HIGH,
                    response_time_hours=4.0,
                    resolution_time_hours=24.0,
                    is_active=True
                ),
                SLAPolicy(
                    name="Critical Priority SLA",
                    description="SLA for critical priority tickets",
                    priority=SLAPriority.CRITICAL,
                    response_time_hours=1.0,
                    resolution_time_hours=8.0,
                    is_active=True
                ),
            ]
            db.add_all(default_sla_policies)
            db.commit()
            print("✅ Default SLA policies created")

        # Create upload directory
        os.makedirs(settings.UPLOAD_DIR, exist_ok=True)

    finally:
        db.close()

    print(f"✨ {settings.APP_NAME} v{settings.APP_VERSION} is ready!")
    print(f"🌐 Environment: {settings.ENVIRONMENT}")
    print(f"📝 API Documentation: http://{settings.HOST}:{settings.PORT}/docs")
    print(f"👤 Default admin: {settings.ADMIN_USERNAME} / {settings.ADMIN_PASSWORD}")
    print("⚠️  Please change the admin password after first login!")

    yield

    # Shutdown
    print("👋 Shutting down...")


# Create FastAPI application
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="IT Helpdesk system for managing support tickets",
    lifespan=lifespan
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth.router)
app.include_router(users.router)
app.include_router(tickets.router)
app.include_router(categories.router)
app.include_router(comments.router)
app.include_router(templates.router)
app.include_router(sla.router)
app.include_router(attachments.router)


@app.get("/")
def read_root():
    """Root endpoint."""
    return {
        "app": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "status": "operational",
        "docs": "/docs"
    }


@app.get("/health")
def health_check():
    """Health check endpoint."""
    return {"status": "healthy"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG
    )
