from flask import Blueprint, request, jsonify
from flask_jwt_extended import (
    create_access_token, get_jwt_identity, jwt_required, get_jwt, verify_jwt_in_request
)
from functools import wraps
from models import User

auth_bp = Blueprint('auth', __name__)

def role_required(role):
    def decorator(fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            verify_jwt_in_request()
            claims = get_jwt()
            if claims['role'] != role:
                return jsonify(msg='Access denied: insufficient permissions'), 403
            return fn(*args, **kwargs)
        return wrapper
    return decorator

@auth_bp.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')

    user = User.query.filter_by(username=username).first()
    if not user or not user.check_password(password):
        return jsonify({'msg': 'Invalid credentials'}), 401

    additional_claims = {
        'role': user.role,
        'full_name': user.full_name
    }
    
    # FIX 1: Wrap user.id in str() so the JWT library gets a string subject
    access_token = create_access_token(
        identity=str(user.id), 
        additional_claims=additional_claims
    )
    return jsonify(
        access_token=access_token,
        role=user.role,
        full_name=user.full_name
    )

@auth_bp.route('/me', methods=['GET'])
@jwt_required()
def me():
    current_user_id = get_jwt_identity() # This will now be a string (e.g., "1")
    claims = get_jwt()
    
    # FIX 2: Convert current_user_id back to an int so SQLAlchemy can query it properly
    user = User.query.get(int(current_user_id)) 
    
    if not user:
        return jsonify({'msg': 'User not found'}), 404
    return jsonify(
        id=user.id,
        username=user.username,
        role=user.role,
        full_name=user.full_name
    )