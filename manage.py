#!/usr/bin/env python3
"""
Library Management System - Administrative Management Script
Use this script for common administrative tasks
"""

import os
import sys
import click
from datetime import datetime, timedelta

# Add project directory to path
project_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_dir)

# Set configuration
os.environ.setdefault('FLASK_CONFIG', 'vps')

from app import app
from models import db, User, Product, Sale, Customer, Category, Expense, Payment


@click.group()
def cli():
    """Library Management System Administrative Commands"""
    pass


@cli.command()
@click.option('--username', prompt='Username', help='Username for the new user')
@click.option('--password', prompt='Password', hide_input=True, help='Password for the new user')
@click.option('--email', prompt='Email (optional)', default='', help='Email address')
@click.option('--role', type=click.Choice(['admin', 'seller']), default='seller', help='User role')
def create_user(username, password, email, role):
    """Create a new user account"""
    with app.app_context():
        # Check if user already exists
        existing_user = User.query.filter_by(username=username).first()
        if existing_user:
            click.echo(f"❌ User '{username}' already exists!")
            return
        
        # Create new user
        user = User(
            username=username.lower().strip(),
            email=email.lower().strip() if email else None,
            role=role,
            is_active=True,
            is_verified=True
        )
        user.set_password(password)
        
        db.session.add(user)
        db.session.commit()
        
        click.echo(f"✅ User '{username}' created successfully with role '{role}'!")


@cli.command()
@click.option('--username', prompt='Username', help='Username to reset password for')
@click.option('--password', prompt='New password', hide_input=True, help='New password')
def reset_password(username, password):
    """Reset user password"""
    with app.app_context():
        user = User.query.filter_by(username=username).first()
        if not user:
            click.echo(f"❌ User '{username}' not found!")
            return
        
        user.reset_password(password)
        click.echo(f"✅ Password reset successfully for user '{username}'!")


@cli.command()
@click.option('--username', prompt='Username', help='Username to unlock')
def unlock_user(username):
    """Unlock a locked user account"""
    with app.app_context():
        user = User.query.filter_by(username=username).first()
        if not user:
            click.echo(f"❌ User '{username}' not found!")
            return
        
        user.unlock_account()
        user.is_active = True
        db.session.commit()
        
        click.echo(f"✅ User '{username}' unlocked successfully!")


@cli.command()
def list_users():
    """List all users and their status"""
    with app.app_context():
        users = User.query.all()
        
        click.echo("\n📋 User List:")
        click.echo("-" * 80)
        click.echo(f"{'Username':<20} {'Role':<10} {'Active':<8} {'Locked':<8} {'Last Login':<20}")
        click.echo("-" * 80)
        
        for user in users:
            is_locked = "Yes" if user.is_account_locked() else "No"
            last_login = user.last_login.strftime("%Y-%m-%d %H:%M") if user.last_login else "Never"
            
            click.echo(f"{user.username:<20} {user.role:<10} {str(user.is_active):<8} {is_locked:<8} {last_login:<20}")


@cli.command()
def init_db():
    """Initialize database with tables"""
    with app.app_context():
        db.create_all()
        click.echo("✅ Database initialized successfully!")


@cli.command()
@click.confirmation_option(prompt='Are you sure you want to reset the database? This will delete all data!')
def reset_db():
    """Reset database (WARNING: Deletes all data!)"""
    with app.app_context():
        db.drop_all()
        db.create_all()
        
        # Create default admin user
        admin = User(
            username='admin',
            role='admin',
            is_active=True,
            is_verified=True
        )
        admin.set_password('admin123')
        db.session.add(admin)
        db.session.commit()
        
        click.echo("✅ Database reset successfully!")
        click.echo("🔑 Default admin user created: admin / admin123")


@cli.command()
def stats():
    """Show system statistics"""
    with app.app_context():
        # Count records
        users_count = User.query.count()
        products_count = Product.query.count()
        categories_count = Category.query.count()
        customers_count = Customer.query.count()
        sales_count = Sale.query.count()
        
        # Recent activity
        recent_sales = Sale.query.filter(
            Sale.created_at >= datetime.utcnow() - timedelta(days=7)
        ).count()
        
        # Low stock products
        low_stock = Product.query.filter(
            Product.stock_quantity <= Product.min_stock_threshold
        ).count()
        
        # Out of stock products
        out_of_stock = Product.query.filter(Product.stock_quantity <= 0).count()
        
        click.echo("\n📊 System Statistics:")
        click.echo("-" * 40)
        click.echo(f"👥 Users: {users_count}")
        click.echo(f"📦 Products: {products_count}")
        click.echo(f"🏷️  Categories: {categories_count}")
        click.echo(f"👤 Customers: {customers_count}")
        click.echo(f"💰 Total Sales: {sales_count}")
        click.echo("-" * 40)
        click.echo(f"📈 Sales (Last 7 days): {recent_sales}")
        click.echo(f"⚠️  Low Stock Products: {low_stock}")
        click.echo(f"❌ Out of Stock Products: {out_of_stock}")


@cli.command()
@click.option('--days', default=7, help='Number of days to keep logs')
def cleanup_logs(days):
    """Clean up old log files"""
    log_dir = os.path.join(project_dir, 'logs')
    if not os.path.exists(log_dir):
        click.echo("No logs directory found.")
        return
    
    cutoff_date = datetime.now() - timedelta(days=days)
    cleaned_files = 0
    
    for filename in os.listdir(log_dir):
        filepath = os.path.join(log_dir, filename)
        if os.path.isfile(filepath):
            file_time = datetime.fromtimestamp(os.path.getmtime(filepath))
            if file_time < cutoff_date:
                os.remove(filepath)
                cleaned_files += 1
                click.echo(f"🗑️  Removed: {filename}")
    
    click.echo(f"✅ Cleaned up {cleaned_files} old log files.")


@cli.command()
def backup_db():
    """Create database backup"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # Check if using PostgreSQL or SQLite
    database_url = app.config.get('SQLALCHEMY_DATABASE_URI', '')
    
    if 'postgresql' in database_url:
        # PostgreSQL backup
        backup_file = f"backup_postgresql_{timestamp}.sql"
        os.system(f"pg_dump library_db > {backup_file}")
        click.echo(f"✅ PostgreSQL database backed up to: {backup_file}")
    
    elif 'sqlite' in database_url:
        # SQLite backup
        import shutil
        db_file = database_url.replace('sqlite:///', '')
        backup_file = f"backup_sqlite_{timestamp}.db"
        shutil.copy2(db_file, backup_file)
        click.echo(f"✅ SQLite database backed up to: {backup_file}")
    
    else:
        click.echo("❌ Unknown database type for backup.")


@cli.command()
def check_health():
    """Check system health"""
    with app.app_context():
        try:
            # Test database connection
            db.session.execute('SELECT 1')
            click.echo("✅ Database connection: OK")
        except Exception as e:
            click.echo(f"❌ Database connection: FAILED - {str(e)}")
        
        # Check critical directories
        dirs_to_check = ['logs', 'uploads', 'static']
        for dir_name in dirs_to_check:
            dir_path = os.path.join(project_dir, dir_name)
            if os.path.exists(dir_path) and os.access(dir_path, os.W_OK):
                click.echo(f"✅ Directory '{dir_name}': OK")
            else:
                click.echo(f"❌ Directory '{dir_name}': Missing or not writable")
        
        # Check environment variables
        critical_vars = ['SECRET_KEY', 'FLASK_CONFIG']
        for var in critical_vars:
            if os.environ.get(var):
                click.echo(f"✅ Environment variable '{var}': Set")
            else:
                click.echo(f"⚠️  Environment variable '{var}': Not set")


if __name__ == '__main__':
    cli() 