import pydicom as dicom
import matplotlib.pyplot as plt
import numpy as np
import cv2
from scipy.signal import find_peaks
from scipy.signal import savgol_filter
import datetime as datetime
import os
import sys

sys.path.append("T:\\_Physics Team PEICTC\\Benjamin\\GitHub\\PEICTC_Machine_QA")
from Helpers.QATrack.QATrackHelpers import QATrack as qat

def get_center_bb(img, center_bb_start, search_window = 30):
    center_bb = {}

    ## Starting point for center bb
    search_array = img[int(center_bb_start['y']-(search_window/2)):int(center_bb_start['y']+(search_window/2)), int(center_bb_start['x']-(search_window/2)):int(center_bb_start['x']+(search_window/2))]
    search_array = cv2.blur(search_array, (5, 5))

    ## Find bb center by getting max value index in search area
    max_index = np.where(search_array == search_array.max())
    max_index = list(zip(max_index[1], max_index[0]))[0]

    ## Update the search area to be centered on the bb
    center_bb_start['y'] = center_bb_start['y'] - (search_window/2) + max_index[1]
    center_bb_start['x'] = center_bb_start['x'] - (search_window/2) + max_index[0]

    search_array = img[int(center_bb_start['y']-(search_window/2)):int(center_bb_start['y']+(search_window/2)), int(center_bb_start['x']-(search_window/2)):int(center_bb_start['x']+(search_window/2))]
    search_array = cv2.blur(search_array, (5, 5))

    if show_plots == True:
        plt.title("Center BB")
        plt.imshow(search_array)
        plt.show()

    ## overcome pixel resolution by fitting polynomial to averaged rows and columns
    gray_row = np.mean(search_array, axis = 0)
    gray_column = np.mean(search_array, axis = 1)

    center_bb['x'] = find_centroid_using_polynomial(range(len(gray_row)), gray_row, 3, 11)
    center_bb['y'] = find_centroid_using_polynomial(range(len(gray_column)), gray_column, 3, 11)

    center_bb['x'] = center_bb_start['x'] - (search_window /2) + center_bb['x']
    center_bb['y'] = center_bb_start['y'] - (search_window /2) + center_bb['y']

    return center_bb

def find_centroid_using_polynomial(x_values, y_values, degree=4, trim = 0):

    # Trim is optional parameter; useful if data passed in contains unwanted data adjacent to peak
    x_values = x_values[trim:len(x_values)-trim]
    y_values = y_values[trim:len(y_values)-trim]

    high_res_x_values, fit = get_poly_values(x_values, y_values, degree)
    if show_plots == True:
        plt.plot(high_res_x_values, fit, 'r-', zorder = 10)

    peaks, _ = find_peaks(fit)
    interpolated_peaks = high_res_x_values[peaks]
    if len(interpolated_peaks) == 0:
        return "NA"
    return float(interpolated_peaks[0])

def get_poly_values(x_values, y_values, degree):
    coefficients = np.polyfit(x_values, y_values, degree)
    high_res_x_values = np.linspace(min(x_values), max(x_values), 2000)
    fit = polynomial(high_res_x_values, *coefficients)
    return high_res_x_values, fit

def polynomial(x, *coefficients):
    return np.polyval(coefficients, x)

def draw_vertical_lines(location, center_bb, line_length = 20, color = 'red'):
    plt.plot([location, location], [center_bb-line_length, center_bb+line_length], color=color, linewidth=1)

def draw_horizontal_lines(center_bb, location, line_length = 20, color = 'red'):
    plt.plot([center_bb - line_length, center_bb + line_length], [location, location], color=color, linewidth=1)

def measure_squares_in_cm(image, center_bb, pixel_spacing_cm):
    
    results_in_cm = {}
    results_in_pixels, interpolated_peaks = find_irradiated_edges(image, center_bb)
    
    for result in results_in_pixels:
        results_in_cm[result] = results_in_pixels[result] * pixel_spacing_cm

        # print("{}: {}".format(result, results_in_cm[result]))
        # print("{}".format(results_in_cm[result]))

    plt.imshow(image)

    draw_horizontal_lines(center_bb['x'], center_bb['y'], line_length= 2)
    draw_vertical_lines(center_bb['x'], center_bb['y'], line_length = 2)

    # Note interpolated peaks are in correct order here; assigned correctly in "find_irradiated_edges()""
    for result in results_in_pixels:
        if 'y1' in result:
            draw_horizontal_lines(center_bb['x'], interpolated_peaks['Up-Down'][0])
        elif 'y2' in result:
            draw_horizontal_lines(center_bb['x'], interpolated_peaks['Up-Down'][1])
        elif 'x1' in result:
            draw_vertical_lines(interpolated_peaks['Left-Right'][0], center_bb['y'])
        elif 'x2' in result:
            draw_vertical_lines(interpolated_peaks['Left-Right'][1], center_bb['y'])

    plt.title("Results. Close Figure to Proceed.")
    plt.xlabel('Y1')
    plt.ylabel('X1', rotation = 0)
    plt.show()

    return results_in_cm

def find_closest_index(x_values, data, search_value):
    toot = list((abs(data[0:len(data)] - search_value)))
    search_index = x_values[toot.index(min(toot))]
    return search_index

def abs_first_derivative_method(data):

    # Calculate derivative from both directions and average results
    flipped_data = data[::-1]
    first_derivative = savgol_filter(np.gradient(data), 5, 3) # for plot only
    first_derivative1 = abs(first_derivative)
    
    if show_plots == True:
        plt.close()
        plt.xlabel("Index (px)")
        plt.ylabel("Arbitrary")
    
        plt.plot((data*0.1)-4450)
        plt.plot(first_derivative+850)
        plt.plot(first_derivative1)
        plt.show()

    first_derivative2 = savgol_filter(abs(np.gradient(flipped_data)), 5, 3)
    first_derivative2 = first_derivative2[::-1]
    first_derivative = (first_derivative1 + first_derivative2) / 2

    return first_derivative

def find_irradiated_edges(image, center_bb):
    neighbors = 5
    offset = 15 # want to avoid bb
    
    # Get ROIs -offset of center bb
    left_right_roi = savgol_filter(np.mean(image[int(center_bb['y']) - offset: int(center_bb['y']) - offset + neighbors, :], axis = 0), 5, 3)
    up_down_roi = savgol_filter(np.mean(image[:, int(center_bb['x']) - offset: int(center_bb['x']) - offset + neighbors], axis = 1), 5, 3)
    

    # Get ROIs +offset of center bb
    offset = - offset
    left_right_roi1 = savgol_filter(np.mean(image[int(center_bb['y']) - offset: int(center_bb['y']) - offset + neighbors, :], axis = 0), 5, 3)
    up_down_roi1 = savgol_filter(np.mean(image[:, int(center_bb['x']) - offset: int(center_bb['x']) - offset + neighbors], axis = 1), 5, 3)
    

    # Average the two ROIs 
    left_right_roi = (left_right_roi + left_right_roi1)/2
    up_down_roi = (up_down_roi + up_down_roi1)/2
    
    # Get absolute of derivative of profiles to identify inflection points in high gradient regions (a.k.a. jaws)
    left_right_roi = abs_first_derivative_method(left_right_roi)
    up_down_roi = abs_first_derivative_method(up_down_roi)

    # Find indices of peaks in absolute derivative profile (a.k.a. inflection points) in pixels
    
    peaks_found = {}
    interpolated_peaks = {}

    peaks_found["Left-Right"] = find_jaws(left_right_roi, "Left-Right")
    interpolated_peaks["Left-Right"] = find_peak_center(left_right_roi, peaks_found["Left-Right"])
    if show_plots == True:
        plt.title("Peaks found in {} direction".format("Left-Right"))
        plt.show()
    else:
        plt.close()

    peaks_found["Up-Down"] = find_jaws(up_down_roi, "Up-Down")
    interpolated_peaks["Up-Down"] = find_peak_center(up_down_roi, peaks_found["Up-Down"])
    if show_plots == True:
        plt.title("Peaks found in {} direction".format("Up-Down"))
        plt.show()
    else:
        plt.close()

    # calculate distance from jaw to center bb to get position in pixels
    # Note: Y2 is the first up-down
    results = {
        "x1": (center_bb['x'] - interpolated_peaks['Left-Right'][0]),
        "x2": (interpolated_peaks['Left-Right'][1] - center_bb['x']),
        "y1": (interpolated_peaks['Up-Down'][1] - center_bb['y']),
        "y2": (center_bb['y'] - interpolated_peaks['Up-Down'][0])
    }
    
    return results, interpolated_peaks

def find_peak_center(roi, peaks_found):
    window = 5
    new_peaks = []
    for peak in peaks_found:
        x_values = list(range(peak-window, peak + window))
        peak = roi[x_values]
        new_peaks.append(find_centroid_using_polynomial(x_values, peak))
    
    return new_peaks

def find_jaws(roi,roi_id):
    peaks_found = []

    # Iterate over peak threshold values to find jaws only
    max_height = 2000
    min_height = 50

    while len(peaks_found) != 2:
        peaks_found, _ = find_peaks(roi, prominence= 0.2, height = (min_height, max_height))
        min_height += 10
        if min_height >= max_height:
            max_height -= 10
            min_height = 50
            if max_height < 0:
                peaks_found = [0, 0]
                print('No jaws found in {} direction.'.format(roi_id))
                return
            
    if show_plots == True:
        plt.plot(roi, zorder = 0, label = roi_id)

    find_peak_center(roi, peaks_found)
    return peaks_found

def calculate_ML14(file, use_bb = True):
    if isinstance(file, str):
        dicom_info = dicom.dcmread(file)
    else:
        dicom_info = file

    machine = dicom_info.RadiationMachineName
    col_angle = dicom_info.BeamLimitingDeviceAngle
    pixel_info = dicom_info.pixel_array
    date = qat.format_date(dicom_info)

    if "270" in str(round(col_angle)):
        pixel_info = np.rot90(pixel_info)
    
    if "90" in str(round(col_angle)):
        pixel_info = np.rot90(np.rot90(np.rot90(pixel_info)))

    pixel_center = {
        "x": int(pixel_info.shape[0]//2),
        "y": int(pixel_info.shape[1]//2)
    }

    if use_bb:
        center = get_center_bb(pixel_info, pixel_center)
    else:
        center = pixel_center

    # Calculate magnification factor
    pixel_spacing_mm = dicom_info.ImagePlanePixelSpacing[0]
    magnification_factor = dicom_info.RadiationMachineSAD / dicom_info.RTImageSID
    pixel_spacing_cm = pixel_spacing_mm * magnification_factor / 10

    results_in_cm = measure_squares_in_cm(pixel_info, center, pixel_spacing_cm)

    for jaw in results_in_cm:
        if results_in_cm[jaw] < 1.5 and results_in_cm[jaw]  > 0.5:
            macro = jaw +"_position_10mm"
            all_results[macro] = np.round(results_in_cm[jaw],3)

        if results_in_cm[jaw] < 3 and results_in_cm[jaw]  > 2:
            macro = jaw +"_position_25mm"
            all_results[macro] = np.round(results_in_cm[jaw], 3)

        if results_in_cm[jaw] < 5.5 and np.round(results_in_cm[jaw], 3)  > 4.5:
            macro = jaw +"_position_50mm"
            all_results[macro] = np.round(results_in_cm[jaw], 3)

        if results_in_cm[jaw] < 8 and results_in_cm[jaw]  > 7:
            macro = jaw +"_position_75mm"
            all_results[macro] = np.round(results_in_cm[jaw], 3)

        if results_in_cm[jaw] < 10.5 and results_in_cm[jaw]  > 9.5:
            macro = jaw +"_position_100mm"
            all_results[macro] = np.round(results_in_cm[jaw], 3)

        if results_in_cm[jaw] < 15.5 and results_in_cm[jaw]  > 14.5:
            macro = jaw +"_position_150mm"
            all_results[macro] = np.round(results_in_cm[jaw], 3)
    
    return machine, date
    
def process_folder():
    global input_folder
    date_list = []
    machine_list = []

    input_folder = input("Drag and drop the folder containing the files to be processed.").replace("& ", "").strip("'").strip('"')
    for dir_path, dir_names, file_names in os.walk(input_folder):
        for file in file_names:
            if ".dcm" in file:
                dicom_info = dicom.dcmread(os.path.join(dir_path, file))
                if not "RTIMAGE" in dicom_info.Modality:
                    continue
                machine, date = calculate_ML14(dicom_info, use_bb=True)
                if machine not in machine_list:
                    machine_list.append(machine)
                if date not in date_list:
                    date_list.append(date)
    
    for result in all_results:
        residuals_mm[result] = (all_results[result] - (float(result.split("_")[-1].strip("m")) /10))*10

    if len(machine_list) > 1:
        print("Please process one machine at a time. Process restarting")
        return False, False

    if len(date_list) > 1:
        date = min(date_list)

    return machine, date

def calculate_average_deviation():
    jaws = {"x1": {},
            "x2": {},
            "y1": {},
            "y2": {}}
    
    plt.figure(figsize = (14, 9))

    for jaw in jaws:
        jaws[jaw]["positions"] = []
        jaws[jaw]["residuals"] = []
        for residual in residuals_mm:
            if jaw in residual:
                jaws[jaw]["positions"].append(float(residual.split("_")[-1].strip("m"))/10)
                jaws[jaw]["residuals"].append(residuals_mm[residual])

        
        plt.plot(jaws[jaw]["positions"], jaws[jaw]["residuals"], marker = 'o', linestyle = '', markersize = 10)

    for jaw in jaws:
        x_values, fit = get_poly_values(jaws[jaw]["positions"], jaws[jaw]["residuals"], degree = 2)
        plt.plot(x_values, fit, linestyle = '--', color = 'black')
        jaws[jaw]["average"] = np.round(np.average(jaws[jaw]["residuals"]), 2)


    plt.legend(["Ave. X1 Deviation = {}".format(jaws["x1"]["average"]),\
                "Ave. X2 Deviation = {}".format(jaws["x2"]["average"]),\
                "Ave. Y1 Deviation = {}".format(jaws["y1"]["average"]),\
                "Ave. Y2 Deviation = {}".format(jaws["y2"]["average"])], loc= (1.01, 0.6), fontsize = 12)
    

    plt.subplots_adjust(right = 0.75)

    plt.title("Deviation from Expected Positions", fontsize = 18)
    plt.xlabel("Expected Position (cm)", fontsize = 16)
    plt.ylabel("Deviation (mm)", fontsize = 16)

    figure_save_location = os.path.join(input_folder, "Deviation Summary.png")

    plt.savefig(figure_save_location)

    all_results["x1_average_deviation"] = jaws["x1"]["average"]

    all_results["x2_average_deviation"] = jaws["x2"]["average"]

    all_results["y1_average_deviation"] = jaws["y1"]["average"]

    all_results["y2_average_deviation"] = jaws["y2"]["average"]
    # all_results["jaws_vs_radiation_png"] = {'filename': figure_save_location,
    #         'value': base64.b64encode(open(figure_save_location, 'rb').read()).decode(),
    #         'encoding': 'base64'}

input_folder = ''
show_plots = False
all_results = {}
residuals_mm = {}
machine, date = process_folder()

calculate_average_deviation()

while machine == False:
    machine, date = process_folder()

qat.log_into_QATrack()
utc_url, macros = qat.get_unit_test_collection(machine, "Jaw Position Accuracy")
tests = qat.format_results(macros, all_results)
qat.post_results(utc_url, tests, date)