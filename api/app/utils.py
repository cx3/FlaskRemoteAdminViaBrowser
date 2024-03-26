import os
import platform
from datetime import datetime

from werkzeug.utils import secure_filename


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


def make_secured_path(path: str) -> str:
    safe = slash(path)
    return os.path.join('/'.join(safe.split('/')[:-1]), secure_filename(safe.split('/')[-1]))
