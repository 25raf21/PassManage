from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from crypto_utils import generate_salt
    
db = SQLAlchemy()

class User(UserMixin, db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    crypto_salt = db.Column(db.LargeBinary, nullable=False, default=generate_salt)
    
    vault_items = db.relationship('VaultItem', backref='owner', lazy=True, cascade="all, delete-orphan")

class VaultItem(db.Model):
    __tablename__ = 'vault_items'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    service_name = db.Column(db.String(150), nullable=False)
    username_email = db.Column(db.String(150), nullable=False)
    encrypted_password = db.Column(db.Text, nullable=False) 