from models import TumblrAPI, TumblrToken, PostView, Profile
from flask import Blueprint, redirect, request, jsonify, session
from utils.auth import verified_user_required, tumblr_required
from app import app, db
import os
import uuid

tumblr = Blueprint(__name__, __name__, url_prefix='/tumblr')
CALLBACK_URL = app.config['BASE_DOMAIN'] + '/tumblr/auth/callback'


@tumblr.route('/auth')
@verified_user_required
def auth(user):
    oauth_token, oauth_token_secret = TumblrAPI.generate_auth_req_token()

    session['tumblr_req_auth_token'], session['tumblr_req_auth_token_secret'] = oauth_token, oauth_token_secret

    redirect_url = request.args.get('redirect_url', None)
    if redirect_url:
        session['redirect_url'] = redirect_url

    return redirect(TumblrAPI.generate_auth_url(oauth_token))


@tumblr.route('/auth/callback')
@verified_user_required
def auth_callback(user):
    oauth_token, oauth_token_secret = TumblrAPI.generate_auth_token(
        request.url,
        session['tumblr_req_auth_token'],
        session['tumblr_req_auth_token_secret']
    )

    session.pop('tumblr_req_auth_token')
    session.pop('tumblr_req_auth_token_secret')

    token_record = TumblrToken(user, oauth_token, oauth_token_secret)

    db.session.add(token_record)
    db.session.commit()

    if 'redirect_url' in session:
        redirect_url = session['redirect_url']
        session.pop('redirect_url')
        return redirect(redirect_url)

    return jsonify(message='Authentication succeeded.'), 200


@tumblr.route('/profile')
@tumblr_required
def profile(tumblr_client):
    return jsonify(Profile.from_tumblr(tumblr_client.info()).as_dict())


@tumblr.route('/profile/posts')
@tumblr_required
def get_all_posts(tumblr_client):
    p = tumblr_client.info()
    total_nr_of_posts = p["user"]["blogs"][0]["posts"]
    response = tumblr_client.posts(tumblr_client._get_blogname(), notes_info=True, limit=total_nr_of_posts)
    unfiltered_posts = response['posts']
    posts = []
    for post in unfiltered_posts:
        posts.append(PostView.from_tumblr(post).as_dict())

    return jsonify({'posts': posts})


@tumblr.route('/view_post/<post_id>')
@tumblr_required
def view_post(tumblr_client, post_id):
    return jsonify(PostView.from_tumblr(tumblr_client._get_post(post_id)).as_dict())


@tumblr.route('/post', methods=['POST'])
@tumblr_required
def post(tumblr_client):
    blogName = tumblr_client._get_blogname()

    type = request.form.get('type')
    text = request.form.get('text', '')

    result = ['nothing happened']

    if type == 'text':
        result = tumblr_client.create_text(blogName, body=text)
    else:
        if 'content' in request.files:
            file = request.files['content']
            temp_dir = '/tmp'
            temp_name = "{}_{}".format(str(uuid.uuid1()), file.filename)
            filepath = os.path.join(temp_dir, temp_name)
            file.save(filepath)

            if type == 'photo':
                result = tumblr_client.create_photo(blogName, data=[filepath], caption=text)
            elif type == 'video':
                result = tumblr_client.create_video(blogName, data=[filepath], caption=text)

            os.remove(filepath)
        elif 'content' in request.form:
            link = request.form.get('content')
            if type == 'photo':
                result = tumblr_client.create_photo(blogName, source=link, caption=text)
            elif type == 'video':
                result = tumblr_client.create_video(blogName, embed=link, caption=text)
    return jsonify(result)
