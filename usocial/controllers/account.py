import pytz

from flask import Blueprint, flash, jsonify, redirect, render_template, request, url_for
from flask_jwt_extended import create_access_token, create_refresh_token, current_user, get_jwt_identity, set_access_cookies, set_refresh_cookies, unset_jwt_cookies, verify_jwt_in_request
from flask_jwt_extended.exceptions import NoAuthorizationError
from sqlalchemy.exc import IntegrityError

from usocial import forms, models as m
from usocial.main import app, db, jwt_required

import config

account_blueprint = Blueprint('account', __name__)

@account_blueprint.route('/', methods=['GET'])
def index():
    try:
        verify_jwt_in_request()
    except NoAuthorizationError:
        default_user = m.User.query.filter_by(id=config.DEFAULT_USER_ID).first()
        if default_user and not default_user.password:
            response = redirect(url_for('feed.items'))
            set_access_cookies(response, create_access_token(identity=default_user.username))
            set_refresh_cookies(response, create_refresh_token(identity=default_user.username))
            return response
        else:
            return redirect(url_for('account.login'))
    return redirect(url_for('feed.items'))

@account_blueprint.route('/account/register', methods=['GET', 'POST'])
def register():
    if current_user:
        return redirect(url_for('feed.items'))

    if request.method == 'GET':
        return render_template('register.html', form=forms.RegisterForm())

    error = None
    username = request.form['username']
    if not username:
        error = "Username is required"
    elif m.User.query.filter_by(username=username).first():
        error = "Username is already in use"
    if error is None:
        try:
            db.session.add(m.User(username))
            db.session.commit()
        except Exception as e:
            app.log_exception(e)
            error = "Failed to create user"

    if error is None:
        return redirect(url_for('account.login'))
    else:
        flash(error)
        return redirect(url_for('account.register'))

@account_blueprint.route('/account/login', methods=['GET', 'POST'])
def login():
    if current_user:
        return redirect(url_for('feed.items'))

    if request.method == 'GET':
        return render_template('login.html', user=None, form=forms.LoginForm())

    username = request.form['username']
    password = request.form['password']
    user = m.User.query.filter_by(username=username).first()
    login_success = False
    if not user:
        app.logger.info("User not found: %s", username)
    else:
        if not user.password:
            app.logger.info("Login success no auth: %s", username)
            login_success = True
        if user.verify_password(password):
            app.logger.info("Login success password: %s", username)
            login_success = True

    if login_success:
        response = redirect(url_for('feed.items'))
        set_access_cookies(response, create_access_token(identity=user.username))
        set_refresh_cookies(response, create_refresh_token(identity=user.username))
        return response
    else:
        flash("Incorrect username or password.")
        return redirect(url_for('account.login'))

@account_blueprint.route('/account/me', methods=['GET'])
@jwt_required
def me():
    q = db.session.query(m.UserItem).filter_by(user_id=current_user.id)
    sum_q = q.statement.with_only_columns([
        db.func.coalesce(db.func.sum(m.UserItem.stream_value_played), 0),
        db.func.coalesce(db.func.sum(m.UserItem.stream_value_paid), 0)])
    played_value, paid_value = q.session.execute(sum_q).one()

    return render_template('me.html', user=current_user, played_value=played_value, paid_value=paid_value)

@account_blueprint.route('/account/password', methods=['GET', 'POST'])
@jwt_required
def password():
    if request.method == 'GET':
        return render_template('password.html', user=current_user,
            form=forms.NewPasswordForm(),
            jwt_csrf_token=request.cookies.get('csrf_access_token'))
    else:
        if request.form['new_password'] != request.form['repeat_new_password']:
            flash("Passwords don't match")
            return redirect(url_for('account.password'))
        current_user.set_password(request.form['new_password'])
        flash("Your password was changed")
        db.session.add(current_user)
        db.session.commit()
        return redirect(url_for('account.me'))

@account_blueprint.route('/account/logout', methods=['GET'])
def logout():
    response = redirect(url_for('feed.items'))
    unset_jwt_cookies(response)
    return response

@account_blueprint.route('/account/volume', methods=['POST'])
@jwt_required
def update_volume():
    current_user.audio_volume = float(request.form['value'])
    db.session.add(current_user)
    db.session.commit()
    return jsonify(ok=True)

@account_blueprint.route('/account/timezone', methods=['POST'])
@jwt_required
def update_timezone():
    try:
        current_user.timezone = pytz.timezone(request.form['value']).zone
    except pytz.exceptions.UnknownTimeZoneError:
        return "Invalid timezone.", 400
    db.session.add(current_user)
    db.session.commit()
    return jsonify(ok=True)
