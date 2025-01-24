"""
download 3d series and save with patient id and year in filename for identification
"""
import logging
import shutil
import pydicom
import numpy as np
import os
import requests
import zipfile
from requests.adapters import HTTPAdapter, Retry
import nibabel as nib

from config import DOWNLOAD_LOG, BASE_URL


# Configure logging
logging.basicConfig(
    filename=DOWNLOAD_LOG, 
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

def download_list(pid_yr_tuples, image_folder):
    failed_list = []
    for pid, yr in pid_yr_tuples:
        dicom_dir = download_series(pid, yr, image_folder)
        if dicom_dir:
            dicom2Npy(dicom_dir, image_folder, de=True) # deletes the dicom file after transferring
            #TODO: dicom2Nifti(dicom_dir, IMAGE_FOLDER, de=True)
        else: # download failed
            failed_list.append((pid,yr))
    return failed_list

def download_series(patient_id, year, output_dicom_folder):
    #TODO: need specific type of reconsturction?
    series_list = get_series_list(patient_id)
    if not series_list:
        logging.warning(f"No series found for Patient ID {patient_id}")
        return

    series = find_valid_series(series_list, year)
    if not series:
        logging.warning(f"No valid series found for Patient ID {patient_id} and year {year}")
        return

    series_instance_uid = series["SeriesInstanceUID"]
    series_dir = os.path.join(output_dicom_folder, f"Patient_{patient_id}_Year_{year}")

    download_helper(series_instance_uid, series_dir)
    logging.info(f"Downloaded and extracted series to {series_dir}")

    return series_dir

def get_series_list(patient_id):
    """
    Retrieves the list of series for a given patient ID.

    :param patient_id: ID of the patient
    :return: List of series (JSON response)
    """
    url = f"{BASE_URL}/getSeries"
    params = {'PatientID': patient_id}
    response = requests.get(url, params=params)
    if response.status_code == 200:
        return response.json()
    else:
        print(url,params)
        logging.error(f"Failed to fetch series for Patient ID {patient_id}. Status code: {response.status_code}")
        return []

def find_valid_series(series_list, year):
    """
    Finds the first series for the given year with more than 50 slices.

    :param series_list: List of series
    :param year: Study year
    :return: Series JSON object or None if no valid series found
    """
    for series in series_list:
        description_parts = series.get("SeriesDescription", "").split(",")
        if (
            len(description_parts) > 0 and
            description_parts[0] == str(year) and
            int(series.get("ImageCount", 0)) > 50
        ):
            return series
    return None

def download_helper(series_instance_uid, output_dir):
    """
    Downloads and extracts a series to the specified directory.

    :param series_instance_uid: SeriesInstanceUID to download
    :param output_dir: Directory to extract the DICOM files
    """
    retry_strategy = Retry(
        total=10,
        backoff_factor=1,
        status_forcelist=[429, 500, 502, 503, 504],
        allowed_methods=["HEAD", "GET", "OPTIONS"]
    )
    adapter = HTTPAdapter(max_retries=retry_strategy)
    session = requests.Session()
    session.mount("https://", adapter)
    session.mount("http://", adapter)

    url = f"{BASE_URL}/getImage"
    params = {'SeriesInstanceUID': series_instance_uid}

    os.makedirs(output_dir, exist_ok=True)
    series_file_path = os.path.join(output_dir, "series.zip")

    try:
        response = session.get(url, params=params, stream=True, timeout=(30, 60))
        response.raise_for_status()

        with open(series_file_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)

        with zipfile.ZipFile(series_file_path, 'r') as zip_ref:
            zip_ref.extractall(output_dir)

        os.remove(series_file_path)
    except requests.exceptions.RequestException as e:
        logging.error(f"Failed to download or extract series: {e}")


def dicom2Npy(dicom_folder, npy_folder, de=False):
    """ stores one 3D dicom series as one .npy file"""
    slice_dir_list = os.listdir(dicom_folder)
    dicom_files = [pydicom.dcmread(os.path.join(dicom_folder, slice_dir)) for slice_dir in slice_dir_list if slice_dir.endswith('.dcm')]
    
    dicom_files.sort(key = lambda x : x.InstanceNumber) #InstanceNumber is an attribute of a dicom image that indicates its position in a series
    dicom_pixelArrays = [ds.pixel_array for ds in dicom_files] #extracts the image from the dicom files as 2D pixel arrays
    
    volume = np.stack(dicom_pixelArrays) #stacks into a 3D volume

    npy_name = os.path.basename(os.path.normpath(dicom_folder)) + ".npy"
    np.save(os.path.join(npy_folder,npy_name), volume)

    if de:
        shutil.rmtree(dicom_folder)
        print(f"DICOM folder {dicom_folder} has been deleted.")

def dicom2Nifti(dicom_folder, output_nifti_folder, voxel_size=(1.0, 1.0, 1.0), de=False):
    """
    Converts a 3D DICOM series to a NIfTI file.
    """
    try:
        # Get all DICOM files in the folder
        slice_dir_list = os.listdir(dicom_folder)
        dicom_files = [pydicom.dcmread(os.path.join(dicom_folder, slice_dir)) for slice_dir in slice_dir_list if slice_dir.endswith('.dcm')]

        # Sort DICOM files by InstanceNumber to ensure proper stack order
        dicom_files.sort(key=lambda x: x.InstanceNumber)
        dicom_pixelArrays = [ds.pixel_array for ds in dicom_files]

        # Stack the 2D pixel arrays to create a 3D volume
        volume = np.stack(dicom_pixelArrays)

        # Create an affine transformation matrix (assuming isotropic voxel spacing)
        affine = np.diag(voxel_size + (1.0,))

        # Create a NIfTI image
        nifti_img = nib.Nifti1Image(volume, affine)

        output_nifti_name = os.path.basename(os.path.normpath(dicom_folder)) + ".nii"
        output_nifti_file = os.path.join(output_nifti_folder, output_nifti_name)
        # Save the NIfTI file
        nib.save(nifti_img, output_nifti_file)
        print(f"NIfTI file saved successfully at {output_nifti_file}")

        # Optionally delete the original DICOM folder
        if de:
            shutil.rmtree(dicom_folder)
            print(f"DICOM folder {dicom_folder} has been deleted.")

    except Exception as e:
        logging.error(f"An error occurred: {e}")

def npy_to_nifti(npy_file, output_nifti_file, voxel_size=(1.0, 1.0, 1.0)):
    """
    Converts a 3D lung scan stored in a .npy file to NIfTI format.

    Parameters:
    - npy_file (str): Path to the input .npy file.
    - output_nifti_file (str): Path for the output NIfTI file.
    - voxel_size (tuple): Tuple of 3 floats defining the voxel size (default is (1.0, 1.0, 1.0)).
    
    Returns:
    - None
    """
    try:
        # Load the 3D array from the .npy file
        lung_scan = np.load(npy_file)
        
        # Validate the input data
        if len(lung_scan.shape) != 3:
            raise ValueError("The input .npy file must contain a 3D array.")

        # Create an affine transformation matrix
        affine = np.diag(voxel_size + (1.0,))
        
        # Create a NIfTI image
        nifti_img = nib.Nifti1Image(lung_scan, affine)
        
        # Save the NIfTI image (uncompressed by specifying .nii extension)
        nib.save(nifti_img, output_nifti_file)
        print(f"NIfTI file saved successfully at {output_nifti_file}")
    except Exception as e:
        logging.error(f"An error occurred: {e}")

if __name__ == '__main__':

    dicom2Npy('/Users/eulawang/Downloads/manifest-1736476126248/NLST/100002/01-02-2000-NA-NLST-LSS-11765/1.000000-1OPAGELSPLUSD3602.512080.00.11.5-72875',
    '/Users/eulawang/Desktop/NLSTPreprocessing/data/3dNpy','100002_1_second.npy', de=False)
    npy_to_nifti("/Users/eulawang/Desktop/NLSTPreprocessing/data/3dNpy/100002_1_second.npy", "100002_1_second.nii", voxel_size=(1.0, 1.0, 1.0))

    # nifti_to_dicom('/Users/eulawang/Downloads/7.nii', '/Users/eulawang/Downloads')
    
    # test_read = np.load('/Users/eulawang/Desktop/NLSTPreprocessing/data/3dNpy/100002_0.npy')
    # print(f'numpy array shape: {test_read.shape}')