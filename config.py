import os

class Config:
    # Key used internally by Flask to ensure the security of sessions and cookies
    SECRET_KEY = os.environ.get('SECRET_KEY')
    if SECRET_KEY is None:
        raise ValueError("No SECRET_KEY set for Flask application")
    
    # Key used to sign and verify JWT tokens
    JWT_SECRET_KEY = os.environ.get('JWT_SECRET_KEY')
    if JWT_SECRET_KEY is None:
        raise ValueError("No JWT_SECRET_KEY set for JWT token signing")

    # Database connection URL
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL')
    if SQLALCHEMY_DATABASE_URI is None:
        raise ValueError("No DATABASE_URL set for database connection")

    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # JWT expiration time in hours
    JWT_EXPIRATION_HOURS = int(os.environ.get('JWT_EXPIRATION_HOURS', 1))
 
    FLASK_DEBUG=1
