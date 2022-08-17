import os

from flask import abort, request
from functools import wraps

AUTH_DISABLED = os.getenv("AUTH_DISABLED")

# print(hashlib.sha256(bytes(pwd, 'utf-8')).hexdigest()[:5])
auth_key_dict = {
    "9900f": ['all'],
    "78fe0": ['all'],
    "bb42e": ['all'],
    "1b071": ['all'],
    "87070": ['all'],
    "67140": ['all'],
    "1f881": ['all'],
    "7a8c3": ['all'],
}
auth_key_dict_old = {
    "marc1234": ['all'],
    "markmedc": ['all'],
    "Markmedc": ['all'],
    "marcmedc": ['all'],
    "Marcmedc": ['all'],
    "Carkmedc": ['all'],
    "carkmedc": ['all'],
    "carksutter": ['all'],
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
