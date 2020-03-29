from models.api import LinkedInAPI
from models.database import LinkedInToken
from flask import Blueprint, redirect, request, jsonify
from utils.auth import login_required, linkedin_required
from app import app, db
from datetime import datetime

linkedin = Blueprint(__name__, __name__, url_prefix='/linkedin')
CALLBACK_URL = app.config['BASE_DOMAIN'] + '/linkedin/auth/callback'


@linkedin.route('/auth')
@login_required
def auth(user):
    return redirect(LinkedInAPI.generate_auth_url(CALLBACK_URL))


@linkedin.route('/auth/callback')
@login_required
def auth_callback(user):
    token = LinkedInAPI.generate_auth_token(CALLBACK_URL, request.url)
    token_record = LinkedInToken(user, token['access_token'],
                                 datetime.fromtimestamp(token['expires_at']))
    db.session.add(token_record)
    db.session.commit()
    return jsonify({'message': 'Authentication succeeded.'}), 200


@linkedin.route('/profile')
@linkedin_required
def profile(linkedin_client):
    return jsonify(linkedin_client.get_profile())