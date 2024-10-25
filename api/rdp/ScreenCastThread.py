import io
import time
import base64
import threading

import pyautogui
from PIL import ImageDraw

from api.app.routes import socketio
from api.app.utils import Singleton


class ScreenCastThread(metaclass=Singleton):
    def __init__(self, guest_casting=False):  # admin_required_decorator: Callable
        print('ScreenCastThread.__init__()')
        self.stop_event = threading.Event()
        # self.admin_required_decorator = admin_required_decorator

        self.guest_casting = guest_casting
        self.thread = threading.Thread(target=self.run, args=(), kwargs={})
        self.thread.daemon = False

        self._admin_connected = False
        self._guest_connected = False

    def set_admin_connected(self, state: bool):
        self._admin_connected = state

    def set_guest_connected(self, state: bool):
        self._guest_connected = state

    def set_guest_casting(self, new_state=False):
        self.guest_casting = new_state

    def run(self):
        print('@@@@@@@@@@@@@ ScreenCastThread run() invoked')
        while not self.stop_event.is_set():
            screenshot = pyautogui.screenshot()
            x, y = pyautogui.position()
            draw = ImageDraw.Draw(screenshot)
            radius = 20
            draw.ellipse((x - radius, y - radius, x + radius, y + radius), outline="green", width=2)
            img_bytes = io.BytesIO()
            screenshot.save(img_bytes, format='PNG')
            img_bytes = img_bytes.getvalue()
            img_base64 = base64.b64encode(img_bytes).decode('utf-8')

            socketio.emit('image', {'image': img_base64}, namespace='/rdp')

            if self.guest_casting:
                socketio.emit('image', {'image': img_base64}, namespace='/cast')

            time.sleep(0.5)
        print('@@@@@@@@@@@@@ ScreenCastThread run() infinity while-loop finished')

    def start(self):
        print('ScreenCastThread started')
        self.thread.start()

    def stop(self):
        print('ScreenCastThread stopped')
        self.stop_event.set()

    def join(self):
        print('ScreenCastThread joined')
        self.thread.join()

    def is_running(self):
        alive = self.thread.is_alive()
        print(f'ScreenCastThread status: {alive}')
        return alive

    def __del__(self):
        self.stop()
