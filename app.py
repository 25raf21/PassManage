import secrets
import string
from flask import Flask, render_template, redirect, url_for, flash, request, session
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from flask_wtf.csrf import CSRFProtect
from werkzeug.security import generate_password_hash, check_password_hash


from models import db, User, VaultItem
from crypto_utils import derive_key, encrypt_password, decrypt_password

app = Flask(__name__)


app.config['SECRET_KEY'] = secrets.token_hex(32)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///vault.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False


csrf = CSRFProtect(app)
db.init_app(app)


login_manager = LoginManager()
login_manager.login_view = 'login'
login_manager.init_app(app)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

def generate_secure_password(length=16):
    """Core Feature: Password Generation Functionality.
    Generates a cryptographically sound random string of characters.
    """
    alphabet = string.ascii_letters + string.digits + "!@#$%^&*()"
    return ''.join(secrets.choice(alphabet) for _ in range(length))



@app.route('/')
def index():
    return redirect(url_for('login'))


@app.route('/register', methods=['GET', 'POST'])
def register():
    """Core Feature: User registration system with password hashing and salting."""
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password')
        
        if not username or not password:
            flash('All configuration entry inputs are required.', 'danger')
            return redirect(url_for('register'))

        if User.query.filter_by(username=username).first():
            flash('This master username has already been registered.', 'danger')
            return redirect(url_for('register'))
            
        hashed_pw = generate_password_hash(password, method='scrypt')
        new_user = User(username=username, password_hash=hashed_pw)
        
        db.session.add(new_user)
        db.session.commit()
        
        flash('Registration complete! Please enter credentials to unlock vault.', 'success')
        return redirect(url_for('login'))
        
    return render_template('register.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password')
        
        user = User.query.filter_by(username=username).first()
        
        if user and check_password_hash(user.password_hash, password):
            login_user(user)
            
            derived_key = derive_key(password, user.crypto_salt)
            session['dk'] = derived_key.decode('utf-8')
            
            return redirect(url_for('dashboard'))
        
        flash('Invalid master verification credentials.', 'danger')
    return render_template('login.html')


@app.route('/dashboard', methods=['GET', 'POST'])
@login_required
def dashboard():
    """Core Feature: Password storage, retrieval, and management panel."""
    if 'dk' not in session:
        logout_user()
        return redirect(url_for('login'))
        
    user_key = session['dk'].encode('utf-8')
    
    if request.method == 'POST':
        action = request.form.get('action')
        
        if action == 'add':
            service = request.form.get('service', '').strip()
            username = request.form.get('username', '').strip()
            plain_pass = request.form.get('password')
            
            if service and username and plain_pass:
                enc_pass = encrypt_password(plain_pass, user_key)
                new_item = VaultItem(
                    user_id=current_user.id,
                    service_name=service,
                    username_email=username,
                    encrypted_password=enc_pass
                )
                db.session.add(new_item)
                db.session.commit()
                flash('Data node successfully encrypted and saved to database.', 'success')
            
        elif action == 'delete':
            item_id = request.form.get('item_id')
            item = VaultItem.query.filter_by(id=item_id, user_id=current_user.id).first()
            if item:
                db.session.delete(item)
                db.session.commit()
                flash('Credential node purged from record ledger.', 'info')

    raw_items = VaultItem.query.filter_by(user_id=current_user.id).all()
    decrypted_vault = []
    
    for item in raw_items:
        try:
            decrypted_password = decrypt_password(item.encrypted_password, user_key)
        except Exception:
            decrypted_password = "[Decryption Context Breach - Session Closed]"
            
        decrypted_vault.append({
            'id': item.id,
            'service_name': item.service_name,
            'username_email': item.username_email,
            'password': decrypted_password
        })
        
    generated_suggestion = generate_secure_password()
    return render_template('dashboard.html', vault=decrypted_vault, suggested_password=generated_suggestion)


@app.route('/logout')
@login_required
def logout():
    """Destroys authentication contexts and wipes memory decryption tracking elements."""
    session.clear()
    logout_user()
    return redirect(url_for('login'))


if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=False, port=5000)