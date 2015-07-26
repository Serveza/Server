from flask import abort, request
from flask_restful import reqparse
from functools import wraps
from werkzeug.local import LocalProxy
from .db import User


def get_user():
    import base64

    # Try with URL args
    parser = reqparse.RequestParser()
    parser.add_argument('api_token', type=str)
    args = parser.parse_args(request)

    api_token = args.api_token
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


def is_logged():
    return get_user() is not None

current_user = LocalProxy(get_user)


def login_required(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        if not is_logged():
            abort(403)

        return f(*args, **kwargs)
    return wrapper

api_token_param = {
    'name': 'api_token',
    'description': 'API token',
    'required': True,
    'dataType': 'string',
}
