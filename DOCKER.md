# Tesla Wall Connector Exporter - Docker Deployment

This directory contains Docker configuration files for running the Tesla Wall Connector Prometheus exporter in a container.

## Quick Start

### Using Docker Compose (Recommended)

1. Clone the repository:
```bash
git clone https://github.com/rdamron/tesla_wallconnector_exporter.git
cd tesla_wallconnector_exporter
```

2. Start the container:
```bash
docker-compose up -d
```

3. Check the logs:
```bash
docker-compose logs -f
```

4. Access metrics:
```bash
curl http://localhost:56852/metrics
```

### Using Docker CLI

Build the image:
```bash
docker build -t twc-exporter .
```

Run the container:
```bash
docker run -d \
  --name twc-exporter \
  -p 56852:56852 \
  -e TWC_HOST=twc.local \
  twc-exporter
```

## Configuration

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `TWC_HOST` | `twc.local` | Tesla Wall Connector hostname or IP address |
| `TWC_PORT` | `56852` | HTTP server port for metrics endpoint |
| `TWC_INTERVAL` | `10` | Update interval in seconds |
| `TWC_BIND` | `0.0.0.0` | Bind address for HTTP server |

### Docker Compose Configuration

Edit the `docker-compose.yml` file or create a `.env` file:

```bash
# .env file
TWC_HOST=192.168.1.100
TWC_PORT=56852
TWC_INTERVAL=15
TWC_BIND=0.0.0.0
```

### Custom Arguments

You can also pass arguments directly to the container:

```bash
docker run -d \
  --name twc-exporter \
  -p 56852:56852 \
  twc-exporter \
  192.168.1.100 -p 56852 -i 15 -b 0.0.0.0
```

Or with docker-compose:
```yaml
services:
  tesla-wallconnector-exporter:
    # ...
    command: ["192.168.1.100", "-p", "56852", "-i", "15", "-b", "0.0.0.0"]
```

## Image Details

- **Base Image**: `python:3.11-slim`
- **Size**: ~50MB (approximately)
- **User**: Runs as non-root user `twc` (UID 1000)
- **Exposed Port**: 56852

## Health Check

The container includes a built-in health check that verifies the HTTP endpoint is responding:

```bash
# Check container health
docker inspect twc-exporter | grep -A 5 Health

# Or with docker-compose
docker-compose ps
```

## Integration with Prometheus

Add to your `prometheus.yml`:

```yaml
scrape_configs:
  - job_name: "tesla_wallconnector"
    static_configs:
      - targets: ["twc-exporter:56852"]
```

If Prometheus is running on the same Docker network:
```yaml
# docker-compose.yml
services:
  prometheus:
    # ...
    networks:
      - monitoring

  tesla-wallconnector-exporter:
    # ...
    networks:
      - monitoring
```

## Networking

### Bridge Network (Default)
The container uses a bridge network by default. This works well for single-host deployments.

### Host Network
For direct network access (useful if the Wall Connector is on your local network):

```bash
docker run -d \
  --name twc-exporter \
  --network host \
  -e TWC_HOST=twc.local \
  twc-exporter
```

Or in docker-compose:
```yaml
services:
  tesla-wallconnector-exporter:
    # ...
    network_mode: host
```

## Troubleshooting

### Cannot Connect to Wall Connector

Check if the container can reach the Wall Connector:
```bash
docker exec twc-exporter ping twc.local
```

### Port Already in Use

Change the host port mapping:
```bash
docker run -d \
  --name twc-exporter \
  -p 9225:56852 \
  twc-exporter
```

### View Logs

```bash
# Docker
docker logs -f twc-exporter

# Docker Compose
docker-compose logs -f
```

### Restart Container

```bash
# Docker
docker restart twc-exporter

# Docker Compose
docker-compose restart
```

## Building from Source

### Standard Build
```bash
docker build -t twc-exporter .
```

### Multi-platform Build
```bash
docker buildx build \
  --platform linux/amd64,linux/arm64,linux/arm/v7 \
  -t twc-exporter \
  .
```

### Build Arguments
The Dockerfile doesn't currently use build arguments, but you can extend it:

```dockerfile
ARG PYTHON_VERSION=3.11
FROM python:${PYTHON_VERSION}-slim
```

Then build with:
```bash
docker build --build-arg PYTHON_VERSION=3.12 -t twc-exporter .
```

## Security Considerations

1. **Non-root User**: The container runs as user `twc` (UID 1000) for security
2. **Minimal Image**: Uses slim Python image to reduce attack surface
3. **No Secrets**: No sensitive data stored in the image
4. **Health Checks**: Automated health monitoring

## Resource Usage

Typical resource consumption:
- **Memory**: ~30-50MB
- **CPU**: <1% (updates every 10 seconds)
- **Network**: Minimal (small JSON payloads)

Set resource limits in docker-compose:
```yaml
services:
  tesla-wallconnector-exporter:
    # ...
    deploy:
      resources:
        limits:
          cpus: '0.5'
          memory: 128M
        reservations:
          cpus: '0.1'
          memory: 32M
```

## Persistence

This exporter is stateless - no volumes are needed. All data is fetched from the Wall Connector on each update cycle.

## Updating

### Docker Compose
```bash
docker-compose pull
docker-compose up -d
```

### Docker CLI
```bash
docker pull twc-exporter:latest
docker stop twc-exporter
docker rm twc-exporter
docker run -d --name twc-exporter -p 56852:56852 twc-exporter
```

## License

MIT License - See the main repository for details.

## Support

For issues specific to the Docker implementation, please open an issue on GitHub.
For general exporter questions, refer to the main [README.md](README.md).
