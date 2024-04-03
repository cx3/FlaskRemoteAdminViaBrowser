import chardet
import platform
import subprocess

from flask import Blueprint, render_template
from api.app.routes import socketio

bp = Blueprint('cmd', __file__, template_folder='api/cmd/templates')


def execute_command(command):
    try:
        if platform.system() == "Windows":
            result = subprocess.check_output(command, shell=True, stderr=subprocess.STDOUT)
            encoding = chardet.detect(result)
            # print('encoding:', encoding)
            result = str(result, encoding=encoding['encoding'])
        else:
            result = subprocess.check_output(command, shell=True, stderr=subprocess.STDOUT, encoding='utf-8')
        return result.strip()
    except (subprocess.CalledProcessError, Exception) as e:  # subprocess.CalledProcessError as e:
        return "Server console returned error: " + str(e)


@bp.route('/')
def cmd_main_route():
    return render_template('index2.html')


@socketio.on('execute_command', namespace='/cmd')
def execute_command_socket(command):
    # print('received cmd: ', command)
    result = execute_command(command)
    socketio.emit('command_result', result, namespace='/cmd')
