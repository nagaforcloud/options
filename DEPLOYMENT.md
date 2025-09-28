# Deployment Guide for Options Wheel Strategy Trading Bot

## Overview

This document provides comprehensive instructions for deploying the Options Wheel Strategy Trading Bot in various environments, including local, Docker, and production server deployments.

## Prerequisites

- Python 3.8+ installed on your system
- Git version control system
- Docker and Docker Compose (for containerized deployments)
- Zerodha API credentials (for live trading)

## Local Deployment

### 1. Clone the Repository

```bash
git clone <repository-url>
cd Trading
```

### 2. Set up Virtual Environment

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
pip install -r requirements-ai.txt  # Optional: for AI features
```

### 4. Configure Environment Variables

Copy the example environment file and update with your credentials:

```bash
cp .env.example .env
```

Edit the `.env` file with your text editor to add your API credentials and other settings.

### 5. Prepare Data

Run the data preparation script to generate sample data or download real data:

```bash
python main.py --mode prepare-data
```

### 6. Run the Application

Choose your preferred mode:

#### Dashboard Mode (Recommended for initial setup):
```bash
python main.py --mode dashboard
```

#### Backtesting Mode:
```bash
python main.py --mode backtest --start-date 2023-01-01 --end-date 2023-03-01
```

#### Live Trading Mode (⚠️ Use with caution):
```bash
python main.py --mode live
```

## Docker Deployment

### 1. Build and Run with Docker

```bash
# Build the image
docker build -t options-wheel-bot .

# Run the container (for dashboard mode)
docker run -d --env-file .env -p 8501:8501 --name options-wheel-bot options-wheel-bot
```

### 2. Use Docker Compose (Recommended)

```bash
# Start the services
docker-compose up -d

# View logs
docker-compose logs -f

# Stop the services
docker-compose down
```

### 3. Custom Docker Configuration

If you want to customize the deployment, create a `docker-compose.override.yml` file:

```yaml
version: '3.8'

services:
  options-wheel-bot:
    environment:
      - DRY_RUN=false  # Enable for live trading
      - ENABLE_NOTIFICATIONS=true
      # Add other custom environment variables
    volumes:
      - ./custom-config:/app/config:ro
```

Then run:
```bash
docker-compose -f docker-compose.yml -f docker-compose.override.yml up -d
```

## Production Deployment

### 1. Systemd Service (Linux)

Create a systemd service file to run the bot as a system service:

1. Copy the provided service file:
```bash
sudo cp options_wheel_bot.service /etc/systemd/system/
```

2. Edit the service file to match your environment:
```bash
sudo nano /etc/systemd/system/options_wheel_bot.service
```

3. Enable and start the service:
```bash
sudo systemctl daemon-reload
sudo systemctl enable options_wheel_bot
sudo systemctl start options_wheel_bot
```

4. Check service status:
```bash
sudo systemctl status options_wheel_bot
```

### 2. Cloud Platform Deployment

#### Deploy on AWS (ECS)

1. Create an ECS cluster
2. Build your Docker image and push to ECR
3. Create a task definition using the image
4. Deploy as a service

#### Deploy on Google Cloud Run

1. Build and push your container to Google Container Registry
2. Deploy to Cloud Run:
```bash
gcloud run deploy options-wheel-bot \
  --image gcr.io/PROJECT-ID/options-wheel-bot \
  --platform managed \
  --port 8501 \
  --set-env-vars DRY_RUN=true
```

#### Deploy on Azure Container Instances

```bash
az container create \
  --resource-group myResourceGroup \
  --name optionswheelbot \
  --image yourregistry.azurecr.io/options-wheel-bot \
  --dns-name-label options-wheel-bot \
  --ports 8501 \
  --environment-variables DRY_RUN=true
```

## Configuration for Different Environments

### Development Environment

Create a `dev.env` file with development-specific settings:

```bash
DRY_RUN=true
ENABLE_NOTIFICATIONS=false
LOG_LEVEL=DEBUG
```

### Staging Environment

Create a `staging.env` file for pre-production testing:

```bash
DRY_RUN=true
ENABLE_NOTIFICATIONS=true
NOTIFICATION_WEBHOOK_URL=https://staging-webhook.example.com
```

### Production Environment

Use secure methods to manage production secrets:

```bash
DRY_RUN=false  # Live trading enabled
ENABLE_NOTIFICATIONS=true
LOG_LEVEL=INFO
MAX_DAILY_LOSS_LIMIT=10000.0
```

## Monitoring and Logging

### Log Files

The bot writes logs to the `logs/` directory:
- `options_wheel_bot.log` - Main application logs
- Daily rotated files for history

### Health Checks

The application includes health check functionality:

```bash
# Run the health check script
python health_check.py
```

### Dashboard Monitoring

The Streamlit dashboard provides real-time monitoring:
- Portfolio performance
- Risk metrics
- Trade history
- System health status

## Maintenance and Operations

### Regular Maintenance Tasks

1. Rotate log files to prevent disk space issues
2. Backup database files in `data/` directory
3. Update dependencies regularly
4. Review and adjust risk parameters based on market conditions

### Backup Strategy

```bash
# Backup trading database
cp data/trading_data.db backup/trading_data_$(date +%Y%m%d_%H%M%S).db

# Backup configuration
tar -czf backup/config_$(date +%Y%m%d_%H%M%S).tar.gz .env config/
```

### Update Process

1. Stop the current instance
2. Pull the latest code changes
3. Update dependencies if needed
4. Test in dry run mode
5. Restart the service

## Security Considerations

### API Key Security

- Never commit API keys to version control
- Use environment variables or secure vaults
- Use separate API credentials for different environments
- Regularly rotate API keys

### Access Control

- Limit access to the dashboard interface
- Use VPN or private networks for production deployments
- Implement proper authentication for dashboard access

### Data Security

- Encrypt sensitive data at rest
- Use SSL/TLS for data in transit
- Regularly audit access logs

## Troubleshooting

### Common Issues

#### 1. API Connection Issues
- Verify API credentials in `.env`
- Check internet connectivity
- Ensure Zerodha API service is available

#### 2. Database Connection Issues
- Check file permissions for `data/` directory
- Verify disk space availability
- Check for database lock issues

#### 3. Docker Container Issues
- Check container logs: `docker logs container_name`
- Verify environment variables are properly set
- Ensure required ports are available

### Performance Issues

- Monitor system resources (CPU, memory, disk)
- Optimize database queries if needed
- Adjust strategy run interval based on system capacity

## Rollback Plan

In case of issues with a new version:

1. Stop the current deployment
2. Deploy the previous stable version
3. Verify functionality
4. Investigate and fix the issue
5. Plan next deployment with fixes

## Additional Resources

- [Zerodha API Documentation](https://kite.trade/docs/)
- [Python KiteConnect Client](https://github.com/zerodha/pykiteconnect)
- [NSE India Market Data](https://www.nseindia.com/)

This deployment guide should help you successfully deploy the Options Wheel Strategy Trading Bot in your preferred environment. Remember to thoroughly test in dry run mode before enabling live trading.