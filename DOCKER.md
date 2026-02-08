# Docker Deployment Guide

This project is containerized using Docker and Docker Compose, following best practices for production deployments.

## Quick Start

### 1. Prerequisites

- Docker Desktop (for Mac/Windows) or Docker Engine + Docker Compose (for Linux)
- Git (to clone the repository)

### 2. Setup Environment Variables

Copy the example environment file and configure your credentials:

```bash
cp .env.example .env
```

Edit `.env` and set your values:
- `SECRET_KEY` - Generate a secure random key
- `ADMIN_EMAIL` and `ADMIN_PASSWORD` - Admin credentials
- `MOSAIC_USERNAME` and `MOSAIC_PASSWORD` - Your McMaster credentials
- Email and SMS settings (optional)

### 3. Build and Run

**Development mode** (without nginx):
```bash
make build
make up
```

Or manually:
```bash
docker compose build
docker compose up -d
```

**Production mode** (with nginx reverse proxy):
```bash
make prod
```

Or manually:
```bash
docker compose --profile production up -d
```

### 4. Access the Application

- **Web App**: http://localhost:5001 (dev) or http://localhost (prod)
- **Admin Panel**: http://localhost:5001/admin/login (dev) or http://localhost/admin/login (prod)
- **Status Page**: http://localhost:5001/status (dev) or http://localhost/status (prod)

## Architecture

The application consists of three main services:

### 1. **Web Service** (`web`)
- Flask application serving the user interface and API
- Runs with Gunicorn (2 workers by default)
- Exposed on port 5001
- Health check endpoint: `/status`

### 2. **Scraper Service** (`scraper`)
- Continuously monitors course availability
- Runs every 5 minutes by default
- Sends notifications when courses open
- Uses Playwright for web scraping

### 3. **Init Service** (`init`)
- Initializes the SQLite database on first run
- Loads subject data from `subjects.json`
- Runs once and exits

### 4. **Nginx Service** (`nginx`) - Production only
- Reverse proxy for the Flask application
- Handles SSL/TLS termination (when configured)
- Rate limiting and DDoS protection
- Static file caching
- Only runs in production profile

## Docker Best Practices Implemented

### Multi-Stage Builds
- Separate builder stage for dependencies
- Smaller final images (only runtime dependencies)
- Build tools excluded from production image

### Layer Caching
- Dependencies installed before copying source code
- BuildKit cache mounts for apt and pip
- Ordered from least to most frequently changing

### Security
- Non-root user (`appuser:1000`)
- Minimal base image (python:3.11-slim)
- Only required packages installed
- No secrets in images (use environment variables)

### Performance
- Shared database volume between services
- Persistent cache for nginx
- Connection pooling and rate limiting

### Observability
- Health checks for web service
- Structured logging to stdout
- Service dependencies managed with `depends_on`

## Available Make Commands

```bash
make help       # Show all available commands
make build      # Build Docker images
make up         # Start services (development)
make prod       # Start services (production with nginx)
make down       # Stop all services
make logs       # View logs from all services
make restart    # Restart all services
make clean      # Remove all containers, networks, and volumes
make shell      # Open shell in web container
```

## Configuration

### Scraper Interval

To change the scraper interval, modify the `command` in `docker-compose.yml`:

```yaml
scraper:
  command: ["python", "-u", "scraper/scraper_loop.py", "--continuous", "10"]
  # Change "10" to desired minutes
```

### Gunicorn Workers

To change the number of workers, modify the `command` in `docker-compose.yml`:

```yaml
web:
  command: ["gunicorn", "--bind", "0.0.0.0:5001", "--workers", "4", "--timeout", "120", "backend.user_app:app"]
  # Change "--workers", "4" to desired number
```

## Data Persistence

All application data is stored in Docker volumes:

- `db_data` - SQLite database (shared between services)
- `nginx_cache` - Nginx cache (production only)

To backup the database:
```bash
docker compose cp web:/app/database/courses.db ./backup.db
```

To restore the database:
```bash
docker compose cp ./backup.db web:/app/database/courses.db
```

## Troubleshooting

### View Logs

```bash
# All services
docker compose logs -f

# Specific service
docker compose logs -f web
docker compose logs -f scraper

# Last 100 lines
docker compose logs --tail=100 web
```

### Restart a Service

```bash
docker compose restart web
docker compose restart scraper
```

### Shell Access

```bash
# Web container
docker compose exec web sh

# Scraper container
docker compose exec scraper sh
```

### Database Issues

If you need to reset the database:
```bash
docker compose down -v  # This removes volumes!
docker compose up -d
```

### Build Issues

Clear Docker build cache:
```bash
docker builder prune -f
docker compose build --no-cache
```

## Production Deployment

### 1. Configure SSL/TLS

Edit `nginx/nginx.conf` and uncomment the HTTPS server block:

```nginx
server {
    listen 443 ssl http2;
    server_name your-domain.com;
    
    ssl_certificate /etc/nginx/ssl/cert.pem;
    ssl_certificate_key /etc/nginx/ssl/key.pem;
    # ... rest of configuration
}
```

Place your SSL certificates in `nginx/ssl/`:
```bash
mkdir -p nginx/ssl
cp /path/to/your/cert.pem nginx/ssl/
cp /path/to/your/key.pem nginx/ssl/
```

### 2. Environment Configuration

- Set strong `SECRET_KEY`
- Use production email/SMS credentials
- Set proper `ADMIN_EMAIL` and `ADMIN_PASSWORD`

### 3. Start Production Services

```bash
docker compose --profile production up -d
```

### 4. Monitor Services

```bash
# Check service status
docker compose ps

# View logs
docker compose logs -f

# Check resource usage
docker stats
```

## Scaling

To run multiple web workers:

```bash
docker compose up -d --scale web=3
```

Note: You'll need to configure a load balancer (already done in nginx config).

## Updates and Maintenance

### Update Application

```bash
git pull
docker compose build
docker compose up -d
```

### Update Base Images

```bash
docker compose pull
docker compose up -d
```

### Cleanup Old Images

```bash
docker image prune -a
```

## Security Considerations

1. **Never commit `.env` file** - It's already in `.gitignore`
2. **Use strong passwords** - Generate with `openssl rand -hex 32`
3. **Enable HTTPS** in production - Use Let's Encrypt or your certificate
4. **Keep images updated** - Regularly rebuild with latest base images
5. **Monitor logs** - Watch for suspicious activity
6. **Rate limiting** - Configured in nginx for DDoS protection

## Support

For issues or questions:
- Check the logs: `docker compose logs -f`
- Review the architecture diagram in `architecture.md`
- Open an issue on GitHub
