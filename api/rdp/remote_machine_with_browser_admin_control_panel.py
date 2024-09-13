import os
import io
import time
import base64
import threading

from functools import wraps

from flask import Blueprint, render_template, request, send_from_directory
from werkzeug.utils import secure_filename

from PIL import ImageDraw
import pyautogui

from api.app.routes import socketio


pg = {'methods': ['POST', 'GET']}


config = {
    'admin_login': 'a',
    'admin_pass': 'a',
    'spectators': {'user1': 'pass1', 'user2': 'pass2'},
    'spectators_allowed': False,
    'spectators_allowed_without_password': False,
    'forbidden_ips': ["127.0.0.1"],

    'host': '0.0.0.0',
    'port': 5000,
    'debug': True,
    'allow_unsafe_werkzeug': True,

    'logged_users': {},
    'last_shot': time.time()
}


bp = Blueprint()


def capture_screen():
    while 1:
        # Capture the screen
        screenshot = pyautogui.screenshot()
        # Get the mouse position
        x, y = pyautogui.position()
        # Draw a green circle around the mouse cursor
        draw = ImageDraw.Draw(screenshot)
        radius = 20
        draw.ellipse((x - radius, y - radius, x + radius, y + radius), outline="green", width=2)
        # Convert the image to bytes
        img_bytes = io.BytesIO()
        screenshot.save(img_bytes, format='PNG')
        img_bytes = img_bytes.getvalue()

        # Encode the image to base64
        img_base64 = base64.b64encode(img_bytes).decode('utf-8')

        # Emit the image to the clients
        socketio.emit('image', {'image': img_base64}, namespace='/cast')
        socketio.emit('image', {'image': img_base64}, namespace='/rdp')

        # Wait for 0.5 seconds
        time.sleep(0.5)


def is_admin(client_ip: str) -> bool:
    for user, ip in config['logged_users'].items():
        if client_ip == ip:
            if user == config['admin_login']:
                return True
    return False


def is_spectator(client_ip: str) -> bool:
    for user, ip in config['logged_users'].items():
        if client_ip == ip:
            if user in config['spectators'].keys():
                return True
    return False


def is_logged(client_ip: str) -> bool:
    result = client_ip in config['logged_users'].values()
    # print('is_logged:', result)
    return result


def is_forbidden_ip(ip: str) -> bool:
    return ip in config['forbidden_ips']


def js_redirect(link: str) -> str:
    link = link if link[0] == '/' else '/' + link
    return f"<script>window.location='{link}';</script>"


