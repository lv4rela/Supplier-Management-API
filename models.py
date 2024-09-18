import uuid
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
import re
import bleach

# Initialize the SQLAlchemy instance to manage the database
db = SQLAlchemy()

# Model class for service types (ServiceType)
class ServiceType(db.Model):
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = db.Column(db.String(50), unique=True, nullable=False)

    # Constructor for the class
    def __init__(self, name):
        self.name = self.sanitize_input(name) # Sanitizes the name input to prevent XSS attacks

    #Function to sanitize input data
    def sanitize_input(self, input_data):
        return bleach.clean(input_data, strip=True)

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name
        }
# Model class for suppliers (Supplier)
class Supplier(db.Model):
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = db.Column(db.String(80), nullable=False)
    business_name = db.Column(db.String(120), nullable=False)
    contact_name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), nullable=False)
    fiscal_address = db.Column(db.String(120), nullable=False)
    service_type_id = db.Column(db.String(36), db.ForeignKey('service_type.id'), nullable=False)
    service_type = db.relationship('ServiceType', backref=db.backref('suppliers', lazy=True))
    severity = db.Column(db.String(20), nullable=False)
    blocked = db.Column(db.Boolean, default=False)

    def __init__(self, name, business_name, contact_name, email, fiscal_address, service_type, severity):
        self.name = self.sanitize_input(name)
        self.business_name = self.sanitize_input(business_name)
        self.contact_name = self.sanitize_input(contact_name)
        self.email = self.validate_email(email)
        self.fiscal_address = self.sanitize_input(fiscal_address)
        self.service_type_id = service_type
        self.severity = self.validate_severity(self.sanitize_input(severity))

    def sanitize_input(self, input_data):
        return bleach.clean(input_data, strip=True)

    # Validating email
    def validate_email(self, email):
        email_regex = r'^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$'
        if not re.match(email_regex, email):
            raise ValueError("Invalid email address")
        return email

    #Function to validate the severity level
    def validate_severity(self, severity):
        allowed_severity = ["low", "medium", "high","highest"]
        if severity.lower() not in allowed_severity:
            raise ValueError(f"Invalid severity level. Allowed values: {', '.join(allowed_severity)}")
        return severity
        
    @staticmethod
    def check_existing_supplier(name):
        return Supplier.query.filter_by(name=name).first() is not None

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "business_name": self.business_name,
            "contact_name": self.contact_name,
            "email": self.email,
            "fiscal_address": self.fiscal_address,
            "service_type": self.service_type.name if self.service_type else None,
            "severity": self.severity,
            "blocked": self.blocked
        }

class User(db.Model):
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    username = db.Column(db.String(80), unique=True, nullable=False)# change this latter to unique=False
    password_hash = db.Column(db.String(120), nullable=False)
    role = db.Column(db.String(20), nullable=False)

    def __init__(self, username, password, role):
        self.username = self.sanitize_input(username)
        self.set_password(password)
        self.set_role(role)

    def sanitize_input(self, input_data):
        return bleach.clean(input_data, strip=True)

    def set_password(self, password):
        if not self.validate_password(password):
            raise ValueError("Invalid password. Password must be at least 8 characters long, include letters, numbers, and special characters.")
        self.password_hash = generate_password_hash(password)

    # functiokn to validate the user password, I know Django has a default function to this, but here i can use the policy i want
    def validate_password(self, password):
        if len(password) < 8:
            return False
        if not re.search(r"[a-zA-Z]", password):
            return False
        if not re.search(r"\d", password):
            return False
        if not re.search(r"[!@#$%^&*(),.?\":{}|<>+]", password):
            return False
        return True

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    
    #maybe it is not the best way to do it..
    def set_role(self, role):
        allowed_roles = ["operational", "admin"]
        if role not in allowed_roles:
            raise ValueError(f"Invalid role. Allowed roles are: {', '.join(allowed_roles)}")
        self.role = role
    
    def to_dict(self):
        return {
            "id": self.id,
            "username": self.username,
            "role": self.role
        }