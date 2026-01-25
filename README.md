#  FastAPI Authentication & User Management

A full-featured authentication and user management system 
built with FastAPI, using JWT, email-based activation, password reset, and role-based access control.
Designed as a scalable backend foundation for real-world applications.

##  Features

Authentication
- User registration with email activation (24h expiration)
- Resend activation email
- Login with JWT access & refresh tokens
- Token refresh
- Logout with refresh token revocation

Password Management
- Change password (requires old password)
- Password reset via email (token-based)
- Password strength validation

User Management
- Role-based access control:
- USER – basic access
- MODERATOR – content management
- ADMIN – full permissions
- Admins can:
- Activate user accounts manually
- Change user roles/groups

Background Tasks
- Automatic cleanup of expired tokens using Celery Beat
- Activation tokens
- Password reset tokens
- Refresh tokens

## 📁 Project Structure

```text
app/
├── config/            # Settings, dependencies, DI
├── database/          # Database configuration
├── exceptions/        # Custom exceptions
├── modules/
│   └── users/
│       ├── models/    # SQLAlchemy models
│       ├── schemas/   # Pydantic schemas
│       ├── routers/   # FastAPI routers
│       ├── services/  # Business logic
│       └── crud/      # Database operations
├── notifications/     # Email & notifications
├── tasks/             # Celery & background tasks
├── templates/         # Email templates
├── utils/             # Shared utilities
└── main.py            # FastAPI entry point
```

### Notes

- Email sending is required for activation and password reset
- Admin-only endpoints are protected by role checks
- Designed to be easily extended (profiles, permissions, audit logs)


### Run with Poetry (Local)

```code
# Clone the repository
git clone https://github.com/your-username/your-repo.git
cd your-repo

# Install dependencies
poetry install

# Activate virtual environment
poetry shell

# Run migrations (if using Alembic)
alembic upgrade head

# Start the application
uvicorn app.main:app --reload
```

### Run with Docker

```code
# Build and start containers
docker-compose up --build
```

### Background Tasks

This project uses Celery + Redis for background tasks
and celery-beat for scheduled jobs (e.g. cleanup of expired tokens).

Containers included in Docker setup:
- FastAPI app
- PostgreSQL
- Redis
- Celery worker
- Celery beat