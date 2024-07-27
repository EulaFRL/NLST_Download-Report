from utils import *


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

def report_composer():
    global prsn_vars, ctab_vars, canc_vars, prsn_v2p, ctab_v2p, canc_v2p, prsn_v2t, ctab_v2t, prsn_v2t
    #  read files into dfs
    df_prsn = read_csv("prsn", prsn_vars)
    df_ctab = read_csv("ctab", ctab_vars)

    #print(df_prsn.iloc[4])

    # substitute values in dfs with corresponding phrases
    var2phrase(df_prsn, prsn_v2t, prsn_v2p)
    var2phrase(df_ctab, ctab_v2t, ctab_v2p)

    #print(df_prsn.iloc[4])

    # traverse prsn to write reports, already sorted by pid(low to high)
    ab_iter_idx = 0  # counter for iterating over ctab
    for index, row in df_prsn.iterrows():
        row.fillna("", inplace=True)
        for year in range(3):
            pid = int(row["pid"][-6:])  # extract the patient ID back from the stringified value
            header = ""
            header += row["pid"] + "\n" + "Screening Year: " + str(year) + "\n"  # header
            if row["scr_iso"+str(year)] == "": continue  # the screening is marked as failed, generate no report
            header += row["scr_iso"+str(year)] + ".\n"  # isolation reading

            cancer_paragraph = ""  # for this year
            cancer_yr = row["cancyr"]
            cancer_yr = int(cancer_yr) if cancer_yr != "" else 100
            # the screening year when the patient is diagnosed with cancer
            # no patient who has been diagnosed with cancer prior to the screen window attended the screen
            # cancer diagnosis later the screening years(0-2) is not of concern
            if cancer_yr == year:
                cancer_paragraph += "Subsequent examinations after this screening have confirmed lung cancer "
                cancer_paragraph += row["de_grade"]
                if row["de_stag"] != "":
                    cancer_paragraph += row["de_stag"]
                else:
                    cancer_paragraph += row["de_stag_7thed"]
                cancer_paragraph += row["de_type"]
                # find the locations of the primary tumor
                locations = [col for col in df_prsn.columns if col.startswith("loc") and row[col] != ""]
                if len(locations) > 0:
                    cancer_paragraph += ". The primary tumor is located in the following location(s): "
                    for loc in locations:
                        cancer_paragraph += row[loc]
                else:
                    cancer_paragraph += "The location of the primary tumor is not identified."

            # abnormalities: sorted by pid, study_yr, and then sct_ab_num
            while ab_iter_idx < df_ctab.shape[0]:
                # print(ab_iter_idx)
                ab_row = df_ctab.iloc[ab_iter_idx].fillna("")  # pick it up from last time
                # break if no more abnormalities for the patient-year
                if ab_row["study_yr"] != year or ab_row["pid"] != pid:
                    # print(ab_row["study_yr"], year, ab_row["pid"], pid)
                    break
                # increment the counter and the iteration pointer
                ab_iter_idx += 1
                # add descriptions of the current abnormality
                ab_report = header + "Abnormality #" + str(ab_row["sct_ab_num"]) + " of the patient "
                ab_report += ab_row["sct_ab_desc"] + ab_row["sct_epi_loc"] + ab_row["sct_long_dia"] \
                                + ab_row["sct_slice_num"] + ab_row["sct_perp_dia"] \
                                + ab_row["sct_margins"] + ab_row["sct_pre_att"] + ".\n"
                # add the cancer paragraph
                ab_report += cancer_paragraph
                # write reports
                write_report(pid, year, ab_row["sct_ab_num"], ab_row["sct_slice_num"], ab_report)
            #if pid == 100505 or pid == 100518 or pid ==100560 or pid ==100570 or pid ==100574 or pid ==100580 or pid ==100619 or pid ==100658 or pid ==100670 or pid ==100681 or pid ==100684 or pid ==100687 or pid ==100697 or pid ==100698:
            #    print(report)

    return
