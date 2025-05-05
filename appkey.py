import os

from flask import abort, request, redirect, url_for
from functools import wraps

AUTH_DISABLED = os.getenv("AUTH_DISABLED")

# print(hashlib.sha256(bytes(pwd, 'utf-8')).hexdigest()[:5])
auth_key_dict = {
    "9900f": ['all'], # marc1234
    "78fe0": ['all'], # markmedc
    "bb42e": ['all'], # Markmedc
    "1b071": ['all'], # marcmedc
    "87070": ['all'], # Marcmedc
    "67140": ['all'], # Carkmedc
    "1f881": ['all'], # carkmedc
    "7a8c3": ['all'], # carksutter
    "b62ee": ['all'], # jonas password
    "0da6e": ['all'], # padel
    "8b38d": ['all'], # dnd
    "99706": ['all'], # minecraft
    "cf6dd": ['all'], # plex
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
    "padel": ['all'],
    "dnd": ['all'],
    "minecraft": ['all'],
    "plex": ['all']
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
                return redirect(url_for('login', access="denied"))
        return decorated_function

    return require_appkey
