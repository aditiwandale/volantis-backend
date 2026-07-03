from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity, get_jwt
from models import Product, Stage, ProcessRecord, QualityCheck, Machine, User
from app import db
from datetime import datetime
from functools import wraps

api_bp = Blueprint('api', __name__)


def role_required(role):
    def decorator(fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            from flask_jwt_extended import verify_jwt_in_request
            verify_jwt_in_request()
            claims = get_jwt()
            if claims['role'] != role:
                return jsonify(msg='Access denied'), 403
            return fn(*args, **kwargs)
        return wrapper
    return decorator


# ==================== PRODUCTS ====================

@api_bp.route('/products', methods=['POST'])
@jwt_required()
def create_product():
    data = request.get_json()
    product = Product(
        product_id=data['product_id'],
        batch_number=data.get('batch_number', ''),
        size=data.get('size', ''),
        material_type=data.get('material_type', ''),
        status='pending',
        current_stage='Raw Material'
    )
    db.session.add(product)
    db.session.commit()
    return jsonify({'msg': 'Product created', 'id': product.id}), 201


@api_bp.route('/products', methods=['GET'])
@jwt_required()
def get_products():
    products = Product.query.order_by(Product.created_at.desc()).all()
    return jsonify([{
        'id': p.id,
        'product_id': p.product_id,
        'batch_number': p.batch_number,
        'size': p.size,
        'material_type': p.material_type,
        'status': p.status,
        'current_stage': p.current_stage,
        'created_at': str(p.created_at)
    } for p in products])


@api_bp.route('/products/<int:id>', methods=['GET'])
@jwt_required()
def get_product(id):
    p = Product.query.get_or_404(id)
    records = ProcessRecord.query.filter_by(product_id=id).order_by(ProcessRecord.created_at).all()
    checks = QualityCheck.query.filter_by(product_id=id).all()
    return jsonify({
        'id': p.id,
        'product_id': p.product_id,
        'batch_number': p.batch_number,
        'size': p.size,
        'material_type': p.material_type,
        'status': p.status,
        'current_stage': p.current_stage,
        'process_records': [{
            'stage': r.stage.name,
            'worker': r.worker.full_name,
            'status': r.status,
            'end_time': str(r.end_time),
            'remarks': r.remarks
        } for r in records],
        'quality_checks': [{
            'result': c.result,
            'inspector': c.inspector.full_name,
            'checked_at': str(c.checked_at),
            'remarks': c.remarks
        } for c in checks]
    })


# ==================== STAGES ====================

@api_bp.route('/stages', methods=['GET'])
@jwt_required()
def get_stages():
    stages = Stage.query.order_by(Stage.sequence_number).all()
    return jsonify([{
        'id': s.id,
        'name': s.name,
        'sequence': s.sequence_number
    } for s in stages])


# ==================== PROCESS RECORDS ====================

@api_bp.route('/process-records', methods=['POST'])
@jwt_required()
def create_process_record():
    data = request.get_json()
    current_user_id = int(get_jwt_identity())

    record = ProcessRecord(
        product_id=data['product_id'],
        stage_id=data['stage_id'],
        worker_id=current_user_id,
        status='completed',
        end_time=datetime.utcnow(),
        remarks=data.get('remarks', '')
    )
    db.session.add(record)

    # Update product's current stage
    product = Product.query.get(data['product_id'])
    stage = Stage.query.get(data['stage_id'])
    product.current_stage = stage.name
    product.status = 'in_progress'

    # If it's the last stage, mark as completed
    last_stage = Stage.query.order_by(Stage.sequence_number.desc()).first()
    if stage.id == last_stage.id:
        product.status = 'completed'

    db.session.commit()
    return jsonify({'msg': 'Stage marked complete', 'record_id': record.id}), 201


@api_bp.route('/process-records', methods=['GET'])
@jwt_required()
def get_process_records():
    product_id = request.args.get('product_id')
    query = ProcessRecord.query
    if product_id:
        query = query.filter_by(product_id=int(product_id))
    records = query.order_by(ProcessRecord.created_at.desc()).all()
    return jsonify([{
        'id': r.id,
        'product_id': r.product_id,
        'stage': r.stage.name,
        'worker': r.worker.full_name,
        'status': r.status,
        'end_time': str(r.end_time),
        'remarks': r.remarks
    } for r in records])


# ==================== QUALITY CHECKS ====================

@api_bp.route('/quality-checks', methods=['POST'])
@jwt_required()
def create_quality_check():
    data = request.get_json()
    current_user_id = int(get_jwt_identity())

    check = QualityCheck(
        product_id=data['product_id'],
        stage_id=data['stage_id'],
        inspector_id=current_user_id,
        diagonal_accuracy=data.get('diagonal_accuracy'),
        angle_90_ok=data.get('angle_90_ok'),
        weld_quality=data.get('weld_quality', ''),
        grinding_finish=data.get('grinding_finish', ''),
        profile_fitting=data.get('profile_fitting', ''),
        result=data['result'],
        remarks=data.get('remarks', ''),
        checked_at=datetime.utcnow()
    )
    db.session.add(check)

    product = Product.query.get(data['product_id'])
    if data['result'] == 'reject':
        product.status = 'rejected'
    elif data['result'] == 'rework':
        product.status = 'rework'

    db.session.commit()
    return jsonify({'msg': 'QC recorded', 'id': check.id}), 201


# ==================== DASHBOARD ====================

@api_bp.route('/dashboard', methods=['GET'])
@jwt_required()
def dashboard():
    total = Product.query.count()
    pending = Product.query.filter_by(status='pending').count()
    in_progress = Product.query.filter_by(status='in_progress').count()
    completed = Product.query.filter_by(status='completed').count()
    rejected = Product.query.filter_by(status='rejected').count()
    rework = Product.query.filter_by(status='rework').count()

    passed_qc = QualityCheck.query.filter_by(result='pass').count()
    failed_qc = QualityCheck.query.filter_by(result='reject').count()

    recent = Product.query.order_by(Product.created_at.desc()).limit(5).all()

    return jsonify({
        'total_products': total,
        'pending': pending,
        'in_progress': in_progress,
        'completed': completed,
        'rejected': rejected,
        'rework': rework,
        'passed_qc': passed_qc,
        'failed_qc': failed_qc,
        'recent_products': [{
            'product_id': p.product_id,
            'status': p.status,
            'current_stage': p.current_stage
        } for p in recent]
    })


# ==================== SEARCH ====================

@api_bp.route('/search', methods=['GET'])
@jwt_required()
def search():
    q = request.args.get('q', '')
    products = Product.query.filter(
        db.or_(
            Product.product_id.like(f'%{q}%'),
            Product.batch_number.like(f'%{q}%')
        )
    ).all()
    return jsonify([{
        'id': p.id,
        'product_id': p.product_id,
        'batch_number': p.batch_number,
        'status': p.status,
        'current_stage': p.current_stage
    } for p in products])


# ==================== REPORTS ====================

@api_bp.route('/report/daily', methods=['GET'])
@jwt_required()
def daily_report():
    today = datetime.utcnow().date()
    products_today = Product.query.filter(
        db.func.date(Product.created_at) == today
    ).count()
    records_today = ProcessRecord.query.filter(
        db.func.date(ProcessRecord.end_time) == today
    ).count()
    qc_today = QualityCheck.query.filter(
        db.func.date(QualityCheck.checked_at) == today
    ).all()

    return jsonify({
        'date': str(today),
        'products_created': products_today,
        'stages_completed': records_today,
        'qc_performed': len(qc_today),
        'qc_passed': sum(1 for q in qc_today if q.result == 'pass'),
        'qc_failed': sum(1 for q in qc_today if q.result == 'reject'),
        'qc_rework': sum(1 for q in qc_today if q.result == 'rework')
    })


@api_bp.route('/report/worker', methods=['GET'])
@jwt_required()
def worker_report():
    workers = User.query.filter_by(role='worker').all()
    result = []
    for w in workers:
        count = ProcessRecord.query.filter_by(worker_id=w.id).count()
        result.append({
            'name': w.full_name,
            'username': w.username,
            'tasks_completed': count
        })
    return jsonify(result)