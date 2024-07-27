import pandas as pd
import os
from config import INPUT_DIR, OUTPUT_DIR
import re

def var2phrase(df, val2textMap, var2prefixMap):
    """
    For a given DataFrame, substitutes the values of specified variables with corresponding text
    and adds prefixes to specified variables' values as per the provided dictionaries.

    :param df: The pandas DataFrame to transform.
    :param val2textMap: Dict mapping "variable name" to another dict of {"value": "text"} for substitution.
    :param var2prefixMap: Dict mapping "variable name" to "prefix" for value concatenation.
    """

    for var, prefix in var2prefixMap.items():   # if the variable needs to be composed into a phrase
        if var in val2textMap.keys():           # if the variable has a numerical->text mapping
            mapping = val2textMap[var]
            def map_value(val):
                if pd.isnull(val):              # Keep null values unchanged
                    return val
                if val in mapping:
                    return mapping[val]         # otherwise substitute with corresponding text
                else:
                    raise ValueError(f"Value '{val}' for variable '{var}' not found in mapping.")
            df[var] = df[var].apply(map_value)  # apply for the whole column
        # add prefix to make it a phrase, apply only to not null values, otherwise kept as null
        #print(var)
        #print(var2prefixMap[var])
        #print(df[var].astype(str))
        df[var] = df[var].astype('string') # cast all to NULLABLE string
        df.loc[df[var].notnull(), var] = var2prefixMap[var] + df.loc[df[var].notnull(), var]


# file I/O
def read_csv(file_name, variable_names):
    """
    Reads specific variables from a CSV file using pandas and optionally applies a mapping to the variables.

    :param file_name: The name of the CSV file to read.
    :param variable_names: A list of column names to read from the file.
    :return: A pandas DataFrame with the specified variables and applied mapping.
    """
    path = os.path.join(INPUT_DIR, "nlst_780_"+file_name+"_idc_20210527.csv")
    try:
        # Check if all specified variable_names are in the CSV file columns
        df_temp = pd.read_csv(path, nrows=0)
        missing_cols = set(variable_names) - set(df_temp.columns)
        if missing_cols:
            raise ValueError(f"Missing variables in {file_name} : {missing_cols}")

        # Read only the specified columns
        df = pd.read_csv(path, usecols=variable_names)

        # Convert all columns that pandas inferred as float to integers
        for col in df.select_dtypes(include='float').columns:
            df[col] = df[col].astype('Int64')

        return df
    except FileNotFoundError:
        print(f"File {file_name} not found in {INPUT_DIR}.")
        return pd.DataFrame()  # Return an empty DataFrame in case of error
    except Exception as e:
        print(f"An error occurred while reading {file_name}: {e}")
        return pd.DataFrame()  # Return an empty DataFrame in case of error


def write_report(pid, study_yr, ab_n, slice_n, content):
    """
    Writes the given content to a report file in the specified output directory.

    :param report_name: The name of the report file to be written (should include .txt or other file extension).
    :param content: The content to write to the report file.
    """
    match = re.search(r'\d{1,3}$', slice_n)
    slice_n = match.group()

    report_name = str(pid) + "_" + str(study_yr) + "_" + str(ab_n) + "_" + slice_n + ".txt"
    path = os.path.join(OUTPUT_DIR, report_name)
    try:
        with open(path, mode='w', encoding='utf-8') as report_file:
            report_file.write(content)
            print(f"Report {report_name} has been written to {OUTPUT_DIR}.")
    except Exception as e:
        print(f"An error occurred while writing {report_name}: {e}")