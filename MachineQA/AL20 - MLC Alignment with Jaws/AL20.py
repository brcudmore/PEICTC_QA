import pydicom as dicom
import os
import matplotlib.pyplot as plt
from scipy.ndimage import median_filter
from scipy.signal import find_peaks, savgol_filter
import numpy as np
import sys
sys.path.append("T:\\_Physics Team PEICTC\\Benjamin\\GitHub\\PEICTC_QA")
from Helpers.QATrackHelpers import QATrack as qat

# create executable by running the following in the terminal while in the directory of the .py file
# pyinstaller -F --hiddenimport=pydicom.encoders.gdcm --hiddenimport=pydicom.encoders.pylibjpeg --hiddenimport=pyTQA.tqa --clean AL20.py

# the folder will be too large to push to github
# move to folder on T drive


# create shortcut for relevant folder in "T:\QA\Data"


image_info = {          # placeholder for relevant dicom headers
    "machine": '',
    "date": '',
    "pixel array": ''
}

development = False     # Change to True to see image and columns defined below

column_window = 20      # sets number of pixels used in ROI
column1 = 395           # 395 - Through base of MLC leaf B and tip of MLC Leaf A
column2 = 875           # 875 - Through base of MLC leaf A and tip of MLC Leaf B

repeat_analysis = 'y'   # user has option while executable is running to process multiple datasets

qat.log_into_QATrack()  # references windows user to to sign into QATrack


def get_image_info(image_path):
    image = dicom.read_file(image_path)
    image_info["machine"] = image['RadiationMachineName'].value
    image_info["date"] = qat.format_date(image)
    image_info["pixel array"] = median_filter(image.pixel_array, 5)

    return image_info


def process_image(column1, column2):
    column1_results = process_column(column1)
    column2_results = process_column(column2)

    run = column2 - column1
    angle_degrees = []

    for bank in column1_results:
        # banks need to be treated differently in order for a negative result to consistently 
        # indicate a clockwise skew
        
        if 'Bank A' in bank:
            rise = (column2_results[bank]['mlc'] - column2_results[bank]['jaw']) - \
                (column1_results[bank]['mlc'] - column1_results[bank]['jaw'])
        else:
            rise = (column1_results[bank]['mlc'] - column1_results[bank]['jaw']) - \
                (column2_results[bank]['mlc'] - column2_results[bank]['jaw'])
        

        angle_degrees.append(np.degrees(np.arctan(rise / run)))
    
    return {
        "mlc_bank_a_alignment": np.round(angle_degrees[0], 1),
        "mlc_bank_b_alignment": np.round(angle_degrees[1], 1)
    }

def process_column(column):

    # calculates average derivate of ROIs then finds jaws and mlc
    column = np.mean(pixel_data[:, column-column_window: column], axis = 1)
    column_gradient = savgol_filter(abs(np.gradient(column)), 7, 3)
    y1, y2 = find_jaws(column_gradient)
    bank_a,  bank_b = find_MLC(column_gradient)

    if development == True:
        plt.plot (column_gradient)
        plt.show()

    return {
        'bank a' : {
            'mlc': bank_a, 
            'jaw': y1},
        'bank b' : {
            'mlc': bank_b,
            'jaw': y2
        }
    }

def find_jaws(column_gradient):

    # find large changes in HU value
    peaks_found, _ = find_peaks(column_gradient, prominence= 100)
    y1 = peaks_found[-1]
    y2 = peaks_found[0]
    return y1, y2


def find_MLC(column_gradient):

    # similar process to find_jaws but inverted and shifted to find center of MLC leaf
    manipulated_column = -column_gradient + column_gradient.max()
    peaks_found, _= find_peaks(manipulated_column, prominence=100)

    bank_b_leaf = peaks_found[0]
    bank_a_leaf = peaks_found[-1]
    return bank_a_leaf, bank_b_leaf


def show_plots():
    plt.imshow(pixel_data, cmap = 'gray')
    plt.axis('off')
    plt.title('MV Image and ROIs for Analysis')
    plt.plot([column1, column1], [390, 890])
    plt.plot([column2, column2], [390, 890])
    plt.show()


print("\n~  AL20 - MLC Leaf Alignment with Jaws  ~\n")

while 'y' in repeat_analysis.lower():

    image_path = input("Drag and drop the file to be processed.\n").replace("& ", "").strip("'").strip('"')
    image_info = get_image_info(image_path)
    pixel_data = np.array(image_info["pixel array"])
    results = process_image(column1, column2)

    if development == True:
        show_plots()

    utc_url, macros = qat.get_unit_test_collection(image_info['machine'], "MLC leaf alignment with jaws")

    if macros == None:
        continue
    
    tests = qat.format_results(macros, results)
    qat.post_results(utc_url, tests, image_info['date'])

    if development == True:
        show_plots()
    
    repeat_analysis = input("Do you want to process another file? (y/n)")