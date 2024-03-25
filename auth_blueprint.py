import os
from functools import wraps

from flask import Blueprint, render_template, request, session, url_for, redirect
import hashlib

bp = Blueprint('auth', __file__)


users = {
    'admin': '6b8d870cd2f23a7bb6e132f47439b5a86547277a930955a8c4053ab0a8d43403693ad78cc4cc30b47b205c221693518efc5e7f80ae1abc749f878f01246bc053'
}


@bp.route('/')
def auth_index_route():
    return redirect(url_for('auth.auth_login_route'))


@bp.route('/login', methods=['GET', 'POST'])
def auth_login_route():
    if request.method == 'GET':
        csrf_token = generate_csrf_token()
        session['csrf_token'] = csrf_token
        return render_template('login.html', csrf_token=csrf_token)

    if request.method == 'POST':
        username = request.json.get('username')
        password = request.json.get('password')
        provided_csrf_token = request.json.get('csrf_token')

        print(username, password, provided_csrf_token)

        if username in users and users[username] == password:
            if not is_valid_csrf_token(provided_csrf_token):
                return render_template('login.html', error_message='Invalid CSRF Token')

            session['username'] = username
            session['remote_addr'] = request.remote_addr
            return redirect(url_for('main_route'))
        else:
            return render_template('login.html', error='Nieprawidłowa nazwa użytkownika lub hasło')


def is_user_authenticated(ip):
    # Sprawdź, czy adres IP użytkownika znajduje się na liście zaufanych adresów IP
    trusted_ips = ['192.168.1.6']  # Dodaj inne zaufane adresy IP według potrzeb

    if ip in trusted_ips:
        if 'username' in session:
            return True
    return False


# Dekorator login_required
def login_required(view):
    @wraps(view)
    def decorated(*args, **kwargs):
        if not is_user_authenticated(request.remote_addr):
            # Jeśli użytkownik nie jest zalogowany, przekieruj go na stronę logowania
            return redirect(url_for('auth.auth_login_route'))
        return view(*args, **kwargs)
    return decorated


def generate_csrf_token():
    token = hashlib.sha256(os.urandom(1024)).hexdigest()  # Generowanie losowego tokena CSRF
    return token


def is_valid_csrf_token(provided_token):
    expected_token = session.get('csrf_token')
    return expected_token and provided_token == expected_token
