from typing import List

import pandas as pd


from api.db.db_dynamic import DynamicAlchemic


def map_pandas_type_to_sqlalchemy(dtype):
    if pd.api.types.is_integer_dtype(dtype):
        return 'Integer'
    elif pd.api.types.is_float_dtype(dtype):
        return 'Float'
    elif pd.api.types.is_bool_dtype(dtype):
        return 'Boolean'
    elif pd.api.types.is_datetime64_any_dtype(dtype):
        return 'DateTime'
    else:
        return 'String'


def analyze_csv_header_and_types(csv_file):
    try:
        df = pd.read_csv(csv_file)
        result = {"columns": [], "auto_indexed": False, "autoincrement_column": None}

        if pd.api.types.is_integer_dtype(df.iloc[:, 0]):
            expected_index = pd.Series(range(1, len(df) + 1))
            if df.iloc[:, 0].reset_index(drop=True).equals(expected_index):
                result["auto_indexed"] = True
                result["autoincrement_column"] = df.columns[0]

        for column in df.columns:
            dtype = str(df[column].dtype)
            if 'int' in dtype:
                col_type = 'Integer'
            elif 'float' in dtype:
                col_type = 'Float'
            elif 'bool' in dtype:
                col_type = 'Boolean'
            elif 'datetime' in dtype:
                col_type = 'DateTime'
            else:
                col_type = 'String'

            result["columns"].append({"name": column, "type": col_type})

        return result
    except Exception as e:
        return {"error": str(e)}


def csv_into_alchemic_database(
        file_path: str, new_table_name: str, alchemic: DynamicAlchemic,
        primary_key_names: List[str], autoincrement_keys: List[str]):

    if not isinstance(new_table_name, str):
        raise TypeError

    if new_table_name in alchemic.table_names():
        raise NameError(f'Table name {new_table_name} is busy')

    try:
        # Load the CSV file into a DataFrame
        df = pd.read_csv(file_path)
        table_name = new_table_name

        # Check if specified primary keys exist in the CSV
        if primary_key_names and all(pk in df.columns for pk in primary_key_names):
            print('All passed primary_keys are ok!')
        else:
            print('Auto-generating primary key column.')
            df.insert(0, 'id', range(1, len(df) + 1))
            primary_key_names = ['id']

        columns = []
        for col_name, dtype in df.dtypes.items():
            col_type = map_pandas_type_to_sqlalchemy(dtype)

            is_primary_key = col_name in primary_key_names
            is_autoincrement = col_name in autoincrement_keys

            column_def = {
                "name": col_name,
                "type": 'Integer' if is_autoincrement else col_type,
                "required": is_primary_key,
                "primary_key": is_primary_key,
                "autoincrement_key": is_autoincrement
            }
            columns.append(column_def)
            print(f"Column '{col_name}':", column_def)

        return {
            **alchemic.create_or_alter_table(table_name, *columns),
            'rows_added': df.to_sql(table_name, alchemic.engine, if_exists='replace', index=False)
        }
    except Exception as e:
        return {
            "status": "error",
            "msg": str(e)
        }
