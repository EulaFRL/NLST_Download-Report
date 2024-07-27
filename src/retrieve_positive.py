import pydicom
import requests
import time
import pydicom
from pydicom.filewriter import write_file
from PIL import Image
import pandas as pd
import numpy as np
import os
import zipfile
import shutil
from collections import Counter
from config import INPUT_DIR, OUTPUT_DIR, IMAGE_OUTPUT_DIR, BASE_URL
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

def download_series(seriesFilePath, base_url, seriesInstanceUID, seriesDir):
    # Configure retries
    retry_strategy = Retry(
        total=10,  # Total number of retries
        backoff_factor=1,  # Time to wait between retries (e.g., 1, 2, 4 seconds)
        status_forcelist=[429, 500, 502, 503, 504],  # HTTP status codes to trigger a retry
        allowed_methods=["HEAD", "GET", "OPTIONS"]  # HTTP methods to retry
    )
    adapter = HTTPAdapter(max_retries=retry_strategy)
    session = requests.Session()
    session.mount("https://", adapter)
    session.mount("http://", adapter)

    url_DL = f"{base_url}/getImage"
    params_DL = {'SeriesInstanceUID': seriesInstanceUID}

    try:
        response_DL = session.get(url_DL, params=params_DL, stream=True, timeout=(30, 60))
        response_DL.raise_for_status()  # Raise an HTTPError for bad responses
        with open(seriesFilePath, 'wb') as f:
            print("start writing the Series", seriesInstanceUID)
            for chunk in response_DL.iter_content(chunk_size=8192):
                f.write(chunk)
        print("Series downloaded successfully:", seriesInstanceUID)
        # Extract the zip file
        with zipfile.ZipFile(seriesFilePath, 'r') as zip_ref:
            zip_ref.extractall(seriesDir)
            os.remove(seriesFilePath)
        print("unzipped successfully")
    except requests.exceptions.ChunkedEncodingError as e:
        print("ChunkedEncodingError occurred:", e)
    except requests.exceptions.RequestException as e:
        print("RequestException occurred:", e)



def ctab_2_dict(df_ctab):
    """
    extract the relevant information for download requests from ctab
    :return: a dictionary dict[(pid, study_yr) : list[(sct_ab_num, sct_slice_num),]]
    """
    # Initialize an empty dictionary to store the result
    ctab_api_dict = {}

    # Group by 'pid' and 'study_yr', and iterate over each group (相当于横着切成几段)
    for (pid, study_yr), group in df_ctab.groupby(['pid', 'study_yr']):
        # Create a list of tuples for each group
        slice_list = list(zip(group['sct_ab_num'], group['sct_slice_num']))
        # Store in dictionary with key as (pid, study_yr)
        ctab_api_dict[(pid, study_yr)] = slice_list

    return ctab_api_dict


pids_to_remove = []  # no image pid
no_good_image = []  # no complete image (pid,year)


def retrieve_positive(np_pids, ctab_api_dict, df_ctab):
    """
    :param np_pids: numpy array of unique pids in ctab
    :return:
    """
    global pids_to_remove, no_good_image
    # iterate over pids
    for pid in np_pids:
        if pid < 113295: continue
        print("pid:", pid)
        # getSeries and delete patients without images
        url = f"{BASE_URL}/getSeries"
        params = {'PatientID': pid}
        response = requests.get(url, params=params)
        if response.status_code == 200 and len(response.content) == 0: # no images
            pids_to_remove.append(pid)
            print("no images!")
        else:  # with images
            print("there are images for this patient!")
            series_list = response.json()
            for study_yr in range(3):
                # if(study_yr != 1): continue
                print("study_yr", study_yr)
                if (pid, study_yr) in ctab_api_dict.keys():  # there are 51 abs in this patient-year
                    print("there are 51 abs in  this pid--year!")
                    maxSliceNum = max(ab[1] for ab in ctab_api_dict[(pid, study_yr)])  # the largest slice number
                    SeriesInstanceUID = None
                    for series in series_list:
                        description_parts = series.get("SeriesDescription", "").split(",")
                        # conditions: study year, not positioning scan, complete series(>= largest slice number)
                        if description_parts[0] == str(study_yr) \
                                and description_parts[1].strip() == "OPA" \
                                and int(series.get("ImageCount", "")) >= maxSliceNum:
                            SeriesInstanceUID = series["SeriesInstanceUID"]
                            break  # retrieve the first series that satisfies the conditions
                    if SeriesInstanceUID == None:
                        print("No series that satisfies this condition: " + str(pid) + ", " + str(study_yr))
                        no_good_image.append((pid, study_yr))
                        print(no_good_image[-1])
                        continue  # to next patient-year
                    # download the pid-year series
                    # url_DL = f"{BASE_URL}/getImage"
                    # params_DL = {'SeriesInstanceUID': SeriesInstanceUID}
                    # while True:
                    #     try:
                    #         response_DL = requests.get(url_DL, params=params_DL, stream=True, timeout=120)
                    #         response_DL.raise_for_status()  # Raise an exception if the request failed
                    #         break  # Exit the loop if the request was successful
                    #     # except requests.exceptions.Timeout:
                    #     #     print("Request timed out. Waiting for 30 seconds before retrying...")
                    #     #     time.sleep()  # Wait for 30 seconds before retrying
                    #     except requests.exceptions.Timeout as e:
                    #         # Handle timeout exceptions
                    #         print(f"Request timed out: {e}, sleep and retry")
                    #         time.sleep(30)
                    #     except requests.exceptions.ConnectionError as e:
                    #         # Handle connection-related exceptions
                    #         print(f"Connection error: {e}, sleep and retry")
                    #         time.sleep(30)
                    #     except Exception as e:
                    #         time.sleep(30)
                    #         # break  # Exit the loop if the request failed for other reasons
                    seriesFilePath = os.path.join(IMAGE_OUTPUT_DIR, str(pid) + '_' + str(study_yr) + '.zip')
                    # with open(seriesFilePath, 'wb') as f:
                    #     print("start writing the Series", SeriesInstanceUID)
                    #     for chunk in response_DL.iter_content(chunk_size=8192):  # @todo: adjust chunk_size for speed
                    #         f.write(chunk)
                    # print("finished writing")
                    seriesDir = os.path.join(IMAGE_OUTPUT_DIR, str(pid) + '_' + str(study_yr))
                    download_series(seriesFilePath, BASE_URL, SeriesInstanceUID, seriesDir)
                    # load dicom series
                    dicom_files = [pydicom.dcmread(os.path.join(seriesDir, f)) for f in os.listdir(seriesDir) if
                                   f.endswith('.dcm')]
                    # Sort the files based on Instance Number or Image Position Patient
                    dicom_files.sort(key=lambda x: int(x.InstanceNumber))
                    # clear the original directory
                    for filename in os.listdir(seriesDir):
                        file_path = os.path.join(seriesDir, filename)
                        try:
                            if os.path.isfile(file_path) or os.path.islink(file_path):
                                os.unlink(file_path)
                            elif os.path.isdir(file_path):
                                shutil.rmtree(file_path)
                        except Exception as e:
                            print(f'Failed to delete {file_path}. Reason: {e}')
                    # write the slices associated with 51 abs back
                    slicesN2Name = {ab[1]: str(ab[1]).zfill(8) + '.dcm' for ab in ctab_api_dict[(pid, study_yr)]}
                    for slice_n in slicesN2Name.keys():
                        slice_filename = os.path.join(seriesDir, slicesN2Name[slice_n])
                        write_file(slice_filename, dicom_files[slice_n - 1])  # convert from 1-based to 0-based index
                    # for slice in os.listdir(seriesDir):
                    #    file_path = os.path.join(seriesDir, slice)
                    #   if slice not in slicesN2Name.values():
                    #       os.remove(file_path)
                    # traverse through the 51 abs in this patient-year, convert to jpeg, rename the files
                    sliceCount = Counter(ab[1] for ab in ctab_api_dict[(pid, study_yr)])
                    for (abs_n, slice_n) in ctab_api_dict[(pid, study_yr)]:
                        old_name = os.path.join(seriesDir, slicesN2Name[slice_n])
                        new_name = os.path.join(seriesDir,
                                                str(pid) + '_' + str(study_yr) + '_' + str(abs_n) + '_' + str(
                                                    slice_n) + '.jpg')
                        # convert dicom to jpeg
                        dcm_img = pydicom.read_file(old_name)
                        img_2d = dcm_img.pixel_array.astype(float)
                        scaled_img = (np.maximum(img_2d, 0) / img_2d.max()) * 255.0
                        scaled_img = np.uint8(scaled_img)
                        img = Image.fromarray(scaled_img)
                        img.save(new_name)
                        if sliceCount[slice_n] > 1:  # there are other abnormalities on the slide who haven't got a file
                            sliceCount[slice_n] -= 1  # reduce the count, do not remove the old image
                        else:  # remove the old image
                            os.remove(old_name)

    return


def remove_from_ctabDF(df_ctab):
    # remove from the dataframe pids that do not have an image
    # or patient-years that have incomplete images
    # store in a new csv file

    global pids_to_remove, no_good_image
    mask_pid = df_ctab['pid'].isin(pids_to_remove)
    mask_pid_study_yr = df_ctab.apply(lambda row: (row['pid'], row['study_yr']) in no_good_image, axis=1)
    mask_combined = mask_pid | mask_pid_study_yr
    df_ctab.drop(df_ctab[mask_combined].index, inplace=True)
    os.remove('../51nodules/nlst_780_ctab_idc_20210527.csv')
    df_ctab.to_csv('../51nodules/nlst_780_ctab_idc_20210527.csv',
                   index=False)  # @todo: change name
    pid_set = set(df_ctab["pid"])

    return pid_set


def remove_from_prsn(pidSet):
    # remove the pids without images (keep those within pidSet)
    # store in a new csv file

    df_prsn = pd.read_csv(os.path.join(INPUT_DIR, "nlst_780_prsn_idc_20210527.csv"))
    mask_pid = ~df_prsn['pid'].isin(pidSet)
    # print(mask_pid)
    df_prsn.drop(df_prsn[mask_pid].index, inplace=True)
    os.remove('../51nodules/nlst_780_prsn_idc_20210527.csv')
    df_prsn.to_csv('../51nodules/nlst_780_prsn_idc_20210527.csv',
                   index=False)  # @todo: change name

    return
