# Cinema API

A production-ready REST API for a **cinema / streaming platform** built with **FastAPI**.
The project provides authentication, a movie catalogue, shopping cart, order management, and Stripe payment processing.

---

## Table of Contents

- [Tech Stack](#tech-stack)
- [Features](#features)
- [Project Structure](#project-structure)
- [Quick Start](#quick-start)
  - [Run with Docker (recommended)](#run-with-docker-recommended)
  - [Run locally with Poetry](#run-locally-with-poetry)
- [Environment Variables](#environment-variables)
- [Creating a Superuser (Admin Account)](#creating-a-superuser-admin-account)
- [Seed Test Data](#seed-test-data)
- [Database Migrations](#database-migrations)
- [Background Tasks](#background-tasks)
- [API Documentation (Swagger)](#api-documentation-swagger)
- [API Endpoints Overview](#api-endpoints-overview)
  - [Authentication](#authentication)
  - [Registration](#registration)
  - [Password Management](#password-management)
  - [Movies](#movies)
  - [Moderator](#moderator)
  - [Cart](#cart)
  - [Orders](#orders)
  - [Payments](#payments)
  - [Admin Payments](#admin-payments)
- [Roles & Access Control](#roles--access-control)
- [Stripe Integration](#stripe-integration)

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Framework | [FastAPI](https://fastapi.tiangolo.com/) |
| ASGI server | [Uvicorn](https://www.uvicorn.org/) |
| Database | PostgreSQL 16 |
| ORM | SQLAlchemy 2 (async) |
| Migrations | Alembic |
| Auth | JWT (HS256) — access + refresh tokens |
| Task queue | Celery + Redis |
| Payments | Stripe |
| Email | MailHog (dev) / SMTP (prod) |
| Containerisation | Docker / Docker Compose |
| Package manager | Poetry |

---

## Features

### Authentication
- User registration with **email activation** (token expires in 24 hours)
- Resend activation email
- Login → **JWT access token** (1 hour) + **refresh token** (7 days)
- Token refresh
- Logout (single device — revokes refresh token)
- Logout all devices (revokes every refresh token)

### Password Management
- Change password (requires current password)
- Password reset via email (one-time token, expires in 1 hour)
- Strong password validation (min 8 chars, uppercase, digit, special character)

### User Management
- Role-based access control (RBAC):
  - `USER` (group 1) — standard access
  - `MODERATOR` (group 2) — content management
  - `ADMIN` (group 3) — full permissions
- Admin can manually activate accounts
- Admin can change user roles

### Movies
- Paginated movie list with **filtering** (year range, IMDb rating) and **sorting** (price, year, IMDb)
- Full-text **search** by title
- Movie detail view
- Like / dislike a movie
- Add / remove movies from **favourites**
- Threaded **comments** (reply to a comment with `parent_id`)
- Browse by **genre** or **star**

### Cart
- Add / remove individual movies
- View cart with totals
- Clear entire cart

### Orders
- Convert cart contents to an **order**
- View order history (paginated)
- Cancel a pending order
- Revalidate order total against current prices before payment

### Payments (Stripe)
- Create a **Stripe PaymentIntent** for an order
- Stripe **webhook** handler (auto-updates order/payment status)
- View own payment history (filterable by status and date range)

### Admin / Moderator
- CRUD for genres, stars, certifications
- Create and update movies
- View all carts and orders
- View all payments (admin only)
- Inspect which carts contain a specific movie before deletion

### Background Tasks (Celery Beat)
- Periodic cleanup of expired activation tokens
- Periodic cleanup of expired password-reset tokens
- Periodic cleanup of expired refresh tokens

---

## Project Structure

```text
.
├── alembic/                  # Database migration scripts
│   └── versions/
├── app/
│   ├── config/               # Settings, DI wiring, email dependencies
│   ├── database/             # SQLAlchemy engine & session factory
│   ├── exceptions/           # Custom exception classes
│   ├── modules/
│   │   ├── cart/             # Cart models, schemas, service, router
│   │   ├── movies/           # Movie catalogue (models, schemas, CRUD, service, routers)
│   │   │   └── routers/
│   │   │       ├── movies_routers.py     # Public movie endpoints
│   │   │       └── moderator_routers.py  # Moderator-only endpoints
│   │   ├── order/            # Order models, schemas, service, router
│   │   ├── payment/          # Stripe payment models, service, routers
│   │   └── users/            # User models, schemas, CRUD, services, routers
│   │       └── routers/
│   │           ├── auth_router.py        # Login / logout / token refresh
│   │           ├── registration_router.py# Register / activate / admin actions
│   │           └── password_router.py    # Change / reset password
│   ├── notifications/        # Email sender & interfaces
│   ├── tasks/                # Celery app & scheduled tasks
│   ├── templates/            # Jinja2 email templates
│   └── utils/                # JWT manager, security helpers
├── main.py                   # FastAPI application entry point
├── alembic.ini
├── docker-compose.yml
├── Dockerfile
├── pyproject.toml
└── .env.sample
```

---

## Quick Start

### Run with Docker (recommended)

```bash
# 1. Clone the repository
git clone https://github.com/your-username/cinema-api.git
cd cinema-api

# 2. Copy and configure environment variables
cp .env.sample .env
# Edit .env and fill in required values (see Environment Variables below)

# 3. Start all services
docker-compose up --build
```

The API will be available at **http://localhost:8000**.
MailHog (email preview) is available at **http://localhost:8025**.

---

### Run locally with Poetry

```bash
# 1. Install dependencies
poetry install

# 2. Activate the virtual environment
poetry shell

# 3. Copy and configure environment variables
cp .env.sample .env
# Make sure PostgreSQL and Redis are running and configured in .env

# 4. Apply database migrations
alembic upgrade head

# 5. Start the application
uvicorn main:app --reload
```

---

## Environment Variables

Copy `.env.sample` to `.env` and fill in the values.

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `SECRET_KEY_ACCESS` | **Yes** | — | Secret key for signing JWT access tokens |
| `SECRET_KEY_REFRESH` | **Yes** | — | Secret key for signing JWT refresh tokens |
| `JWT_SIGNING_ALGORITHM` | No | `HS256` | JWT signing algorithm |
| `POSTGRES_USER` | No | `postgres` | PostgreSQL username |
| `POSTGRES_PASSWORD` | No | `postgres` | PostgreSQL password |
| `POSTGRES_HOST` | No | `postgres` | PostgreSQL hostname (Docker service name) |
| `POSTGRES_DB_PORT` | No | `5432` | PostgreSQL port |
| `POSTGRES_DB` | No | `fastapi_db` | PostgreSQL database name |
| `STRIPE_SECRET_KEY` | **Yes** | — | Stripe secret API key |
| `STRIPE_WEBHOOK_SECRET` | **Yes** | — | Stripe webhook signing secret |
| `DOCS_USERNAME` | No | `admin` | HTTP Basic username to access `/docs` and `/redoc` |
| `DOCS_PASSWORD` | No | `changeme` | HTTP Basic password to access `/docs` and `/redoc` |
| `BASE_URL` | No | `http://localhost:8000` | Public base URL (used in email links) |
| `LOGIN_TIME_DAYS` | No | `7` | Refresh token lifetime in days |

---

## Creating a Superuser (Admin Account)

Before you can test admin or moderator endpoints you need to seed the `user_groups` table and create an admin account directly via `psql`.

**1. Connect to the database:**

```bash
# Via Docker (use actual values from your .env)
docker exec -it postgres psql -U postgres -d fastapi_db

# Or locally
psql -U postgres -d fastapi_db
```

**2. Seed user groups (run once):**

```sql
INSERT INTO user_groups (name) VALUES ('USER'), ('MODERATOR'), ('ADMIN')
ON CONFLICT DO NOTHING;
```

**3. Create an admin user:**

```sql
INSERT INTO users (email, _hashed_password, is_active, group_id)
VALUES (
  'admin@cinema.local',
  '$2b$12$<bcrypt_hash_of_your_password>',
  true,
  3
);
```

> Generate a bcrypt hash with: `python -c "from passlib.context import CryptContext; print(CryptContext(schemes=['bcrypt']).hash('Admin123!'))"`

**4. Log in via the API:**

```bash
curl -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email": "admin@cinema.local", "password": "Admin123!"}'
```

Use the returned `access_token` as a Bearer token in Swagger UI
(`Authorization → Bearer <token>`) or in your HTTP client.

---

## Seed Test Data

`seed_data.py` populates the database with ready-to-use fixtures so every API
endpoint can be exercised immediately after start-up.

### What gets created

| Entity | Count | Details |
|--------|-------|---------|
| User groups | 3 | `USER`, `MODERATOR`, `ADMIN` |
| Users | 3 | One per role (see credentials below) |
| Certifications | 5 | G, PG, PG-13, R, NC-17 |
| Genres | 10 | Action, Animation, Comedy, Crime, Documentary, Drama, Horror, Romance, Sci-Fi, Thriller |
| Directors | 5 | Nolan, Villeneuve, Tarantino, Ridley Scott, Spielberg |
| Stars | 10 | DiCaprio, Murphy, Hanks, Streep, Chalamet, Zendaya, … |
| Movies | 10 | Full details incl. price, IMDb rating, genres, cast |

### Test credentials

| Email | Password | Role |
|-------|----------|------|
| `admin@cinema.local` | `Admin123!` | ADMIN |
| `moderator@cinema.local` | `Moder123!` | MODERATOR |
| `user@cinema.local` | `User1234!` | USER |

### Running the script

```bash
# Make sure the services are running first
docker-compose up -d

# Run the seed script inside the web container
docker exec -it web python seed_data.py
```

The script is **idempotent** — running it multiple times will skip rows that
already exist without raising errors.

---

## Database Migrations

```bash
# Apply all pending migrations
alembic upgrade head

# Create a new migration after changing models
alembic revision --autogenerate -m "describe your change"

# Roll back the last migration
alembic downgrade -1
```

---

## Background Tasks

The project uses **Celery** with a **Redis** broker for background and scheduled tasks.

| Task | Schedule | Description |
|------|----------|-------------|
| `cleanup_tokens` | Periodic | Deletes expired activation, password-reset, and refresh tokens |

Docker Compose starts two additional containers for this:
- `celery_worker` — processes tasks
- `celery_beat` — schedules periodic tasks

To run workers manually:
```bash
# Worker
celery -A app.tasks.celery_app.celery_app worker -l info

# Beat scheduler
celery -A app.tasks.celery_app.celery_app beat -l info
```

---

## API Documentation (Swagger)

> **Access is restricted to authorised staff only.**

The interactive documentation is served at two URLs:

| URL | Description |
|-----|-------------|
| `GET /docs` | Swagger UI |
| `GET /redoc` | ReDoc |

Both endpoints are protected with **HTTP Basic Authentication**.
Set the credentials in `.env`:

```env
DOCS_USERNAME=admin
DOCS_PASSWORD=your-strong-password
```

When you navigate to `/docs` your browser will prompt for a username and password.
The raw OpenAPI 3.0 schema is available at `GET /openapi.json` (same credentials required).

---

## API Endpoints Overview

All protected endpoints require:
```
Authorization: Bearer <access_token>
```

### Authentication

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| `POST` | `/auth/login` | — | Log in, receive access & refresh tokens |
| `POST` | `/auth/refresh` | — | Exchange refresh token for a new access token |
| `POST` | `/auth/logout` | — | Revoke the supplied refresh token |
| `POST` | `/auth/logout-all` | Bearer | Revoke all refresh tokens for the current user |

### Registration

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| `POST` | `/auth/register` | — | Register a new account (sends activation email) |
| `POST` | `/auth/activate` | — | Activate account with email token |
| `POST` | `/auth/resend-activation` | — | Resend activation email |
| `POST` | `/auth/{user_id}/activate` | Admin | Manually activate a user account |
| `POST` | `/auth/{user_id}/change-group` | Admin | Change a user's role group |

### Password Management

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| `POST` | `/auth/password-reset/request` | — | Send password-reset email |
| `POST` | `/auth/password-reset/complete` | — | Reset password with emailed token |
| `POST` | `/auth/change-password` | Bearer | Change password (requires old password) |

### Movies

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| `GET` | `/cinema/movies/` | — | Paginated list with filters, sorting, search |
| `GET` | `/cinema/movies/{movie_id}/` | — | Movie detail |
| `POST` | `/cinema/movies/{movie_id}/like` | Bearer | Like or dislike a movie |
| `POST` | `/cinema/movies/{movie_id}/favorite` | Bearer | Add to favourites |
| `DELETE` | `/cinema/movies/{movie_id}/favorite` | Bearer | Remove from favourites |
| `GET` | `/cinema/movies/favorites` | Bearer | List favourite movies (filterable) |
| `POST` | `/cinema/movies/{movie_id}/comments` | Bearer | Add a comment / reply |
| `GET` | `/cinema/genres/` | — | List genres with movie counts |
| `GET` | `/cinema/genres/{genre_id}/movies` | — | Movies by genre (paginated) |
| `GET` | `/cinema/stars/` | — | List stars with movie counts |
| `GET` | `/cinema/stars/{star_id}/stars` | — | Movies by star (paginated) |

**Movie list query parameters:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `page` | int | 1 | Page number |
| `per_page` | int | 10 | Items per page (max 20) |
| `year_from` | int | — | Filter: release year ≥ value |
| `year_to` | int | — | Filter: release year ≤ value |
| `imdb` | float | — | Filter: IMDb rating ≥ value |
| `sort_by` | enum | — | Sort field: `price`, `year`, `imdb` |
| `order` | enum | `asc` | Sort direction: `asc`, `desc` |
| `search` | string | — | Full-text search by title (min 2 chars) |

### Moderator

> All endpoints require **Moderator** or **Admin** role.

| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/moderator/genres` | Create genre |
| `PUT` | `/moderator/genres/{genre_id}` | Update genre |
| `DELETE` | `/moderator/genres/{genre_id}` | Delete genre |
| `POST` | `/moderator/movies/` | Create movie |
| `PUT` | `/moderator/movies/{movie_id}` | Update movie |
| `POST` | `/moderator/stars` | Create star |
| `PUT` | `/moderator/stars/{star_id}` | Update star |
| `DELETE` | `/moderator/stars/{star_id}` | Delete star |
| `POST` | `/moderator/certification/` | Create certification |
| `GET` | `/moderator/carts` | View all users' carts |
| `GET` | `/moderator/carts/movie/{movie_id}` | Find carts containing a specific movie |
| `GET` | `/moderator/orders` | List all orders with filters |

### Cart

> All endpoints require **Bearer** authentication.

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/cart/` | View current cart with items |
| `POST` | `/cart/items` | Add a movie to the cart |
| `DELETE` | `/cart/items/{movie_id}` | Remove a movie from the cart |
| `DELETE` | `/cart/` | Clear the entire cart |
| `POST` | `/cart/checkout` | Checkout — *not yet implemented* (use `/orders/`) |

### Orders

> All endpoints require **Bearer** authentication.

| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/orders/` | Place an order from the cart |
| `GET` | `/orders/` | List current user's orders (paginated) |
| `GET` | `/orders/{order_id}` | Get a specific order |
| `PATCH` | `/orders/{order_id}/cancel` | Cancel a pending order |
| `POST` | `/orders/{order_id}/revalidate` | Revalidate order total |

### Payments

> All endpoints require **Bearer** authentication.

| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/payments/{order_id}` | Create Stripe PaymentIntent for an order |
| `GET` | `/payments/my` | List the current user's payments |

**`GET /payments/my` query parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `payment_status` | enum | Filter: `pending`, `succeeded`, `failed`, `refunded` |
| `date_from` | datetime | Filter: created at ≥ value (ISO 8601) |
| `date_to` | datetime | Filter: created at ≤ value (ISO 8601) |

### Admin Payments

> Requires **Admin** role.

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/admin/payments/` | List all payments with optional filters |

**`GET /admin/payments/` query parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `user_id` | int | Filter by user |
| `status` | enum | Filter by payment status |
| `date_from` | datetime | Filter: created at ≥ value (ISO 8601) |
| `date_to` | datetime | Filter: created at ≤ value (ISO 8601) |

---

## Roles & Access Control

| group_id | Role | Permissions |
|----------|------|-------------|
| 1 | USER | Standard API access (movies, cart, orders, payments) |
| 2 | MODERATOR | All USER permissions + manage movies, genres, stars, certifications, view all carts/orders |
| 3 | ADMIN | All MODERATOR permissions + manage users, view all payments |

Roles are enforced via FastAPI dependencies:
- `get_current_user` — requires valid Bearer token
- `get_current_moderator_user` — requires `group_id == 2`
- `get_current_admin_user` — requires `group_id == 3`

---

## Stripe Integration

The API uses **Stripe** for payment processing.

### Payment flow

```
User adds movies to cart
        ↓
POST /orders/          → creates Order (status: PENDING)
        ↓
POST /payments/{id}    → creates Stripe PaymentIntent, returns client_secret / external_id
        ↓
Frontend uses Stripe.js to confirm the payment intent
        ↓
Stripe sends event to POST /payments/webhook
        ↓
Webhook handler updates Order + Payment status → sends confirmation email
```

### Stripe configuration

```env
STRIPE_SECRET_KEY=sk_test_...
STRIPE_WEBHOOK_SECRET=whsec_...
```

To test webhooks locally, use the [Stripe CLI](https://stripe.com/docs/stripe-cli):

```bash
stripe listen --forward-to localhost:8000/payments/webhook
```
