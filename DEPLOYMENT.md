# Library Management System - VPS Deployment Guide

This guide will help you deploy the Library Management System on a VPS server with enhanced security and production-ready configuration.

## Prerequisites

- Ubuntu 20.04/22.04 VPS server
- Root or sudo access
- Domain name (optional but recommended)
- Basic Linux command line knowledge

## Quick Deployment (Automated)

1. **Upload project files to your VPS:**
   ```bash
   # On your local machine
   scp -r library-system/ root@your-server-ip:/tmp/
   ```

2. **Run the automated deployment script:**
   ```bash
   # On your VPS server
   cd /tmp/library-system
   chmod +x deploy.sh
   sudo ./deploy.sh
   ```

3. **Configure your environment:**
   ```bash
   cd /var/www/library-management
   sudo nano .env
   ```
   Update the configuration with your settings.

## Manual Deployment

### 1. System Setup

```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install dependencies
sudo apt install -y python3 python3-pip python3-venv python3-dev \
    nginx postgresql postgresql-contrib redis-server \
    supervisor git curl ufw fail2ban

# Create project directory
sudo mkdir -p /var/www/library-management
cd /var/www/library-management
```

### 2. Application Setup

```bash
# Clone or upload your project files
# Assuming files are already uploaded

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install --upgrade pip
pip install -r requirements.txt

# Create necessary directories
mkdir -p uploads logs
sudo chown -R www-data:www-data /var/www/library-management
```

### 3. Database Setup

```bash
# Setup PostgreSQL
sudo -u postgres createdb library_db
sudo -u postgres createuser -P library_user  # Set password: secure_password
sudo -u postgres psql -c "GRANT ALL PRIVILEGES ON DATABASE library_db TO library_user;"

# Or use SQLite (simpler, but not recommended for production)
# The app will automatically create SQLite database if PostgreSQL is not configured
```

### 4. Environment Configuration

```bash
# Copy environment template
cp env.template .env

# Edit configuration
nano .env
```

**Important settings in .env:**
```bash
# Security
SECRET_KEY=your-super-secret-key-here-change-this-in-production
FLASK_CONFIG=vps

# Database (PostgreSQL)
DATABASE_URL=postgresql://library_user:secure_password@localhost/library_db

# Or for SQLite (fallback)
# Leave DATABASE_URL empty for SQLite

# Security
HTTPS_ENABLED=true  # Set to false if no SSL

# Email (for password reset)
MAIL_USERNAME=your-email@gmail.com
MAIL_PASSWORD=your-app-password
MAIL_DEFAULT_SENDER=your-email@gmail.com
```

### 5. Initialize Database

```bash
export FLASK_CONFIG=vps
python3 -c "
from app import app, db
from models import User
with app.app_context():
    db.create_all()
    # Create admin user
    admin = User.query.filter_by(username='admin').first()
    if not admin:
        admin = User(username='admin', role='admin', is_active=True, is_verified=True)
        admin.set_password('admin123')  # CHANGE THIS!
        db.session.add(admin)
        db.session.commit()
        print('Admin user created')
"
```

### 6. Gunicorn Configuration

Create `gunicorn.conf.py`:
```python
bind = "127.0.0.1:8000"
workers = 4
worker_class = "sync"
timeout = 120
user = "www-data"
group = "www-data"
accesslog = "/var/www/library-management/logs/gunicorn_access.log"
errorlog = "/var/www/library-management/logs/gunicorn_error.log"
loglevel = "info"
```

### 7. Systemd Service

Create `/etc/systemd/system/library-management.service`:
```ini
[Unit]
Description=Library Management System
After=network.target

[Service]
Type=forking
User=www-data
Group=www-data
WorkingDirectory=/var/www/library-management
Environment=PATH=/var/www/library-management/venv/bin
Environment=FLASK_CONFIG=vps
ExecStart=/var/www/library-management/venv/bin/gunicorn --config gunicorn.conf.py wsgi:application
ExecReload=/bin/kill -s HUP $MAINPID
Restart=always
RestartSec=3

[Install]
WantedBy=multi-user.target
```

Enable and start the service:
```bash
sudo systemctl daemon-reload
sudo systemctl enable library-management
sudo systemctl start library-management
```

### 8. Nginx Configuration

Create `/etc/nginx/sites-available/library-management`:
```nginx
server {
    listen 80;
    server_name your-domain.com;  # Change this
    
    # Security headers
    add_header X-Frame-Options "DENY" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;
    
    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
    
    location /static/ {
        alias /var/www/library-management/static/;
        expires 1y;
    }
    
    location /uploads/ {
        alias /var/www/library-management/uploads/;
        expires 1y;
    }
}
```

Enable the site:
```bash
sudo ln -s /etc/nginx/sites-available/library-management /etc/nginx/sites-enabled/
sudo rm /etc/nginx/sites-enabled/default
sudo nginx -t
sudo systemctl restart nginx
```

### 9. SSL Setup (Recommended)

```bash
# Install Certbot
sudo apt install certbot python3-certbot-nginx

# Get SSL certificate
sudo certbot --nginx -d your-domain.com

# Auto-renewal
sudo systemctl enable certbot.timer
```

### 10. Security Setup

```bash
# Configure firewall
sudo ufw enable
sudo ufw allow ssh
sudo ufw allow 'Nginx Full'

# Configure fail2ban
sudo systemctl enable fail2ban
sudo systemctl start fail2ban
```

## Security Features

### Enhanced Authentication
- Account lockout after 5 failed attempts
- Password expiration (90 days)
- Secure password hashing (PBKDF2)
- Password reset via email
- Session protection

### Security Headers
- X-Frame-Options: DENY
- X-Content-Type-Options: nosniff
- X-XSS-Protection: 1; mode=block
- Content Security Policy
- HTTPS enforcement (when enabled)

### Rate Limiting
- Login attempts: 10 per minute
- Password reset: 5 per minute
- API calls: 1000 per hour
- General requests: configurable

## Monitoring & Maintenance

### Log Locations
- Application logs: `/var/www/library-management/logs/`
- Nginx logs: `/var/log/nginx/`
- System logs: `/var/log/syslog`

### Useful Commands

```bash
# Check service status
sudo systemctl status library-management
sudo systemctl status nginx

# View logs
sudo tail -f /var/www/library-management/logs/library_system.log
sudo tail -f /var/log/nginx/error.log

# Restart services
sudo systemctl restart library-management
sudo systemctl restart nginx

# Update application
cd /var/www/library-management
source venv/bin/activate
git pull  # if using git
pip install -r requirements.txt
sudo systemctl restart library-management
```

### Database Backup

```bash
# PostgreSQL backup
sudo -u postgres pg_dump library_db > backup_$(date +%Y%m%d).sql

# SQLite backup (if using SQLite)
cp library_production.db backup_$(date +%Y%m%d).db
```

## Troubleshooting

### Common Issues

1. **Service won't start:**
   ```bash
   sudo journalctl -u library-management -f
   ```

2. **Nginx 502 error:**
   - Check if Gunicorn is running
   - Verify socket/port configuration

3. **Database connection errors:**
   - Check PostgreSQL service
   - Verify connection credentials in .env

4. **Permission errors:**
   ```bash
   sudo chown -R www-data:www-data /var/www/library-management
   ```

### Default Credentials

**Important:** Change these immediately after deployment!
- Username: `admin`
- Password: `admin123`

## Post-Deployment Checklist

- [ ] Change default admin password
- [ ] Configure email settings
- [ ] Set up SSL certificate
- [ ] Configure backups
- [ ] Test all functionality
- [ ] Set up monitoring
- [ ] Update DNS records
- [ ] Configure log rotation

## Support

For issues and questions:
1. Check logs for error messages
2. Verify all services are running
3. Check firewall and security settings
4. Ensure all dependencies are installed 