from download_3d import *
from compose_text import *
from config import ABN_CSV_PATH, PRSN_CSV_PATH, POS_IMAGE_FOLDER, NEG_IMAGE_FOLDER, PARQUET_PATH, REPORT_FOLDER

import pandas as pd
import os
import random

def main():
    abnormalities = pd.read_csv(ABN_CSV_PATH)
    all_patient_years = set((row['pid'], row['study_yr']) for _,row in pd.read_csv(PRSN_CSV_PATH, names=['pid', 'study_yr']).iterrows())
    
    cvd_pos_list = list(set((row['pid'], row['study_yr']) for _,row in abnormalities[abnormalities['sct_ab_desc'] == 60].iterrows()))
    # avoid all scans where the patient has been labeled CVD positive but not in that year, because their CVD labels are unclear
    cvd_pos_pid = (pid for pid,yr in cvd_pos_list)
    scans_to_avoid = [(pid,yr) for pid,yr in all_patient_years if pid in cvd_pos_pid and (pid,yr) not in cvd_pos_list]
    
    #extract the nodule(lung cancer or not) sclice numbers into a dictionary with (pid,year):[list of lung nodule slice numbers]
    nodule_slice_dict = dict()
    for _,row in abnormalities[abnormalities['sct_ab_desc'] == 51].iterrows():
        if (row['pid'], row['study_yr']) not in nodule_slice_dict.keys():
            nodule_slice_dict[(row['pid'], row['study_yr'])] = []
        nodule_slice_dict[(row['pid'], row['study_yr'])].append(row['sct_slice_num'])

    lung_pos_list = list(set((row['pid'], row['study_yr']) for _,row in abnormalities[abnormalities['sct_ab_desc'] == 51].iterrows()))
    lung_pos_list = [x for x in lung_pos_list if x not in scans_to_avoid]

    # get the list of (pid,yr) that contains positive lung cancer nodules(51 nodules) and download the images to POS_IMAGE_FOLDER
    lung_pos_failed = download_list(lung_pos_list, POS_IMAGE_FOLDER)
    lung_pos_list = [x for x in lung_pos_list if x not in lung_pos_failed]

    # get the list of (pid,yr) that contains positive CVD nodules and check whether they are in the positive list, if not, put into the lung_neg_cvd_pos list and download to NEG_IMAGE_FOLDER
    lung_neg_cvd_pos_list = [x for x in cvd_pos_list if x not in lung_pos_list and x not in scans_to_avoid]
    lung_neg_cvd_pos_failed = download_list(lung_neg_cvd_pos_list, NEG_IMAGE_FOLDER)
    lung_neg_cvd_pos_list = [x for x in lung_neg_cvd_pos_list if x not in lung_neg_cvd_pos_failed]

    # download a named amount of lung negative cases by random sampling after excluding the positive cases
    lung_neg_count = len(lung_pos_list)
    lung_neg_list = random.sample([x for x in all_patient_years if x not in lung_pos_list and x not in scans_to_avoid], lung_neg_count)
    lung_neg_failed = download_list(lung_neg_list, NEG_IMAGE_FOLDER)
    lung_neg_list = [x for x in lung_neg_list if x not in lung_neg_failed]

    #generate reports
    # report_composer() # write reports for all scans that contains a nodule

    generate_parquet(nodule_slice_dict, lung_pos_list, cvd_pos_pid, lung_neg_cvd_pos_list, lung_neg_list, PARQUET_PATH)

def generate_parquet(nodule_slice_dict, lung_pos_list, cvd_pos_pid, lung_neg_cvd_pos_list, lung_neg_list, out_path):
    """each row in parquet ~ one scan(one 3d series): 
    patient id, year, unique id, 
    [lung pos slice numbers],
    scan lung cancer report,
    scan lung cancer label,
    scan CVD label

    2D slices are stored with filenames pid_year_abnormalityIndex_sliceNumber.jpg and they should be uniquely identifiable without abnormalityIndex
    3D images are stored with filenames pid_year.npy or .nii
    """

    patient_ids = []
    years = []
    unique_ids = []
    lung_pos_slice_numbers_s = []
    scan_lung_cancer_reports = []
    scan_lung_cancer_labels = []
    scan_CVD_labels = []

    for pid,yr in lung_pos_list:
        patient_ids.append(pid)
        years.append(yr)
        unique_ids.append(f"{pid}_{yr}")
        lung_pos_slice_numbers_s.append(nodule_slice_dict[(pid,yr)])

        with open(os.path.join(REPORT_FOLDER, f"{pid}_{yr}.txt")) as report_file:
            report = report_file.read()
        scan_lung_cancer_reports.append(report)

        scan_lung_cancer_labels.append(1)
        if pid in cvd_pos_pid:
            scan_CVD_labels.append(1)
        else:
            scan_CVD_labels.append(0)

    #report for scans with no nodule identified, since it is not already written
    no_nodule_report = """
    Isolation reading of the image gives the preliminary result of negative screen. No abnormalities were identified in this screening.
    """
    
    for pid,yr in lung_neg_cvd_pos_list:
        patient_ids.append(pid)
        years.append(yr)
        unique_ids.append(f"{pid}_{yr}")
        lung_pos_slice_numbers_s.append([])
        
        if (pid,yr) in nodule_slice_dict.keys:
            scan_lung_cancer_reports.append(nodule_slice_dict[(pid,yr)])
        else:
            scan_lung_cancer_reports.append(no_nodule_report)

        scan_lung_cancer_labels.append(0)
        scan_CVD_labels.append(1)

    for pid,yr in lung_neg_list: #lung neg and cvd neg
        patient_ids.append(pid)
        years.append(yr)
        unique_ids.append(f"{pid}_{yr}")
        lung_pos_slice_numbers_s.append([])

        if (pid,yr) in nodule_slice_dict.keys:
            scan_lung_cancer_reports.append(nodule_slice_dict[(pid,yr)])
        else:
            scan_lung_cancer_reports.append(no_nodule_report)

        scan_lung_cancer_labels.append(0)
        scan_CVD_labels.append(0)
    
    df = pd.DataFrame({
        "patient_id" : patient_ids,
        "year" : years,
        "unique_id" : unique_ids,
        "lung_pos_slice_numbers" : lung_pos_slice_numbers_s,
        "scan_lung_cancer_reports" : scan_lung_cancer_reports,
        "scan_lung_cancer_labels" : scan_lung_cancer_labels,
        "scan_CVD_labels" : scan_CVD_labels 
    })

    print("Converted to DataFrame, Start Saving as .parquet")

    df.to_parquet(out_path, index=False)

if __name__ == '__main__':
    main()