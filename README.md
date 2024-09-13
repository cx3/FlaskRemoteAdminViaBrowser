Flask Remote Admin via web browser - like a pro

### BEFORE YOU pip install -r requirements.txt ###

If you want to run this server on machine that does not provide GUI (no windows but console only), you will not be 
able to run RDP plugin - so therefore in [root]/server.py comment lines 6 and 10.  In requirements.txt delete line
with pyautogui or it will install tons of packages to your machine for using windows GUI!!!   Instead of mouse and
keyboard you have flexible server files navigation, cmd-line util, and simple editor with syntaxt highlightings :)


By default server needs authentication (user: admin, pass: admin). Password is hashed before sending it to server.
Authentication is session based - switching server off and on needs login again. Remote Desktop plugin at /rdp/*  routes
needs another authentication.  Very basic session control - little bit unsafe. Switch server off when you do not need it
working. Remember - this application is for learning people how to develop simple Flask applications.

For testing purposes you can switch auth process off by changing:
/api/app/routes.py    LOC 21
app.config['LOGIN_REQUIRED_SECURE_DECORATOR'] = True    into False   



Short info about plugins:



/app - main application routes - explore files in browser like in windowed based operating system

 * listing files in folders
 
 * server background thread for files searcher that works fine even in very deep and large files structure
   every new found files are shown on the fly in client browser

 * browsing and extracting various archives formats

 * two side file transfer - uploading and downloading files
 
 * remote downloading files like Linux wget command
 
 * packing files and directories for downloading them from server to client (to do :) )
 
 * simple text editor with syntax highlighting for most know computer languages
 
 * audio/video media player
 
 * html photo editor

 * html photo explorer


/cmd - emulator (!!!)  of server's side terminal - not always commands works however its syntax is correct!

 * Working under remote Python debugger, executed code inspector, simple Python IDE

/db

 * SQLite/Postgres dynamic database editor - in future
 
/rdp - Remote Desktop Protocol

 * After loging with another credencials as an administrator, one  can control  server's mouse and keyboard to 
 work with server by the browser.  The  configuration panel allows to manage other users to see the controlled 
 screen. Flask_SocketIO is used for broadcasting screen of server machine. Remember to switch RDP off when you
 do not need it - casting screen is run on the separated thread that eats resources.
 
 Lot of things to-do that even no sense to describe them :)
