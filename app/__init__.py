import click
from flask import Flask, render_template, redirect, url_for
from flask_login import LoginManager
from sqlalchemy.exc import OperationalError
from app.config import get_config
from app.db import db, init_app as init_db
from app.models import User
import os


login_manager = LoginManager()


def create_app():
    app = Flask(__name__, template_folder="templates", static_folder="static")
    app.config.from_object(get_config())
    app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY')

    import cloudinary
    import cloudinary.uploader

    cloudinary.config(
        cloud_name="CLOUDINARY_CLOUD_NAME",
        api_key="CLOUDINARY_API_KEY",
        api_secret="CLOUDINARY_API_SECRET"
    )

    # Init extensions
    init_db(app)
    login_manager.init_app(app)
    login_manager.login_view = "auth.login"

    # Register blueprints
    from app.blueprints.auth import auth_bp
    from app.blueprints.dashboard import dashboard_bp
    from app.blueprints.news import news_bp
    from app.blueprints.products import products_bp
    from app.blueprints.profile import profile_bp
    from app.blueprints.share import share_bp
    from app.blueprints.withdrawal import withdrawal_bp
    from app.blueprints.admin import admin_bp

    app.register_blueprint(auth_bp,        url_prefix="/auth")
    app.register_blueprint(dashboard_bp,   url_prefix="/")
    app.register_blueprint(news_bp,   url_prefix="/news")
    app.register_blueprint(products_bp,    url_prefix="/products")
    app.register_blueprint(profile_bp,     url_prefix="/profile")
    app.register_blueprint(share_bp,        url_prefix="/share")
    app.register_blueprint(withdrawal_bp,  url_prefix="/withdrawal")
    app.register_blueprint(admin_bp,      url_prefix="/admin")


    # ── Custom Error Handlers for Database Connection Issues ─────
    
    @app.errorhandler(OperationalError)
    def handle_operational_error(error):
        """Handle SQLAlchemy OperationalError (database connection issues)."""
        app.logger.error(f"Database connection error: {str(error)}")
        return render_template('errors/network_error.html'), 503


    @app.errorhandler(500)
    def handle_internal_error(error):
        """Handle internal server errors, check if it's a database issue."""
        error_str = str(error)
        
        # Check if error is database-related
        db_error_keywords = [
            'connection', 'timeout', 'refused', 'unreachable', 
            'neon', 'postgres', 'sqlalchemy', 'operational'
        ]
        
        is_db_error = any(keyword in error_str.lower() for keyword in db_error_keywords)
        
        if is_db_error:
            app.logger.error(f"Database-related 500 error: {error_str}")
            return render_template('errors/network_error.html'), 503
        
        # For other 500 errors, use default or custom template
        return render_template('errors/500.html'), 500


    @app.before_request
    def check_db_connection():
        """Check database connection before each request."""
        try:
            # Simple lightweight query to test connection
            db.session.execute('SELECT 1')
        except OperationalError as e:
            app.logger.error(f"Database connection failed in before_request: {str(e)}")
            # Rollback the failed session
            db.session.rollback()
            # Return network error page
            return render_template('errors/network_error.html'), 503
        except Exception as e:
            # Log other errors but don't block request
            app.logger.warning(f"Database check warning: {str(e)}")
            db.session.rollback()


    # ── CLI Commands ────────────────────────────────────────────
    
    @app.cli.command("seed-db")
    def seed_db_command():
        """Seed the database with default products and news."""
        try:
            from app.seed import run_seeds
            run_seeds()
            click.echo("Database seeded.")
        except OperationalError as e:
            click.echo("Network Error: Could not connect to database.")
            click.echo("Please check your internet connection and try again.")
            click.echo(f"Error: {str(e)}")

    @app.cli.command("make-admin")
    @click.argument("phone")
    def make_admin_command(phone):
        """Grant admin access to a user by phone number."""
        try:
            from app.models import User
            user = User.query.filter_by(phone=phone).first()
            if not user:
                click.echo(f"User {phone} not found.")
                return
            user.is_admin = True
            db.session.commit()
            click.echo(f"User {phone} is now an admin.")
        except OperationalError as e:
            click.echo("Network Error: Could not connect to database.")
            click.echo("Please check your internet connection and try again.")

    @app.cli.command("create-admin")
    @click.argument("phone")
    @click.argument("password")
    def create_admin_command(phone, password):
        """Create a new admin user with phone and password."""
        try:
            # Check if user already exists
            existing_user = User.query.filter_by(phone=phone).first()
            if existing_user:
                click.echo(f"User with phone {phone} already exists.")
                return

            # Create new user
            admin = User(
                phone=phone,
                is_admin=True
            )
            admin.set_password(password)

            db.session.add(admin)
            db.session.commit()

            click.echo(f"Admin created successfully: {phone}")

        except OperationalError as e:
            db.session.rollback()
            click.echo("Network Error: Could not connect to database.")
            click.echo("Please check your internet connection and try again.")
            click.echo(f"Error: {str(e)}")
        except Exception as e:
            db.session.rollback()
            click.echo("Error creating admin")
            click.echo(str(e))

    return app


# ── User Loader (outside create_app) ────────────────────────────

@login_manager.user_loader
def load_user(user_id):
    """Load user with error handling for network issues."""
    try:
        return User.query.get(int(user_id))
    except OperationalError:
        # Return None if database is unreachable - user will be treated as logged out
        return None
    except Exception:
        return None