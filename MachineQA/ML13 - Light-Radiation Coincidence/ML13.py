import numpy as np
import matplotlib.pyplot as plt
from scipy.signal import savgol_filter
from PIL import Image
from scipy.signal import find_peaks, medfilt
from scipy.ndimage import rotate
import cv2
import datetime as datetime
import os
import time
import base64
import sys

# Author Ben Cudmore 
# to package into executable, run the following line in the terminal when in the py directory.
# pyinstaller -F --hiddenimport=pyTQA.tqa --console --onedir --clean py

sys.path.append("T:\\_Physics Team PEICTC\\Benjamin\\GitHub\\PEICTC_QA")
from Helpers.QATrackHelpers import QATrack as qat

def get_input_path():

    image_path = input("\nDrag and drop the scanned film file into terminal and hit enter.\n").replace("& ", "").strip("'")
    
    if '3426' in image_path:
        linac = '3426'
        print('\nThe file is from the TrueBeam3426 folder and will be processed accordingly.')
    elif '5833' in image_path:
        linac = '5833'
        print('\nThe file is from the TrueBeam5833 folder and will be processed accordingly.')
    else:
        linac = ''


    while "3426" not in linac and "5833" not in linac:
        linac = input("\nPlease enter the four digit number of the TrueBeam the film was delivered on (3426 or 5833):\n")
    
    confirmation = input("\nIs this the file you would like to process?\nPlease enter 'y' or 'n'.\n".format(image_path))

    while confirmation.lower() != 'y':
        image_path = input("\nDrag and drop the scanned film file into terminal and hit enter.\n").replace("& ", "").strip("'")
        confirmation = input("\nVerify the file path. Is this the file you would like to process?:\nPlease enter 'y' or 'n'.\n".format(image_path))

    return linac, image_path

def get_skew(img, run = 300):
    row_1 = savgol_filter(get_abs_derivative(img[img.shape[0]//2 - (run //2),:]), 21, 3)
    row_2 = savgol_filter(get_abs_derivative(img[img.shape[0]//2 + (run //2),:]), 21, 3)
    row_1_peaks = []
    row_2_peaks = []

    if show_plots == True:
        plt.plot(row_1)
        plt.plot(row_2)
        plt.title("Checking for Skew (Main peaks should be aligned)")
        plt.show()

    prominence = 3
    while len(row_1_peaks) != 4:
        row_1_peaks, _ = find_peaks(row_1, prominence = prominence)
        prominence -= 0.05

    while len(row_2_peaks) != 4:
        row_2_peaks, _ = find_peaks(row_2, prominence = prominence)
        prominence -= 0.05

    rise = (row_1_peaks[0] - row_2_peaks[0] + row_1_peaks[-1] - row_2_peaks[-1]) / 2
    slope = rise/run
    angle = np.degrees(np.arctan(slope))

    return angle


def get_abs_derivative(array_1D):
    abs_derivative = savgol_filter(abs(np.gradient(array_1D)), 7, 3)
    return np.array(abs_derivative)

def get_new_start(img, center_bb_start, search_window = 20):
    search_array = img[round(center_bb_start['y']-search_window/2):round(center_bb_start['y']+search_window/2), round(center_bb_start['x']-search_window/2):round(center_bb_start['x']+search_window/2)]
    gray_blurred = cv2.blur(search_array, (5, 5)) 
    center_bb_intermediate1 = {}
    gray_row = np.mean(gray_blurred, axis = 0)
    gray_column = np.mean(gray_blurred, axis = 1)

    center_bb_intermediate = {}
    center_bb_intermediate1['x'] = find_centroid_using_polynomial(range(len(gray_row)), gray_row)
    center_bb_intermediate1['y'] = find_centroid_using_polynomial(range(len(gray_column)), gray_column)

    if show_plots == True:
        plt.imshow(gray_blurred)
        plt.title("BB Search")
        plt.show()

    center_bb_intermediate['x'] = center_bb_start['x'] - (search_window /2) + center_bb_intermediate1['x']
    center_bb_intermediate['y'] = center_bb_start['y'] - (search_window /2) + center_bb_intermediate1['y']

    return center_bb_intermediate, center_bb_intermediate1

def get_center_bb(img, center_bb_start):
    
    center_bb = {}

    new_start, difference = get_new_start(img, center_bb_start)
    count = 0

    # keep adjusting bb ROI until the bb is centered for consistency
    while abs(difference['x']) < 9.5 or abs(difference['x']) > 10.5 or abs(difference['y']) < 9.5 or abs(difference['y']) > 10.5:
        count += 1
        new_start, difference = get_new_start(img, new_start)
        if count == 10:
            break

    # crop out extra film and film holder
    irradiated_film = img[round(new_start['y'])-crop_px:round(new_start['y'])+crop_px, round(new_start['x'])-crop_px:round(new_start['x'])+crop_px]

    # Indices were rounded so remainders from center bb in uncropped image are required 
    x_remainder = new_start['x'] % 1

    if x_remainder >=0.5:
        x_remainder =  x_remainder - 1

    y_remainder = new_start['y'] % 1

    if y_remainder >=0.5:
        y_remainder =  y_remainder - 1

    center_bb['x'] = (irradiated_film.shape[1] / 2) + x_remainder
    center_bb['y'] = (irradiated_film.shape[0] / 2) + y_remainder

    return irradiated_film, center_bb

def first_derivative_method(data):

    for i in range(len(data)):
        if data[i] < 1:
            data[i] = 141

    # Compute the first derivative
    flipped_data = data[::-1]

    first_derivative1 = savgol_filter(abs(np.gradient(data)), 20, 3)
    first_derivative2 = savgol_filter(abs(np.gradient(flipped_data)), 20, 3)
    first_derivative2 = first_derivative2[::-1]

    first_derivative = (first_derivative1 + first_derivative2) / 2

    return first_derivative

def replace_zeros_with_nearest_neighbor(arr):
    # Iterate through the array
    for i in range(len(arr)):
        if arr[i] == 0:  # If the current element is zero
            left = i - 1
            right = i + 1

            # Find the nearest non-zero neighbor to the left
            while left >= 0:
                if arr[left] != 0:
                    arr[i] = arr[left]
                    break
                left -= 1

            # Find the nearest non-zero neighbor to the right
            while right < len(arr):
                if arr[right] != 0:
                    if arr[i] == 0 or abs(i - left) > abs(right - i):
                        arr[i] = arr[right]
                    break
                right += 1

    return arr



def find_irradiated_edges(image, center_bb):
    offset = -30
    neighbors = 20
    peaks = {}
    peaks['Left-Right'] = []
    peaks['Up-Down'] = []

    left_right_roi = replace_zeros_with_nearest_neighbor(np.mean(image[int(center_bb['y']) - offset - neighbors: int(center_bb['y']) - offset, :], axis = 0))
    up_down_roi = replace_zeros_with_nearest_neighbor(np.mean(image[:, int(center_bb['x']) - offset - neighbors: int(center_bb['x']) - offset], axis = 1))

    left_right_roi = first_derivative_method(left_right_roi)
    up_down_roi = first_derivative_method(up_down_roi)

    max_height = 6
    min_height = 0.2


    while len(peaks['Left-Right']) != 6:
        peaks['Left-Right'], _ = find_peaks(left_right_roi, prominence= 0.2, height = (min_height, max_height))
        min_height += 0.02
        if min_height >= max_height:
            max_height -= 0.2
            min_height = 0.2

    min_height = 0.2
    max_height = 6

    while len(peaks['Up-Down']) != 6:
        peaks['Up-Down'], _ = find_peaks(up_down_roi, prominence= 0.2, height = (min_height, max_height))
        min_height +=0.02
        if min_height >= max_height:
            max_height -= 0.2
            min_height = 0.2


    interpolated_peaks = {}
    window = 5
    for direction in peaks:
        interpolated_peaks[direction] = {}
        new_peaks = []

        for peak in peaks[direction]:
            x_values = list(range(peak-window, peak + window))
            if 'Left-Right' in direction:
                roi = left_right_roi

            elif 'Up-Down' in direction:
                roi = up_down_roi
            peak = roi[x_values]

            new_peaks.append(find_centroid_using_polynomial(x_values, peak))

        if show_plots == True:
            plt.title("Peaks found in {} direction".format(direction))
            plt.plot(roi, zorder = 0, label = 'Original peaks')
            plt.legend()
            plt.show()
        else:
            plt.close()

        interpolated_peaks[direction] = new_peaks

    results = {

        "lvr6mv5y1": (center_bb['y'] - interpolated_peaks['Left-Right'][2]),
        "lvr6mv5y2": (interpolated_peaks['Left-Right'][3] - center_bb['y']),
        "lvr6mv5x1": (center_bb['x'] - interpolated_peaks['Up-Down'][2]),
        "lvr6mv5x2": (interpolated_peaks['Up-Down'][3] - center_bb['x']),
        "lvr6mv10y1": (center_bb['y'] - interpolated_peaks['Left-Right'][1]),
        "lvr6mv10y2": (interpolated_peaks['Left-Right'][4] - center_bb['y']),
        "lvr6mv10x1": (center_bb['x'] - interpolated_peaks['Up-Down'][1]),
        "lvr6mv10x2": (interpolated_peaks['Up-Down'][4] - center_bb['x']),
        "lvr6mv15y1": (center_bb['y'] - interpolated_peaks['Left-Right'][0]),
        "lvr6mv15y2": (interpolated_peaks['Left-Right'][5] - center_bb['y']),
        "lvr6mv15x1": (center_bb['x'] - interpolated_peaks['Up-Down'][0]),
        "lvr6mv15x2": (interpolated_peaks['Up-Down'][5] - center_bb['x'])
        }
    
    return results, interpolated_peaks

def convert_pixels_to_cm(results, dpi):
    results_in_cm = {}
    for side in results:
        results_in_cm[side] = round((results[side] / dpi[0] * 2.54), 2)

    return results_in_cm


def polynomial(x, *coefficients):
        return np.polyval(coefficients, x)

def find_centroid_using_polynomial(x_values, peak, degree=4):

    coefficients = np.polyfit(x_values, peak, degree)

    high_res_x_values = np.linspace(x_values[0], x_values[-1], 2000)
    interpolated_fit_curve = polynomial(high_res_x_values, *coefficients)


    if show_plots == True:
        plt.plot(high_res_x_values, interpolated_fit_curve, 'r-', zorder = 10)

    peaks, _ = find_peaks(interpolated_fit_curve)
    interpolated_peaks = high_res_x_values[peaks]
    if len(interpolated_peaks) == 0:
        return "NA"

    return float(interpolated_peaks[0])


def post_to_qatrack(linac, results_in_cm):
    qat.log_into_qat()
    utc_url, macros = qat.get_unit_test_collection(linac, "Light/Radiation Coincidence")
    formatted_results = qat.format_results(macros, results_in_cm)
    date = qat.format_date(image_path)
    qat.post_results(utc_url, formatted_results, date)

def open_film_tif():

    linac, image_path = get_input_path()

    if "\\\\" not in image_path:
        image_path.replace("\\", "\\\\")
    image = cv2.imread(image_path, cv2.IMREAD_GRAYSCALE)

    return image, linac, image_path

def rotate_film(image, angle):
    plt.close()

    if abs(angle) >= 0.5:
        updated_image = rotate(image, angle, reshape = False, order = 2)        
    else:
        updated_image = rotate(image, 0, reshape = False, order = 2)
    if show_plots == True:
        if abs(angle) >=0.5:
            fig, axes = plt.subplots(1, 2, figsize=(10, 5))
            # Display the first image
            axes[0].imshow(image, cmap = 'viridis')
            axes[0].set_title('Original Image')
            axes[0].axis('off')

            # Display the second image
            axes[1].imshow(updated_image, cmap = 'viridis')
            axes[1].set_title('Skew Corrected Image')
            axes[1].axis('off')

        else:
            
            plt.title('No Skew Correction Required')
            plt.imshow(updated_image, cmap = 'viridis')

        plt.show()  

    return updated_image

def measure_squares(image):

    results_in_pixels, interpolated_peaks = find_irradiated_edges(image, center_bb)

    img = Image.open(image_path).convert('L')
    dpi = img.info['dpi']

    results_in_cm = convert_pixels_to_cm(results_in_pixels, dpi)

    for result in results_in_cm:
        print("{}: {}".format(result, results_in_cm[result]))
    
    plt.imshow(image, cmap = 'viridis') # vmin= 90, vmax=160,
    draw_horizontal_lines(center_bb['x'], center_bb['y'], line_length= 2)
    draw_vertical_lines(center_bb['y'], center_bb['x'], line_length = 2)

    for direction in interpolated_peaks:
        for i in interpolated_peaks[direction]:
            if "Left-Right" in direction:
                draw_vertical_lines(i, center_bb['x'])
            if "Up-Down" in direction:
                draw_horizontal_lines(i, center_bb['y'])

    plt.title("Results. Close Figure to Proceed.")
    plt.xlabel('X2')
    plt.ylabel('Y1', rotation = 0)

    plt.show()
    figure_save_location = image_path.rstrip('.tif') + " Analysis.png"
    plt.savefig(figure_save_location)

    attachments =   [{'filename': "Jaw Deviation Summary.png",
            'value': base64.b64encode(open(figure_save_location, 'rb').read()).decode(),
            'encoding': 'base64'}]

    return results_in_cm

def find_irradiated_film_center(pixel_array):
    film_rows = []
    film_columns = []
    
   
    blurred_pixel_array = medfilt(pixel_array, 9)

    for i in range(10, blurred_pixel_array.shape[1], 10):
        search = blurred_pixel_array[:, i].min()
        if search < 140:
            film_columns.append(i)

    for i in range(10, blurred_pixel_array.shape[0], 10):
        search = blurred_pixel_array[i, :].min()
        if search < 140:
            film_rows.append(i)

    return {
        'row': ((film_rows[-1] - film_rows[0]) //2) + film_rows[0],
        'column': ((film_columns[-1] - film_columns[0]) //2) + film_columns[0]}

# Function to draw horizontal lines
def draw_vertical_lines(y, center_bb, line_length = 20, color = 'red'):
    plt.plot([y, y], [center_bb-line_length, center_bb+line_length], color=color, linewidth=1)

# Function to draw vertical lines
def draw_horizontal_lines(x, center_bb, line_length = 20, color = 'red'):
    plt.plot([center_bb - line_length, center_bb + line_length], [x, x], color=color, linewidth=1)

def approximate_center(img):
    
    irradiated_film_center = find_irradiated_film_center(image)

    row_start = irradiated_film_center['row']

    left_right_roi = savgol_filter(np.average(img[row_start - 50: row_start + 50, :], 0), 21, 3)
    sensitivity = 50
    peaks = []

    while len(peaks) < 2:
        filtered_roi = left_right_roi.copy()
        sensitivity += 5
        for i in range(len(filtered_roi)):
            if filtered_roi[i] > sensitivity:
                filtered_roi[i] = 0

        filtered_roi = first_derivative_method(filtered_roi)

        if show_dev_plots == True:
            plt.plot(left_right_roi)
            plt.plot(filtered_roi)
            plt.title('Finding center in left-right direction')
            plt.legend('left-right ROI')
            plt.legend('Filtered first derivative')
            plt.show()

        peaks, _ = find_peaks(filtered_roi,prominence=2)
        if len(peaks) == 0:
            continue
        if peaks[-1] - peaks[0] < 360 or peaks[-1] - peaks[0] > 390:
            peaks = []
            
    left_right_start = ((peaks[-1] - peaks[0]) // 2) + peaks[0]
    

    column_start = img.shape[1] // 2
    up_down_roi = savgol_filter(np.average(img[:, column_start - 50: column_start + 50], 1), 21, 3)
    sensitivity = 50
    peaks = []

    while len(peaks) < 2:
        filtered_roi = up_down_roi.copy()
        sensitivity += 5
        for i in range(len(filtered_roi)):
            if filtered_roi[i] > sensitivity:
                filtered_roi[i] = 0

        filtered_roi = first_derivative_method(filtered_roi)

        if show_dev_plots == True:
            plt.plot(up_down_roi)
            plt.plot(filtered_roi)
            plt.title('Finding center in up-down direction')
            plt.legend('up-down ROI')
            plt.legend('Filtered first derivative')
            plt.show()

        peaks, _ = find_peaks(filtered_roi, prominence = 2)
        if len(peaks) == 0:
           continue
        if peaks[-1] - peaks[0] < 360 or peaks[-1] - peaks[0] > 390:
            peaks = []

    up_down_start = ((peaks[-1] - peaks[0]) // 2) + peaks[0]

    center_start = {'x': left_right_start, 'y': up_down_start}

    # plt.imshow(img)
    # plt.show()

    return center_start

field_size_cm = 15.75
crop_px = round(field_size_cm / 2.54 * 96 / 2)
image_path = ''

display_plots = input("\n~  Light/Radiation Coincidence Analysis  ~\n\nDo you want to see analysis plots for this session?\nPlease enter 'y' or 'n'.\n")

show_dev_plots = False

if 'y' in display_plots.lower():
    show_plots = True
else:
    show_plots = False

image, linac, image_path = open_film_tif()
image = medfilt(image, 9)

 
center_bb_start = approximate_center(image)
irradiated_film, center_bb = get_center_bb(image, center_bb_start)

angle = get_skew(irradiated_film)
rotated_film = rotate_film(irradiated_film, angle)
results_in_cm = measure_squares(rotated_film)

resp = input("\nAre you satisfied with the analysis? Please enter 'y' or 'n'.\n")

if 'y' in resp.lower():
    post_to_qatrack(linac, results_in_cm)
else:
    print("\nI wasn't built to accept criticism...\n")
    time.sleep(1)
    print("Self destructing in...")
    for i in range(4):
        print(3-i)
        time.sleep(1)

os.system('exit')