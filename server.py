import os

from flask import send_from_directory

from api.app.routes import app, socketio
from api.auth.auth_blueprint import bp as auth_bp
from api.auth.auth_blueprint import login_required
from api.cmd.cmd_blueprint import bp as cmd_bp
from api.db.db_blueprint import bp as db_bp
from api.rdp.rdp_blueprint import rdp_bp


app.register_blueprint(auth_bp, url_prefix='/auth')
app.register_blueprint(rdp_bp, url_prefix='/rdp')
app.register_blueprint(cmd_bp, url_prefix='/cmd')
app.register_blueprint(db_bp, url_prefix='/db')


def is_dict(x):
    return isinstance(x, dict)


def is_list(x):
    return isinstance(x, list)


app.jinja_env.globals['is_dict'] = is_dict
app.jinja_env.globals['is_list'] = is_list


if app.config.get('LOGIN_REQUIRED_SECURE_DECORATOR', False):
    def startswith(name):
        for _ in ['auth', 'rdp']:
            if name.startswith(_):
                return True
        return False

    for rule in app.url_map.iter_rules():
        if 'favicon.ico' in rule.endpoint or 'favicon.ico' in str(rule):
            continue
        if rule.endpoint != 'static' and not startswith(rule.endpoint):
            print('Rule:', rule, '\t\tdecorated endpoint:', rule.endpoint)
            view_func = app.view_functions[rule.endpoint]
            app.view_functions[rule.endpoint] = login_required(view_func)


@app.route('/site_map')
@app.route('/site-map')
def site_map_route():
    links = []
    for i, rule_ in enumerate(app.url_map.iter_rules()):
        endpoint = rule_.endpoint
        link = f'<a href="{rule_}">({i})  {endpoint}</a>'
        links.append(link)
    return "</br>".join(links)


@app.route('/favicon.ico')
def favicon():
    return send_from_directory(
        os.path.join('/'.join(__file__.replace('\\', '/').split('/')[:-1]), 'static/'),
        'favicon.ico',
        mimetype='image/vnd.microsoft.icon')


if __name__ == '__main__':
    socketio.run(
        app,
        host="0.0.0.0",
        port=5000,
        debug=True,
        allow_unsafe_werkzeug=True,
        log_output=True,
        use_reloader=True
    )
