from typing import List, Dict, Any
from itertools import chain

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


find_records('OrderDetails', 'OrderID', 10251)



def find_records_return_dicts(table_name, column_name, value):
    if table_name not in tables_dict:
        raise AttributeError(f"Tabela o nazwie '{table_name}' nie istnieje.")

    table = tables_dict[table_name]
    col_names = [_.name for _ in table.columns]

    if column_name not in table.columns:
        raise AttributeError(f"Kolumna '{column_name}' nie istnieje w tabeli '{table_name}'.")

    query = select(table).where(table.columns[column_name] == value)

    with engine.connect() as conn:
        result = conn.execute(query)
        records = list(result.fetchall())

        if records:
            for i in range(len(records)):
                records[i] = dict(zip(col_names, records[i]))

    return records


def find_records_return_dicts_expand_fk(table_name, column_name, value):
    if table_name not in tables_dict:
        raise AttributeError(f"Tabela o nazwie '{table_name}' nie istnieje.")

    table = tables_dict[table_name]
    col_names = [_.name for _ in table.columns]

    if column_name not in table.columns:
        raise AttributeError(f"Kolumna '{column_name}' nie istnieje w tabeli '{table_name}'.")

    query = select(table).where(table.columns[column_name] == value)

    with engine.connect() as conn:
        result = conn.execute(query)
        records = list(result.fetchall())

        if records:
            for i in range(len(records)):
                records[i] = dict(zip(col_names, records[i]))



print(find_records_return_dicts('OrderDetails', 'OrderID', 10251))


def get_record_dict(table_name, column_name, value, name_only=False):

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
                fk.extend(list(column_name.foreign_keys))
        else:
            for i, column_name in enumerate(column_names):
                fk.extend(list(column_name.foreign_keys))
                record_dict[column_name] = record[i]
    fk = list(set(fk))

    for x in fk:
        if 'FOREIGNS' not in record_dict:
            record_dict['FOREIGNS'] = []

        ref_table, col_name = str(x.column).split('.')

        value = 0
        for col_obj in record_dict:
            if hasattr(col_obj, 'name'):
                if col_obj.name == col_name:
                    value = record_dict[col_obj]
                    break
            else:
                if col_obj == col_name:
                    value = record_dict[col_obj]
                    break

        ref_dict = get_record_dict(ref_table, col_name, value, False)

        record_dict['FOREIGNS'].append(ref_dict)

    return record_dict


def get_record_dict2(table_name, column_name, value, name_only=False):

    records = find_records(table_name, column_name, value)

    if not records:
        return []

    column_objs = tables_dict[table_name].columns
    # foreign_keys_objs = [list(_.foreign_keys) for _ in column_objs if _.foreign_keys]

    foreign_key_objs = list(chain.from_iterable([list(_.foreign_keys) for _ in column_objs if _.foreign_keys]))
    foreign_key_ref_names = [_.target_fullname for _ in foreign_key_objs]
    column_objs_names = [_.name for _ in column_objs]

    for record in records:
        record: List[int]

        for i, col_name in enumerate(column_objs_names):
            for fkrn in foreign_key_ref_names:
                if col_name in fkrn:
                    ref_table_name, ref_col_name = fkrn.split('.')
                    find_records(ref_table_name, ref_col_name, record[i])





get_record_dict2('OrderDetails', 'OrderID', 10251)
exit()


def get_records_dict_expand_fk(
        table_name: str,
        column_name: str,
        value: Any,
        name_only=False) -> List[Dict[str, Any] or Dict[str, Dict]]:

    records = find_records(table_name, column_name, value)

    if not records:
        return []

    column_objs = tables_dict[table_name].columns
    column_names = [_.name for _ in column_objs]

    foreign_key_objs = [key for _ in column_objs if _.foreign_keys for key in list(_.foreign_keys)]
    foreign_key_names = [_.target_fullname for _ in foreign_key_objs]

    '''print('foreign_key_objs', foreign_key_objs)
    print('foreign_key_names', foreign_key_names)
    print('column_names:', column_names)'''

    results = []

    for record in records:
        result_dict = dict()

        for i, col_value in enumerate(record):
            if foreign_key_names:
                for next_foreign_key in foreign_key_names:
                    ref_table_name, ref_col_name = next_foreign_key.split('.')
                    if column_names[i] == ref_col_name:
                        result_dict[column_names[i]] = {
                            'value': col_value,
                            'foreign': get_record_dict(ref_table_name, ref_col_name, col_value, name_only=name_only)
                        }
            else:
                result_dict[column_names[i]] = col_value

        results.append(result_dict)
    return results



def get_records_expand_foreign_keys(
        table_name: str,
        column_name: str,
        value: Any,
        name_only=False) -> List[Dict[str, Any] or Dict[str, Dict]]:

    records = find_records(table_name, column_name, value)

    if not records:
        return []

    column_objs = tables_dict[table_name].columns
    column_names = [_.name for _ in column_objs]

    foreign_key_objs = [key for _ in column_objs if _.foreign_keys for key in list(_.foreign_keys)]
    foreign_key_names = [_.target_fullname for _ in foreign_key_objs]

    results = []

    for record in records:
        result_dict = dict()

        for i, col_value in enumerate(record):
            if foreign_key_names:
                for next_foreign_key in foreign_key_names:
                    ref_table_name, ref_col_name = next_foreign_key.split('.')
                    if column_names[i] == ref_col_name:
                        result_dict[column_names[i]] = {
                            'value': col_value,
                            'foreign': get_record_dict(ref_table_name, ref_col_name, col_value, name_only=name_only)
                        }
            else:
                result_dict[column_names[i]] = col_value

        results.append(result_dict)
    return results



def test():
    print('TEST:')
    results = get_records_expand_foreign_keys('OrderDetails', 'OrderID', 10251, True)
    # print('result:', result)
    import pprint
    for result in results:
        print(result)
    #result = get_record_dict_expand_fk('OrderDetails', 'OrderID', 10251)
    #print(result)


# Przykład użycia
if __name__ == "__main__":
    test()
