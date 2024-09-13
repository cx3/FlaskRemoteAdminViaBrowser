from typing import Any

from sqlalchemy import create_engine, MetaData, select
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker


class DynamicAlchemic:
    def __init__(self, db_uri):
        self.engine = create_engine(db_uri)
        self.metadata = MetaData()
        self.metadata.reflect(bind=self.engine)
        self.metadata.create_all(self.engine)

        self.tables_dict = {table_name: self.metadata.tables[table_name] for table_name in self.metadata.tables}

        self.Base = declarative_base()
        self.session = sessionmaker(bind=self.engine)()

    def find_records(self, table_name, column_name, value):
        if table_name not in self.tables_dict:
            return f"Tabela o nazwie '{table_name}' nie istnieje."

        table = self.tables_dict[table_name]

        if column_name not in table.columns:
            return f"Kolumna '{column_name}' nie istnieje w tabeli '{table_name}'."
        print('>>>', table.columns[column_name])

        query = select(table.columns).where(table.columns[column_name] == value)

        with self.engine.connect() as conn:
            result = conn.execute(query)
            records = result.fetchall()

        record_dicts = []
        for record in records:
            record_dict = {}
            for i, column in enumerate(table.columns):
                record_dict[column.name] = record[i]
            record_dicts.append(record_dict)

        return record_dicts

    def find_records_expand_foreign_keys(self, table_name, column_name, value):
        if table_name not in self.tables_dict:
            return f"Tabela o nazwie '{table_name}' nie istnieje."

        table = self.tables_dict[table_name]

        if column_name not in table.columns:
            return f"Kolumna '{column_name}' nie istnieje w tabeli '{table_name}'."

        query = select(table.columns).where(table.columns[column_name] == value)

        with self.engine.connect() as conn:
            result = conn.execute(query)
            records = result.fetchall()

        record_dicts = []
        for record in records:
            record_dict = {}
            for i, column in enumerate(table.columns):
                if column.foreign_keys:
                    foreign_key_dict = {}
                    for j, fk in enumerate(column.foreign_keys):
                        foreign_table_name = fk.column.table.name
                        foreign_column_name = fk.column.name
                        foreign_key_dict[foreign_table_name + '.' + foreign_column_name] = record[i]#record[fk.parent.name]
                    record_dict[column.name] = foreign_key_dict
                else:
                    record_dict[column.name] = record[i]
            record_dicts.append(record_dict)

        return record_dicts

    def get_model_by_table_name(self, table_name: str):
        if table_name in self.tables_dict:
            table = self.tables_dict[table_name]
            columns = table.columns.keys()
            model_name = table_name.capitalize()
            Model = type(model_name, (self.Base,), {'__tablename__': table_name})
            return Model
        else:
            return None

    def edit_record(self, table_name: str, unique_column_name: str, unique_value: Any, **kwargs):
        if table_name not in self.tables_dict:
            return f"Tabela o nazwie '{table_name}' nie istnieje."

        table = self.tables_dict[table_name]

        if unique_column_name not in table.columns:
            return f"Kolumna '{unique_column_name}' nie istnieje w tabeli '{table_name}'."

        # Sprawdź, czy podana wartość unikalna istnieje w kolumnie
        query = select(table.columns).where(getattr(table.columns, unique_column_name) == unique_value)
        with self.engine.connect() as conn:
            result = conn.execute(query)
            record = result.fetchone()

        if not record:
            return f"Nie znaleziono rekordu w tabeli '{table_name}' dla kolumny '{unique_column_name}' o wartości '{unique_value}'."

        # Utwórz słownik z pary kolumna-wartość do aktualizacji rekordu
        update_data = {}
        for column_name, value in kwargs.items():
            if column_name not in table.columns:
                return f"Kolumna '{column_name}' nie istnieje w tabeli '{table_name}'."
            update_data[column_name] = value

        # Aktualizuj rekord
        update_query = table.update().where(getattr(table.columns, unique_column_name) == unique_value).values(
            update_data)
        with self.engine.connect() as conn:
            conn.execute(update_query)

        return f"Rekord w tabeli '{table_name}' dla kolumny '{unique_column_name}' o wartości '{unique_value}' został zaktualizowany."


# Przykład użycia
if __name__ == "__main__":
    db_handler = DynamicAlchemic('sqlite:///C:/proj/some_sqlite.db')
    # ('OrderDetails', 'OrderID', 10251)
    result = db_handler.find_records("OrderDetails", "OrderID", 10251)
    print(result)
    print('\n\n\n\n\n')
    result_expand_fk = db_handler.find_records_expand_foreign_keys("OrderDetails", "OrderID", 10251)
    print(result_expand_fk)
