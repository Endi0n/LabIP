from requests_oauthlib import OAuth2Session
from models.database import AppKey
import urllib
import json


class LinkedInAPI:
    APP_KEY = AppKey.query.filter_by(platform='LINKEDIN').one()
    CLIENT_KEY = APP_KEY.client_key
    CLIENT_SECRET = APP_KEY.client_secret

    application_token = None

    @staticmethod
    def generate_auth_url(callback_url):
        # Step 1
        authorization_base_url = 'https://www.linkedin.com/oauth/v2/authorization'
        linkedin = OAuth2Session(LinkedInAPI.CLIENT_KEY, redirect_uri=callback_url,
                                 scope=['r_liteprofile', 'r_organization_social', 'w_organization_social', 'rw_organization_admin'])

        authorization_url, state = linkedin.authorization_url(authorization_base_url)
        return authorization_url

    @staticmethod
    def generate_auth_token(callback_url, url):
        # Step 2
        linkedin = OAuth2Session(LinkedInAPI.CLIENT_KEY, redirect_uri=callback_url)
        return linkedin.fetch_token('https://www.linkedin.com/oauth/v2/accessToken',
                                    client_secret=LinkedInAPI.CLIENT_SECRET,
                                    include_client_id=True,
                                    authorization_response=url)

    def __init__(self, token):
        self.__linkedin = OAuth2Session(LinkedInAPI.CLIENT_KEY, token={'access_token': token})

    def get_profile(self):
        return json.loads(self.__linkedin.get(
            'https://api.linkedin.com/v2/me?projection=(id,firstName,lastName,profilePicture('
            'displayImage~digitalmediaAsset:playableStreams),headline)'
        ).content.decode())

    def get_followers(self):
        organization_urn = self.get_companies()['elements'][0]['organizationalTarget']
        return json.loads(
            self.__linkedin.get(
                f'https://api.linkedin.com/v2/networkSizes/{organization_urn}?edgeType=CompanyFollowedByMember'
            ).content.decode())

    def get_companies(self):
        return json.loads(
            self.__linkedin.get(
                'https://api.linkedin.com/v2/organizationalEntityAcls?q=roleAssignee&role=ADMINISTRATOR'
            ).content.decode())

    def get_self_posts(self, start, count):
        # TODO:
        return json.loads(self.__linkedin.get(
            f'https://api.linkedin.com/v2/shares?q=owners&owners={self.get_organization_urn()}&sharesPerOwner=1000'
            f'&start={start}&count={count}'
        ).content.decode())

    def get_self_posts2(self):
        self.__linkedin.headers.update({'X-Restli-Protocol-Version': '2.0.0'})

        organization_urn = self.get_companies()['elements'][0]['organizationalTarget']
        return json.loads(self.__linkedin.get(
            f'https://api.linkedin.com/v2/ugcPosts?q=authors&authors=List({urllib.parse.quote(organization_urn)})'
        ).content.decode())

    def get_post(self, post_id):
        return json.loads(self.__linkedin.get('https://api.linkedin.com/v2/shares/' + post_id).content.decode())

    def get_organization_urn(self):
        return self.get_companies()['elements'][0]['organizationalTarget']

    def upload_file(self, file):
        #Step 1
        data = json.loads(self.__linkedin.post(
            f'https://api.linkedin.com/v2/assets?action=registerUpload',
            json={
                "registerUploadRequest": {
                    "owner": self.get_organization_urn(),
                    "recipes": [
                        "urn:li:digitalmediaRecipe:feedshare-image"
                    ],
                    "serviceRelationships": [
                        {
                            "identifier": "urn:li:userGeneratedContent",
                            "relationshipType": "OWNER"
                        }
                    ],
                    "supportedUploadMechanism": [
                        "SYNCHRONOUS_UPLOAD"
                    ]
                }
            }
        ).content.decode())

        urn = data['value']['asset']
        upload_url = data['value']['uploadMechanism']['com.linkedin.digitalmedia.uploading.MediaUploadHttpRequest']['uploadUrl']

        #Step 2
        data = json.loads(self.__linkedin.put(upload_url, files=file).content.decode())
        return urn


    def post(self, post_draft):
        files = [self.upload_file(file) for file in post_draft.files]

        data = json.loads(self.__linkedin.post(
            f'https://api.linkedin.com/v2/shares',
            json={
                "distribution": {
                    "linkedInDistributionTarget": {}
                },
                "owner": self.get_organization_urn(),
                "text": {
                    "text": post_draft.text
                },
                "content": {
                    "contentEntities": [{"entity": file} for file in files],
                    "title": "Test Share with Content title",
                    "landingPageUrl": "https://www.linkedin.com/",
                    "shareMediaCategory": "IMAGE"
                }
            }
        ).content.decode())
        pass


if __name__ == '__main__':
    import os

    callback_url = os.getenv('BASE_DOMAIN')
    print(LinkedInAPI.generate_auth_url(callback_url))
    code = input('Paste the code: ')
    state = input('Paste the state: ')
    authorization_response = f'{callback_url}?code={code}&state={state}'
    token = LinkedInAPI.generate_auth_token(callback_url, authorization_response)
    print(token)
    obj = LinkedInAPI(token['access_token'])
    print(obj.get_profile())
