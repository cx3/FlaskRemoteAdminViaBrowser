import os

import chardet
import platform
import subprocess

from flask import Blueprint, render_template, request, jsonify
from api.app.routes import socketio, list_dir, list_dir_route
from api.app.utils import slash, list_dir
from api.cmd.inspector import inspect_globals, inspect_values, serialize, inspect_object

bp = Blueprint('cmd', __file__, template_folder='api/cmd/templates')


@bp.route('/')
def cmd_main_route():
    return render_template('cmd_index2.html', cwd=slash(os.getcwd()))


def execute_command(command):
    try:
        if platform.system() == "Windows":
            result = subprocess.check_output(command, shell=True, stderr=subprocess.STDOUT)
            encoding = chardet.detect(result)
            result = str(result, encoding=encoding['encoding'])
        else:
            result = subprocess.check_output(command, shell=True, stderr=subprocess.STDOUT, encoding='utf-8')
        return result.strip()
    except (subprocess.CalledProcessError, Exception) as e:  # subprocess.CalledProcessError as e:
        print(f'/cmd execute command exception {type(e)}, {e}')
        return "Server console returned error: " + str(e)


@socketio.on('xterm_input', namespace='/xterm')
def execute_xterm(*args, **data):
    print(f'execute_xterm  args={args}     data={data}')
    command = args[0]['command']  # WTF????
    result = subprocess.run(command, shell=True, capture_output=True, text=True)
    print('result obj:        ', result)
    print('result to be sent: ', result.stdout)
    socketio.emit('xterm_output', result.stdout + result.stderr, namespace='/xterm')


@bp.route('/xterm', methods=['POST', 'GET'])
@bp.route('/xterm.js', methods=['POST', 'GET'])
def cmd_xterm_route():
    return render_template('cmd_xterm.html', cwd=slash(os.getcwd()), request_args=request.args)


@bp.route('/py-i')
@bp.route('/python/interactive')
def cmd_python_interactive_route():
    result = inspect_globals()
    return render_template('python_interactive.html', cwd=slash(os.getcwd()), python_globals=result)


@bp.route('/py-i/test')
def cmd_python_test():
    from api.cmd.inspector import MyClass
    mc = MyClass()
    return jsonify(inspect_object(bp, True))


@socketio.on('execute_command', namespace='/cmd')
def execute_command_socket(command):
    # print('received cmd: ', command)
    result = execute_command(command)
    socketio.emit('command_result', result, namespace='/cmd')
