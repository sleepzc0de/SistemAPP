from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.urls import url_parse
from app import db
from app.models.user import User
from app.models.satker import Satker

auth_bp = Blueprint('auth', __name__, url_prefix='/auth')

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))
    
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        remember = True if request.form.get('remember') else False
        
        # Validate input
        if not username or not password:
            flash('Username dan password harus diisi.', 'danger')
            return render_template('auth/login.html')
        
        # Check if user exists
        user = User.query.filter_by(username=username).first()
        
        if not user or not user.verify_password(password):
            flash('Username atau password salah.', 'danger')
            return render_template('auth/login.html')
        
        # Check if user is active
        if not user.is_active:
            flash('Akun Anda dinonaktifkan. Hubungi administrator.', 'danger')
            return render_template('auth/login.html')
        
        # Login user
        login_user(user, remember=remember)
        user.update_last_login()
        
        # Redirect to next page or dashboard
        next_page = request.args.get('next')
        if not next_page or url_parse(next_page).netloc != '':
            next_page = url_for('main.index')
        
        flash('Login berhasil!', 'success')
        return redirect(next_page)
    
    return render_template('auth/login.html')

@auth_bp.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Anda telah berhasil logout.', 'info')
    return redirect(url_for('auth.login'))

@auth_bp.route('/register', methods=['GET', 'POST'])
@login_required
def register():
    # Only admin can register new users
    if not current_user.is_admin:
        flash('Anda tidak memiliki hak akses untuk halaman ini.', 'danger')
        return redirect(url_for('main.index'))
    
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        password_confirm = request.form.get('password_confirm')
        satker_id = request.form.get('satker_id')
        is_admin = True if request.form.get('is_admin') else False
        
        # Validate input
        if not username or not email or not password or not password_confirm or not satker_id:
            flash('Semua field harus diisi.', 'danger')
            satkers = Satker.query.all()
            return render_template('auth/register.html', satkers=satkers)
        
        if password != password_confirm:
            flash('Password dan konfirmasi password tidak cocok.', 'danger')
            satkers = Satker.query.all()
            return render_template('auth/register.html', satkers=satkers)
        
        # Check if username or email already exists
        if User.query.filter_by(username=username).first():
            flash('Username sudah digunakan.', 'danger')
            satkers = Satker.query.all()
            return render_template('auth/register.html', satkers=satkers)
        
        if User.query.filter_by(email=email).first():
            flash('Email sudah digunakan.', 'danger')
            satkers = Satker.query.all()
            return render_template('auth/register.html', satkers=satkers)
        
        # Create new user
        new_user = User(
            username=username,
            email=email,
            password=password,
            satker_id=satker_id,
            is_admin=is_admin
        )
        
        db.session.add(new_user)
        db.session.commit()
        
        flash(f'User {username} berhasil didaftarkan!', 'success')
        return redirect(url_for('auth.register'))
    
    # GET request
    satkers = Satker.query.all()
    return render_template('auth/register.html', satkers=satkers)

@auth_bp.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    if request.method == 'POST':
        email = request.form.get('email')
        current_password = request.form.get('current_password')
        new_password = request.form.get('new_password')
        
        # Update email
        if email and email != current_user.email:
            # Check if email is already used
            if User.query.filter_by(email=email).first():
                flash('Email sudah digunakan.', 'danger')
                return redirect(url_for('auth.profile'))
            
            current_user.email = email
            db.session.commit()
            flash('Email berhasil diperbarui.', 'success')
        
        # Update password
        if current_password and new_password:
            if not current_user.verify_password(current_password):
                flash('Password saat ini salah.', 'danger')
                return redirect(url_for('auth.profile'))
            
            current_user.password = new_password
            db.session.commit()
            flash('Password berhasil diperbarui.', 'success')
        
        return redirect(url_for('auth.profile'))
    
    return render_template('auth/profile.html')