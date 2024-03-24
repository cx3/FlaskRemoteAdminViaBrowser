import os
import platform
import mimetypes
from datetime import datetime

from flask import Flask, jsonify, request, render_template, send_file, url_for, redirect
from werkzeug.utils import secure_filename
from flask_socketio import SocketIO, emit


app = Flask(__name__)
app.config['SECRET_KEY'] = os.urandom(32)
socketio = SocketIO(app)


@app.route('/')
def main_route():
    return """
    <script>
        window.location.href='/list_dir?server_dir=C:/STABLED/stable-diffusion-webui-master/extensions/deforum/';
    </script>
    """


def slash(path: str) -> str:
    return path.replace('\\', '/')


def get_file_type(name):
    if '.' not in name:
        return 'text'

    ext = name.split('.')[-1].lower()

    if ext in ['pdf', 'doc', 'docx', 'xls', 'xlsx', 'ppt', 'pptx', 'odt']:
        return 'document'
    if ext in ['jpg', 'jpeg', 'png', 'gif', 'bmp', 'svg', 'tif', 'tiff']:
        return 'image'
    if ext in ['mp3', 'wav', 'ogg', 'flac', 'aac', 'wma', 'm4a']:
        return 'audio'
    if ext in ['mp4', 'avi', 'mkv', 'mov', 'wmv', 'flv', 'webm', 'mpeg', 'mpg']:
        return 'video'
    if ext in ['txt', 'c', 'cpp', 'h', 'hpp', 'java', 'py', 'pyc', 'pyd', 'pyo', 'html', 'htm', 'css', 'js',
               'php', 'php3', 'php4', 'php5', 'phtml', 'rb', 'rhtml', 'pl', 'pm', 'sh', 'bash', 'zsh',
               'sql', 'swift', 'go', 'rust', 'scala', 'csharp', 'cs', 'vb', 'vbs', 'lua', 'dart', 'jsx',
               'tsx', 'vue', 'ts', 'sass', 'scss', 'less', 'asm', 'asmx', 'aspx', 'ascx', 'ejs', 'jade',
               'pug', 'twig', 'xml', 'json', 'yaml', 'yml', 'ini', 'cfg', 'conf', 'htaccess',
               'dockerfile', 'bat', 'cmd', 'jsx', 'tsx', 'coffee', 'handlebars', 'hbs', 'md', 'markdown',
               'r', 'R', 'plsql', 'sql', 'psql', 'scss', 'styl', 'yaml', 'yml', 'twig', 'json',
               'graphql', 'jsx', 'tsx', 'ejs', 'pug', 'scss', 'less', 'elm', 'lua', 'cshtml', 'svelte',
               'pl', 'pm', 't', 'r', 'rmd', 'groovy', 'kt', 'kts', 'nim', 'd', 'di', 'p', 'pas', 'scala',
               'swift', 'vb', 'vbs', 'xml', 'plist', 'xsd', 'dtd', 'diff', 'haskell', 'erl', 'hrl',
               'clojure', 'fish', 'toml', 'gd', 'gdscript', 'phps', 'ejs', 'jinja', 'axml', 'smali',
               'xml', 'pyi', 'qbs', 'slim', 'styl', 'tsx', 'pm6', 'p6', 'pl6', 't6', 'raku', 'rmd',
               'vbhtml', 'vbproj', 'xib', 'storyboard', 'xq', 'xquery', 'cake', 'clj', 'cljs', 'cljc',
               'diff', 'patch', 'fish', 'gd', 'gdscript', 'graphql', 'h', 'hh', 'hxx', 'haml', 'ini',
               'cfg', 'lisp', 'lsp', 'nim', 'nimble', 'nix', 'plist', 'pp', 'puppet', 'ps', 'ps1',
               'psm1', 'psd1', 're', 'rei', 'rs', 'rlib', 'scss', 'sass', 'svelte', 'sw', 'vue', 'vuejs',
               'xaml', 'yaml', 'yml', 'yml.dist', 'yml', 'yaml', 'zsh']:
        return 'text'

    return 'document'


# Funkcja do listowania plików i ich detali
def list_dir(server_dir='/', only_dirs=False):

    if server_dir in [None, '', '*']:
        server_dir = os.getcwd()

    if server_dir[-1] not in ['\\', '/']:
        server_dir += '/'

    files_data = []
    dirs_data = []

    icons = {
        'document': 'fa-solid fa-file-lines',
        'text': 'fa-solid fa-code',
        'audio': 'fa-solid fa-music',
        'video': 'fa-solid fa-file',
        'image': 'fa-solid fa-file-image'
    }

    # Sprawdzenie czy serwer działa pod kontrolą systemu Windows
    if platform.system() == 'Windows':
        server_dir = os.path.abspath(server_dir)
        if len(server_dir) == 2:  # Jeśli wybrany jest tylko dysk (np. 'C:')
            server_dir += '\\'

    server_dir = slash(server_dir)

    if os.path.isfile(server_dir):
        server_dir = os.getcwd()

    # Sprawdzenie czy ścieżka katalogu istnieje
    if os.path.exists(server_dir) and os.path.isdir(server_dir):
        for file_name in os.listdir(server_dir):
            file_path = slash(os.path.join(server_dir, file_name))

            file_details = {
                'name': file_name,
                'size': os.path.getsize(file_path),
                'created_at': datetime.fromtimestamp(os.path.getctime(file_path)).strftime('%Y-%m-%d %H:%M:%S'),
                'full_path': file_path,

                # Dodaj inne szczegóły w zależności od rozszerzenia pliku
                # Możesz użyć np. modułu python-magic do rozpoznawania typu pliku
            }

            if os.path.isfile(file_path):
                if only_dirs:
                    continue

                file_details['type'] = get_file_type(file_name)
                file_details['icon'] = icons[file_details['type']]
                files_data.append(file_details)
            else:
                file_details['type'] = 'directory'
                dirs_data.append(file_details)

    return {'server_dir': server_dir, 'files': files_data, 'dirs': dirs_data}


@app.route('/list_dir')
def list_dir_route():
    server_dir = slash(request.args.get('server_dir', os.getcwd()))

    if os.path.isfile(server_dir):
        return redirect(url_for('list_dir_route', server_dir='/'.join(server_dir.split('/')[:-1])))

    content = list_dir(server_dir)
    current_path = slash(content['server_dir']).split('/')

    # return render_template('list_dir2.html', current_path=current_path, content=content, server_dir=server_dir)
    return render_template(
        'list_dir3.html', current_path=current_path, content=content, server_dir=server_dir
    )


@app.route('/get_folders', methods=['GET', 'POST'])
def get_folders_route():
    print('/get_folders:')
    if request.method == 'POST':
        try:
            print(request.form['folder_id'])

            sub_dirs = list_dir(request.form['folder_id'], only_dirs=True)
            print(sub_dirs)
            return jsonify(sub_dirs), 200
        except (WindowsError, OSError) as e:
            return jsonify({'error': str(e)}), 400


def make_secured_path(path: str) -> str:
    safe = slash(path)
    return os.path.join('/'.join(safe.split('/')[:-1]), secure_filename(safe.split('/')[-1]))


@app.route('/file', methods=['GET', 'POST'])
def get_file_route():
    path = request.args.get('path', False)
    mime_type, encodings = mimetypes.guess_type(path)

    if request.method == 'GET':
        if not path:
            return ''

        if os.path.exists(path):
            if os.path.isfile(path):
                # ext = path.replace("\\", '/').split('/')[-1]
                resp = send_file(path, mimetype=mime_type)
                print(f"mime={mime_type}, encodings={encodings}")
                return resp

    if request.method == 'POST':
        safe = make_secured_path(path)

        print('request.method == POST')
        if os.path.isfile(safe):
            print('isfile')
            if 'text' in mime_type:
                print('text in mime')

                open(safe + '_NEW', 'wt').write(request.form['data'])
                return jsonify({'msg': 'DATA SAVED ON THE SERVER'})
            else:
                if not encodings:
                    encodings = 'utf-8'

                open(safe + '_NEW', 'wb').write(bytes(request.form['data'].encode(encoding=encodings)))
                print('saved as binary')
        return "ok"


@app.route('/upload', methods=['POST'])
def upload_route():
    if request.method == 'POST':
        dest = request.args.get('dest', False)
        print('upload post, dest=', dest)

        if os.path.isdir(dest):
            print("isdir!")
            print(request.files)
            return jsonify(response={'msg': 'zajebiscja!'})
    return 'BLEEE'


@app.route('/ace', methods=['POST', 'GET'])
def ace_editor_route():
    if request.method == 'GET':
        file = request.args.get('file', False)
        if not file:
            return jsonify({'msg': 'param file is empty'}), 400
        if not os.path.isfile(file):
            return jsonify({'msg': 'cannot read passed file, it does not exist'}), 400
        return render_template('ace.html', file=file)


@socketio.on('search_files')
def search_files(data):
    server_dir = slash(data['serverDir'])

    if not os.path.isdir(server_dir):
        server_dir = os.getcwd()

    search_query = data['searchQuery'].lower()
    date_from = datetime.strptime(data['dateFrom'], "%Y-%m-%d") if data['dateFrom'] else None
    date_to = datetime.strptime(data['dateTo'], "%Y-%m-%d") if data['dateTo'] else None

    if search_query:
        # Wyszukiwanie plików na serwerze na podstawie zapytania i zakresu daty
        for root, dirs, files in os.walk(server_dir):
            for file in files:
                file_path = slash(os.path.join(root, file))
                if search_query in file.lower():
                    file_time = datetime.fromtimestamp(os.path.getmtime(file_path))
                    if (not date_from or file_time >= date_from) and (not date_to or file_time <= date_to):

                        file_details = {
                            'name': file,
                            'size': os.path.getsize(file_path),
                            'created_at': datetime.fromtimestamp(
                                os.path.getctime(file_path)).strftime(
                                '%Y-%m-%d %H:%M:%S'),
                            'full_path': file_path,
                            'type': get_file_type(file)
                        }

                        if os.path.isdir(file):
                            file_details['type'] = 'directory'
                        else:
                            file_details = {
                                **file_details,
                                'edit': url_for('ace_editor_route', file=file_details['full_path']),
                                'download': url_for('get_file_route', path=file_details['full_path']),
                                'go_folder': url_for('list_dir_route', server_dir=file_details['full_path'])
                            }

                        emit('file_found', file_details)
    emit('search_finished')


@app.route('/search')
def search_route():
    return render_template('search.html')


@app.route('/audio', methods=['GET'])
def audio_route():
    return ''


@app.route('/video', methods=['GET'])
def video_route():
    file = slash(request.args.get('file'))

    if os.path.isfile(file):
        return render_template('video.html', file=url_for('get_file_route', path=file))

    return "<script>alert('Incorrect video link');</script>"


@app.route('/image', methods=['GET'])
def image_route():
    return ''


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)