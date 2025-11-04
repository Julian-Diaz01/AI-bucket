# n8n Docker Setup

This folder contains the Docker configuration for running n8n with PostgreSQL database.

## Prerequisites

- Docker installed on your system
- Docker Compose installed (usually comes with Docker Desktop)

## Quick Start

1. **Start n8n and PostgreSQL:**
   ```bash
   docker-compose up -d
   ```

2. **Access n8n:**
   - Open your browser and navigate to: http://localhost:5678
   - You'll be prompted to create your first user account

3. **Stop n8n:**
   ```bash
   docker-compose down
   ```

4. **Stop and remove all data (volumes):**
   ```bash
   docker-compose down -v
   ```

## Configuration

### Environment Variables

Edit the `.env` file to customize your configuration:

- **Database credentials**: Change `POSTGRES_PASSWORD` and `POSTGRES_NON_ROOT_PASSWORD` for security
- **n8n port**: Change `N8N_PORT` if you want to use a different port
- **Basic Authentication**: Set `N8N_BASIC_AUTH_ACTIVE=true` and configure `N8N_BASIC_AUTH_USER` and `N8N_BASIC_AUTH_PASSWORD`
- **Webhook URL**: Update `WEBHOOK_URL` if you're exposing n8n publicly
- **Timezone**: Adjust `GENERIC_TIMEZONE` and `TZ` to your timezone

### Data Persistence

- **n8n data**: Stored in Docker volume `n8n_data` (workflows, credentials, etc.)
- **PostgreSQL data**: Stored in Docker volume `postgres_data` (database files)

## Docker Commands

### View logs
```bash
docker-compose logs -f n8n
```

### View PostgreSQL logs
```bash
docker-compose logs -f postgres
```

### Restart services
```bash
docker-compose restart
```

### Update n8n to latest version
```bash
docker-compose pull
docker-compose up -d
```

## Backup

### Backup n8n data
```bash
docker run --rm -v n8n_n8n_data:/data -v $(pwd):/backup alpine tar czf /backup/n8n_backup.tar.gz /data
```

### Backup PostgreSQL data
```bash
docker exec n8n_postgres pg_dump -U n8n n8n > n8n_database_backup.sql
```

## Troubleshooting

- **Port already in use**: Change `N8N_PORT` in `.env` file
- **Database connection issues**: Check if PostgreSQL container is healthy: `docker-compose ps`
- **Reset everything**: Run `docker-compose down -v` to remove all containers and volumes

## Security Notes

⚠️ **Important**: Change the default passwords in `.env` before deploying to production!

For production deployments, consider:
- Enabling basic authentication
- Using HTTPS (set `N8N_PROTOCOL=https`)
- Using secure database passwords
- Setting up reverse proxy (nginx, Traefik, etc.)
- Regular backups

