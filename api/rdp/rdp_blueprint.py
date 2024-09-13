import io
import os
import time
import json
import base64
import threading
from hashlib import sha512

from functools import wraps
from typing import Optional

from flask import Blueprint, current_app, render_template, request, send_from_directory, jsonify
from werkzeug.utils import secure_filename
from PIL import ImageDraw
import pyautogui

from api.app.routes import socketio
import api.rdp.ScreenCastThread as Sct


config = {
    'admin_login': 'admin',
    'admin_pass': '7fd43140c30a71ef23031db36b85433b1db9469262dbe52342575bc0a7bd51b01b129e67583a7509307c395f69e177c7ce7'
                  '57f1d766e1d2a31e6a52badfdecf7',

    'spectators': {
        'user1': 'f0bff4032ac51813b3bc55539e9347ff7ca5b6c580549963c1d694b8317e26b9b4974a50bd7440fd5c8b69e2a974c5fb209c'
                 'df95bfe6d8f55b4805d976745e4d',
        'user2': 'f0bff4032ac51813b3bc55539e9347ff7ca5b6c580549963c1d694b8317e26b9b4974a50bd7440fd5c8b69e2a974c5fb209c'
                 'df95bfe6d8f55b4805d976745e4d'
    },

    'spectators_allowed': False,
    'spectators_allowed_without_password': True,
    'forbidden_ips': ["127.0.0.1"],

    'allow_unsafe_werkzeug': True,

    'logged_users': {},
    'last_shot': time.time(),

    'rdp_thread': Optional[Sct.ScreenCastThread],
}


pg = {'methods': ['POST', 'GET']}
rdp_bp = Blueprint('rdp', __file__, template_folder='api/rdp/templates')

"""
        NO CACHE AND NO SESSION FOR SAFETY PURPOSES. EVERY SERVER RESTART (LOGOUT) DELETES SESSION INFORMATION
"""


def hashed_password(text):
    def hash_(t):
        result = t
        for _ in range(358):
            result = sha512(result.encode('utf-8')).hexdigest()
        return result
    return hash_(hash_(text)[:32])


def is_admin(client_ip: str) -> bool:
    for user, ip in config['logged_users'].items():
        if client_ip == ip:
            if user == config['admin_login']:
                return True
    return False


def is_spectator(client_ip: str) -> bool:
    for user, ip in config['logged_users'].items():
        if client_ip == ip:
            if user in config['spectators'].keys():
                return True
    return False


def is_logged(client_ip: str) -> bool:
    return client_ip in config['logged_users'].values()


def is_forbidden_ip(ip: str) -> bool:
    return ip in config['forbidden_ips']


def js_redirect(link: str) -> str:
    link = link if link[0] == '/' else '/' + link
    return f"<script>window.location='{link}';</script>"


@rdp_bp.route('/ip', **pg)
def get_ip_route():
    return request.remote_addr


@rdp_bp.route('/login', **pg)
def login_route():

    if request.args.get('error', False) == 'ban':
        return 'Admin disallows you to login'

    if request.method == 'GET':
        if is_admin(request.remote_addr):
            return js_redirect('/rdp/config/')
        if request.remote_addr in config['logged_users'].values():
            return js_redirect('/rdp/cast')
        if is_spectator(request.remote_addr):
            return js_redirect('/rdp/cast')
        return render_template('rdp_login.html')

    if request.method == 'POST':
        args = dict(request.form)
        print(args)

        if 'user' in args and 'pass' in args:
            if args['user'] in config['logged_users']:
                return 'This login is busy'
            if args['user'] == config['admin_login'] and args['pass'] == config['admin_pass']:
                config['logged_users'][args['user']] = request.remote_addr
                print(f'RDP ADMIN {request.remote_addr} has logged in')
                return js_redirect('/rdp/admin')

            if config['spectators_allowed']:
                for user, passwd in config['spectators'].items():
                    print('check', user, passwd, args['user'], args['pass'])
                    if args['user'] == user and passwd == args['pass']:
                        config['logged_users'][args['user']] = request.remote_addr
                        print(f'User "{user}" at ip:{request.remote_addr} has logged in')
                        return js_redirect('/rdp/cast')
            else:
                print(f'Somebody at {request.remote_addr} tried to login but failed due to spectators are disabled')
                return 'Spectators are disabled by admin'
        return render_template(
            'rdp_login.html',
            error='Pass both valid user name and password. One user cannot login twice'
        )


@rdp_bp.route('/logout', **pg)
def logout_route():
    name_to_logout = False
    for user, ip in config['logged_users'].items():
        if ip == request.remote_addr:
            name_to_logout = user
            break
    if name_to_logout:
        del config['logged_users'][name_to_logout]
        print(f'User {name_to_logout} at {request.remote_addr} logout')
    return js_redirect('/rdp/login?next=/rdp/admin')


def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if is_logged(get_ip_route()):
            return f(*args, **kwargs)
        return js_redirect('/rdp/login?next=/rdp')
    return decorated_function


def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if is_admin(get_ip_route()):
            return f(*args, **kwargs)
        return js_redirect('/rdp/login?next=/rdp/admin')
    return decorated_function


def guard(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        ip = get_ip_route()
        if ip in config['forbidden_ips']:
            return js_redirect('/rdp/login?error=ban')
        if is_admin(ip):
            return f(*args, **kwargs)
        if is_logged(ip):
            return f(*args, **kwargs)
        if config['spectators_allowed']:
            if config['spectators_allowed_without_password']:
                return f(*args, **kwargs)
        return js_redirect("/rdp/login?next=/rdp/cast")
    return decorated_function  # ()


def get_dict_by_name(name: str):
    return globals().get(name)


@rdp_bp.route('/', **pg)
@admin_required
def main_route():
    return js_redirect('/rdp/admin')


@rdp_bp.route('/casting', methods=['POST', 'GET'])
@admin_required
def is_rdp_casting():
    if isinstance(config.get('rdp_thread', None), Sct.ScreenCastThread):
        return jsonify({"status": config['rdp_thread'].is_running()})
    return jsonify({"status": False})


@rdp_bp.route('/toggle', methods=['POST'])
@admin_required
def toggle_rdp_thread():
    rdp_thread: Optional[Sct.ScreenCastThread] = config.get('rdp_thread', None)

    print('>>> toggle POST args=', request.args)
    if request.is_json:
        print('>>> toggle POST json=', request.json)
    print('rdp_thread before toggled', rdp_thread)

    if rdp_thread is None:
        print('toggle pierwszy if - tworzenie i odpalenie watku print screen')
        # Utworzenie nowego wątku i jego uruchomienie
        rdp_thread: Sct.ScreenCastThread = Sct.ScreenCastThread()
        rdp_thread.start()
        config['rdp_thread'] = rdp_thread
        return jsonify({'status': 'running'})

    if isinstance(rdp_thread, Sct.ScreenCastThread):
        print('### toggle isinstance, yes isinstance')
        if not rdp_thread.is_running():
            print('### toggle if not running -> toggle, make thread running')
            rdp_thread.start()
            return jsonify({'status': 'running'})
        else:
            print('### toggle thread is running -> toggle, make thread stop, join, ')
            rdp_thread.stop()
            rdp_thread.join()  # Zaczekaj, aż wątek się zakończy
            config['rdp_thread'] = Sct.ScreenCastThread()
    return jsonify({'status': 'stopped'})


@rdp_bp.route('/dict/<name>', methods=['GET', 'POST'])
@rdp_bp.route('/dict/', methods=['GET', 'POST'], defaults={'name': 'config'})
@admin_required
def rdp_edit_dict_route(name: str = 'config'):
    dictionary = get_dict_by_name(name)

    if not dictionary:
        return f"Słownik o nazwie '{name}' nie istnieje.", 404

    if request.method == 'POST':
        updated_dict = {}
        print(request.form)

        for key in dictionary.keys():
            updated_dict[key] = request.form.get(key)

        globals()[name] = json.loads(json.dumps(updated_dict))

    return render_template("config_edit.html", name=name, dictionary=dictionary)


@rdp_bp.route('/dict2/<name>', methods=['GET', 'POST'])
@rdp_bp.route('/dict2/', methods=['GET', 'POST'], defaults={'name': 'config'})
# @admin_required
def edit_dict2(name: str):
    dictionary = get_dict_by_name(name)

    if not dictionary:
        return f"Słownik o nazwie '{name}' nie istnieje.", 404

    if request.method == 'POST':
        new_dict = {}
        for key, value in request.json.items():
            try:
                new_dict[key] = json.loads(value)
            except json.JSONDecodeError:
                # Jeśli nie uda się przekonwertować, zachowaj jako string
                new_dict[key] = value

        globals()[name] = json.loads(json.dumps(new_dict))
        return jsonify(success=True)

    return render_template('config_edit3.html', dictionary=dictionary, name=name)


@rdp_bp.route('/config')
@admin_required
def rdp_config_route():
    x = Sct.ScreenCastThread()
    # x.start()
    config['rdp_thread'] = x

    running = x.is_running()
    if isinstance(config.get('rdp_thread', None), Sct.ScreenCastThread):
        running = config['rdp_thread'].is_running()

    return render_template(
        'rdp_config2.html',
        dictionary=get_dict_by_name('config'),
        name='config',
        running=str(running).lower(),  # Javascript needs lower
        routes=[
            (_.endpoint, _.rule)
            for _ in current_app.url_map.iter_rules() if _.endpoint.startswith(rdp_bp.name + '.')
        ]
    )


@rdp_bp.route('/logged', **pg)
@admin_required
def logged_route():
    return str(config['logged_users'])


@rdp_bp.route('/logout_all')
@admin_required
def logout_all_route():
    config['logged_users'] = {}
    return js_redirect('/login?next=/cast')


@rdp_bp.route('/cast')
@guard
def cast():
    return render_template('rdp_cast.html')


@rdp_bp.route('/admin', **pg)
@admin_required
def rdp_admin_route():
    return render_template('rdp_admin.html')


@rdp_bp.route('/download', methods=['GET'])
@login_required
def download():
    path = request.args.get('path', False)
    if path:
        sep = os.path.sep

        if os.name == 'nt':
            path = rf'{path}'.replace('/', '\\')
        else:
            path = rf'{path}'.replace('\\', '/')

        if sep in path:
            split = path.split(sep)
            dir_ = sep.join(split[:-1])
            name = split[-1]
        else:
            dir_ = os.getcwd()
            name = path
        return send_from_directory(secure_filename(dir_), name)
    return 'download error: ' + path


@rdp_bp.route('/upload', **pg)
@guard
def upload_route():
    cwd = os.getcwd()
    if request.method == 'POST':
        dir_ = request.args.get('dir', cwd)
        file = request.files['file']
        if file.filename == '':
            return '/upload error empty filename'

        if not os.path.isdir(dir_):
            return f'Incorrect directory: {dir_}'

        path = secure_filename(os.path.join(dir_, file.filename))
        file.save(path)
        return '/upload OK: ' + path
    if request.method == 'GET':
        return render_template('upload.html', dest_dir=cwd)


@socketio.on('connect', namespace='/cast')
def connect_cast():
    print('Client connected to /cast')


@socketio.on('disconnect', namespace='/cast')
def disconnect_cast():
    print('Client disconnected from /cast')


@socketio.on('connect', namespace='/rdp')
@guard
def connect_rdp():
    print('Client connected to /rdp')


@socketio.on('disconnect', namespace='/rdp')
def disconnect_rdp():
    print('Client disconnected from /rdp')


@socketio.on('mouse_event', namespace='/rdp')
@admin_required
def handle_mouse_event(data):
    x, y = data['x'], data['y']
    pyautogui.moveTo(x, y)


@socketio.on('click_event', namespace='/rdp')
@admin_required
def handle_click_event(data):
    button = data['button']
    if button == 'left':
        pyautogui.click()
    elif button == 'right':
        pyautogui.click(button='right')


@socketio.on('keyboard_event', namespace='/rdp')
@admin_required
def handle_keyboard_event(data):
    key = data['key']
    pyautogui.press(key)
