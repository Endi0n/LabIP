from models.database import User
from flask import Blueprint, request, jsonify
from flask_login import login_user, logout_user, login_required
from app import db
import bcrypt

auth = Blueprint(__name__, __name__, url_prefix='/auth')


@auth.route('/signup', methods=['POST'])
def signup():
    name = request.form.get('name')
    email = request.form.get('email')
    password = request.form.get('password')

    if len(password) < 7:
        return jsonify({'error': 'Password must be at least 7 characters long.'}), 400

    user = User.query.filter_by(email=email).first()

    if user:
        return jsonify({'error': 'There is already an account registered with this email.'}), 409

    salt = bcrypt.gensalt()
    hash = bcrypt.hashpw(password.encode(), salt).decode()

    user = User(email, hash, name)
    db.session.add(user)
    db.session.commit()

    login_user(user)

    return jsonify({'message': 'Registration succeeded.'}), 201


@auth.route('/login', methods=['POST'])
def login():
    email = request.form.get('email')
    password = request.form.get('password')

    user = User.query.filter_by(email=email).first()
    if not user:
        return jsonify({'error': 'Wrong email.'}), 401

    if not bcrypt.checkpw(password.encode(), user.password.encode()):
        return jsonify({'error': 'Wrong password.'}), 401

    login_user(user)

    return jsonify({'message': 'Authentication succeeded.'})


@auth.route('/logout', methods=['POST'])
@login_required
def logout():
    logout_user()
