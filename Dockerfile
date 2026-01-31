# Use Python 3.11 slim image for smaller size
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Create a non-root user to run the application
RUN useradd -m -u 1000 twc && \
    chown -R twc:twc /app

# Copy the Python script
COPY twc_fetcher.py .

# Switch to non-root user
USER twc

# Default environment variables (can be overridden)
ENV TWC_ADDRESS=twc.local \
    TWC_PORT=56852 \
    TWC_INTERVAL=10 \
    TWC_BIND=0.0.0.0

# Expose the metrics port
EXPOSE 56852

# Health check to ensure the service is running
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
    CMD python3 -c "import urllib.request; urllib.request.urlopen('http://localhost:${TWC_PORT}/').read()" || exit 1

# Run the exporter
ENTRYPOINT ["python3", "twc_fetcher.py"]

# Default arguments (can be overridden)
CMD []
