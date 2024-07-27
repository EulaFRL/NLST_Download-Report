from retrieve_positive import *
from report_composer import report_composer
import pandas as pd
import os
from config import *


def main():
    # report_composer()
    # read into DF
    df_ctab = pd.read_csv(os.path.join(INPUT_DIR, "nlst_780_ctab_idc_20210527.csv"))
    # retrieve the images
    ctab_api_dict = ctab_2_dict(df_ctab)
    pid_set = list(set(key[0] for key in ctab_api_dict.keys()))
    pid_set = sorted(pid_set)
    retrieve_positive(pid_set, ctab_api_dict, df_ctab)
    # # remove no image pid / no good image pid--study_yr from
    # DF
    # # and save the csv of the filtered ctab
    # pid_set = remove_from_ctabDF(df_ctab)  # overwrites original csv
    # remove_from_prsn(pid_set)  # overwrites original csv
    # read from filtered csv and compose the reports, one for each abnormality
    # report_composer()


if __name__ == '__main__':
    main()
