from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_jwt_extended import JWTManager
from flask_cors import CORS
from config import Config

db = SQLAlchemy()
jwt = JWTManager()

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    db.init_app(app)
    jwt.init_app(app)
    CORS(app)

    with app.app_context():
        import models
        db.create_all()
        seed_stages()

    import auth
    app.register_blueprint(auth.auth_bp, url_prefix='/api/auth')

    import routes
    app.register_blueprint(routes.api_bp, url_prefix='/api')

    return app


def seed_stages():
    from models import Stage
    if Stage.query.first() is None:
        stages = [
            'Raw Material', 'Shearing', 'Notching', 'Bending',
            'Angle Bending', '90° Pull Correction', 'Corner Welding',
            'Grinding', 'Angle Cutting', 'Angle Welding',
            'Diagonal Checking', 'Aluminium Profile Cutting',
            'Frame Making', 'Hole Marking', 'Rivet Nut Process',
            'Final Inspection'
        ]
        for i, name in enumerate(stages, 1):
            db.session.add(Stage(name=name, sequence_number=i))
        db.session.commit()
        print("✅ 16 stages seeded!")