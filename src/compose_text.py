# from utils import *
import pandas as pd
import re
import os

from config import REPORT_FOLDER, ABN_CSV_PATH, PRSN_CSV_PATH

#  prsn: participants; ctab: abnormalities without comparisons;  canc: lung cancer

#  relevant variables in each file
prsn_vars = ["pid", "scr_iso0", "scr_iso1", "scr_iso2", "cancyr", "de_grade", "de_stag", "de_stag_7thed", "de_type",
             "loccar", "loclhil", "loclin", "locllow", "loclmsb", "loclup", "locmed", "locoth", "locrhil",
             "locrlow", "locrmid", "locrmsb", "locrup", "locunk"]

ctab_vars = ["pid", "study_yr", "sct_ab_num", "sct_found_after_comp", "sct_ab_desc", "sct_epi_loc", "sct_long_dia",
             "sct_slice_num", "sct_perp_dia", "sct_margins", "sct_pre_att"]

canc_vars = []

#  variable to prefix mappings for each file
prsn_v2p = {"pid": "Patient ID: ", "scr_iso0": "Isolation reading of the image gives the preliminary result of ", "scr_iso1": "Isolation reading of the image gives the preliminary result of ", "scr_iso2": "Isolation reading of the image gives the preliminary result of ",
            "de_grade": "of ", "de_stag": ", ", "de_stag_7thed": ", ", "de_type": ", type ",
            #@todo: 这是第一个的情况, 后边就直接用 prsn_v2t 里的值，不要用 df 里的值
            "loccar": "", "loclhil": "", "loclin": "", "locllow": "", "loclmsb": "", "loclup": "", "locmed": "", "locoth": "", "locrhil": "", "locrlow": "", "locrmid": "", "locrmsb": "", "locrup": "", "locunk": ""}

ctab_v2p = {"sct_ab_desc": "is a(n) ", "sct_epi_loc": "; the epicenter of the nodule is located in ",
            "sct_long_dia": "; the longest diameter found is ", "sct_slice_num": "mm in CT slice #",
            "sct_perp_dia": ", and the longest diameter perpendicular to it is ",
            "sct_margins": "mm; the margin of the nodule is ",
            "sct_pre_att": "; the predominant attenuation of the nodule is "}

canc_v2p = {}


#@todo: general rule: 值等于 None 就把整个 phrase 给 drop 了？
# variable to value->text mapping for each file
prsn_v2t = {"scr_iso0":    {1: "negative screen, no significant abnormalities",
                            2: "negative screen, minor abnormalities not suspicious for lung cancer",
                            3: "negative screen, significant abnormalities not suspicious for lung cancer",
                            4: "positive, change unspecified, nodule(s) >= 4 mm or enlarging nodule(s), "
                               "mass(es), other non-specific abnormalities suspicious for lung cancer",
                            10: None, 11: None, 13: None, 14: None, 15: None, 17: None, 23: None, 24: None, 95: None, 97: None},
            "scr_iso1": {1: "negative screen, no significant abnormalities", 2: "negative screen, minor abnormalities not suspicious for lung cancer", 3: "negative screen, significant abnormalities not suspicious for lung cancer", 4: "positive, change unspecified, nodule(s) >= 4 mm or enlarging nodule(s), mass(es), other non-specific abnormalities suspicious for lung cancer", 10: None, 11: None, 13: None, 14: None, 15: None, 17: None, 23: None, 24: None, 95: None, 97: None}, "scr_iso2": {1: "negative screen, no significant abnormalities", 2: "negative screen, minor abnormalities not suspicious for lung cancer", 3: "negative screen, significant abnormalities not suspicious for lung cancer", 4: "positive, change unspecified, nodule(s) >= 4 mm or enlarging nodule(s), mass(es), other non-specific abnormalities suspicious for lung cancer", 10: None, 11: None, 13: None, 14: None, 15: None, 17: None, 23: None, 24: None, 95: None, 97: None},
            "de_grade":    {2: "grade well differentiated (G1)", 3: "grade moderately differentiated (G2)",
                            4: "grade poorly differentiated (G3)", 5: "grade undifferentiated (G4)",
                            1: None, 6: None, 8: None, 9: None},
            "de_stag":    {110: "stage IA", 120: "stage IB", 210: "stage IIA", 220: "stage IIB", 310: "stage IIIA",
                            320: "stage IIIB", 400: "stage IV",
                            900: "stage cannot be assessed due to Occult Carcinoma (cancer cells are found, but the primary tumor cannot be identified)",
                            994: None, 888: None, 999: None},
            "de_stag_7thed":{110: "stage IA", 120: "stage IB", 210: "stage IIA", 220: "stage IIB", 310: "stage IIIA", 320: "stage IIIB", 400: "stage IV", 900: "stage cannot be assessed due to Occult Carcinoma (cancer cells are found, but the primary tumor cannot be identified)", 999: None},
            "de_type": {8140: "Adenocarcinoma", 8250: "Bronchiolo-alveolar adenocarcinoma", 8046: "Non-small cell carcinoma",
                        8070: "Squamous cell carcinoma", 8042: "Oat cell carcinoma", 8013: "Large cell neuroendocrine carcinoma",
                        8240: "Carcinoid tumor", 8010: "Carcinoma", 8041: "Small cell carcinoma", 8560: "Adenosquamous carcinoma",
                        8071: "Squamous cell carcinoma, large cell, keratinizing", 8072: "Squamous cell carcinoma, nonkeratinizing",
                        8260: "Papillary adenocarcinoma", 8481: "Mucin-producing adenocarcinoma", 8323: "Mixed cell adenocarcinoma",
                        8012: "Large cell carcinoma", 8252: "Bronchiolo-alveolar carcinoma, non-mucinous", 8246: "Neuroendocrine carcinoma",
                        8253: "Bronchiolo-alveolar adenocarcinoma, mucinous", 8490: "Signet ring cell carcinoma",
                        8083: "Basaloid squamous cell carcinoma", 8075: "Squamous cell carcinoma, adenoid",
                        8480: "Mucinous carcinoma", 8550: "Acinar cell carcinoma", 8254: "Bronchiolo-alveolar carcinoma, mixed mucinous and non-mucinous",
                        8255: "Adenocarcinoma", 8045: "Combined small cell carcinoma", 8033: "Pseudosarcomatous carcinoma",
                        8000: "Neoplasm", 8050: "Papillary carcinoma", 8570: "Adenocarcinoma with squamous metaplasia",
                        8032: "Spindle cell carcinoma", 8021: "Carcinoma, anaplastic", 8084: "Squamous cell carcinoma, clear cell type",
                        8249: "Atypical carcinoid tumor", 8980: "Carcinosarcoma", 8044: "Small cell carcinoma, intermediate cell",
                        8310: "Clear cell adenocarcinoma", 8022: "Pleomorphic carcinoma", 8052: "Papillary squamous cell carcinoma", 8001: "Tumor cells"},
            "loccar": {0: None, 1: "Carina, "}, "loclhil": {0: None, 1: "Left Hilum, "}, "loclin": {0: None, 1: "Lingula, "},
            "locllow": {0: None, 1: "Left lower lobe, "}, "loclmsb": {0: None, 1: "Left main stem bronchus, "}, "loclup": {0: None, 1: "Left upper lobe, "},
            "locmed": {0: None, 1: "Mediastinum, "}, "locoth": {0: None, 1: "outside the main regions, "}, "locrhil": {0: None, 1: "Right Hilum, "},
            "locrlow": {0: None, 1: "Right lower lobe, "}, "locrmid": {0: None, 1: "Right middle lobe, "}, "locrmsb": {0: None, 1: "Right main stem bronchus, "},
            "locrup": {0: None, 1: "Right upper lobe, "}, "locunk": {0: None, 1: "an unknown location"}}

ctab_v2t = {"sct_ab_desc": {51: "Non-calcified nodule or mass (opacity >= 4 mm diameter)",
            52: "Non-calcified micronodule(s) (opacity < 4 mm diameter)", 53: "Benign lung nodule(s) (benign calcification)",
            54: "Atelectasis, segmental or greater", 55: "Pleural thickening or effusion",
            56: "Non-calcified hilar/mediastinal adenopathy or mass (>= 10 mm on short axis)",
            57: "Chest wall abnormality (bone destruction, metastasis, etc.)",
            58: "Consolidation", 59: "Emphysema", 60: "Significant cardiovascular abnormality",
            61: "Reticular/reticulonodular opacities, honeycombing, fibrosis, or scar",
            62: "6 or more nodules, not suspicious for cancer (opacity >= 4 mm)",
            63: "Other potentially significant abnormality above the diaphragm",
            64: "Other potentially significant abnormality below the diaphragm", 65: "Other minor abnormality noted"},
            "sct_epi_loc": {1: "Right Upper Lobe", 2: "Right Middle Lobe", 3: "Right Lower Lobe", 4: "Left Upper Lobe",
            5: "Lingula", 6: "Left Lower Lobe", 8: None},
            "sct_margins": {1: "Spiculated (Stellate)", 2: "Smooth", 3: "Poorly defined", 9: "Unable to determine"},
            "sct_pre_att": {1: "Soft Tissue", 2: "Ground glass", 3: "Mixed", 4: "Fluid/water", 6: "Fat", 7: "Other", 9: "Unable to determine"}}

canc_v2t = {}

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

def write_report(pid, study_yr, content):
    """
    Writes the given content to a report file in the specified output directory.

    :param report_name: The name of the report file to be written (should include .txt or other file extension).
    :param content: The content to write to the report file.
    """
    if not os.path.exists(REPORT_FOLDER):
        os.mkdir(REPORT_FOLDER)
    report_name = str(pid) + "_" + str(study_yr) + ".txt"
    path = os.path.join(REPORT_FOLDER, report_name)
    try:
        with open(path, mode='w', encoding='utf-8') as report_file:
            report_file.write(content)
            print(f"Report {report_name} has been written to {REPORT_FOLDER}.")
    except Exception as e:
        print(f"An error occurred while writing {report_name}: {e}")

def read_csv(file_name, variable_names, path):
    """
    Reads specific variables from a CSV file using pandas and optionally applies a mapping to the variables.

    :param file_name: The name of the CSV file to read.
    :param variable_names: A list of column names to read from the file.
    :return: A pandas DataFrame with the specified variables and applied mapping.
    """
    # path = os.path.join(INPUT_DIR, "nlst_780_"+file_name+"_idc_20210527.csv")
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
        print(f"File {file_name} not found in {path}.")
        return pd.DataFrame()  # Return an empty DataFrame in case of error
    except Exception as e:
        print(f"An error occurred while reading {file_name}: {e}")
        return pd.DataFrame()  # Return an empty DataFrame in case of error

def report_composer():
    """write reports for all scans that contains a nodule"""

    global prsn_vars, ctab_vars, canc_vars, prsn_v2p, ctab_v2p, canc_v2p, prsn_v2t, ctab_v2t, prsn_v2t
    # Read files into DataFrames
    df_prsn = read_csv("prsn", prsn_vars, PRSN_CSV_PATH)
    df_ctab = read_csv("ctab", ctab_vars, ABN_CSV_PATH)

    # Substitute values in DataFrames with corresponding phrases
    var2phrase(df_prsn, prsn_v2t, prsn_v2p)
    var2phrase(df_ctab, ctab_v2t, ctab_v2p)

    # Traverse `df_prsn` to write reports, already sorted by pid (low to high)
    ab_iter_idx = 0  # Counter for iterating over `df_ctab`
    for index, row in df_prsn.iterrows():
        row.fillna("", inplace=True)
        for year in range(3):
            pid = int(row["pid"][-6:])  # Extract patient ID from the stringified value
            report = ""

            # Header
            # report += row["pid"] + "\n" + "Screening Year: " + str(year) + "\n"
            if row["scr_iso" + str(year)] == "":
                continue  # Screening marked as failed, generate no report
            report += row["scr_iso" + str(year)] + ".\n"

            # Abnormalities: aggregated into a single paragraph
            ab_paragraph = ""
            ab_ct = 0  # Count of abnormalities for this patient-year
            while ab_iter_idx < df_ctab.shape[0]:
                ab_row = df_ctab.iloc[ab_iter_idx].fillna("")  # Pick up from last time
                if ab_row["study_yr"] != year or ab_row["pid"] != pid:
                    break  # Stop if no more abnormalities for this patient-year

                # Increment counters
                ab_ct += 1
                ab_iter_idx += 1

                # Add description of the abnormality
                ab_paragraph += "Abnormality #" + str(ab_row["sct_ab_num"]) + ": "
                ab_paragraph += ab_row["sct_ab_desc"] + ab_row["sct_epi_loc"] + ab_row["sct_long_dia"] \
                                + ab_row["sct_slice_num"] + ab_row["sct_perp_dia"] \
                                + ab_row["sct_margins"] + ab_row["sct_pre_att"] + ".\n"

            # Append abnormalities to the report
            report += str(ab_ct) + " abnormalities were identified in this screening.\n" + ab_paragraph

            # Cancer diagnosis details
            cancer_yr = row["cancyr"]
            cancer_yr = int(cancer_yr) if cancer_yr != "" else 100
            if cancer_yr == year:
                report += "Subsequent examinations after this screening have confirmed lung cancer "
                report += row["de_grade"]
                report += row["de_stag"] if row["de_stag"] != "" else row["de_stag_7thed"]
                report += row["de_type"]

                # Primary tumor locations
                locations = [col for col in df_prsn.columns if col.startswith("loc") and row[col] != ""]
                if locations:
                    report += ". The primary tumor is located in the following location(s): "
                    report += ", ".join(row[loc] for loc in locations)
                else:
                    report += " The location of the primary tumor is not identified."

            # Write the final report
            write_report(pid, year, report)

