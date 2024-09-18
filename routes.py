from flask import Blueprint, request, jsonify, g
from models import db, Supplier, User, ServiceType
from auth import requires_auth, generate_jwt

routes = Blueprint('routes', __name__)

@routes.route('/suppliers', methods=['GET'])
@requires_auth
def get_suppliers():
    filters = []
    
    if request.args.get('name'):
        sanitized_name = Supplier.sanitize_input(Supplier, request.args.get('name'))
        filters.append(Supplier.name.ilike(f"%{sanitized_name}%"))
    
    if request.args.get('severity'):
        sanitized_severity = Supplier.validate_severity(Supplier, request.args.get('severity'))
        filters.append(Supplier.severity == sanitized_severity)
    
    if request.args.get('service_type'):
        sanitized_service_type_name = Supplier.sanitize_input(Supplier, request.args.get('service_type'))
        service_type = ServiceType.query.filter_by(name=sanitized_service_type_name).first()
        if service_type:
            filters.append(Supplier.service_type_id == service_type.id)
        else:
            return jsonify({"error": f"Service type '{sanitized_service_type_name}' not found"}), 404
    
    if g.user['role'] != 'admin':
        filters.append(Supplier.blocked == False)

    suppliers = Supplier.query.filter(*filters).all()
    
    if not suppliers:
        return jsonify({"error": "There is no supplier registered, please register a new supplier"}), 404
    
    response = []
    for supplier in suppliers:
        supplier_data = supplier.to_dict()
        if g.user['role'] == 'admin':
            supplier_data["status"] = "Blocked" if supplier.blocked else "Active"
        else:
            supplier_data = {
                "name": supplier.name,
                "service_type": supplier.service_type.name if supplier.service_type else None,
                "severity": supplier.severity
            }
        response.append(supplier_data)

    return jsonify(response)

@routes.route('/supplier/register', methods=['POST'])
@requires_auth
def create_supplier():
    if g.user['role'] != 'admin':
        return jsonify({"message": "Only admins can create suppliers"}), 403

    data = request.json

    if Supplier.check_existing_supplier(data['name']):
        return jsonify({"error": "A supplier with this name already exists."}), 400

    service_type_name = data.get('service_type')
    service_type = ServiceType.query.filter_by(name=service_type_name).first()
    if not service_type:
        service_type = ServiceType(name=service_type_name)
        db.session.add(service_type)
        db.session.commit()

    try:
        supplier = Supplier(
            name=data['name'],
            business_name=data['business_name'],
            contact_name=data['contact_name'],
            email=data['email'],
            fiscal_address=data['fiscal_address'],
            service_type=service_type.id,
            severity=data['severity']
        )
        db.session.add(supplier)
        db.session.commit()
        return jsonify(supplier.to_dict()), 201
    except Exception as e:
        db.session.rollback()  # Reverte qualquer mudança no banco de dados se ocorrer erro
        return jsonify({"error": "An error occurred while creating the supplier", "message": str(e)}), 500

@routes.route('/suppliers/blocked', methods=['PUT'])
@requires_auth
def block_supplier():
    if g.user['role'] != 'admin':
        return jsonify({"message": "Only admins can block suppliers"}), 403

    data = request.json
    supplier_id = data.get('id')

    if not supplier_id:
        return jsonify({"message": "Supplier ID is required"}), 400

    supplier = Supplier.query.get_or_404(supplier_id)
    
    if supplier.blocked:
        return jsonify({"message": "Supplier is already blocked"}), 400
    
    supplier.blocked = True
    db.session.commit()
    
    return jsonify(supplier.to_dict()), 200
    
@routes.route('/suppliers/unblocked', methods=['PUT'])
@requires_auth
def unblock_supplier():
    # Check if the user has the 'admin' role
    if g.user['role'] != 'admin':
        return jsonify({"message": "Only admins can unblock suppliers"}), 403

    # Retrieve the data from the request
    data = request.json
    supplier_id = data.get('id')

    # Check if the supplier ID was provided
    if not supplier_id:
        return jsonify({"message": "Supplier ID is required"}), 400

    # Find the supplier by ID
    supplier = Supplier.query.get_or_404(supplier_id)
    
    # Check if the supplier is already unblocked
    if not supplier.blocked:
        return jsonify({"message": "Supplier is already unblocked"}), 400
    
    # Unblock the supplier
    supplier.blocked = False
    db.session.commit()
    
    # Return the unblocked supplier's information
    return jsonify(supplier.to_dict()), 200

@routes.route('/users/register', methods=['POST'])
@requires_auth
def create_user():
    if g.user['role'] != 'admin':
        return jsonify({"message": "Only admins can create users"}), 403

    data = request.json

    existing_user = User.query.filter_by(username=data['username']).first()
    if existing_user:
        return jsonify({"error": "A user with this username already exists."}), 400

    try:
        user = User(
            username=data['username'],
            password=data['password'],
            role=data['role']
        )
    except ValueError as e:
        return jsonify({"error": "Invalid data", "message": str(e)}), 400

    db.session.add(user)
    db.session.commit()
    return jsonify(user.to_dict()), 201

@routes.route('/users', methods=['GET'])
@requires_auth
def get_users():
    if g.user['role'] != 'admin':
        return jsonify({"message": "Only admins can view users"}), 403

    users = User.query.all()

    if not users:
        return jsonify({"error": "No users found"}), 404

    response = [user.to_dict() for user in users]

    return jsonify(response), 200

@routes.route('/auth/login', methods=['POST'])
def login():
    data = request.json
    user = User.query.filter_by(username=data['username']).first()
    if user is None or not user.check_password(data['password']):
        return jsonify({"message": "Invalid credentials"}), 401

    token = generate_jwt(user)
    return jsonify({"token": token})
