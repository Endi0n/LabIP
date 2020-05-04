from models.database import *
from models.api import *


def stats_snapshot():
    linkedin_platform_id = Platform.query.filter_by(name='LINKEDIN').one().id
    tumblr_platform_id = Platform.query.filter_by(name='TUMBLR').one().id
    twitter_platform_id = Platform.query.filter_by(name='TWITTER').one().id

    for token in LinkedInToken.query.all():
        try:
            client = LinkedInAPI(token.token)
            followers_row = FollowersCount(token.user_id, linkedin_platform_id, client.get_profile()['followers'], True)
            db.session.add(followers_row)
        except:
            pass

    for token in TumblrToken.query.all():
        try:
            client = TumblrAPI(token.token, token.token_secret)
            followers_row = FollowersCount(token.user_id, tumblr_platform_id, client.get_profile()['followers'], True)
            db.session.add(followers_row)
        except:
            pass

    for token in TwitterToken.query.all():
        try:
            client = TwitterAPI(token.token, token.token_secret)
            followers_row = FollowersCount(token.user_id, twitter_platform_id, client.get_profile()['followers'], True)
            db.session.add(followers_row)
        except:
            pass

    db.session.commit()


stats_snapshot()
