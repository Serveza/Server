from flask.ext.login import LoginManager
from .db import User

login_manager = LoginManager()

@login_manager.user_loader
def user_loader(user_id):
    return User.query.get(int(user_id))

@login_manager.request_loader
def user_request_loader(request):
    import base64

    # Try with URL args
    api_token = request.args.get('api_token')
    if not api_token:
        header = request.headers.get('Authorization')
        if header:
            encoded_api_token = header[len('Basic '):]
            try:
                api_token = base64.b64decode(api_token)
            except TypeError:
                pass

    user = None
    if api_token:
        user = User.query.filter(User.api_token == api_token).first()

    return user
