from itsdangerous import TimedJSONWebSignatureSerializer, BadData
from django.conf import settings

locker = TimedJSONWebSignatureSerializer(
    secret_key='settings.SECRET_KEY',
    expires_in=3600
)


def generate_access_token(openid):
    result = locker.dumps({'openid': openid})
    return result.decode()


def check_access_token(access_token):
    try:
        result = locker.loads(access_token)
    except BadData as e:
        print(e)
    else:
        return result.get('openid')


