from flask import Blueprint, current_app, render_template, request, redirect, url_for
from sqlalchemy import inspect


db = dict()


def get_db():
    app = current_app
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///C:/proj/some_sqlite.db'
    db['instance'] = app.config['db_instance']
    db['instance'].reflect()


def get_tables():
    tables = []
    for table_name in db['instance'].metadata.tables.keys():
        tables.append(table_name)
    return tables


bp = Blueprint('db', __file__, template_folder='api/db/templates')


@bp.route('/', methods=['POST', 'GET'])
def db_index_route():
    if 'instance' not in db:
        get_db()
        db['tables'] = get_tables()

    return redirect(url_for('db.get_tables_route'))


def get_records(table_name):
    db_ = db['instance']
    table = db_.metadata.tables[table_name]
    model_class = type(table_name.capitalize(), (db_.Model,), {"__table__": table})
    model_class: db_.Model
    records = model_class.query.all()
    return records


def get_model_by_table_name(table_name):
    '''class Model(db_.Model):
        __tablename__ = table_name
        id = db_.Column(db_.Integer, primary_key=True)
        # Dodaj inne kolumny zgodnie ze strukturą tabeli

    return Model'''
    return db['instance'].metadata.tables[table_name]


@bp.route('/get_record/<table_name>/<int:id_>')
def get_record_route(table_name, id_):
    # Pobieranie modelu na podstawie nazwy tabeli
    Model = get_model_by_table_name(table_name)

    # Wykonanie zapytania, aby znaleźć rekord o określonym id
    record = Model.query.get(id_)

    if record:
        return f'Record found: {record}'
    else:
        return 'Record not found'


def get_record(table_name, unique_id_key_name: str, unique_id_key_value: int) -> dict:
    if globals()['db'] is None:
        db_index_route()
    db_ = db['instance']
    table = db_.metadata.tables[table_name]
    model_class: db_.Model = type(table_name.capitalize(), (db_.Model,), {"__table__": table})

    return model_class.query.column(unique_id_key_name)


@bp.route('/test')
def test_route():
    return str(get_record('OrderDetails', 'OrderId', 10251))


# Funkcja do pobierania nazw kolumn z tabeli
def get_columns(table_name):
    db_ = db['instance']
    table = db_.metadata.tables[table_name]
    return table.columns.keys()


@bp.route('/tables')
def get_tables_route():
    if globals()['db'] is None:
        db_index_route()
    tables = get_tables()
    print(tables)
    return render_template('db_tables.html', tables=tables)


@bp.route('/table/')
def view_table_no_arg():
    return redirect(url_for('db.get_tables_route'))


@bp.route('/table/<table_name>')
def view_table(table_name):
    if not table_name or table_name == '':
        return redirect(url_for('db.get_tables_route'))

    records = get_records(table_name)
    columns = get_columns(table_name)

    return render_template('db_table.html', table_name=table_name, records=records, columns=columns)


@bp.route('/table_ext/<table_name>')
def extended_table_view(table_name):
    if not table_name or table_name == '':
        return redirect(url_for('db.get_tables_route'))
    db_index_route()
    db_ = globals()['db']

    # model: db_.Model = db_.Model.metadata.tables[table_name]
    # print(dir(model))

    # if not table_name in globals().keys() !!!!

    model: db_.Model = type(table_name.capitalize(), (db_.Model,), {'__tablename__': table_name})

    # Pobranie wszystkich foreign keys dla danego modelu
    inspector = inspect(db_.engine)
    foreign_keys = inspector.get_foreign_keys(table_name)

    print('foreign_keys', foreign_keys)

    # Pobranie nazw kolumn dla danego modelu
    columns = get_columns(table_name)

    # Przygotowanie danych dla widoku
    data = []
    for record in model.query.all():
        row = {}
        for column in columns:
            if column in foreign_keys:
                print('column in foreign keys: ', column)
                referenced_table_name = foreign_keys[column][0]['referred_table']
                referenced_table = db_.Model.metadata.tables[referenced_table_name]
                foreign_key_value = getattr(record, column)
                referenced_record = referenced_table.query.get(foreign_key_value)
                row[column] = referenced_record
            else:
                row[column] = getattr(record, column)
        data.append(row)

    return render_template('db_extended_table.html', table_name=table_name, columns=columns, data=data)


@bp.route('/edit/<table_name>/<id>', methods=['GET', 'POST'])
def edit_record(table_name, id):
    if globals()['db'] is None:
        db_index_route()
    db_ = db['instance']
    table = db_.metadata.tables[table_name]
    model_class = type(table_name.capitalize(), (db_.Model,), {"__table__": table})

    print(dir(model_class))

    record = model_class.query.get_or_404(id)

    if request.method == 'POST':
        for column in table.columns:
            setattr(record, column.name, request.form[column.name])
        try:
            db_.session.commit()
            return redirect(url_for('db.view_table', table_name=table_name))
        except:
            return 'Wystąpił błąd podczas edycji rekordu.'

    else:
        columns = get_columns(table_name)
        return render_template('db_edit.html', table_name=table_name, record=record, columns=columns)

# AI IE EDGE / CHAT GPT 4   POWERED CODE:

