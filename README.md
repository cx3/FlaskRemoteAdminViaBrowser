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

--------------------------------------------------------------------------------------------------------------

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

--------------------------------------------------------------------------------------------------------------


/cmd - emulator (!!!)  of server's side terminal - not always commands works however its syntax is correct!

 * Working under remote Python debugger, executed code inspector, simple Python IDE

--------------------------------------------------------------------------------------------------------------


/db - Early version of browser based database editor for most popular database types like: SQLite, PostgreSQL
  MariaDB, powered by SQLAlchemy and Pandas Python's libraries. Admin can create new tables using HTML forms,
  add new entries, edit them, display tables in simple way or with expandable foreign keys - with possibility
  to edit records in simplified way or with foreign keys.  It is just a beginning of advanced database editor
  known from systems like phpMyAdmin. Using any databases type will not need SQLs language skills due to good 
  God had sent people keyboard and mouse in previous  century for navigating  through windowed world of GUI's. 

 * server:port/db  - main database editor view, almost all CRUD functions database Admin needs is here

 * db/tables   -  HTML with links to tables in current database

 * db/info/<table_name>  -  JSON format of tables in current database

 * db/info/columns/<table_name>  -  JSON format, column names of table

 * db/info/structure/<table_name>  - JSON format, list of dicts like:  
        info = {
            'name': col_name,
            'type': col_info.type,
            'unique': col_info.unique,
            'default': col_info.default,
            'nullable': col_info.nullable,
            'constraints': col_info.constraints,
            'primary_key': col_info.primary_key,
            'foreign_keys': col_info.foreign_keys,
            'autoincrement': col_info.autoincrement
        }

 * db/info/primaries  -  JSON format, list of all foreign references   [table_name.primary_column...]

 * db/info/content/<table_name>

    JSON format,  all table content with info about foreign_keys, primary_keys, all records, structure of
    columns in choosen table. It is used by other routes to render table view and further CRUD operations

 * db/add_record/<table_name>   -  HTML form for adding new record with foreign keys handling

 * db/get_record/<table_name>/<pk>/<pk_value>  -   JSON, fetch record by table_name, existing primary_key  and
   
   value under that primary key

 * db/table/<table_name>  -  HTML form with basic table view (unfolded foreign keys), add or edit records

 * db/table/fk/<table_name>  -  HTML form for browsing and editing tables having foreign keys

 * db/edit/<table_name>/<primary_key>/<value>  -  HTML form for updating records with foreign keys

 * db/new_table
 * db/create_table  -  HTML form for creating tables that columns can reference to other tables using their
                       primary keys

 * db/upload  [method POST]  -  utility for uploading CSV/XLS/XLSX/db files with content that can be loaded to
                                current or new databases  (idea just started to become a code)

 * db/uploaded   db/uploaded?file=/path/to/uploaded/file

   Routes for adding new databases or creating tables from common tabelaric content or ready databases 


--------------------------------------------------------------------------------------------------------------
 
/rdp - Remote Desktop Protocol

 * After loging with another credencials as an administrator, one  can control  server's mouse and keyboard to 
 work with server by the browser.  The  configuration panel allows to manage other users to see the controlled 
 screen. Flask_SocketIO is used for broadcasting screen of server machine. Remember to switch RDP off when you
 do not need it - casting screen is run on the separated thread that eats resources.
 
 Lot of things to-do that even no sense to describe them :)

 Mouse and keyboard enabled and tested, yupi!
