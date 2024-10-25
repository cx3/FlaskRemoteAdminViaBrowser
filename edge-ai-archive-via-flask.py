from flask import Flask, request, render_template
import py7zr
import zipfile
import rarfile
import os
import datetime

app = Flask(__name__)


def get_archive_info(file_path):
    archive_info = []
    if file_path.endswith('.zip'):
        with zipfile.ZipFile(file_path, 'r') as archive:
            for info in archive.infolist():
                archive_info.append({
                    'name': info.filename,
                    'size': info.file_size,
                    'date': datetime.datetime(*info.date_time).strftime('%Y-%m-%d %H:%M:%S'),
                    'extension': os.path.splitext(info.filename)[1]
                })
    elif file_path.endswith('.rar'):
        with rarfile.RarFile(file_path, 'r') as archive:
            for info in archive.infolist():
                archive_info.append({
                    'name': info.filename,
                    'size': info.file_size,
                    'date': datetime.datetime(*info.date_time).strftime('%Y-%m-%d %H:%M:%S'),
                    'extension': os.path.splitext(info.filename)[1]
                })
    elif file_path.endswith('.7z'):
        with py7zr.SevenZipFile(file_path, 'r') as archive:
            for info in archive.list():
                archive_info.append({
                    'name': info.filename,
                    'size': info.size,
                    'date': datetime.datetime.fromtimestamp(info.mtime).strftime('%Y-%m-%d %H:%M:%S') if info.mtime else 'N/A',
                    'extension': os.path.splitext(info.filename)[1]
                })
    return archive_info


def build_tree(archive_info):
    tree = {}
    for file in archive_info:
        parts = file['name'].split('/')
        current_level = tree
        for part in parts:
            if part not in current_level:
                current_level[part] = {}
            current_level = current_level[part]
    return tree


def render_tree(tree, parent_path=''):
    html = '<ul>'
    for key, value in tree.items():
        full_path = os.path.join(parent_path, key)
        if value:
            html += f'<li><a href="?file={{ file_path }}&folder={full_path}/">{key}/</a>{render_tree(value, full_path)}</li>'
        else:
            html += f'<li><a href="?file={{ file_path }}&folder={full_path}">{key}</a></li>'
    html += '</ul>'
    return html


@app.route('/archive')
def archive():
    file_path = request.args.get('file')
    folder_path = request.args.get('folder', '')

    if not file_path or not os.path.exists(file_path):
        return "File not found", 404

    archive_info = get_archive_info(file_path)
    tree = build_tree(archive_info)

    current_files = [file for file in archive_info if file['name'].startswith(folder_path) and '/' not in file['name'][len(folder_path):]]

    return render_template('archive.html', tree=tree, current_files=current_files, folder_path=folder_path, file_path=file_path, render_tree=render_tree)


if __name__ == '__main__':
    app.run(debug=True)
