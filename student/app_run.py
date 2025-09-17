from app import create_app
import os

# Flask CLIのために環境変数を設定
os.environ.setdefault('FLASK_APP', 'app_run.py')

# Flaskアプリ作成
app = create_app()

# Flask-Migrate CLI support
@app.cli.command()
def init_db():
    """Initialize the database with migrations."""
    from flask_migrate import init, migrate, upgrade
    from app.database import db
    
    print("Initializing database with migrations...")
    
    # Create migrations directory if not exists
    if not os.path.exists('migrations'):
        init()
        print("Migration repository initialized.")
    
    # Create initial migration
    migrate(message='Initial migration')
    print("Initial migration created.")
    
    # Apply migrations
    upgrade()
    print("Database initialized successfully!")

if __name__ == "__main__":
    app.debug = True
    app.run()
