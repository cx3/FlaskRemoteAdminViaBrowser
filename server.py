from api.app.routes import app, socketio
from api.auth.auth_blueprint import bp as auth_bp
from api.auth.auth_blueprint import login_required
from api.cmd.cmd_blueprint import bp as cmd_bp
from api.db.db_blueprint import bp as db_bp

app.register_blueprint(auth_bp, url_prefix='/auth')
app.register_blueprint(cmd_bp, url_prefix='/cmd')
app.register_blueprint(db_bp, url_prefix='/db')


def is_dict(x):
    if isinstance(x, dict):
        print('is_dict', type(x))
    return isinstance(x, dict)


app.jinja_env.globals['is_dict'] = is_dict

if app.config.get('LOGIN_REQUIRED_SECURE_DECORATOR', True):
    for rule in app.url_map.iter_rules():
        if rule.endpoint != 'static' and not rule.endpoint.startswith('auth'):
            print('Rule:', rule, '\t\tdecorated endpoint:', rule.endpoint)
            view_func = app.view_functions[rule.endpoint]
            app.view_functions[rule.endpoint] = login_required(view_func)


if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', port=5000, debug=True, allow_unsafe_werkzeug=True)
