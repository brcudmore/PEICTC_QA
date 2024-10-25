print("~ Ad-Hoc Jaw Junctions ~\n")
print("Please wait while the app loads.\n")

import pydicom as dicom
import matplotlib.pyplot as plt
import numpy as np
from scipy.signal import find_peaks, medfilt
import datetime as datetime
import os

from time import sleep


### 

# Create by Ben Cudmore
# Package this code as an executable by running the following line in the terminal:
# pyinstaller -F --hiddenimport=pydicom.encoders.gdcm --hiddenimport=pydicom.encoders.pylibjpeg --clean evaluating_jaw_junctions.py

# START READING AFTER FUNCTIONS DEFINED

###

def find_film_roi(pixel_array):

    # this function find the exposed film by iterating over every nth row and column 
    # to find pixel values over a threshold.

    # the threshold value needs to be 40,000 for EBT3 and 5,000 for EBT4
    
    threshold = 40000

    film_rows = []
    film_columns = []

    # pixel_array is heavily blurred so gaps between film strips are not detected
    blurred_pixel_array = medfilt(pixel_array, 21)
    count = 0
    while len(film_rows) <= 1:
        count+=1
        for i in range(10, blurred_pixel_array.shape[1], 10):
            search = blurred_pixel_array[:, i].max()
            if search > threshold:
                film_columns.append(i)

        for i in range(10, blurred_pixel_array.shape[0], 10):
            search = blurred_pixel_array[i, :].max()
            if search > threshold:
                film_rows.append(i)

        threshold = 4000

        if count >= 2:
            break

    return {
        'rows': film_rows,
        'columns': film_columns}

def get_roi_indices(irradiated_film):
    
    # This function defines the four corners of the roi minus a buffer to prevent 
    # the plastic holding down film from interfering with results.
    
    roi_indices = {}
    roi_factor = 0.85
    
    for key in irradiated_film:
        #look at (e.g.) rows first
        direction = irradiated_film[key]
        # find start and end of roi
        film_width = direction[-1] - direction[0]

        center_of_film = (film_width // 2) + direction[0]

        # want to avoid plastic holding film down so add extra trim
        if 'column' in key:
            roi_factor = 0.75

        # divide by two so you can align roi with center of exposed film 
        measurement_window = int((film_width * roi_factor) / 2)

        # save roi corners
        roi_indices[key] = [center_of_film - measurement_window, center_of_film + measurement_window]

    return roi_indices

def identify_individual_film_strip_edges(roi):

    # this function ensures the threshold value (minprominence) for identifying individual film strips
    expected_film_strip_count = input("Please enter the number of irradiated film present\n")
    print("\n")
    film_strip_count = 0
    max_prominence = 300
    min_prominence = 50

    try:
        expected_film_strip_count = int(expected_film_strip_count.strip(" "))
    except:
        expected_film_strip_count = int(input("\nPlease enter an integer\n").strip(" "))

    while expected_film_strip_count != film_strip_count:
    
        min_prominence += 20
        peaks = []
        edges = []

        search = np.abs(np.gradient(np.mean(roi[:, 40:70], 1)))

        # added max prominence of 5000 so that unused film is not detected
        peaks, _ = find_peaks(search, prominence = [min_prominence, 5000], distance = 50)
        
        ### run this code to see the plots
        # plt.imshow(roi)
        # plt.show()

        # plt.plot(search)
        # plt.show()
        ###

        # The beginning and ending indices of the roi are counted as edges along with peaks
        edges = np.concatenate(([0], peaks, [roi.shape[1]]))
        film_strip_count = len(edges) - 1

        # Something is wrong if prominence reaches 0. This prevents the loop from running indefinitely
        if min_prominence >= max_prominence:
            print("The code could not find exactly {} exposed film strips.\nMake sure all exposed film are adjacent to eachother in the exposed scan.\n".format(expected_film_strip_count))
            sleep(1)
            return(False, False)

    return(edges, film_strip_count)

def calculate_junction(pixel_array: np.ndarray, roi_indices: dict, window: int = 25):

    global pixel_spacing
    global save_figures
    global dir_path
    global film_strip_ids

    row = roi_indices['rows']
    column = roi_indices['columns']

    # Use four corners to get full roi from pixel_array
    roi = pixel_array[row[0]:row[1], column[0]: column[1]]
    film_strip_count = False

    while film_strip_count == False:
        film_edges, film_strip_count = identify_individual_film_strip_edges(roi)

    # Plot a preview of the ROI
    plt.imshow(roi, cmap='YlGnBu')
    plt.title("Irradiated Film Strips")
    plt.show()
    
    # Asks user for input necessary for labeling figures if they are to be saved
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
        # Generic film names if not saving figures
        film_strip_ids = list(range(film_strip_count+1))

    # Process each film strip one at a time
    for i in range(len(film_edges)-1):
        
        # Find center of film along the short length
        film_strip_center = int(((film_edges[i+1] - film_edges[i]) / 2) + film_edges[i])
        film_strip_roi = roi[film_strip_center - window : film_strip_center + window, :]

        # Normalize mean to 100
        film_strip_roi_norm = normalize_to_mean(film_strip_roi)

        # create profile by averaging rows
        film_strip_profile = np.mean(film_strip_roi_norm, 0)
        print("\nProcessing {}".format(film_strip_ids[i]))
        

        junction_dose = search_for_junction(film_strip_profile)

        # Plot results
        fig, axs = plt.subplots(2, 1, figsize=(10, 8))

        axs[0].imshow(film_strip_roi_norm, vmin=80, vmax=110, cmap = 'YlGnBu')

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

    # Junction assumed to be the largest positive or negative peak
    film_max = film_strip_profile.max()
    film_min = film_strip_profile.min()

    # returns absolute value
    junction = max(film_max-100, 100 - film_min)

    if junction < 5:
        print('The junction dose is less than |5%|\n')
        return 'Less than |5%|'
    elif junction < 10:
        print('The junction dose is less than |10%|\n')
        return 'Less than |10%|'
    elif junction > 10:
        print('The junction dose is Greater than |10%|\n')
        return 'Greater than |10%|'

def normalize_to_mean(array):
    clipped_array = array[:, 40:array.shape[1]-40]
    array_mean = np.mean(clipped_array)
    array = (clipped_array / array_mean) * 100

    return array


file_path1 = "T:\\QA\\Data\\JawCalibration\\TrueBeam5833\\2024-10\\Results\\testing2\\FilmQA_EBT-Dose_LRA-Lewis_MedFilt-9px.dcm"
file_path0 = "T:\\QA\\Data\\JawCalibration\\TrueBeam5833\\2024-10\\Results\\FilmQA_EBT-Dose_LRA-Lewis_MedFilt-9px.dcm"

file0 = dicom.dcmread(file_path0).pixel_array
file1 = dicom.dcmread(file_path1).pixel_array

file_diff = file0-file1
plt.imshow(file_diff)
plt.show()

file_path = ""
pixel_spacing: float
save_figures = True

input_folder = input("Drag and drop the folder containing the files to be processed.\n").replace("& ", "").strip("'").strip('"')

# Process each dicom dose plane in the selected folder
# Dicom dose planes are create in MATLAB by entering filmqa in the command line

for dir_path, dir_names, file_names in os.walk(input_folder):
    for file in file_names:
        if ".dcm" in file:
            file_path = os.path.join(dir_path, file)
            print("\nProcessing {}\n".format(file))

            # Access the pixel array
            dicom_info = dicom.dcmread(file_path)
            pixel_array = dicom_info.pixel_array
            pixel_spacing = dicom_info.PixelSpacing[0]

            # Evaluate jaw junctions
            film_roi = find_film_roi(pixel_array)
            roi_indices = get_roi_indices(film_roi)
            calculate_junction(pixel_array, roi_indices)
