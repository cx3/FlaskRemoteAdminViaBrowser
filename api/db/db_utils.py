from sqlalchemy import create_engine, MetaData, Table, select

# Tworzenie połączenia z bazą danych
engine = create_engine('sqlite:///C:/proj/some_sqlite.db')

# Tworzenie obiektu MetaData
metadata = MetaData()

# Ładowanie struktury tabel z bazy danych
metadata.reflect(bind=engine)

# Pobieranie nazw wszystkich tabel i tworzenie słownika
tables_dict = {table_name: metadata.tables[table_name] for table_name in metadata.tables}


def find_records(table_name, column_name, value):
    if table_name not in tables_dict:
        return f"Tabela o nazwie '{table_name}' nie istnieje."

    table = tables_dict[table_name]

    if column_name not in table.columns:
        return f"Kolumna '{column_name}' nie istnieje w tabeli '{table_name}'."

    query = select(table).where(table.columns[column_name]==value)

    with engine.connect() as conn:
        result = conn.execute(query)
        records = result.fetchall()

    return records


def get_record_dict(table_name, column_name, value, name_only=False):

    def extend_fk():pass

    records = find_records(table_name, column_name, value)

    if not records:
        return {}

    column_names = tables_dict[table_name].columns
    record_dict = {}
    fk = []
    for record in records:
        if name_only:
            for i, column_name in enumerate(column_names):
                record_dict[column_name.name] = record[i]
        else:
            for i, column_name in enumerate(column_names):
                s = ""
                for d in dir(column_name):
                    if '__' not in d and not d.startswith('_'):
                        s += d + ', '
                print(s)
                fk.append(column_name)

                record_dict[column_name] = record[i]
    fk = list(set(fk))
    print('fk:')
    for x in fk:
        print('>>>', x)

    return record_dict


def get_record_dict_expand_fk(table_name, column_name, value):
    record = get_record_dict(table_name, column_name, value, name_only=False)

    for key in record:
        print(key, record[key])


def test():
    result = get_record_dict('OrderDetails', 'OrderID', 10251)
    print(result)

    #result = get_record_dict_expand_fk('OrderDetails', 'OrderID', 10251)
    #print(result)


# Przykład użycia
if __name__ == "__main__":
    test()
