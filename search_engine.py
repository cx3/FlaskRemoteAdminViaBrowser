import os
import threading
import time
import bisect
from datetime import datetime
from typing import List, Dict

from dateutil import parser
import platform
import mimetypes
from datetime import datetime
from flask_socketio import SocketIO, emit

from utils import get_file_type


def get_file_data(filepath):
    file_info = {}
    try:
        filepath = filepath.replace('\\', '/')
        stat_info = os.stat(filepath)
        file_info['path'] = filepath
        file_info['name'] = filepath.split('/')[-1]
        file_info['size'] = stat_info.st_size
        file_info['created_at'] = datetime.fromtimestamp(stat_info.st_ctime).isoformat()
        # file_info['last_access'] = datetime.fromtimestamp(stat_info.st_atime).isoformat()
        file_info['permissions'] = stat_info.st_mode
        file_info['extension'] = os.path.splitext(filepath)[
            1]  # path, name, size, created_at, permissions, extensions, actions

        file_info['type'] = get_file_type(file_info['name'])
        return file_info
    except Exception as e:
        print(f"Error processing file {filepath}: {e}")
        return None


def match_query(file_info, **use_filters):
    matches = 0
    for key, value in use_filters.items():
        if key == 'starts_with':
            if file_info['name'].startswith(value):
                matches += 1
        if key == 'ends_with':
            if file_info['name'].endswith(value):
                matches += 1
        if key == 'partial_name':
            if value in file_info['name']:
                matches += 1
        if key == 'min_size':
            if int(file_info['size']) >= int(value):
                matches += 1
        if key == 'max_size':
            if int(file_info['size']) <= int(value):
                matches += 1
        '''if key == 'created_after':

        if key == 'created_before':
        if key == 'extension':'''

    return True if matches >= len(use_filters) else False


class FileSearcher:
    socketio: SocketIO

    def __init__(self, root_dir, **query):
        self.root_dir = root_dir
        socketio = query.get('socketio', False)

        self.sort_by = query.get('sortby', 'column_size_radio')

        if self.sort_by.count('_') != 2:
            self.sort_by = 'column_size_radio'

        self.sort_by = self.sort_by.split('_')[1]

        if self.sort_by == 'created':
            self.sort_by += '_at'

        if not isinstance(socketio, SocketIO):
            raise TypeError('Pass arg socketio to FileSearcher!')

        self.socketio = socketio
        self.query = query
        self.result = []
        self.current_index = 0
        self.search_thread = threading.Thread(target=self._search_files_autosort_insert)
        self.search_thread.start()
        self._killed = False
        time.sleep(0.25)

    def kill(self):
        self._killed = True

    def __getitem__(self, key):
        if isinstance(key, slice):
            start, stop, step = key.start, key.stop, key.step
            if start is None:
                start = 0
            if stop is None:
                stop = len(self.result)
            return self.result[start:stop:step]
        else:
            return self.result[key]

    def __iter__(self):
        return self

    def __next__(self):
        if self.current_index < len(self.result):
            result = self.result[self.current_index]
            self.current_index += 1
            return result
        else:
            raise StopIteration()

    def __len__(self):
        return len(self.result)

    def sort(self, column_name, reverse=False) -> bool:
        if not self.result:
            return False
        if column_name in self.result[0].keys():
            self.result = sorted(self.result, key=lambda x: x[column_name], reverse=reverse)
            return True
        return False

    def _search_files(self):

        filters = [
            'starts_with', 'ends_with', 'partial_name', 'min_size', 'max_size', 'created_after', 'created_before',
            'extension'
        ]

        use_filters = {}

        for key, value in self.query.items():
            if key in filters and value != '':
                use_filters[key] = value

        iters = 0
        for dirs, _, filenames in os.walk(self.root_dir):
            if self._killed:
                break

            for filename in filenames:
                filepath = os.path.join(dirs, filename)
                file_data = get_file_data(filepath)
                iters += 1
                if match_query(file_data, **use_filters):
                    self.result.append(file_data)

                    if len(self.result) < 100:
                        self.socketio.emit(
                            'render_new_page',
                             {
                                 'results': self.result,
                                 'size': len(self.result),
                                 'page': 1,
                                 'id': id(self)
                             },
                             namespace='/custom_search'
                        )

                    if len(self.result) % 100 == 0:
                        print("Next hundred found")
                        self.socketio.emit(
                            'next_hundred_found',
                            {
                                'found': len(self.result) // 100, 'iters': iters
                            },
                            namespace='/custom_search'
                        )

        self.socketio.emit(
            'search_finished',
            {
                'len': len(self.result),
                'pages': len(self.result) // 100,
                'iters': iters
            },
            namespace='/custom_search'
        )
        print('search finished emitted')

    def _search_files_autosort_insert(self):

        filters = [
            'starts_with', 'ends_with', 'partial_name', 'min_size', 'max_size', 'created_after', 'created_before',
            'extension'
        ]

        use_filters = {}

        for key, value in self.query.items():
            if key in filters and value != '':
                use_filters[key] = value

        iters = 0
        for dirs, _, filenames in os.walk(self.root_dir):
            if self._killed:
                break
            for filename in filenames:
                filepath = os.path.join(dirs, filename)
                file_data = get_file_data(filepath)
                iters += 1
                if match_query(file_data, **use_filters):
                    if not self.result:
                        self.result.append(file_data)
                    else:
                        index = bisect.bisect_left(
                            [item[self.sort_by] for item in self.result],
                            file_data[self.sort_by]
                        )
                        self.result.insert(index, file_data)

                    if len(self.result) < 100:
                        self.socketio.emit(
                            'render_new_page',
                             {
                                 'results': self.result,
                                 'size': len(self.result),
                                 'page': 1,
                                 'id': id(self)
                             },
                             namespace='/custom_search'
                        )

                    if len(self.result) % 100 == 0:
                        # print("Next hundred found")
                        self.socketio.emit(
                            'next_hundred_found',
                            {
                                'found': len(self.result) // 100, 'iters': iters
                            },
                            namespace='/custom_search'
                        )

        if len(self.result) < 100:
            self.socketio.emit(
                'next_hundred_found',
                {
                    'found': 1, 'iters': iters
                },
                namespace='/custom_search'
            )

        self.socketio.emit(
            'search_finished',
            {
                'len': len(self.result),
                'pages': len(self.result) // 100,
                'iters': iters
            },
            namespace='/custom_search'
        )
        print('search finished emitted')

    def wait_until_finished(self):
        self.search_thread.join()

    def is_finished(self):
        return not self.search_thread.is_alive()


def filter_results(results, **kwargs):
    return [file for file in results if match_query(file, **kwargs)]


def sort_results(results, **kwargs):
    def _get_sort_key(file_info, **sort_params):
        sort_key = []
        for key, reverse in sort_params.items():
            if key == 'size':
                sort_key.append((file_info.get(key, 0), reverse))
            elif key == 'created_at':
                sort_key.append((file_info.get(key, datetime.min), reverse))
        return tuple(sort_key)

    if kwargs:
        results.sort(key=lambda file_info: _get_sort_key(file_info, **kwargs))
    return results
