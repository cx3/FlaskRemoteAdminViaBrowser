/*@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@2*/
// params from link to inputs in form
document.addEventListener('DOMContentLoaded', function() {
    var urlParams = new URLSearchParams(window.location.search);

    function hasParam(param) {
        return urlParams.has(param);
    }
    function getParamValue(param) {
        return hasParam(param) ? urlParams.get(param) : '';
    }
    let inputs = document.querySelectorAll('.form-control');

    inputs.forEach(function(input) {
        var paramName = input.id;
        var paramValue = getParamValue(paramName);

        if (paramValue!=='') {
            input.value = paramValue;
            console.log(paramName+"-->"+paramValue);
        }
    });

    let radios = document.querySelectorAll('input[type="radio"]');

    radios.forEach(function(radio){
        var paramName = radio.id;
        var paramValue = getParamValue(paramName);

        if (paramValue!=='') {
            radio.checked = true;
        }
    });

    searchFiles();
});



document.addEventListener('DOMContentLoaded', function() {
    var checkboxes = document.querySelectorAll('.column-checkbox');
    checkboxes.forEach(function(checkbox) {
        checkbox.addEventListener('change', function() {
            var columnId = checkbox.id.replace('_checkbox', '');
            var column = document.getElementById(columnId);

            if (checkbox.checked) {
                column.style.display = '';
            } else {
                column.style.display = 'none';
            }
        });
    });
});




function fullPathToLinkedDirList(path) {
    let dirs = path.split('/');
    let linkedDirs = {};

    for (let i=0;  i<dirs.length - 1;  ++i) {
        linkedDirs[dirs[i]] = dirs.slice(0,i+1).join("/");
    }
    return linkedDirs;
}




function rowClicked(row) {

    var file_info = JSON.parse(row.getAttribute("data-json-text"));

    let modal = new bootstrap.Modal(document.getElementById('gfg'));
    //document.getElementById('modal-title-span').innerHTML = file_info.path;

    let linkedDirs = fullPathToLinkedDirList(file_info.path);
    let x = "{{ url_for('list_dir_route', server_dir='') }}";
    let rootTitle = document.getElementById('badgesDiv');
    rootTitle.innerHTML = "";

    for (let key in linkedDirs) {
        let h5 = document.createElement("h5");
        h5.innerHTML = '<a class="badge text-bg-warning" href="' + x + linkedDirs[key] + ' " target="_blank">' + key + '/</a>';
        rootTitle.appendChild(h5);
    }

    h5 = document.createElement("h5");
    h5.innerHTML = '<span class="badge text-bg-danger" href="' + x + file_info.name + ' ">' + file_info.name + '</span>';
    rootTitle.appendChild(h5);

    let body = document.getElementById('modal-body');

/*<span class="badge rounded-pill bg-primary">Primary</span>
<span class="badge rounded-pill bg-secondary">Secondary</span>
<span class="badge rounded-pill bg-success">Success</span>
<span class="badge rounded-pill bg-danger">Danger</span>
<span class="badge rounded-pill bg-warning text-dark">Warning</span>
<span class="badge rounded-pill bg-info text-dark">Info</span>
<span class="badge rounded-pill bg-light text-dark">Light</span>
<span class="badge rounded-pill bg-dark">Dark</span>*/


    body.innerHTML = "";

    let a = document.createElement("a");
    a.setAttribute("class", "badge rounded-pill bg-success");
    a.textContent = 'Download';
    a.href = "{{ url_for('get_file_route', path='')}}" + file_info.path;
    a.setAttribute("download", file_info.name);
    body.appendChild(a);

let disp = document.getElementById('modal-display-data');

    if (file_info.type === 'document' || file_info.type === 'text') {
        a = document.createElement("a");
        a.setAttribute("class", "badge rounded-pill bg-info");
        a.textContent = 'Edit';
        a.href = "{{ url_for('ace_editor_route', file='')}}" + file_info.path;
        a.setAttribute("target", "_blank");
        body.appendChild(a);

        disp.innerHTML = 'ace';
    }
    if (file_info.type === 'image') {
        let img = document.createElement('img');
        img.setAttribute("src", "{{ url_for('get_file_route', path='')}}" + file_info.path);
        disp.innerHTML = "";
        disp.appendChild(img);
    }
    if (file_info.type === 'audio') {
        disp.innerHTML = 'audio';
    }
    if (file_info.type === 'video') {
        disp.innerHTML = 'video';
    }

    modal.show();
}






var const_status_text = '';


function setStatus() {
    var txt = const_status_text;
    for (var i=0;  i<arguments.length;  ++i) {
        txt += arguments[i] + " ";
    }
    document.getElementById('status-bar-tr').textContent = txt;
}


var socket = io.connect('/custom_search');
var root_dir = '';
var totalPages = 1;


socket.on('search_results', function(data) {
    setStatus("searching started...");
    renderPage(1);
});



socket.on('next_hundred_found', function (data) {
    totalPages = data.found;
    setStatus("pages: " + totalPages + ", total files parsed: " + data.iters + "   ");
});



socket.on('show_sorted', function(data) { 
    document.getElementById('page').value = 1;
    renderPage(1);
});




function renderTable(data) {
    var tbody = document.getElementById('dynamicContent');
    tbody.innerHTML = '';

    let trim_by = document.getElementById('root_dir').value.length;

    function _trim(text) {
        text = text.slice(trim_by);
        let a = '';
        let lsi = text.lastIndexOf('/');
        if (lsi !== -1) {
            a = text.substring(0, lsi + 1);
        } else {
            a = text;
        }
        if (a.length > 30) {
            return '...' + text.slice(-30);
        } else {
            return text;
        }
    }


    data.results.forEach(function(result) {
        var row = document.createElement('tr');

        Object.keys(result).forEach(function(key, index) {
            var cell = document.createElement('td');

            if (key === 'path') {
                let t = _trim(result[key]);
                cell.textContent = t;
                cell.setAttribute('data-trim-text', t);
                cell.setAttribute('data-original-text', result[key]); // Zapisanie oryginalnego tekstu w atrybucie
                cell.addEventListener('mouseover', function() {
                    this.textContent = this.getAttribute('data-original-text'); // Wyświetlenie oryginalnego tekstu przy najechaniu myszą
                });
                cell.addEventListener('mouseout', function() {
                    this.textContent = this.getAttribute('data-trim-text');
                });
            } else if (key === 'created_at') {
                cell.textContent = new Date(result[key]).toLocaleString();
            } else if (key === 'permissions') {
                cell.textContent = translatePermissions(result[key]);
            } else {
                cell.textContent = result[key];
            }
            row.appendChild(cell);
        });

        row.setAttribute('data-json-text', JSON.stringify(result));
        row.addEventListener('dblclick', function() { rowClicked(this); }); // Obsługa podwójnego kliknięcia na wiersz
        tbody.appendChild(row);
    });


    var columnCheckboxes = document.querySelectorAll('.column-checkbox');

    columnCheckboxes.forEach(function(checkbox, index) {
        checkbox.addEventListener('change', function() {
            var columnIndex = index;
            var cells = tbody.querySelectorAll('tr td:nth-child(' + (columnIndex + 1) + ')');

            if (checkbox.checked) {
                cells.forEach(function(cell) {
                    cell.style.display = '';
                });
            } else {
                cells.forEach(function(cell) {
                    cell.style.display = 'none';
                });
            }
        });
    });
}





socket.on('render_new_page', function(data){ renderTable(data); });




var searchThreadStatus = 'ready';



socket.on('search_finished', function(data) {

    if (data.killed) {
        setStatus("Searching thread killed");
    }

    totalPages = data.pages;
    setStatus("Searching finished. Found", data.len, " files with ", data.iters, " iterations, pages count:", data.pages, "pages");

    searchThreadStatus = 'finished';
});


function searchFiles() {
    var formData = {}; // Obiekt przechowujący dane formularza
    var formInputs = document.querySelectorAll('.form-control');

    formInputs.forEach(function(input) {
        formData[input.id] = input.value; // Dodaj wartość inputu do obiektu formData
    });

    // Pobierz wartość strony
    var page = document.getElementById('page').value;

    let radioButtons = document.querySelectorAll('input[type="radio"]');
    let sortby = "";
    radioButtons.forEach(function(radio) {
        if (radio.checked) {
            formData['sortby'] = radio.id;
        }
    });

    // Wyślij dane do serwera
    socket.emit('search_files', {
        root_dir: formData['root_dir'],
        search_params: formData,
        page: page,
    });

    searchThreadStatus = 'working';
    let btn = document.getElementById("searchStop");
    btn.textContent = 'STOP';
    btn.setAttribute('onclick', 'stopThread()');
}



function stopThread() {
    searchThreadStatus = 'ready';
    let btn = document.getElementById("searchStop");
    btn.textContent = 'Search';
    btn.setAttribute('onclick', 'sendForm()');
    socket.emit('stop_thread', {});
}



function renderPage(value) {
    console.log("renderPage(value):  totalPages: " + totalPages);
    if (value <= totalPages) {
        socket.emit('get_page', {page: value, root_dir:root_dir});
    }
}




document.addEventListener('DOMContentLoaded', function() {
    var headers = document.querySelectorAll('th[id^="column_"]');
    headers.forEach(function(header) {
        header.addEventListener('click', function() {
            var columnId = this.id;
            sortTable(columnId);
        });
    });
});

var sortDirection = {}; // Obiekt przechowujący kierunek sortowania dla każdej kolumny





function sortTable(columnId) {

    if (document.getElementById('searchStop').textContent !== 'Search') {
        console.log("wait kurwa");
    }

    // Ustawienie początkowego kierunku sortowania na rosnący, jeśli nie został jeszcze ustawiony dla tej kolumny
    if (!sortDirection[columnId]) {
        sortDirection[columnId] = 'asc';
    } else {
        // Odwróć kierunek sortowania po kolejnym kliknięciu w tę samą kolumnę
        sortDirection[columnId] = sortDirection[columnId] === 'asc' ? 'desc' : 'asc';
    }
    console.log("sorting request");
    socket.emit('sort_and_show', {'column': columnId});
}








function sortTableOnThisPage(columnId) {

    var table, rows, switching, i, x, y, shouldSwitch;
    table = document.getElementById("dynamicTable");
    switching = true;

    // Ustawienie początkowego kierunku sortowania na rosnący, jeśli nie został jeszcze ustawiony dla tej kolumny
    if (!sortDirection[columnId]) {
        sortDirection[columnId] = 'asc';
    } else {
        // Odwróć kierunek sortowania po kolejnym kliknięciu w tę samą kolumnę
        sortDirection[columnId] = sortDirection[columnId] === 'asc' ? 'desc' : 'asc';
    }

    while (switching) {
        switching = false;
        rows = table.rows;

        for (i = 1; i < (rows.length - 1); i++) {
            shouldSwitch = false;
            x = rows[i].getElementsByTagName("TD")[getColumnIndex(columnId)];
            y = rows[i + 1].getElementsByTagName("TD")[getColumnIndex(columnId)];

            var comparison;
            if (columnId.toLowerCase() === 'column_size') {
                comparison = compareNumberValues(x.innerHTML.toLowerCase(), y.innerHTML.toLowerCase());
            } else {
                comparison = compareValues(x.innerHTML.toLowerCase(), y.innerHTML.toLowerCase());
            }

            // Sprawdź, czy należy zamienić pozycje wierszy
            if ((sortDirection[columnId] === 'asc' && comparison > 0) ||
                (sortDirection[columnId] === 'desc' && comparison < 0)) {
                shouldSwitch = true;
                break;
            }
        }

        if (shouldSwitch) {
            rows[i].parentNode.insertBefore(rows[i + 1], rows[i]);
            switching = true;
        }
    }
}

// Funkcja pomocnicza do porównywania wartości
function compareValues(a, b) {
    if (a === b) {
        return 0;
    }
    return a > b ? 1 : -1;
}

// Funkcja pomocnicza do porównywania liczb
function compareNumberValues(a, b) {
    return parseFloat(a) - parseFloat(b);
}

function getColumnIndex(columnId) {
    var headers = document.querySelectorAll('th[id^="column_"]');
    for (var i = 0; i < headers.length; i++) {
        if (headers[i].id === columnId) {
            return i;
        }
    }
    return -1;
}



function translatePermissions(st_mode) {
    const S_IRUSR = 0o400; // 0400 -> Prawo odczytu dla właściciela
    const S_IWUSR = 0o200; // 0200 -> Prawo zapisu dla właściciela
    const S_IXUSR = 0o100; // 0100 -> Prawo wykonania dla właściciela
    const S_IRGRP = 0o40;  // 0040 -> Prawo odczytu dla grupy
    const S_IWGRP = 0o20;  // 0020 -> Prawo zapisu dla grupy
    const S_IXGRP = 0o10;  // 0010 -> Prawo wykonania dla grupy
    const S_IROTH = 0o4;   // 0004 -> Prawo odczytu dla innych
    const S_IWOTH = 0o2;   // 0002 -> Prawo zapisu dla innych
    const S_IXOTH = 0o1;   // 0001 -> Prawo wykonania dla innych

    let permissions = '';

    // Prawa dostępu dla właściciela
    if (st_mode & S_IRUSR) permissions += 'r';
    else permissions += '-';
    if (st_mode & S_IWUSR) permissions += 'w';
    else permissions += '-';
    if (st_mode & S_IXUSR) permissions += 'x';
    else permissions += '-';

    // Prawa dostępu dla grupy
    if (st_mode & S_IRGRP) permissions += 'r';
    else permissions += '-';
    if (st_mode & S_IWGRP) permissions += 'w';
    else permissions += '-';
    if (st_mode & S_IXGRP) permissions += 'x';
    else permissions += '-';

    // Prawa dostępu dla innych
    if (st_mode & S_IROTH) permissions += 'r';
    else permissions += '-';
    if (st_mode & S_IWOTH) permissions += 'w';
    else permissions += '-';
    if (st_mode & S_IXOTH) permissions += 'x';
    else permissions += '-';

    return permissions;
}

/* Przykład użycia
var st_mode = 0o755; // np. wynik z stat_info.st_mode
var permissions = translatePermissions("33206");
console.log(permissions); // Wyświetli "rwxr-xr-x"   */
