from api.app.routes import app, socketio
from api.auth.auth_blueprint import bp as auth_bp
from api.auth.auth_blueprint import login_required
from api.cmd.cmd_blueprint import bp as cmd_bp

app.register_blueprint(auth_bp, url_prefix='/auth')
app.register_blueprint(cmd_bp, url_prefix='/cmd')

for rule in app.url_map.iter_rules():
    print('Rule:', rule, '\t\tdecorated endpoint:', rule.endpoint)
    if rule.endpoint != 'static' and not rule.endpoint.startswith('auth'):
        view_func = app.view_functions[rule.endpoint]
        app.view_functions[rule.endpoint] = login_required(view_func)

if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', port=5000, debug=False, allow_unsafe_werkzeug=True)
