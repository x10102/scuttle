from flask import Blueprint, render_template, request, redirect, url_for, flash, session, current_app as c
from forms import LoginForm, PasswordChangeForm
from flask_login import login_user, login_required, logout_user
from passwords import pw_hash
from logging import info, warning

# TODO: Move templates
UserAuth = Blueprint('UserAuth', __name__)

@UserAuth.route('/login', methods=["GET", "POST"])
def login():
    dbs = c.config['database']

    if request.method == "GET":
        return render_template('auth/login.j2', form=LoginForm())

    form = LoginForm()
    if not form.validate_on_submit():
        for e in form.errors.values():
            flash(e[0], category="error")
        return redirect(url_for('UserAuth.login'))

    uid = dbs.verify_login(form.username.data, form.password.data)
    if not uid:
        warning(f'Failed login attempt as "{form.username.data}" from {request.remote_addr}')
        flash('Nesprávné uživatelské jméno nebo heslo')
        return redirect(url_for('UserAuth.login'))
    u = dbs.get_user(uid)
    if u.temp_pw:
        session['PRE_LOGIN_UID'] = uid
        return redirect(url_for('UserAuth.pw_change'))
    info(f'User {u.nickname} (ID: {u.uid}) successfully logged in from {request.remote_addr}')
    login_user(dbs.get_user(uid))
    return redirect(url_for('index'))


@UserAuth.route('/user/logout')
@login_required
def logout():
    logout_user()
    flash('Uživatel odhlášen')
    return redirect(url_for('index'))

@UserAuth.route('/user/pw_change', methods=["GET", "POST"])
def pw_change():
    dbs = c.config['database']

    if 'PRE_LOGIN_UID' not in session:
        return redirect(url_for('index'))

    if request.method == "GET":
        return render_template('auth/pw_change.j2', form=PasswordChangeForm())
    
    form = PasswordChangeForm()

    if not form.validate_on_submit():
        for e in form.errors.values():
            flash(e[0], category="error")
        return redirect(url_for('UserAuth.pw_change'))

    dbs.update_password(session['PRE_LOGIN_UID'], pw_hash(form.pw.data))
    user = dbs.get_user(session['PRE_LOGIN_UID'])
    login_user(user)
    del session['PRE_LOGIN_UID']
    info(f"Permanent password created for {user.nickname} (ID: {user.uid})")
    return redirect(url_for('index'))

@UserAuth.route('/user/new/pw')
def temp_pw():
    dbs = c.config['database']

    if 'tpw' not in session:
        return redirect(url_for('UserAuth.login'))
    u = dbs.get_user(session['tmp_uid'])
    tpw = session['tpw']
    del session['tpw']
    del session['tmp_uid']
    return render_template('auth/temp_pw.j2', user=u, tpw=tpw)
