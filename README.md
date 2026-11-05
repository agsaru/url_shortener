# URL Shortener API

A fast, scalable, and robust URL shortening service built with **FastAPI**, **PostgreSQL**, and **Redis**. It features URL analytics, rate limiting, custom aliases, and caching for high-performance redirects.

## Features

- 🚀 **FastAPI**: Asynchronous, highly performant web framework.
- 💾 **PostgreSQL & SQLAlchemy**: Reliable relational database handling with ORM.
- ⚡ **Redis Caching**: Extremely fast redirects via cached URLs.
- 📊 **Analytics Tracking**: Tracks total visit counts and last visit timestamps.
- 🛡️ **Rate Limiting**: Protects endpoints (e.g., 5 requests/minute for shortening) using `slowapi`.
- 🔗 **Custom Aliases**: Users can define their own custom short codes.
- 🔄 **Database Migrations**: Integrated with `Alembic` for schema version control.
- 🐳 **Dockerized**: Easy setup using `docker-compose`.

---

## Prerequisites

If you are running the project locally without Docker, you will need:
- Python 3.12+
- PostgreSQL
- Redis Server

---

## ⚙️ Environment Variables

Create a `.env` file in the root directory and add the following variables:

```env
# Database Configuration
DATABASE_URL=postgresql://user:password@localhost:5432/dbname
# If using Docker, it might look like: postgresql://user:password@db:5432/dbname

# Redis Configuration
REDIS_URL=redis://localhost:6379/0
# If using Docker: redis://redis:6379/0

# Public URL used in generated short links
PUBLIC_BASE_URL=http://localhost:8080

# Application Secrets
HASHED_SALT=your_super_secret_random_salt_string
```

`PUBLIC_BASE_URL` must be the externally reachable HTTP or HTTPS address of
the API. It is used instead of the request `Host` header so clients cannot
make the service generate links for an untrusted domain.

# 🛠️ Setup & Installation

You can run this application either using **Docker (Recommended)** or **locally**.

---

## Method 1: Using Docker (Recommended)

### 1. Clone the repository

```bash
git clone <repository-url>
cd <repository-name>
```

### 2. Create the `.env` file

Create a `.env` file in the project root and configure it as described above.

### 3. Build and start the containers

```bash
docker-compose up -d --build
```

### 4. Run database migrations

Run Alembic inside the backend container to create the database tables.

```bash
docker-compose exec backend alembic upgrade head
```

### 5. Access the application

- **API Base URL:** `http://localhost:8080`
- **Swagger UI:** `http://localhost:8080/docs`

---

## Method 2: Local Development

### 1. Create and activate a virtual environment

**Linux/macOS**

```bash
python -m venv venv
source venv/bin/activate
```

**Windows**

```powershell
python -m venv venv
venv\\Scripts\\activate
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

### 3. Start PostgreSQL and Redis

Ensure both PostgreSQL and Redis are running locally, then update your `.env` file with the appropriate connection details.

### 4. Run database migrations

```bash
alembic upgrade head
```

### 5. Start the FastAPI server

```bash
uvicorn src.main:app --host 0.0.0.0 --port 8000 --reload
```

---

## Testing

Install the project dependencies and run the regular test suite:

```bash
pip install -r requirements.txt
pytest
```

The concurrency tests use PostgreSQL and are skipped unless `TEST_DATABASE_URL` is set. Point it to a dedicated test database, never your production database:

```bash
export TEST_DATABASE_URL="postgresql://user:password@localhost:5432/url_shortener_test"
pytest tests/test_concurrency.py
```

The concurrency tests synchronize competing requests at their initial database checks to exercise duplicate-destination and duplicate-alias races.

Rate limiting uses the configured Redis instance, so the limit is shared across
backend workers and containers.

---

# 📚 API Endpoints

## 1. Shorten a URL

- **Endpoint:** `POST /shorten`
- **Rate Limit:** `5 requests/minute`

### Request Body

```json
{
  "longUrl": "https://www.example.com/very/long/path/that/needs/shortening",
  "custom_alias": "my-custom-link"
}
```

> `custom_alias` is optional.

Equivalent HTTP URLs (such as host-name case, query parameter order, or a default port difference) are
normalized, and submitting the same destination URL again returns the existing
short URL with **200 OK**. Providing a different custom alias for an already
shortened URL, or choosing an alias already in use, returns **409 Conflict**.
Invalid URLs and aliases return **422 Unprocessable Entity**. Custom aliases
may contain only letters, numbers, underscores, and hyphens, with a maximum
length of 64 characters.
Only HTTP and HTTPS URLs are accepted. The service validates URL syntax but
does not perform DNS or availability checks, because destinations can become
unreachable after shortening and network checks would make requests unreliable.
URLs containing embedded usernames or passwords are rejected.

### Response (201 Created)

```json
{
  "success": true,
  "shortURL": "http://localhost:8000/my-custom-link",
  "createdAt": "2026-06-25T05:40:17.732Z",
  "message": "New Short Url created successfully"
}
```

---

## 2. Redirect to Original URL

- **Endpoint:** `GET /{short_code}`

### Description

Redirects the client to the original URL.

Additional behavior:

- Checks Redis cache before querying the database.
- Stores the URL in Redis for **24 hours (86400 seconds)** after a cache miss.
- Checks expiration for cached and database-backed URLs.
- Updates analytics before returning the redirect.
- Returns an HTTP **307 Temporary Redirect**.

### Response

```
307 Temporary Redirect
```

---

## 3. Get URL Statistics

- **Endpoint:** `GET /stats/{short_code}`

### Response (200 OK)

```json
{
  "success": true,
  "urlStats": {
    "lastVisit": "2026-06-25T06:12:00.000Z",
    "visitCount": 42,
    "createdAt": "2026-06-25T05:40:17.732Z"
  }
}
```

---

# 🗄️ Database Migrations (Alembic)

Whenever you modify the SQLAlchemy models (e.g., in `src/models/model.py`), create and apply a new migration.

## Generate a migration

```bash
alembic revision --autogenerate -m "Description of changes"
```

## Apply the migration

```bash
alembic upgrade head
```

---

# 📄 License

This project is licensed under the **MIT License**.

See the `LICENSE` file for more information.
