print("~ Ad-Hoc Jaw Junctions ~\n")
print("Please wait while the app loads.\n")

import pydicom as dicom
import matplotlib.pyplot as plt
import numpy as np
import cv2
from scipy.signal import find_peaks, medfilt
from scipy.signal import savgol_filter
import datetime as datetime
import os
import sys
import base64

# pyinstaller -F --hiddenimport=pydicom.encoders.gdcm --hiddenimport=pydicom.encoders.pylibjpeg --clean ML14.py

sys.path.append("T:\\_Physics Team PEICTC\\Benjamin\\GitHub\\PEICTC_QA")
from Helpers.QATrackHelpers import QATrack as qat

def find_film_roi(pixel_array):
    film_rows = []
    film_columns = []
    # blur image to not detect gaps between film
    blurred_pixel_array = medfilt(pixel_array, 21)

    for i in range(10, blurred_pixel_array.shape[1], 10):
        search = blurred_pixel_array[:, i].max()
        if search > 45000:
            film_columns.append(i)

    for i in range(10, blurred_pixel_array.shape[0], 10):
        search = blurred_pixel_array[i, :].max()
        if search > 45000:
            film_rows.append(i)

    return {
        'rows': film_rows,
        'columns': film_columns}

def get_roi_indices(irradiated_film):
    roi_indices = {}
    roi_factor = 0.85
    for key in irradiated_film :

        direction = irradiated_film[key]
        film_width = direction[-1] - direction[0]

        center_of_film = (film_width // 2) + direction[0]

        # want to avoid plastic holding film down
        if 'column' in key:
            roi_factor = 0.75

        measurement_window = int((film_width * roi_factor) / 2)

        roi_indices[key] = [center_of_film - measurement_window, center_of_film + measurement_window]

    return roi_indices

def identify_individual_film_strip_edges(roi):
    expected_film_strip_count = input("Please enter the number of irradiated film present\n")
    film_strip_count = 0
    prominence = 1000

    try:
        expected_film_strip_count = int(expected_film_strip_count.strip(" "))
    except:
        expected_film_strip_count = int(input("\nPlease enter an integer\n").strip(" "))

    while expected_film_strip_count != film_strip_count:
        prominence -= 50
        peaks = []
        edges = []

        search = np.abs(np.gradient(np.mean(roi[:, 50:60], 1)))
        peaks, _ = find_peaks(search, prominence = prominence, distance = 50)
        # plt.imshow(roi)
        # plt.show()

        # plt.plot(search)
        # plt.show()
        edges = np.concatenate(([0], peaks, [roi.shape[1]]))
        film_strip_count = len(edges) - 1

    return(edges, film_strip_count)

def calculate_junction(pixel_array: np.ndarray, roi_indices: dict, window: int = 25):
    global pixel_spacing
    global save_figures
    global dir_path
    global film_strip_ids

    row = roi_indices['rows']
    column = roi_indices['columns']
    roi = pixel_array[row[0]:row[1], column[0]: column[1]]
    
    film_edges, film_strip_count = identify_individual_film_strip_edges(roi)

    plt.imshow(roi, cmap='YlGnBu')
    plt.title("Irradiated Film Strips")
    plt.show()
    

    if save_figures == True:
        film_strip_ids = input("\nThere were {} exposed film strips detected.\nPlease enter unique IDs (separated by commas) in the order of left to right in exposed scan.\n".format(film_strip_count))
        film_strip_ids = film_strip_ids.split(",")

        while film_strip_count != len(film_strip_ids):
            film_strip_ids = input("Wrong number of IDs. Please enter {} IDs.\n".format(film_strip_count))
            film_strip_ids = film_strip_ids.split(",")

        count = -1
        for i in film_strip_ids:
            count += 1
            film_strip_ids[count] = i.lstrip(" ")

    else:
        film_strip_ids = list(range(film_strip_count+1))

    for i in range(len(film_edges)-1):

        film_strip_center = int(((film_edges[i+1] - film_edges[i]) / 2) + film_edges[i])
        film_strip_roi = roi[film_strip_center - window : film_strip_center + window, :]
        film_strip_roi_norm = normalize_to_mean(film_strip_roi)
        film_strip_profile = np.mean(film_strip_roi_norm, 0)
        print("\nProcessing {}".format(film_strip_ids[i]))
        ###
        junction_dose = search_for_junction(film_strip_profile)
        ###
        print("\n")

        fig, axs = plt.subplots(2, 1, figsize=(10, 8))

        axs[0].imshow(film_strip_roi_norm, vmin=80, vmax=110, cmap = 'YlGnBu')
        ### needs to be i+1 if not saving figures
        axs[0].set_title('Film Strip ROI {}'.format(film_strip_ids[i]))
        x_values_in_cm = np.arange(len(film_strip_profile)) * float(pixel_spacing) / 10

        axs[1].set_ylim(([89.9, 110.1]))
        axs[1].plot(x_values_in_cm, film_strip_profile)
        axs[1].axhline(y= 95, color = 'orange', linestyle = '--')
        axs[1].axhline(y= 90, color = 'r', linestyle = '--')
        axs[1].axhline(y= 105, color = 'orange', linestyle = '--')
        axs[1].axhline(y= 110, color = 'r', linestyle = '--')

        axs[1].set_title('Film Strip Profile:  Junction Dose {}'.format(junction_dose))
        axs[1].set_ylabel('Dose (%)')
        axs[1].set_xlabel('Distance (cm)')


        plt.tight_layout()
        

        if save_figures:
            save_location = os.path.join(dir_path, "Film Strip {}.png".format(film_strip_ids[i]))
            plt.savefig(save_location)

        plt.show()
        
def search_for_junction(film_strip_profile):

    film_max = film_strip_profile.max()
    film_min = film_strip_profile.min()

    # film previouslt normalized mean to 100

    junction = max(film_max-100, 100 - film_min)

    if junction < 5:
        print('The junction dose is less than |5%|')
        return 'Less than |5%|'
    elif junction < 10:
        print('The junction dose is less than |10%|')
        return 'Less than |10%|'
    elif junction > 10:
        print(junction)
        print('The junction dose is Greater than |10%|')
        return 'Greater than |10%|'

    # if (film_max - film_mean) >= 10:
    #     junction_dose = film_max - film_mean
    
    # elif (film_min - film_mean) <= -10:
    #     junction_dose = film_min - film_mean
    
    # else:
    #     sign = 1
    #     peak_location, peak_qualities = find_peaks(film_strip_profile, prominence= 3)
        
    #     if len(peak_location) == 1:
    #         pass

        
    #     elif len(peak_location) == 0:
    #         # try inverting the dose profile to look for dips in dose
    #         peak_location1, peak_qualities1 = find_peaks(-film_strip_profile, prominence= 3)
    #         sign = -1

    #         if len(peak_location1) == 0:
    #             # no peaks with prominence greater than 3% found in profile or inverted profile
    #             return ('Less than 3%')
    #         else:
    #             peak_qualities = peak_location1
          

    #     junction_dose = peak_qualities['prominences'][0] * sign
    
    # return np.round(junction_dose)


def normalize_to_mean(array):
    ### Need to decide how this is calculated
    # array_max = np.max(array)
    clipped_array = array[:, 40:array.shape[1]-40]
    array_mean = np.mean(clipped_array)
    array = (clipped_array / array_mean) * 100

    return array
   
file_path = ""
pixel_spacing: float
save_figures = True

input_folder = input("Drag and drop the folder containing the files to be processed.\n").replace("& ", "").strip("'").strip('"')

for dir_path, dir_names, file_names in os.walk(input_folder):
    for file in file_names:
        if ".dcm" in file:
            file_path = os.path.join(dir_path, file)
            print("\nProcessing {}\n".format(file))
            dicom_info = dicom.dcmread(file_path)
            pixel_array = dicom_info.pixel_array
            pixel_spacing = dicom_info.PixelSpacing[0]
            film_roi = find_film_roi(pixel_array)
            roi_indices = get_roi_indices(film_roi)
            calculate_junction(pixel_array, roi_indices)
