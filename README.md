# Nearby Services Finder

A full-stack geo-based service finder that lets authenticated users store and search nearby services (hospitals, ATMs, shops, etc.) using real coordinates. Built with Django + GeoDjango on the backend and an interactive Leaflet.js map as a bonus frontend.

## Tech Stack

- **Django 6.0.5** + **Django REST Framework 3.17**
- **GeoDjango** — spatial model fields and radius queries
- **PostgreSQL + PostGIS** — geospatial database
- **JWT Authentication** — via `djangorestframework-simplejwt`
- **Bootstrap 5** + **Leaflet.js** — frontend map UI (bonus)
- **drf-spectacular** — auto-generated Swagger/OpenAPI docs

---

## Prerequisites

- Python 3.10+
- PostgreSQL with PostGIS extension
- GDAL / GEOS system libraries (required by GeoDjango)

**Ubuntu/Debian:**
```bash
sudo apt install postgresql postgresql-contrib postgis gdal-bin libgdal-dev libgeos-dev
```

**Fedora/RHEL:**
```bash
sudo dnf install postgresql postgresql-server postgis gdal gdal-devel geos geos-devel
```

---

## Setup

### 1. Clone the repository
```bash
git clone <repo-url>
cd Nearby_Services_Finder
```

### 2. Create and activate virtual environment
```bash
python -m venv .venv
source .venv/bin/activate
```

### 3. Install dependencies
```bash
pip install -r requirements.txt
```

### 4. Set up PostgreSQL database
```bash
psql -U postgres
```
```sql
CREATE DATABASE nearby_services_db;
\c nearby_services_db
CREATE EXTENSION postgis;
\q
```

### 5. Configure database credentials
Copy the example env file and fill in your PostgreSQL password:
```bash
cp .env.example .env
```

Edit `.env`:
```
DB_NAME=nearby_services_db
DB_USER=postgres
DB_PASSWORD=your_password_here
DB_HOST=localhost
DB_PORT=5432
```

### 6. Run migrations
```bash
python manage.py migrate
```

### 7. Create an admin user
```bash
python manage.py createsuperuser
```

Then assign the ADMIN role via Django shell:
```bash
python manage.py shell
```
```python
from accounts.models import User
user = User.objects.get(username="your_superuser_username")
user.role = "ADMIN"
user.save()
```

### 8. Run the server
```bash
python manage.py runserver
```

- API: `http://localhost:8000/api/`
- Frontend: `http://localhost:8000/login/`
- Swagger UI: `http://localhost:8000/api/schema/swagger-ui/`

---

## Sample Data

Seed categories and services scattered across any map area in one command:

```bash
python manage.py populate_dummy_data --lat 19.9975 --lng 73.7898 --spread-km 25 --count 200
```

| Flag | Default | Description |
|------|---------|-------------|
| `--lat` | 19.987026 | Center latitude |
| `--lng` | 73.784008 | Center longitude |
| `--spread-km` | 25 | Max spread radius (km) |
| `--count` | 200 | Number of services to create |
| `--clear` | off | Delete existing services before seeding |

This also creates 10 categories (Plumber, Doctor, ATM, etc.) and a `staff_seeder` STAFF user as the services owner.

### Manual seeding via Django shell

```python
from services.models import Category, Service
from accounts.models import User
from django.contrib.gis.geos import Point

hospital = Category.objects.create(name="Hospital")
atm = Category.objects.create(name="ATM")
admin = User.objects.get(username="your_superuser_username")

Service.objects.create(name="Apollo Hospital", category=hospital, location=Point(73.7898, 19.9975), rating=4.5, created_by=admin)
Service.objects.create(name="SBI ATM", category=atm, location=Point(73.7870, 19.9960), rating=3.5, created_by=admin)
```

---

## API Endpoints

Base URL: `http://localhost:8000`

All protected endpoints require:
```
Authorization: Bearer <access_token>
```

### Authentication — `/api/auth/`

| Method | Endpoint | Permission | Description |
|--------|----------|------------|-------------|
| POST | `/api/auth/register/` | Public | Register a new user |
| POST | `/api/auth/` | Public | Login — returns access + refresh tokens |
| POST | `/api/auth/refresh/` | Public | Refresh access token |
| GET | `/api/auth/profile/` | Authenticated | Get current user profile |
| GET | `/api/auth/users/` | Admin only | List all users |
| PATCH | `/api/auth/users/<id>/assign-role/` | Admin only | Assign role to a user |

**Register:**
```json
POST /api/auth/register/
{
    "username": "john",
    "email": "john@example.com",
    "password": "securepassword"
}
```

**Login:**
```json
POST /api/auth/
{
    "username": "john",
    "password": "securepassword"
}
```

**Assign Role:**
```json
PATCH /api/auth/users/2/assign-role/
{
    "role": "STAFF"
}
```

---

### Categories — `/api/services/categories/`

| Method | Endpoint | Permission | Description |
|--------|----------|------------|-------------|
| GET | `/api/services/categories/` | Authenticated | List all categories |
| POST | `/api/services/categories/create/` | Admin only | Create a category |
| PATCH | `/api/services/categories/<id>/update/` | Admin only | Update a category |
| DELETE | `/api/services/categories/<id>/delete/` | Admin only | Delete a category |

**Create Category:**
```json
POST /api/services/categories/create/
{
    "name": "Hospital"
}
```

---

### Services — `/api/services/services/`

| Method | Endpoint | Permission | Description |
|--------|----------|------------|-------------|
| GET | `/api/services/services/` | Authenticated | List all services |
| GET | `/api/services/services/?category=Hospital` | Authenticated | Filter by category |
| POST | `/api/services/services/create/` | Staff / Admin | Add a new service |
| GET | `/api/services/services/<id>/` | Authenticated | Get service detail |
| PATCH | `/api/services/services/<id>/update/` | Staff / Admin | Update a service |
| DELETE | `/api/services/services/<id>/delete/` | Admin only | Delete a service |

**Create Service:**
```json
POST /api/services/services/create/
{
    "name": "Apollo Hospital",
    "category": 1,
    "latitude": 19.9975,
    "longitude": 73.7898,
    "rating": 4.5
}
```

---

### Nearby Search — `/api/services/services/nearby/`

| Method | Endpoint | Permission | Description |
|--------|----------|------------|-------------|
| GET | `/api/services/services/nearby/` | Authenticated | Find services within a radius |

**Query Parameters:**

| Param | Required | Description |
|-------|----------|-------------|
| `lat` | Yes | User's latitude |
| `lng` | Yes | User's longitude |
| `radius` | No | Radius in km (default: 5) |
| `category` | No | Filter by category name |

**Examples:**
```
GET /api/services/services/nearby/?lat=19.9975&lng=73.7898&radius=10
GET /api/services/services/nearby/?lat=19.9975&lng=73.7898&radius=5&category=Hospital
```

**Response:**
```json
{
    "count": 2,
    "results": [
        {
            "id": 1,
            "name": "Apollo Hospital",
            "category": "Hospital",
            "rating": 4.5,
            "distance_km": 0.0,
            "latitude": 19.9975,
            "longitude": 73.7898
        },
        {
            "id": 2,
            "name": "City Hospital",
            "category": "Hospital",
            "rating": 4.0,
            "distance_km": 1.23,
            "latitude": 19.9900,
            "longitude": 73.7950
        }
    ]
}
```

---

## Roles & Permissions

| Role | Permissions |
|------|-------------|
| **USER** | Register, login, view services, search nearby, filter by category |
| **STAFF** | All USER permissions + create and update services |
| **ADMIN** | Full access — manage users, assign roles, manage categories, delete services |

Default role on registration: **USER**

Roles are assigned by an Admin via `PATCH /api/auth/users/<id>/assign-role/`.

---

## Token Lifetimes

| Token | Lifetime |
|-------|----------|
| Access Token | 30 minutes |
| Refresh Token | 7 days |

---

## API Documentation (Swagger)

Auto-generated OpenAPI docs are available after starting the server:

- **Swagger UI:** `http://localhost:8000/api/schema/swagger-ui/`
- **OpenAPI JSON:** `http://localhost:8000/api/schema/`

---

## Frontend (Bonus)

A template-based frontend is included. No build step needed — runs alongside the Django server.

| URL | Description |
|-----|-------------|
| `/login/` | Login page |
| `/register/` | Register page |
| `/map/` | Interactive Leaflet map with nearby search |
| `/services/` | Service list with add/edit/delete (role-based) |
| `/admin-panel/` | Category management + user role assignment (Admin only) |

Features:
- JWT tokens stored in `localStorage`, auto-refreshed on expiry
- Map search: click to set location or use "Use My Location"
- Radius slider (1–50 km) + category filter
- Service markers with popups (name, category, rating, distance)
- Role-based UI: staff/admin see add/edit, admin sees delete + admin panel
