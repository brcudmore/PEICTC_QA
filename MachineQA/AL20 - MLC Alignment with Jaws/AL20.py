import pydicom as dicom
import os
import matplotlib.pyplot as plt
from scipy.ndimage import median_filter
from scipy.signal import argrelextrema
import numpy as np

image_info = {
    "Machine Name": '',
    "Image Type": '',
    "Image Date": '',
    "Image UID": '',
    "Pixel Data": ''

}
def get_rsd(array_1D):
    rsd = []
    for value in range(len(array_1D-rsd_window)):
        rsd_window_mean = np.mean(array_1D[value : value + rsd_window])
        rsd_window_std = np.std(array_1D[value : value + rsd_window])
        rsd.append((rsd_window_std/rsd_window_mean)*100)
    return np.array(rsd)

def find_jaws(rsd_array):
    toot = argrelextrema(rsd_array, np.greater)
    rsd_maxima = []
    for value in toot[0]:
        if rsd_array[value] > 0.5:
            rsd_maxima.append(value)
    y1 = rsd_maxima[-1] + (rsd_window * 0.5)
    y2 = rsd_maxima[0] + (rsd_window * 0.5)
    return y1, y2

def find_MLC(rsd_array):
    toot = argrelextrema(rsd_array, np.less)
    rsd_minima = []
    for value in toot[0]:
        if rsd_array[value] > 0.5:
            rsd_minima.append(value)
    bank_B_leaf = rsd_minima[0] + (rsd_window * 0.5)
    bank_A_leaf = rsd_minima[-1] + (rsd_window * 0.5)
    return bank_B_leaf, bank_A_leaf

def get_image_info(image_path):
    image = dicom.read_file(image_path)
    image_info["Machine Name"] = image['RadiationMachineName'].value
    image_info["Image Type"] = image['RTImageDescription'].value
    image_info["Image Date"] = image['ContentDate'].value
    image_info["Image UID"] = image['SeriesInstanceUID'].value
    image_info["Pixel Data"] = median_filter(image.pixel_array, 5)

    return image_info

def process_column(column):
    column = pixel_data[:, column]
    column_rsd = get_rsd(column)
    y1, y2 = find_jaws(column_rsd)
    bank_B, bank_A = find_MLC(column_rsd)
    return [y2, bank_B, bank_A, y1]

def process_image(column1, column2):
    column1_results = process_column(column1)
    column2_results = process_column(column2)

    run = column2 - column1
    angle_degrees = []

    for i in [0, 2]:
        rise = (column1_results[i+1] - column1_results[i]) - (column2_results[i+1] - column2_results[i])
        angle_degrees.append(np.degrees(np.arctan(rise / run)))
    
    return {
        "Bank B skew (deg)": angle_degrees[0],
        "Bank A skew (deg)": angle_degrees[1]
    }

def show_plots():
    # Figure 1
    plt.imshow(pixel_data, cmap = 'gray')
    plt.axis('off')
    plt.title('MV Image and ROIs for Analysis')
    plt.plot([column1, column1], [390, 890])
    plt.plot([column2, column2], [390, 890])
    plt.show()

    # Figure 2
    column1_array = pixel_data[:, column1]
    column1_rsd = get_rsd(column1_array)
    column2_array = pixel_data[:, column2]
    column2_rsd = get_rsd(column2_array)

    plt.plot(column1_rsd)
    plt.title('Column 1 (Blue ROI) RSD used to Identify Jaws and Leaves')
    plt.annotate('Y2', xy = (390, 2.65), xytext = (171,2.65), arrowprops = dict(facecolor ='red', shrink = 0.05))

    plt.annotate('Bank B Leaf Base', xy = (458, 1.26), xytext = (0,0.5), arrowprops = dict(facecolor ='red', shrink = 0.05))

    plt.annotate('Bank A Leaf Tip', xy = (798, 1.17), xytext = (1000,0.5), arrowprops = dict(facecolor ='red', shrink = 0.05))
    plt.annotate('Y1', xy = (872, 2.58), xytext = (1071,2.58), arrowprops = dict(facecolor ='red', shrink = 0.05))
    plt.show()


development = True # Change to True to see image and columns defined below

rsd_window = 16     # 16 (Must be even)
column1 = 395       # 395 - Through base of MLC leaf B and tip of MLC Leaf A
column2 = 875       # 875 - Through base of MLC leaf A and tip of MLC Leaf B

repeat_analysis = 'y'

while 'y' in repeat_analysis.lower():
    image_path = input("Drag and drop the file to be processed.").replace("& ", "").strip("'").strip('"')
    image_info = get_image_info(image_path)
    pixel_data = image_info["Pixel Data"]
    results = process_image(column1, column2)
    print(results)
    if development == True:
        show_plots()
    
    repeat_analysis = input("Do you want to process another file? (y/n)")