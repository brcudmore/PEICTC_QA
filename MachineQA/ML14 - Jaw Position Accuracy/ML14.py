print("~ Monthly Jaw Position Accuracy (ML14) ~\n")
print("Please wait while the app loads.\n")
import pydicom as dicom
import matplotlib.pyplot as plt
import numpy as np
import cv2
from scipy.signal import find_peaks
from scipy.signal import savgol_filter
import datetime as datetime
import os
import sys
import base64


###

# All functions are defined before the actual code is written. 
# To follow along, please scroll to the bottom of the file.

###

sys.path.append("T:\\_Physics Team PEICTC\\Benjamin\\GitHub\\PEICTC_QA")
from Helpers.QATrackHelpers import QATrack as qat

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

    high_res_x_values, fit= get_poly_values(x_values, y_values, degree)
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

def find_80_percent_width(interpolated_peaks: dict):
    left_right = (interpolated_peaks["Left-Right"][1] - interpolated_peaks["Left-Right"][0]) * 0.8
    up_down = (interpolated_peaks["Up-Down"][1] - interpolated_peaks["Up-Down"][0]) * 0.8

    return left_right, up_down


def measure_squares_in_cm(image, center, pixel_spacing_cm):
    
    results_in_cm = {}
    results_in_pixels, interpolated_peaks = find_irradiated_edges(image, center)

    for result in results_in_pixels:
        results_in_cm[result] = np.round(results_in_pixels[result] * pixel_spacing_cm, 3)


        print("{}: {} cm".format(result, results_in_cm[result]))
        # print("{}".format(results_in_cm[result]))

    plt.imshow(image)

    draw_horizontal_lines(center['x'], center['y'], line_length= 2)
    draw_vertical_lines(center['x'], center['y'], line_length = 2)

    # Note interpolated peaks are in correct order here; assigned correctly in "find_irradiated_edges()""
    for result in results_in_pixels:
        if 'y1' in result:
            draw_horizontal_lines(center['x'], interpolated_peaks['Up-Down'][0])
        elif 'y2' in result:
            draw_horizontal_lines(center['x'], interpolated_peaks['Up-Down'][1])
        elif 'x1' in result:
            draw_vertical_lines(interpolated_peaks['Left-Right'][0], center['y'])
        elif 'x2' in result:
            draw_vertical_lines(interpolated_peaks['Left-Right'][1], center['y'])

    plt.title("Close Figure to Proceed.")
    plt.xlabel('Y1')
    plt.ylabel('X1', rotation = 0)
    plt.show()

    return results_in_cm

def find_closest_index(x_values, data, search_value):
    differences = list((abs(data[0:len(data)] - search_value)))
    search_index = x_values[differences.index(min(differences))]
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

def find_irradiated_edges(image, center_bb, combined_image = None):

    if isinstance(image, np.ndarray):
        dicom_info = image
    else:
        dicom_info = image
        image = image.pixel_array

    neighbors = 5
    offset = 25 # want to avoid bb

    # Get ROIs -offset of center bb
    left_right_roi = savgol_filter(np.mean(image[int(center_bb['y']) - offset: int(center_bb['y']) - offset + neighbors, :], axis = 0), 5, 3)
    up_down_roi = savgol_filter(np.mean(image[:, int(center_bb['x']) - offset: int(center_bb['x']) - offset + neighbors], axis = 1), 5, 3)
    

    # Get ROIs +offset of center bb
    offset = - offset
    left_right_roi1 = savgol_filter(np.mean(image[int(center_bb['y']) - offset: int(center_bb['y']) - offset + neighbors, :], axis = 0), 5, 3)
    up_down_roi1 = savgol_filter(np.mean(image[:, int(center_bb['x']) - offset: int(center_bb['x']) - offset + neighbors], axis = 1), 5, 3)
    

    # Will not average offsets if one of the jaws is at zero
    if min(left_right_roi) - min(left_right_roi1) > 2000:
        left_right_roi = left_right_roi1

    elif min(left_right_roi) - min(left_right_roi1) < -2000:
        left_right_roi = left_right_roi

    else:
        # Average the two ROIs 
        left_right_roi = (left_right_roi + left_right_roi1)/2
    
    # Will not average offsets if one of the jaws is at zero
    if min(up_down_roi) - min(up_down_roi1) > 2000:
        up_down_roi = up_down_roi1

    elif min(up_down_roi) - min(up_down_roi1) < -2000:
        up_down_roi = up_down_roi

    else:
        up_down_roi = up_down_roi1
        # Average the two ROIs 
        # up_down_roi = (up_down_roi + up_down_roi1)/2


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

    if combined_image:
        left, right = find_50_percent_dose(left_right_roi, combined_image["Left-Right"]) 

        up, down = find_50_percent_dose(up_down_roi, combined_image["Up-Down"]) 
        interpolated_peaks["Left-Right"] = [left, right]
        interpolated_peaks["Up-Down"] = [up, down]

        results = {
        "x1": (center_bb['x'] - left),
        "x2": (right - center_bb['x']),
        "y1": (down - center_bb['y']),
        "y2": (center_bb['y'] - up)
    }
        
        pixel_spacing_mm = dicom_info.ImagePlanePixelSpacing[0]
        magnification_factor = dicom_info.RadiationMachineSAD / dicom_info.RTImageSID
        pixel_spacing_cm = pixel_spacing_mm * magnification_factor / 10
        results_in_cm = {}

        for jaw in results:
            results_in_cm[jaw] = results[jaw] * pixel_spacing_cm
            print(results_in_cm[jaw])
            if results_in_cm[jaw] < 0.5 and results_in_cm[jaw]  > -0.5:
                macro = jaw +"_position_0mm"
                all_results[macro] = results_in_cm[jaw]

            if results_in_cm[jaw] < 1.5 and results_in_cm[jaw]  > 0.5:
                macro = jaw +"_position_10mm"
                all_results[macro] = results_in_cm[jaw]

            if results_in_cm[jaw] < 3 and results_in_cm[jaw]  > 2:
                macro = jaw +"_position_25mm"
                all_results[macro] = results_in_cm[jaw]

            if results_in_cm[jaw] < 5.5 and results_in_cm[jaw]  > 4.5:
                macro = jaw +"_position_50mm"
                all_results[macro] = results_in_cm[jaw]

            if results_in_cm[jaw] < 8 and results_in_cm[jaw]  > 7:
                macro = jaw +"_position_75mm"
                all_results[macro] = results_in_cm[jaw]

            if results_in_cm[jaw] < 10.5 and results_in_cm[jaw]  > 9.5:
                macro = jaw +"_position_100mm"
                all_results[macro] = results_in_cm[jaw]

            if results_in_cm[jaw] < 15.5 and results_in_cm[jaw]  > 14.5:
                macro = jaw +"_position_150mm"
                all_results[macro] = results_in_cm[jaw]
        print("\n\n")

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
    global center

    if isinstance(file, str):
        dicom_info = dicom.dcmread(file)
    else:
        dicom_info = file

    machine = dicom_info.RadiationMachineName
    date = qat.format_date(dicom_info)
    col_angle = dicom_info.BeamLimitingDeviceAngle
    pixel_info = dicom_info.pixel_array

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
        if 'x' in center.keys():
            pass
        else:
            center = pixel_center
            print("WARNING:\nNo images were used to identify center of collimator rotation.\nResults may be inaccurate.")

    # Calculate magnification factor
    pixel_spacing_mm = dicom_info.ImagePlanePixelSpacing[0]
    magnification_factor = dicom_info.RadiationMachineSAD / dicom_info.RTImageSID
    pixel_spacing_cm = pixel_spacing_mm * magnification_factor / 10
    
    results_in_cm = measure_squares_in_cm(pixel_info, center, pixel_spacing_cm)

    for jaw in results_in_cm:
        if results_in_cm[jaw] < 0.5 and results_in_cm[jaw]  > -0.5:
            macro = jaw +"_position_0mm"
            all_results[macro] = results_in_cm[jaw]

        if results_in_cm[jaw] < 1.5 and results_in_cm[jaw]  > 0.5:
            macro = jaw +"_position_10mm"
            all_results[macro] = results_in_cm[jaw]

        if results_in_cm[jaw] < 3 and results_in_cm[jaw]  > 2:
            macro = jaw +"_position_25mm"
            all_results[macro] = results_in_cm[jaw]

        if results_in_cm[jaw] < 5.5 and results_in_cm[jaw]  > 4.5:
            macro = jaw +"_position_50mm"
            all_results[macro] = results_in_cm[jaw]

        if results_in_cm[jaw] < 8 and results_in_cm[jaw]  > 7:
            macro = jaw +"_position_75mm"
            all_results[macro] = results_in_cm[jaw]

        if results_in_cm[jaw] < 10.5 and results_in_cm[jaw]  > 9.5:
            macro = jaw +"_position_100mm"
            all_results[macro] = results_in_cm[jaw]

        if results_in_cm[jaw] < 15.5 and results_in_cm[jaw]  > 14.5:
            macro = jaw +"_position_150mm"
            all_results[macro] = results_in_cm[jaw]
    
    return machine, date

def organize_images(input_folder):
    analysis_images = {}
    cal_images = []

    for dir_path, dir_names, file_names in os.walk(input_folder):
        for file in file_names:
            if ".dcm" in file:
                file_path = os.path.join(dir_path, file)
                dicom_info = dicom.dcmread(file_path)

                if not "RTIMAGE" in dicom_info.Modality:
                    continue
                file_path = os.path.join(dir_path, file)
                dicom_info = dicom.dcmread(file_path)
                if np.round(dicom_info.BeamLimitingDeviceAngle) == 90 or np.round(dicom_info.BeamLimitingDeviceAngle) == 270:
                    cal_images.append(dicom_info)
                    
                else:
                    irradiation_event = dicom_info.IrradiationEventUID

                    if irradiation_event in analysis_images.keys():
                        analysis_images[irradiation_event].append(dicom_info)
                    else:
                        analysis_images[irradiation_event] = []
                        analysis_images[irradiation_event].append(dicom_info)
    
    return cal_images, analysis_images

def find_center_of_rotation(cal_images):
    global center
    center_of_rotation = {'270': float, '90': float}
    for dicom_info in cal_images:
        col_angle = dicom_info.BeamLimitingDeviceAngle
        pixel_info = dicom_info.pixel_array

        if "270" in str(round(col_angle)):
            cal_270 = True
            center = {'x': pixel_info.shape[0]//2, 'y': pixel_info.shape[1]//2}
            results, interpolated_peaks = find_irradiated_edges(pixel_info, center)
            center_of_rotation['270'] = {
                    'x1': interpolated_peaks["Up-Down"][0],
                    'x2': interpolated_peaks["Up-Down"][1],
                    'y1': interpolated_peaks["Left-Right"][0],
                    'y2': interpolated_peaks["Left-Right"][1]
                    }

        elif "90" in str(round(col_angle)):
            cal_90 = True
            center = {'x': pixel_info.shape[0]//2, 'y': pixel_info.shape[1]//2}
            results, interpolated_peaks = find_irradiated_edges(pixel_info, center)
            center_of_rotation['90'] = {
                    'x1': interpolated_peaks["Up-Down"][1],
                    'x2': interpolated_peaks["Up-Down"][0],
                    'y1': interpolated_peaks["Left-Right"][1],
                    'y2': interpolated_peaks["Left-Right"][0]
                    }
            

                    
    if cal_90 and cal_270:
        # X jaws are in up-down direction so it is the row between them 
        # that is of interest. Slightly different for X1 and X2 so an average is calculated
        row1 = ((center_of_rotation["90"]['x1'] - center_of_rotation["270"]['x1'])/2) + center_of_rotation["270"]['x1']
        row2 = ((center_of_rotation["270"]['x2'] - center_of_rotation["90"]['x2'])/2) + center_of_rotation["90"]['x2']
        # Rows are 'y' because this is (x,y) notation when looking at figure
        center['y'] = np.average([row1,row2])

        # Y jaws are in left-right direction so it is the column between them 
        # that is of interest. Slightly different for Y1 and Y2 so an average is calculated
        column1 = ((center_of_rotation["90"]['y1'] - center_of_rotation["270"]['y1'])/2) + center_of_rotation["270"]['y1']
        column2 = ((center_of_rotation["270"]['y2'] - center_of_rotation["90"]['y2'])/2) + center_of_rotation["90"]['y2']  
        # Columns are 'x' because this is (x,y) notation when looking at figure  
        center['x'] = np.average([column1, column2])

def process_folder(use_bb = False):

    global input_folder
    date_list = []
    machine_list = []
    machine = ""
    input_folder = input("Drag and drop the folder containing the files to be processed.\n").replace("& ", "").strip("'").strip('"')
    
    
    cal_images, analysis_images = organize_images(input_folder)
    find_center_of_rotation(cal_images)
    count = 0

    for irradiation_event in analysis_images:
        # update == to 2 to process combined images
        if len(analysis_images[irradiation_event]) == 5:
            image_50_percent = analysis_images[irradiation_event][0].pixel_array
            combined_image = get_combined_image(analysis_images[irradiation_event][0], analysis_images[irradiation_event][1])

            _, interpolated_peaks = find_irradiated_edges(image_50_percent, center)
            left_right, up_down = find_80_percent_width(interpolated_peaks)

            left = int(center['y'] - (left_right / 2))
            right = int(center['y'] + (left_right / 2))
            up = int(center['y'] - (up_down / 2))
            down = int(center['y'] + (up_down / 2))
            
            left_right_mean_80_percent = np.mean(image_50_percent[int(center['y']) - 10 : int(center['y'])+ 10, left:right])
            up_down_mean_80_percent = np.mean(image_50_percent[up:down, int(center['x']) - 10 : int(center['x'])+ 10])
    

            results, interpolated_peaks = find_irradiated_edges(combined_image, center, combined_image = \
                                                         {"Left-Right": left_right_mean_80_percent,
                                                          "Up-Down": up_down_mean_80_percent})
            machine = combined_image.RadiationMachineName
            date = qat.format_date(combined_image)
        
        else:
            count += 1
            print("\nResults from image {}.".format(count))
            dicom_info = analysis_images[irradiation_event][-1]
            machine, date = calculate_ML14(dicom_info, use_bb)


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
    global attachments
    jaws = {"x1": {},
            "x2": {},
            "y1": {},
            "y2": {}}
    
    plt.figure(figsize = (14, 9))

    for jaw in jaws:
        jaws[jaw]["positions"] = []
        jaws[jaw]["residuals"] = []
        jaws[jaw]["iso"] = "NA"
        for residual in residuals_mm:
            if jaw in residual:
                jaws[jaw]["positions"].append(float(residual.split("_")[-1].strip("m"))/10)
                jaws[jaw]["residuals"].append(residuals_mm[residual])
                if jaws[jaw]["positions"][-1] == 0:
                    jaws[jaw]["iso"] = np.round(jaws[jaw]["residuals"][-1],2)
                

        
        plt.plot(jaws[jaw]["positions"], jaws[jaw]["residuals"], marker = 'o', linestyle = '', markersize = 10)

    for jaw in jaws:
        x_values, fit = get_poly_values(jaws[jaw]["positions"], jaws[jaw]["residuals"], degree = 2)
        plt.plot(x_values, fit, linestyle = '--', color = 'black')
        jaws[jaw]["average"] = np.round(np.average(jaws[jaw]["residuals"]), 2)

    font_size = 24
    plt.legend(["X1\n0 mm = {}\nAve = {}\n".format(jaws["x1"]["iso"], jaws["x1"]["average"],),\
                "X2\n0 mm = {}\nAve = {}\n".format(jaws["x2"]["iso"], jaws["x2"]["average"],),\
                "Y1\n0 mm = {}\nAve = {}\n".format(jaws["y1"]["iso"], jaws["y1"]["average"],),\
                "Y2\n0 mm = {}\nAve = {}\n".format(jaws["y2"]["iso"], jaws["y2"]["average"],)], loc= (1.01, 0.1), fontsize = font_size-4)
    
    plt.subplots_adjust(right = 0.75)

    plt.title("{}: Jaw Deviation from Expected Positions ({})".format(machine, date.split(" ")[0]), fontsize = font_size)
    plt.ylim([-1, 1])
    plt.xticks(fontsize = font_size-4)
    plt.yticks(fontsize = font_size-4)
    plt.xlabel("Expected Position (cm)", fontsize = font_size)
    plt.ylabel("Deviation (mm)", fontsize = font_size)

    figure_save_location = os.path.join(input_folder, "Jaw Deviation Summary.png")

    plt.savefig(figure_save_location)

    all_results["x1_average_deviation"] = jaws["x1"]["average"]

    all_results["x2_average_deviation"] = jaws["x2"]["average"]

    all_results["y1_average_deviation"] = jaws["y1"]["average"]

    all_results["y2_average_deviation"] = jaws["y2"]["average"]

    all_results["predicted_x_junction_mm"] = np.round(jaws["x1"]["iso"] + jaws["x2"]["iso"], 2)
    all_results["predicted_y_junction_mm"] = np.round(jaws["y1"]["iso"] + jaws["y2"]["iso"], 2)
    
    attachments =   [{'filename': "Jaw Deviation Summary.png",
            'value': base64.b64encode(open(figure_save_location, 'rb').read()).decode(),
            'encoding': 'base64'}]

def interpolate_data(data, points = 20):
    interp_data = []
    for i in range(len(data) - 1):
        new_points = np.linspace(data[i], data[i+1], num=points, endpoint=False)
        interp_data.extend(new_points)
    
    x_values = np.linspace(0, len(data), len(interp_data))

    return x_values, interp_data

def find_50_percent_dose(data, search_value):
    data1 = data[0:len(data)//2]
    data2 = data[len(data)//2: len(data)]
    index1 = find_closest_index(data1, search_value)
    index2 = find_closest_index(data2, search_value) + len(data) / 2

    return index1, index2

def get_combined_image(image1, image2):

    pixel_array1 = image1.pixel_array
    pixel_array2 = image2.pixel_array

    combined_pixel_array = pixel_array1 + pixel_array2

    combined_image = image1.copy()

    combined_image.PixelData = combined_pixel_array.tobytes()
    # combined_image.save_as("T:\\_Physics Team PEICTC\\Benjamin\\_Test Development\\ML14 - Collimation Position Accuracy\\development\\finding_50_percent\\2024-07-31\\30x30 combined_image.dcm")
    return combined_image

###

# Created by Ben Cudmore
# create executable by running the following while in the directory of the .py file
# pyinstaller -F --hiddenimport=pydicom.encoders.gdcm --hiddenimport=pydicom.encoders.pylibjpeg --consol --clean ML14.py

###


input_folder = ''
show_plots = False
all_results = {}
attachments = []
residuals_mm = {}
center = {}


machine, date = process_folder(use_bb = False)

calculate_average_deviation()

while machine == False:
    machine, date = process_folder()

print("\nPosting to QATrack...\n")
qat.log_into_QATrack()
utc_url, macros = qat.get_unit_test_collection(machine, "Jaw Position Accuracy")
tests = qat.format_results(macros, all_results)
qat.post_results(utc_url, tests, date, attachments = attachments)

