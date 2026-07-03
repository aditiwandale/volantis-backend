from app import db
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime

class User(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(20), nullable=False)
    full_name = db.Column(db.String(100))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)


class Product(db.Model):
    __tablename__ = 'products'
    id = db.Column(db.Integer, primary_key=True)
    product_id = db.Column(db.String(50), unique=True, nullable=False)
    batch_number = db.Column(db.String(50))
    size = db.Column(db.String(20))
    material_type = db.Column(db.String(50))
    status = db.Column(db.String(20), default='pending')
    current_stage = db.Column(db.String(50), default='Raw Material')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class Stage(db.Model):
    __tablename__ = 'stages'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True, nullable=False)
    sequence_number = db.Column(db.Integer, nullable=False)


class ProcessRecord(db.Model):
    __tablename__ = 'process_records'
    id = db.Column(db.Integer, primary_key=True)
    product_id = db.Column(db.Integer, db.ForeignKey('products.id'), nullable=False)
    stage_id = db.Column(db.Integer, db.ForeignKey('stages.id'), nullable=False)
    worker_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    status = db.Column(db.String(20), default='completed')
    start_time = db.Column(db.DateTime)
    end_time = db.Column(db.DateTime, default=datetime.utcnow)
    remarks = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    product = db.relationship('Product', backref='process_records')
    stage = db.relationship('Stage', backref='process_records')
    worker = db.relationship('User', backref='process_records')


class QualityCheck(db.Model):
    __tablename__ = 'quality_checks'
    id = db.Column(db.Integer, primary_key=True)
    product_id = db.Column(db.Integer, db.ForeignKey('products.id'), nullable=False)
    stage_id = db.Column(db.Integer, db.ForeignKey('stages.id'), nullable=False)
    inspector_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    diagonal_accuracy = db.Column(db.Float)
    angle_90_ok = db.Column(db.Boolean)
    weld_quality = db.Column(db.String(20))
    grinding_finish = db.Column(db.String(20))
    profile_fitting = db.Column(db.String(20))
    result = db.Column(db.String(10), nullable=False)
    remarks = db.Column(db.Text)
    checked_at = db.Column(db.DateTime, default=datetime.utcnow)

    product = db.relationship('Product', backref='quality_checks')
    stage = db.relationship('Stage', backref='quality_checks')
    inspector = db.relationship('User', backref='quality_checks')


class Machine(db.Model):
    __tablename__ = 'machines'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50))
    type = db.Column(db.String(50))
    status = db.Column(db.String(20), default='operational')