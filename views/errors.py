from flask import jsonify
import oauthlib.oauth1 as oauth1
import oauthlib.oauth2 as oauth2
import jwt.exceptions
from smtplib import SMTPException
from sqlalchemy.exc import SQLAlchemyError
from twitter.error import TwitterError
from models.api.linkedin import LinkedInError
import utils.mail
from app import app
import os


if os.getenv('REWRITE_ERROR_OUTPUT'):
    # Warning: If you set REWRITE_ERROR_OUTPUT you won't longer get Python's default tracklog for your exception

    @app.errorhandler(500)
    def internal_error_handler(e):
        app.logger.error(str(e))
        utils.mail.send_internal_error_email(f'{str(e)}\nOriginal error: {str(e.original_exception)}')
        return jsonify(error='Internal server error.'), 500


    @app.errorhandler(NotImplementedError)
    def not_implemented_error_handler(e):
        return jsonify(error='Method not implemented.'), 501


    @app.errorhandler(KeyError)
    def missing_parameter_error_handler(e):
        app.logger.error(str(e))
        return jsonify(error=e.args[0]), 400


    @app.errorhandler(oauth2.TokenExpiredError)
    def oauth2_token_expired_error_handler(e):
        return jsonify(error='OAuth2 token expired.'), 401


    @app.errorhandler(oauth1.OAuth1Error)
    @app.errorhandler(oauth2.OAuth2Error)
    def oauth_error_handler(e):
        app.logger.error(e.description)
        utils.mail.send_internal_error_email(e.description)
        return jsonify(error=e.description), 503


    @app.errorhandler(jwt.exceptions.InvalidTokenError)
    def invalid_jwt_token_error_handler(e):
        return jsonify(error='Invalid token.'), 400


    @app.errorhandler(SMTPException)
    def smtp_error_handler(e):
        app.logger.error(e.message)
        return jsonify(error='Internal server error.'), 500


    @app.errorhandler(SQLAlchemyError)
    def sqlalchemy_error_handler(e):
        app.logger.error(e.message)
        utils.mail.send_internal_error_email(e.message)
        return jsonify(error='Internal server error.'), 500

    @app.errorhandler(TwitterError)
    def twitter_error(e):
        return jsonify(e.message), 500

    @app.errorhandler(TwitterError)
    def twitter_error(e):
        return jsonify(error=e.message), 500
