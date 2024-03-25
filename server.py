from app_routes import app
from auth_blueprint import bp, login_required

app.register_blueprint(bp, url_prefix='/auth')

for rule in app.url_map.iter_rules():
    print(rule, rule.endpoint)
    if rule.endpoint != 'static' and not rule.endpoint.startswith('auth'):
        view_func = app.view_functions[rule.endpoint]
        app.view_functions[rule.endpoint] = login_required(view_func)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
