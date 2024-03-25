import mimetypes
import os
from datetime import datetime

from utils import slash, list_dir, make_secured_path, get_file_type
from search_engine import FileSearcher
from flask_socketio import SocketIO

from flask import Flask, request, redirect, url_for, render_template, jsonify, send_file, session
from flask_socketio import emit


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


@app.route('/list_dir')
def list_dir_route():
    """
    In web browser we put list_dir?server_dir=/existing/path/to/folder/on/server  in the link and this function builds
    a view of folder passed to parameter.
    :return: front-end code for web browser with content of folder passed to parameter
    """
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
                # print('text in mime')

                open(safe + '_NEW', 'wt').write(request.form['data'])
                return jsonify({'msg': 'DATA SAVED ON THE SERVER'})
            else:
                if not encodings:
                    encodings = 'utf-8'

                open(safe + '_NEW', 'wb').write(bytes(request.form['data'].encode(encoding=encodings)))
                # print('saved as binary')
        return "ok"


@app.route('/upload', methods=['POST'])
def upload_route():
    """
    Due to some other stuff to improve, this function by now DOES not allow to upload files
    :return:
    """
    if request.method == 'POST':
        dest = request.args.get('dest', False)
        print('upload post, dest=', dest)

        if os.path.isdir(dest):
            # print("isdir!")
            print(request.files)
            return jsonify(response={'msg': 'zajebiscja!'})
    return 'BLEEE'


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
        return render_template('ace.html', file=file)


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


@app.route('/image', methods=['GET'])
def image_route():
    return ''


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

    emit('search_results',
         {
             'results': paginated_results,
             'id': id(file_searcher)
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
    When heavy file search task gives us too much results / works too long etc - we kill the thread.
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
    x.sort(column)
    globals()['file_searcher'] = x
    print('sort finish')
    # emit('render_new_page', {'page': 1})
    emit('show_sorted', {}, namespace='/custom_search')
