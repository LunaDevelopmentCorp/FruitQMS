from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, login_required, current_user
from flask_babel import gettext as _
from app import db
from app.models import User, AuditLog
from app.forms import LoginForm, RegistrationForm, ChangePasswordForm

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard.index'))

    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data.strip().lower()).first()
        if user and user.check_password(form.password.data):
            login_user(user)
            flash(_('Login successful!'), 'success')
            next_page = request.args.get('next')
            return redirect(next_page) if next_page else redirect(url_for('dashboard.index'))
        else:
            flash(_('Invalid email or password'), 'danger')
    elif request.method == 'POST':
        flash(_('Please correct the errors below.'), 'warning')

    return render_template('auth/login.html', form=form)


@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard.index'))

    form = RegistrationForm()
    if form.validate_on_submit():
        # Check if email or username already exists
        if User.query.filter_by(email=form.email.data.strip().lower()).first():
            flash(_('Email already registered.'), 'danger')
            return render_template('auth/register.html', form=form)

        if User.query.filter_by(username=form.username.data.strip()).first():
            flash(_('Username already taken.'), 'danger')
            return render_template('auth/register.html', form=form)

        user = User(
            name=form.name.data.strip(),
            username=form.username.data.strip(),
            email=form.email.data.strip().lower(),
            role=form.role.data
        )
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()

        flash(_('Registration successful! Please log in.'), 'success')
        return redirect(url_for('auth.login'))
    elif request.method == 'POST':
        flash(_('Please correct the errors below.'), 'warning')

    return render_template('auth/register.html', form=form)


@auth_bp.route('/change-password', methods=['GET', 'POST'])
@login_required
def change_password():
    form = ChangePasswordForm()
    if form.validate_on_submit():
        if not current_user.check_password(form.current_password.data):
            flash(_('Current password is incorrect.'), 'danger')
            return render_template('auth/change_password.html', form=form)

        if form.new_password.data != form.confirm_password.data:
            flash(_('New passwords do not match.'), 'danger')
            return render_template('auth/change_password.html', form=form)

        current_user.set_password(form.new_password.data)
        db.session.commit()
        flash(_('Password changed successfully!'), 'success')
        return redirect(url_for('dashboard.index'))

    return render_template('auth/change_password.html', form=form)


@auth_bp.route('/profile')
@login_required
def profile():
    return render_template('auth/profile.html')


@auth_bp.route('/manage-users')
@login_required
def manage_users():
    if current_user.role != 'qa_manager':
        flash(_('Only QA Managers can manage users.'), 'danger')
        return redirect(url_for('dashboard.index'))

    users = User.query.all()
    return render_template('auth/manage_users.html', users=users)


@auth_bp.route('/toggle-user/<int:user_id>', methods=['POST'])
@login_required
def toggle_user(user_id):
    if current_user.role != 'qa_manager':
        flash(_('Permission denied.'), 'danger')
        return redirect(url_for('dashboard.index'))

    user = User.query.get(user_id)
    if not user or user.id == current_user.id:
        flash(_('Cannot modify this user.'), 'danger')
        return redirect(url_for('auth.manage_users'))

    user.is_active = not user.is_active
    db.session.commit()

    status = _('activated') if user.is_active else _('deactivated')
    flash(_('User "%(name)s" %(status)s.', name=user.name, status=status), 'success')
    return redirect(url_for('auth.manage_users'))


@auth_bp.route('/logout')
@login_required
def logout():
    logout_user()
    flash(_('You have been logged out.'), 'info')
    return redirect(url_for('main.index'))
