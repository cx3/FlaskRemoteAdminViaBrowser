from datetime import datetime
from typing import Any, Dict, List, Set

from sqlalchemy.exc import NoResultFound, ArgumentError, SQLAlchemyError
from sqlalchemy import (create_engine, select, MetaData, Column, Integer, String, Float, Boolean, DateTime, Text,
                        ForeignKey, BigInteger, Numeric, Date, Time, Interval, JSON, Table)
from sqlalchemy.orm import scoped_session, sessionmaker, declarative_base, registry

from api.app.utils import Singleton
from flask import jsonify


def map_column_type(column_type, max_length=None):
    if column_type == "Integer":
        return Integer
    elif column_type == "String" and max_length:
        return String(max_length)
    elif column_type == "String":
        return String
    elif column_type == "Float":
        return Float
    elif column_type == "Boolean":
        return Boolean
    elif column_type == "DateTime":
        return DateTime
    elif column_type == "Text":
        return Text
    elif column_type == "BigInt":
        return BigInteger
    elif column_type == "Numeric":
        return Numeric
    elif column_type == "Date":
        return Date
    elif column_type == "Time":
        return Time
    elif column_type == "Interval":
        return Interval
    elif column_type == "JSON":
        return JSON
    elif column_type == 'ForeignKey':
        return ForeignKey
    # Add more types as needed
    else:
        raise ValueError(f"Unsupported column type: {column_type}")


def convert_value_to_column_type(column_type, val):
    if isinstance(column_type, Integer):
        return int(val) if val is not None else None
    elif isinstance(column_type, Float):
        return float(val) if val is not None else None
    elif isinstance(column_type, Boolean):
        return bool(val)
    elif isinstance(column_type, DateTime):
        return datetime.strptime(val, "%a, %d %b %Y %H:%M:%S %Z") if val else None
        # return datetime.strptime(val, '%Y-%m-%d %H:%M:%S') if val else None
    elif isinstance(column_type, Date):
        return datetime.strptime(val, '%Y-%m-%d').date() if val else None
    elif isinstance(column_type, Time):
        return datetime.strptime(val, '%H:%M:%S').time() if val else None
    elif isinstance(column_type, String):
        return str(val) if val is not None else None
    else:
        return val


class DynamicAlchemic(metaclass=Singleton):
    def __init__(self, db_uri):
        self.engine = create_engine(db_uri)
        self.metadata = MetaData()
        self.metadata.reflect(bind=self.engine)
        self.Base = declarative_base()
        self.session = sessionmaker(bind=self.engine)()

        self.tables_dict = {table_name: self.metadata.tables[table_name] for table_name in self.metadata.tables}
        self.models_dict = {}
        self.mapper_registry = registry()

        for key in self.tables_dict.keys():
            self.get_model_by_table_name(key)

    def get_table_by_name(self, table_name: str):
        return self.tables_dict.get(table_name, False)

    def get_model_by_table_name(self, table_name: str):
        if table_name in self.models_dict:
            return self.models_dict[table_name]

        if table_name in self.tables_dict:
            table = self.tables_dict[table_name]
            primary_keys = [col for col in table.columns if col.primary_key]

            if not primary_keys:
                raise Exception(f"Table '{table_name}' has not defined primary key.")

            model_name = table_name.capitalize()
            model_class = type(model_name, (self.Base,), {'__table__': table})
            try:
                self.mapper_registry.map_imperatively(model_class, table)
            except ArgumentError:
                pass

            self.models_dict[table_name] = model_class
            return model_class
        raise NameError

    def get_models(self):
        return self.models_dict.copy()

    def table_names(self):
        return tuple(self.tables_dict.keys())

    def column_names(self, table_name):
        if table_name not in self.tables_dict:
            return f"Table with name '{table_name}' does not exists."
        return [str(_) for _ in  self.tables_dict[table_name].columns]

    def column_types(self, table_name):
        if table_name not in self.tables_dict:
            return f"Table named '{table_name}' does not exists."
        return self.tables_dict[table_name]

    def table_structure(self, table_name, values_to_str=True, remove_odds=True):
        result = []
        model = self.get_model_by_table_name(table_name)
        if not model:
            raise NameError(f'No such table {table_name}')

        for col_name, col_info in model.__table__.columns.items():
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

            if remove_odds:
                removed = {}
                for key, value in info.items():
                    if key == 'primary_key' and not value:
                        continue
                    if value is None or value == set():
                        continue
                    removed[key] = value
                info = removed

            if values_to_str:
                info = {k: str(v) for k, v in info.items()}

            result.append(info)
        return result

    def get_primary_keys(self, table_name) -> List[str]:
        result = []
        for column in self.table_structure(table_name, False, True):
            if column.get('primary_key', False):
                result.append(column['name'])
        return result

    def get_foreign_keys_dict(self, table_name, to_str=False) -> List[Dict[str, Set[Any]]]:
        """
        Returns dict that keys are table fields name with foreign key reference to table
        Passing to_str==False returns dict that values are SQLAlchemy instances of ForeignKey
        Passing to_str==True returns dict that values are Python's str of
        """
        result = []
        for column in self.table_structure(table_name, False):
            fk = column.get('foreign_keys', False)
            if fk:
                if to_str:
                    fk = [_.parent.name + '.' + _.column.name for _ in fk]
                result.append({column['name']: fk})
        return result

    def get_foreign_keys(self, table_name) -> List[str]:
        result = []
        for _ in self.get_foreign_keys_dict(table_name, False):
            result.extend(_)
        return list(set(result))

    def get_record_by_pk(self, table_name: str, primary_key_name: str, value: int):
        model_class = self.get_model_by_table_name(table_name)
        if not model_class:
            return None

        value = int(value)
        query = select(model_class.__table__).where(getattr(model_class, primary_key_name) == value)

        with alchemic.engine.connect() as conn:
            result = conn.execute(query)
            record = result.fetchone()

        if record:
            return {col.name: value for col, value in zip(model_class.__table__.columns, record)}, 200
        return None

    def get_record_by_pk_expand_fk(self, table_name: str, primary_key: str, value: Any):
        """
        Pobiera rekord z tabeli o nazwie `table_name` na podstawie wartości kolumny `column_name`
        oraz zwraca dane z rozwiniętymi kluczami obcymi.

        Args:
            table_name (str): Nazwa tabeli, z której chcemy pobrać rekord.
            primary_key (str): Nazwa kolumny, po której szukamy rekordu.
            value (Any): Wartość, która ma być porównana w `column_name`.

        Returns:
            dict: Słownik z danymi rekordu oraz rozwiniętymi wartościami kluczy obcych.
        """
        model_class = self.get_model_by_table_name(table_name)
        if not model_class:
            return None

        with self.engine.connect() as conn:
            query = select(model_class.__table__).where(getattr(model_class, primary_key) == value)
            result = conn.execute(query)
            record = result.fetchone()

            if not record:
                return None

            record_dict = {col.name: value for col, value in zip(model_class.__table__.columns, record)}
            foreign_keys = self.get_foreign_keys_dict(table_name)

            for fk in foreign_keys:
                fk_column_name = list(fk.keys())[0]  # Column name with foreign key
                fk_column = fk[fk_column_name]  # ForeignKey object

                if record_dict.get(fk_column_name):
                    fk_table_name = list(fk_column)[0].column.table.name
                    fk_table_pk = list(fk_column)[0].column.name

                    fk_value = record_dict[fk_column_name]
                    fk_model_class = self.get_model_by_table_name(fk_table_name)

                    if fk_model_class:
                        fk_query = select(fk_model_class.__table__).where(
                            getattr(fk_model_class, fk_table_pk) == fk_value)
                        fk_result = conn.execute(fk_query).fetchone()

                        if fk_result:
                            record_dict[fk_column_name] = {col.name: value for col, value in
                                                           zip(fk_model_class.__table__.columns, fk_result)}
                    else:
                        record_dict[fk_column_name] = f"Error: Model for table '{fk_table_name}' not found"
        return record_dict

    def all_records(self, table_name):
        model = self.get_model_by_table_name(table_name)
        if not model:
            return f"Table named '{table_name}' does not exists."

        try:
            records = self.session.query(model).all()
            return [record.__dict__ for record in records]
        except NoResultFound:
            return f"No records for table '{table_name}'."

    def update_record_by_pk(self, table_name: str, primary_key: str, value: Any, **kwargs):
        model = self.get_model_by_table_name(table_name)
        if not model:
            raise TypeError(f"Table named '{table_name}' does not exists")
        scoped = scoped_session(sessionmaker(bind=self.engine))
        session = scoped()
        try:
            record = session.query(model).filter(getattr(model, primary_key) == value).one_or_none()
            if not record:
                raise NameError(
                    f"Not found any record for table '{table_name}' for column '{primary_key}' and value '{value}'.")

            for key, val in kwargs.items():
                if not hasattr(model, key):
                    raise NameError(f"Column '{key}' does not belong to table '{table_name}'.")

                column = getattr(model, key).property.columns[0].type
                val = convert_value_to_column_type(column, val)
                setattr(record, key, val)
            session.commit()

        except Exception as e:
            session.rollback()
            raise e
        finally:
            session.close()
        return True

    def is_record_type_valid_with_table(self, table_name: str, data: dict):
        columns = self.table_structure(table_name)

        for column in columns:
            column_name = column['name']
            column_type = column['type'].lower()

            if column_name in data:
                value = data[column_name]

                if 'integer' in column_type or 'bigint' in column_type or 'serial' in column_type:
                    try:
                        value = int(value)
                    except ValueError:
                        return {"error": f"Invalid type for {column_name}, expected Integer or BigInt"}
                elif 'float' in column_type or 'real' in column_type or 'double precision' in column_type or 'numeric' in column_type:
                    try:
                        value = float(value)
                    except ValueError:
                        return {"error": f"Invalid type for {column_name}, expected Float, Numeric or Real"}
                elif 'string' in column_type or 'Text' in column_type or 'UUID' in column_type or 'JSON' in column_type or 'JSONB' in column_type:
                    if not isinstance(value, str):
                        return {"error": f"Invalid type for {column_name}, expected String or Text"}
                elif 'boolean' in column_type:
                    if value not in ['true', 'false', '0', '1']:
                        return {"error": f"Invalid type for {column_name}, expected Boolean (true/false)"}
                    if value in ['true', '1']:
                        value = True
                    else:
                        value = False
                elif 'date' in column_type or 'datetime' in column_type:
                    pass
                elif 'array' in column_type:
                    if not isinstance(value, list):
                        return {"error": f"Invalid type for {column_name}, expected Array"}
                data[column_name] = value
        return {"ok": data}

    def add_new_record(self, table_name: str, record: dict, check_valid=True):
        if check_valid:
            test = self.is_record_type_valid_with_table(table_name, record)
            if 'error' in test:
                raise ValueError(test['error'])
            record = test['ok']

        table = self.tables_dict[table_name]
        try:
            insert_statement = table.insert().values(**record)
            self.session.execute(insert_statement)
            self.session.commit()
            return {"message": "Record added successfully", "done": True}
        except Exception as e:
            self.session.rollback()
            return {"error": str(e)}

    def create_or_alter_table(self, table_name: str, *columns, **kwargs):
        print('alchemic.create_or_alter_table')

        alter_allowed = kwargs.get('alter_allowed', False)

        try:
            table_columns = []
            for column in columns:
                print('column dict to iter:', column)
                col_name = column.get("name")
                col_type = column.get("type")
                default = column.get("default", None)
                max_length = column.get("max_length", None)
                is_required = column.get("required", 'false') == 'true'
                primary_key = column.get("primary_key", False)
                autoincrement = column.get("autoincrement_key", False)

                if col_type == 'ForeignKey':
                    column_type = Integer
                    reference = column.get('foreign_reference')
                    if not reference:
                        raise ValueError(f"Foreign key column '{col_name}' must specify 'foreign_reference'")
                    fk_reference = ForeignKey(reference)
                    print(f"Adding foreign key: name={col_name}, type={column_type}, reference={reference}")
                    table_columns.append(Column(col_name, column_type, fk_reference,
                                                primary_key=primary_key, nullable=not is_required))
                else:
                    column_type = map_column_type(col_type, max_length)
                    print(f"Adding column: name={col_name}, type={column_type}, primary_key={primary_key}")
                    if default is None:
                        table_columns.append(Column(col_name, column_type, autoincrement=autoincrement,
                                                    nullable=not is_required, primary_key=primary_key))
                    else:
                        table_columns.append(Column(col_name, column_type, autoincrement=autoincrement,
                                                    default=default, nullable=not is_required, primary_key=primary_key))

            new_table = Table(table_name, self.metadata, *table_columns, extend_existing=True)
            print('######## Created new table:', new_table)

            self.metadata.create_all(self.engine)
            self.tables_dict = {table_name: self.metadata.tables[table_name] for table_name in self.metadata.tables}
            self.models_dict = {}
            self.mapper_registry = registry()

            for key in self.tables_dict.keys():
                self.get_model_by_table_name(key)

            return {
                "status": "ok",
                "message": f"Table '{table_name}' created successfully",
                "model": str(new_table)
            }
        except SQLAlchemyError as e:
            return {
                "status": "error",
                "message": str(e)
            }


alchemic = DynamicAlchemic('sqlite:///C:/proj/some_sqlite.db')
