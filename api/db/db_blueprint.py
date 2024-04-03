from flask import Blueprint, current_app, render_template, request, redirect, url_for
from flask_sqlalchemy import SQLAlchemy


def get_db():
    app = current_app.config
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite://C/proj/some_sqlite.db'
    db = SQLAlchemy()
    # Automatyczne wczytanie modeli i relacji
    db.reflect()
    return db


bp = Blueprint('db', __file__, template_folder='api/db/templates')



db=get_db()



'''class Task(db.Model):
    __table__ = db.Model.metadata.tables['task']'''


# Funkcja do pobierania listy tabel
def get_tables():
    tables = []
    for table_name in db.metadata.tables.keys():
        tables.append(table_name)
    return tables


# Funkcja do pobierania rekordów z tabeli
def get_records(table_name):
    table = db.metadata.tables[table_name]
    model_class = type(table_name.capitalize(), (db.Model,), {"__table__": table})
    model_class: db.Model
    records = model_class.query.all()
    return records


# Funkcja do pobierania nazw kolumn z tabeli
def get_columns(table_name):
    table = db.metadata.tables[table_name]
    return table.columns.keys()


@bp.route('/')
def index():
    tables = get_tables()
    return render_template('index.html', tables=tables)


@bp.route('/table/<table_name>')
def view_table(table_name):
    records = get_records(table_name)
    columns = get_columns(table_name)
    return render_template('table.html', table_name=table_name, records=records, columns=columns)


@bp.route('/edit/<table_name>/<int:id>', methods=['GET', 'POST'])
def edit_record(table_name, id):
    table = db.metadata.tables[table_name]
    model_class = type(table_name.capitalize(), (db.Model,), {"__table__": table})
    record = model_class.query.get_or_404(id)

    if request.method == 'POST':
        for column in table.columns:
            setattr(record, column.name, request.form[column.name])
        try:
            db.session.commit()
            return redirect(url_for('view_table', table_name=table_name))
        except:
            return 'Wystąpił błąd podczas edycji rekordu.'

    else:
        columns = get_columns(table_name)
        return render_template('edit.html', table_name=table_name, record=record, columns=columns)
