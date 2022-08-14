import os

from flask import abort, request
from functools import wraps

AUTH_DISABLED = os.getenv("AUTH_DISABLED")

auth_key_dict = {
    "marc1234": ['all'],
    "markmedc": ['all'],
    "Markmedc": ['all'],
    "marcmedc": ['all'],
    "Marcmedc": ['all'],
    "Carkmedc": ['all'],
    "carkmedc": ['all']
}


def require_appkey_factory(app):
    def require_appkey(view_function):
        @wraps(view_function)
        def decorated_function(*args, **kwargs):
            allowed = False
            if app.config['AUTH_DISABLED'] == "1":
                allowed = True
            elif request.args.get('key'):
                try:
                    allowed_routes = auth_key_dict[request.args.get('key')]
                except KeyError:
                    pass
                else:
                    if request.path in allowed_routes or 'all' in allowed_routes:
                        allowed = True

            if allowed:
                return view_function(*args, **kwargs)
            else:
                abort(401)
        return decorated_function

    return require_appkey
