import os
import mimetypes
import threading
from datetime import datetime

from api.app.utils import slash, list_dir, make_secured_path, get_file_type
from api.app.search_engine import FileSearcher
from api.app.utils import threaded_download, get_server_state, kill_process, system_info, slash
from api.app.archives_utils import list_archive_file, extract_archive_file

from flask import Flask, request, redirect, url_for, render_template, jsonify, send_file
from flask_socketio import SocketIO, emit
from flask_sqlalchemy import SQLAlchemy
from werkzeug.utils import secure_filename
from PIL import Image

app = Flask(__name__)
app.config['SECRET_KEY'] = os.urandom(64)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///C:/proj/some_sqlite.db'
app.config['LOGIN_REQUIRED_SECURE_DECORATOR'] = False  # setting to False - no authentication needed

app.config['default_folder_viewer'] = 'list_dir4.html'  # 'list_dir4_icons.html'
db = SQLAlchemy(app)
app.config['db_instance'] = db
socketio = SocketIO(app)

download_status = {}


@app.route('/')
@app.route('/dashboard')
def main_route():
    info = system_info()
    info_text = f"System: {info['System']} {info['Version']}"
    node_name = f"{info['Node Name']}"
    processor = f"{info['Processor']}"

    return render_template(
        'dashboard1.html',
        info_text=info_text,
        node_name=node_name,
        processor=processor
    )


@app.route('/explorer')
def main_files_route():
    return f"""
    <script>
        window.location.href='/list_dir?server_dir={slash(os.getcwd())}';
    </script>
    """


@app.route('/stats', methods=['POST', 'GET'])
def server_stats_route():
    if request.method == 'GET':
        sort_by = request.args.get('sort_by', 'memory_info')
        order = request.args.get('reverse', True)
        units = request.args.get('units', 'b')
        limit = request.args.get('limit', -1)

        return get_server_state(sort_by, order, units, limit)

    if request.method == 'POST':
        pid = request.args.get('kill_by_pid', False)
        if isinstance(pid, int):
            kill_process(pid)
        return jsonify({'response': 'after os.kill by pid'})


@app.route('/dir_exists')
def dir_exists_route():
    return jsonify({"response": os.path.isdir(request.args.get('path', False))})


@app.route('/list_dir', methods=['POST', 'GET'])
def list_dir_route():
    """
    In web browser we put list_dir?server_dir=/existing/path/to/folder/on/server  in the link and this function builds
    a view of folder passed to parameter.
    :return: front-end code for web browser with content of folder passed to parameter
    """
    if request.method == 'GET':
        server_dir = slash(request.args.get('server_dir', os.getcwd()))

        if os.path.isfile(server_dir):
            return redirect(url_for('list_dir_route', server_dir='/'.join(server_dir.split('/')[:-1])))

        content = list_dir(server_dir)
        current_path = slash(content['server_dir']).split('/')

        print('items:', len(content['files']))

        # return render_template('list_dir2.html', current_path=current_path, content=content, server_dir=server_dir)
        return render_template(
            app.config['default_folder_viewer'], current_path=current_path, content=content, server_dir=server_dir
        )
    if request.method == 'POST':
        if request.args.get('toggle_folder_viewer', None):
            if app.config['default_folder_viewer'] == 'list_dir4.html':
                app.config['default_folder_viewer'] = 'list_dir4_icons.html'
            else:
                app.config['default_folder_viewer'] = 'list_dir4.html'
        return jsonify({"response": "ok"})


@app.route('/get_dir_content')
def get_dir_content_route():
    dir_path = request.args.get('server_dir')
    if os.path.isfile(dir_path):
        dir_path = os.path.dirname(dir_path)
    dir_path = dir_path if os.path.isdir(dir_path) else os.getcwd()
    return jsonify({
        "server_dir": dir_path,
        "content": list_dir(dir_path)
    })


@app.route('/get_folders', methods=['GET', 'POST'])
def get_folders_route():
    """
    /get_folders?folder_id=/path/to/folder    this function returns list of names of folders in folder passed in param
    :return: list of folders, json format
    """
    print('/get_folders:')
    if request.method == 'POST':
        try:
            print(request.form['folder_id'])
            sub_dirs = list_dir(request.form['folder_id'], only_dirs=True)
            print(sub_dirs)
            return jsonify(sub_dirs), 200
        except (WindowsError, OSError) as e:
            return jsonify({'error': str(e)}), 400


@app.route('/file', methods=['GET', 'POST'])
def get_file_route():
    """
    /file?path=/path/to/file  - with method get allows to download file from server, with post method it saves updated
    content of a file
    :return:
    """
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
            # print('isfile')
            if 'text' in mime_type:
                open(safe, 'wt').write(request.form['data'])
                return jsonify({'msg': 'DATA SAVED ON THE SERVER'})
            else:
                if not encodings:
                    encodings = 'utf-8'

                open(safe, 'wb').write(bytes(request.form['data'].encode(encoding=encodings)))
                # print('saved as binary')
        return "ok"


@app.route('/archive')
def list_archive_route():
    if request.method == 'GET':
        file = request.args.get('file', False)
        dest = request.args.get('dest', False)
        mode = request.args.get('mode', 'list')
        password = request.args.get('password', None)

        print(f'/archive?file={file}&mode={mode} ....')

        if os.path.isfile(file):
            if get_file_type(file) != 'archive':
                return jsonify({"response": "not archive file"})
            if mode == 'raw':
                return jsonify(raw=list_archive_file(file, password))
            if mode == 'list':
                content = list_archive_file(file, password)
                print('>>>>> archive content', content)
                return render_template('list_archive2.html', data=content, mode='list')
            if mode == 'extract':
                dest = '/'.join(slash(file).split('/')[:-1]) if not dest else dest
                extract_archive_file(file, dest, password)
                return redirect(url_for('list_dir_route', server_dir=dest))
        else:
            return jsonify({"response": f"file {file} does not exists"})


@app.route('/upload', methods=['POST'])
def upload_route():
    """
    Due to some other stuff to improve, this function by now DOES not allow to upload files
    :return:
    """
    if request.method == 'POST':
        if 'file' not in request.files:
            return jsonify(response={'msg': 'No file part'}), 400

        upload_dir = request.form.get('dest_dir', os.getcwd())
        if not os.path.isdir(upload_dir):
            upload_dir = os.getcwd()

        file = request.files['file']
        if file.filename == '':
            return jsonify(response={'msg': 'No selected file'}), 400
        if file:  # (fileand allowed_file(file.filename)):
            filename = secure_filename(file.filename)
            file.save(os.path.join(upload_dir, filename))
            return jsonify(response={'msg': 'File successfully uploaded'}), 200

    return jsonify({"msg": "error"})


@app.route('/ace', methods=['POST', 'GET'])
def ace_editor_route():
    """
    /ace?file=/path/to/file  - ACE editor for source codes in various programming languages with syntax highlighting
    :return: json format error or ACE editor with content of loaded file from path on the server
    """
    if request.method == 'GET':
        file = request.args.get('file', False)
        if not file:
            return jsonify({'msg': 'param file is empty'}), 400
        if not os.path.isfile(file):
            return jsonify({'msg': 'cannot read passed file, it does not exist'}), 400
        return render_template('ace2.html', file=file)

    if request.method == 'POST':
        pack = request.get_json()
        file = pack.get('filename', False)
        data = pack.get('content', False)
        if file and data:
            file = make_secured_path(file)
            open(file, 'wb').write(data)
            return {"response": "file saved"}
        return render_template('ace2.html', file=file)


@app.route('/zip_selected', methods=['POST', 'GET'])
def zip_selected_files_route():
    return jsonify({"msg": "implement it later"})


@app.route('/remote_download', methods=['POST', 'GET'])
def remote_download_route():
    if request.method == 'POST':
        data = request.get_json()
        dest_dir = data.get('dest_dir', False)
        url = data.get('url', False)
        print('/remote_download json', data)

        if not url:
            return jsonify({"status": "error = empty url"})

        if not os.path.isdir(dest_dir):
            dest_dir = os.getcwd()

        task_id = threading.get_ident()

        download_status[task_id] = {'total_size': 0, 'downloaded_size': 0, 'done': False}
        thread = threading.Thread(target=threaded_download, args=(url, dest_dir, task_id, download_status))
        thread.start()
        return jsonify({"downloads": download_status})

    if request.method == 'GET':
        to_remove = []
        for key in download_status:
            if download_status[key]['done']:
                to_remove.append(key)
        for key in to_remove:
            del download_status[key]
        if download_status:
            return jsonify({"downloads": download_status})
        return jsonify({})


@socketio.on('search_files')
def search_files(data):
    """
    In advanced_search_form / _form_results.html - when user clicks Search or when passed link with parameters to the
    browser with GET method, this function is launched and on separate thread it collects info about matching files to
    the query passed in data param.
    Even working on big collection of files with heavy query, task on thread allows to send back to the web client new
    results on the fly, what makes page dynamic.
    :param data: structured query taken from web form
    :return: we never take care about it due to it is an internal business of flask_socketio
    """
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
    """
    Basic front end file searcher
    :return:
    """
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


@app.route('/get_media_files')
def get_media_files_route(*args):
    files_or_dirs = []
    for next_item in [request.args.values(), *args]:
        if isinstance(next_item, (tuple, list)):
            files_or_dirs.extend(next_item)
        else:
            files_or_dirs.append(next_item)

    media_dir = request.args.get('server_dir', os.getcwd())
    audio_extensions = ['mp3', 'wav', 'flac', 'aac', 'ogg', 'wma', 'm4a', 'aiff', 'alac', 'pcm']
    video_extensions = ['mp4', 'mkv', 'avi', 'mov', 'wmv', 'flv', 'webm', 'vob', 'ogv', 'm4v']

    def filter_media_files(files, audio_ext, video_ext):
        media_files = []
        for file in files:
            ext = os.path.splitext(file)[1][1:].lower()
            if ext in audio_ext or ext in video_ext:
                media_files.append(file)
        return media_files

    playlist = []
    for next_entry in files_or_dirs:
        if os.path.isfile(next_entry):
            playlist.append(next_entry)
        elif os.path.isdir(next_entry):
            playlist.extend([_['full_path'] for _ in list_dir(media_dir)['files']])
        else:
            pass

    return filter_media_files(playlist, audio_extensions, video_extensions)


@app.route('/mediaplayer', methods=['POST', 'GET'])
def media_route(*args):
    # https://developer.mozilla.org/en-US/docs/Web/Media/Audio_and_video_delivery/buffering_seeking_time_ranges
    files_or_dirs = []
    for next_item in [*request.args.values(), *args]:
        if isinstance(next_item, (tuple, list)):
            files_or_dirs.extend(*next_item)
        else:
            files_or_dirs.append(next_item)

    audio_ext = ['mp3', 'wav', 'flac', 'aac', 'ogg', 'wma', 'm4a', 'aiff', 'alac', 'pcm']
    video_ext = ['mp4', 'mkv', 'avi', 'mov', 'wmv', 'flv', 'webm', 'vob', 'ogv', 'm4v']

    playlist = []
    for next_entry in files_or_dirs:
        if os.path.isfile(next_entry):
            playlist.append(next_entry)
        elif os.path.isdir(next_entry):
            playlist.extend([_['full_path'] for _ in list_dir(next_entry)['files']])
        else:
            pass

    pairs = []
    for item in playlist:
        ext = item.split('.')[-1]
        if ext in audio_ext:
            pairs.append([item, 'audio'])
        if ext in video_ext:
            pairs.append([item, 'video'])

    if request.method == 'GET':
        return render_template(
            'floating_players.html',
            playlist=pairs
        )


@app.route('/image', methods=['GET'])
def image_route():
    file = request.args.get('file', False)
    if os.path.isfile(file):
        if get_file_type(file) == 'image':
            x, y = Image.open(file).size
            return f"""
            <html><body> <img src="/file?path={file}" width="{x}" height="{y}"> </body></html>
            """
    return ''


@app.route('/paint', methods=['POST', 'GET'])
def paint_edit_route():
    media_dir = request.args.get('media_dir', False)
    if media_dir:
        return render_template('paint_editor2.html', mode="new", **request.args)
    return render_template('paint_editor1.html', **request.args)


@app.route('/modalWindows', methods=['GET'])
@app.route('/modalWindows.html', methods=['GET'])
def modal_windows_route():
    cwd = request.args.get('server_dir', os.getcwd())
    return render_template('modalWindows.html', cwd=slash(cwd))


@app.route('/nested_dict.html')
def nested_dict_route():
    return render_template('nested_dict7.html')


@app.route('/advanced_search')
def advanced_search_route():
    """
    When no args passed to link it renders advanced search files form.
    When passed arguments to link it builds a query and starts search for files on the server building results on a
    separate thread. With flask_socketio it allows to show dynamic results page.
    :return: front end
    """
    if request.method == 'GET':
        if len(request.args) == 0:
            return render_template('advanced_search_form.html')
        return redirect(url_for('advanced_results_route', **request.args.to_dict()))


@app.route('/advanced_search/results')
def advanced_results_route():
    # print("RESULTS!", request.path)

    if not request.args:
        return redirect(url_for('advanced_search_route'))
    return render_template(
        'advanced_search_form_results.html',  # **request.args.to_dict()
    )


@socketio.on('search_files', namespace='/custom_search')
def handle_search_files(data):
    """
    In advanced_search_form(_results) when clicked Search button, search files matching to the query is launched in the
    background, emitting results to web client makes it dynamic - instead of waiting for sometimes long task for first
    results. Function emits results of matching files in portions per hundred.
    :param data: search files query passed from the web browser
    :return: we never take care - it is internal business of flask_socketio
    """

    # print("socketio search_files", str(data))
    root_dir = data.get('root_dir', os.getcwd())
    search_params = data.get('search_params', {})
    search_params['root_dir'] = root_dir
    search_params['socketio'] = socketio
    # print("@socketio.on   search_params: ", search_params)

    file_searcher = FileSearcher(**search_params)
    globals()['file_searcher'] = file_searcher  # REFACTOR IT ONE DAY...

    page = 1  # data.get('page', 1)
    items_per_page = 100
    start_index = (page - 1) * items_per_page
    end_index = start_index + items_per_page
    if end_index > len(file_searcher):
        end_index = len(file_searcher)
    paginated_results = file_searcher[start_index:end_index]

    emit('search_results', {
            'results': paginated_results,
            'id': id(file_searcher),
            'totalLen': len(file_searcher),
            'is_finished': file_searcher.is_finished()
        },
        namespace='/custom_search'
    )


@socketio.on('get_page', namespace='/custom_search')
def handle_get_page(data):
    """
    By changing in web browser page number, it emits new portion of data - a found results of passed earlier a search
    query.
    :param data:
    :return:
    """
    page = int(data.get('page', 1))
    items_per_page = 100
    start_index = (page - 1) * items_per_page
    end_index = start_index + items_per_page

    print(f"socketio get_page\t\tpage={page}  start_index={start_index}   endindex={end_index}")

    x = globals()['file_searcher']
    if not x:
        pass
    else:
        if end_index > len(x):
            end_index = len(x)
        paginated_results = x[start_index:end_index]

        print(f"len paginated results {len(paginated_results)}")

        emit('render_new_page',
             {
                 'results': paginated_results,
                 'size': len(paginated_results),
                 'page': page,
                 'id': id(x)
             },
             namespace='/custom_search'
             )


@socketio.on('stop_thread', namespace='/custom_search')
def handle_stop_thread(data):
    """
    When heavy file search task gives us too much results / works too long etc... - we kill the thread.
    :param data:
    :return:
    """
    x = globals()['file_searcher']

    if x:
        x.kill()

    emit(
        'search_finished',
        {
            'killed': 'killed'
        },
        namespace='/custom_search'
    )


@socketio.on('sort_and_show', namespace='/custom_search')
def handle_sort_and_show(data):
    """
    When we have some found files matching to the query and now we want to change column that we want to sort by it.
    :param data:
    :return:
    """
    # print('sort_and_show')
    column = data.get('column', 'column_created_at')
    column = column.replace('column_', '')
    print('sorting...')
    x: FileSearcher = globals()['file_searcher']
    x.sort(column, True if data.get('order', 'asc') else False)
    globals()['file_searcher'] = x
    print('sort finish')
    # emit('render_new_page', {'page': 1})
    emit('show_sorted', {}, namespace='/custom_search')
