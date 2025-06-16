# Library Management System - Usage Guide

## 🚀 Quick Start

### Development Mode (Local Testing)

For local development and testing:

```bash
# Install minimal dependencies
pip install -r requirements-dev.txt

# Run development server
python run_dev.py
```

**Access the application:**
- URL: http://localhost:5000
- Default login: `admin` / `admin123`

### Production Mode (Full Security)

For production deployment:

```bash
# Install all dependencies
pip install -r requirements.txt

# Set environment
export FLASK_CONFIG=vps

# Run with production settings
python app.py
```

## 🔧 Configuration Options

### Development Configuration
- Debug mode enabled
- SQLite database (automatic)
- Security features disabled
- No rate limiting
- CSRF protection disabled

### Production Configuration
- Security headers enabled
- Rate limiting active
- Account lockout protection
- Password expiration (90 days)
- PostgreSQL support
- Email password reset
- Audit logging

## 🔐 Security Features (Production Only)

### Authentication
- ✅ Account lockout after 5 failed attempts
- ✅ Password expiration warnings
- ✅ Secure session management
- ✅ Password reset via email
- ✅ Strong password hashing

### Security Headers
- ✅ XSS Protection
- ✅ Content Security Policy
- ✅ Frame Options (clickjacking protection)
- ✅ Content Type Options

### Rate Limiting
- ✅ Login attempts: 10 per minute
- ✅ Password reset: 5 per minute
- ✅ General API: 1000 per hour

## 🛠️ Management Commands

```bash
# Create new user
python manage.py create-user --username newuser --role admin

# Reset password
python manage.py reset-password --username admin

# Show system statistics
python manage.py stats

# Check system health
python manage.py check-health

# Backup database
python manage.py backup-db
```

## 📁 File Structure

```
library-system/
├── app.py                 # Main application
├── run_dev.py            # Development server
├── wsgi.py               # Production WSGI
├── manage.py             # Management commands
├── config.py             # Configuration settings
├── models.py             # Database models
├── forms.py              # Web forms
├── requirements.txt      # Production dependencies
├── requirements-dev.txt  # Development dependencies
├── env.template          # Environment variables template
├── deploy.sh             # VPS deployment script
├── DEPLOYMENT.md         # Deployment guide
└── templates/            # HTML templates
    └── auth/             # Authentication templates
```

## 🔑 Default Credentials

**⚠️ Change immediately after first login!**
- Username: `admin`
- Password: `admin123`

## 🐛 Troubleshooting

### Common Issues

1. **ModuleNotFoundError:**
   ```bash
   pip install -r requirements-dev.txt  # For development
   pip install -r requirements.txt      # For production
   ```

2. **Database errors:**
   ```bash
   python manage.py init-db
   ```

3. **Permission errors:**
   ```bash
   chmod +x run_dev.py
   chmod +x manage.py
   ```

### Development vs Production

| Feature | Development | Production |
|---------|------------|------------|
| Debug Mode | ✅ Enabled | ❌ Disabled |
| Security Headers | ❌ Disabled | ✅ Enabled |
| Rate Limiting | ❌ Disabled | ✅ Enabled |
| Account Lockout | ❌ Disabled | ✅ Enabled |
| CSRF Protection | ❌ Disabled | ✅ Enabled |
| Password Reset | ❌ Optional | ✅ Required |
| SSL/HTTPS | ❌ Optional | ✅ Recommended |

## 📞 Support

- Check logs in `logs/` directory
- Use `python manage.py check-health` for diagnostics
- Review `DEPLOYMENT.md` for production setup 