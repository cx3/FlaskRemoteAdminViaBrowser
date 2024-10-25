import os
from functools import wraps

from flask import Blueprint, render_template, request, redirect, url_for, jsonify
from sqlalchemy import select
from werkzeug.utils import secure_filename

from api.app.utils import slash
from api.db.db_dynamic import alchemic
from api.db.db_csv_helpers import analyze_csv_header_and_types, csv_into_alchemic_database


bp = Blueprint('db', __file__, template_folder='api/db/templates')


"""
    TODO: ALL /db/ NEEDS ONE BIG REFACTORING !!!!!!!!!! BIG BURDEL HERE
"""


def set_db(f):
    """
    For future purposes - switching databases, connecting to other database servers, etc
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        return f(*args, **kwargs)
    return decorated_function


def get_records(table_name):
    return alchemic.all_records(table_name)


def get_record(table_name, unique_id_key_name: str, unique_id_key_value: int) -> dict:
    return alchemic.find_records(table_name, unique_id_key_name, unique_id_key_value)


def get_columns(table_name):
    return alchemic.column_names(table_name)


def get_primary_keys(table_name):
    return alchemic.get_primary_keys(table_name)


def get_foreign_key_names(table_name):
    result = []
    for _ in alchemic.get_foreign_keys_dict(table_name, to_str=True):
        result.extend(list(_.keys()))
    return list(set(result))


@bp.route('/upload', methods=['POST'])
def upload_route():
    if request.method == 'POST':
        if 'file' not in request.files:
            return jsonify(response={'msg': 'No file part'}), 400

        custom_upload_dir = slash(os.path.join(os.getcwd(), 'api/db/dbs/'))
        upload_dir = request.form.get('dest_dir', custom_upload_dir)

        if not os.path.isdir(upload_dir):
            upload_dir = custom_upload_dir

        file = request.files['file']
        if file.filename == '':
            return jsonify(response={'msg': 'No selected file'}), 400
        if file:
            filename = secure_filename(file.filename)
            file.save(os.path.join(upload_dir, filename))
            return jsonify({'msg': 'File successfully uploaded', 'filename': filename}), 200
    return jsonify({"msg": "error"})


@bp.route('/uploaded', methods=['GET', 'POST'])
def uploaded_route():
    if request.method == 'GET':
        file = request.args.get('file', False)
        if file:
            file = slash(file)
            short_name = file.split('/')[-1].split('.')[0]
            ext = file.split('.')[-1].lower()

            if ext == 'csv':
                return render_template(
                    'db_uploaded_csv.html',
                    selected_file=file,
                    short_name=short_name,
                    table_names=alchemic.table_names(),
                    file_info=analyze_csv_header_and_types(file)
                )
        return render_template('db_all_uploaded_files.html')

    if request.method == 'POST':
        args = request.json
        file = args.get('selected_file')
        new_table_name = args.get('new_table_name'),
        primary_keys = args.get('primary_keys')
        autoincrement_keys = args.get('autoincrement_keys')

        if not new_table_name:
            return jsonify({'msg': 'Empty table name'})
        if not primary_keys:
            return jsonify({'msg': 'No primary keys selected'})

        if isinstance(new_table_name, (list, tuple)):
            new_table_name = new_table_name[0]

        result = csv_into_alchemic_database(file, new_table_name, alchemic, primary_keys, autoincrement_keys)
        print('result>', result)
        if result.get('status', False) == 'ok':
            return jsonify(result), 200
        return jsonify(result), 404


@set_db
@bp.route('/', methods=['POST', 'GET'])
def db_index_route():
    return render_template('db_index.html', server_dir=slash(os.getcwd()))


@bp.route('/tables')
def get_tables_route():
    return render_template('db_tables.html', tables=alchemic.table_names())


@bp.route('/info/table_names')
def view_info_about_tables_route():
    return jsonify({'result': alchemic.table_names()})


@bp.route('/info/columns/<table_name>')
def view_info_about_columns_route(table_name=''):
    if table_name:
        if table_name in alchemic.table_names():
            return jsonify({'result': alchemic.column_names(table_name)})
    return jsonify({'result': 'error'})


@bp.route('/info/structure/<table_name>')
def view_info_structure_table_route(table_name=''):
    try:
        columns = alchemic.table_structure(table_name)
        return jsonify(columns), 200
    except Exception as e:
        return jsonify({"error": str(type(e)) + ':  ' + str(e)}), 400


@bp.route('/info/primaries')
def view_info_primaries_route():
    result = []
    for table_name in alchemic.table_names():
        for next_info in alchemic.table_structure(table_name):
            if 'primary_key' in next_info:
                result.append(f"{table_name}.{next_info['name']}")
    return jsonify({'result': result})


@bp.route('/info/content/<table_name>', methods=['GET'])
def get_table_structure(table_name):

    def parse_fk(data):
        result = {}
        for entry in data:
            if 'foreign_keys' in entry:
                result[entry['name']] = str(entry['foreign_keys']).split("('")[1].split("')")[0]
        return result

    columns = alchemic.table_structure(table_name, True)
    records = alchemic.all_records(table_name)
    primary = get_primary_keys(table_name)
    foreign = parse_fk(columns)

    for i in range(len(records)):
        if '_sa_instance_state' in records[i]:
            del records[i]['_sa_instance_state']

    return jsonify({'columns': columns, 'records': records, 'foreign': foreign, 'primary': primary})


@bp.route('/add_record/<table_name>', methods=['POST', 'GET'])
def add_record_to_table_route(table_name=''):
    if request.method == 'GET':
        columns = alchemic.table_structure(table_name)
        return render_template('db_table_add_record.html', table_name=table_name, columns=columns)
    if request.method == 'POST':
        data = request.json
        result = alchemic.add_new_record(table_name, data)
        if result.get('done', False):
            return result, 200
        return result, 400


@bp.route('/get_record/<table_name>/<primary_key_name>/<int:uid>')
def get_record_by_pk_and_uid(table_name: str, primary_key_name: str, uid: int):
    model_class = alchemic.get_model_by_table_name(table_name)
    if not model_class:
        return f'Table {table_name} does not exist', 404

    uid = int(uid)
    query = select(model_class.__table__).where(getattr(model_class, primary_key_name) == uid)

    with alchemic.engine.connect() as conn:
        result = conn.execute(query)
        record = result.fetchone()

    if record:
        return {col.name: value for col, value in zip(model_class.__table__.columns, record)}, 200
    return 'Record not found', 404


@bp.route('/table/<table_name>')
def view_table_route(table_name):
    if not table_name or table_name == '':
        return redirect(url_for('db.get_tables_route'))

    records = get_records(table_name)
    columns = get_columns(table_name)
    primary = get_primary_keys(table_name)
    foreign = alchemic.get_foreign_keys_dict(table_name, to_str=True)

    columns_names = []
    for column in columns:
        name = str(column).split('.')[-1]
        columns_names.append(name)

    return render_template(
        'db_table.html',
        table_name=table_name,
        records=records,
        columns=columns_names,
        primary=primary,
        foreign=foreign
    )


@bp.route('/table/fk/<table_name>')
def view_table_ext_fk_route(table_name):
    if not table_name or table_name == '':
        return redirect(url_for('db.get_tables_route'))
    records = alchemic.session.query(alchemic.get_model_by_table_name(table_name)).all()
    columns = alchemic.column_names(table_name)
    primary_keys = alchemic.get_primary_keys(table_name)
    foreign_keys = alchemic.get_foreign_keys_dict(table_name, to_str=True)
    expanded_records = []

    for record in records:
        record_dict = {col.name: getattr(record, col.name) for col in record.__table__.columns}

        for pk in primary_keys:
            expanded_record = alchemic.get_record_by_pk_expand_fk(table_name, pk, record_dict[pk])
            if expanded_record:
                expanded_records.append(expanded_record)
            else:
                expanded_records.append(record_dict)

    return render_template(
        'db_table_fk.html',
        table_name=table_name,
        records=expanded_records,
        primary=primary_keys,
        foreign=foreign_keys,
        columns=[str(col).split('.')[-1] for col in columns]
    )


@bp.route('/edit/<table_name>/<primary_key_name>/<int:uid>', methods=['GET', 'POST'])
def edit_record_by_primary_route(table_name, primary_key_name, uid):
    model_class = alchemic.get_model_by_table_name(table_name)
    uid = int(uid)
    query = select(model_class.__table__).where(getattr(model_class, primary_key_name) == uid)
    with alchemic.engine.connect() as conn:
        result = conn.execute(query)
        record = result.fetchone()

    if request.method == 'GET':
        columns = get_columns(table_name)
        columns_names = []

        for column in columns:
            name = str(column).split('.')[-1]
            columns_names.append(name)

        primary = get_primary_keys(table_name)
        foreign = get_foreign_key_names(table_name)

        return render_template(
            'db_edit.html',
            table_name=table_name,
            record=record,
            primary=primary,
            foreign=foreign,
            columns=columns_names,
        )

    if request.method == 'POST':
        print('editing, post, request.json:', request.json)
        form = request.json
        form.pop(primary_key_name)

        try:
            if alchemic.update_record_by_pk(table_name, primary_key_name, uid, **form):
                return jsonify({'ok': 'Record updated successfully'}), 200
        except (TypeError, NameError) as e:
            return jsonify({'error': f'Error: {e}'}), 404


@bp.route('/new_table', methods=['GET', 'POST'])
@bp.route('/create_table', methods=['GET', 'POST'])
def new_table_route():
    if request.method == 'GET':
        return render_template('db_new_table.html')
    if request.method == 'POST':
        form = request.json
        table_name = form.get('table_name', False)

        if not table_name or table_name == '':
            return jsonify({'error': 'Empty table name'}), 404

        if table_name in alchemic.table_names():
            return jsonify({'error': f'Table {table_name} exists'}), 404

        columns = form.get('columns', False)
        if not columns:
            return jsonify({'error:' 'Empty columns'}), 404

        has_primary = False

        for i in range(len(columns)):
            column = columns[i]
            print('column:', column)
            if 'name' not in column:
                return jsonify({'error': 'Empty column name'}), 404
            if 'type' not in column:
                return jsonify({'error': 'Empty column type'}), 404
            if 'primary_key' in column:
                has_primary = True
            if 'max_length' in column:
                try:
                    column['max_length'] = int(column['max_length'])
                except ValueError:
                    column['max_length'] = False
            columns[i] = column

        if not has_primary:
            return jsonify({'error': 'No primary key'}), 404

        return alchemic.create_or_alter_table(table_name, *columns)
