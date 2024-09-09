
import os as os
import datetime as datetime

import pydicom as dicom

from pylinac import StandardImagingQCkV
from pylinac import StandardImagingQC3

import numpy as np
from scipy.signal import savgol_filter, find_peaks
import matplotlib.pyplot as plt
from PIL import Image as Image
from scipy.signal import find_peaks
import csv
import warnings
import cv2
import sys

sys.path.append("T:\\_Physics Team PEICTC\\Benjamin\\GitHub\\PEICTC_QA")
from Helpers.QATrackHelpers import QATrack as qat

class PlanarImaging:

    warnings.filterwarnings("ignore", category=UserWarning, module='pylinac')

    input_path = "T:\\QA\\Data\\Monthly Imaging\\_Input Folder\\Planar Imaging"
    processed_path = "T:\\QA\\Data\\Monthly Imaging\\_Processed"
    show_plots = False
    show_unprocessed_plots = True
    archive_files = True

    def post_planar_results_to_qatrack(qatrack_results):
        # Input folder can handle result sets from multiple months and multiple linacs
        for machine in qatrack_results:
            for date_key in qatrack_results[machine]:
                unit_test_collection_url, macros = qat.get_unit_test_collection(machine, "Planar Imaging")
                if type(unit_test_collection_url) != None:
                    formatted_results = qat.format_results(macros, qatrack_results[machine][date_key]["Results"])

                    date = qatrack_results[machine][date_key]["Acquisition Date"]
                    qat.post_results(unit_test_collection_url, formatted_results, date)
    
    def generate_baselines(test_list_results, macros):
        compiled_results = {}
    
        # Initialize the compiled_results dictionary
        for machine in test_list_results:
            compiled_results[machine] = {'Date': []}
        
        # Flatten the nested dictionary and populate compiled_results
        for machine, machine_data in test_list_results.items():
            for date_key, results in machine_data.items():
                compiled_results[machine]["Date"].append(date_key)
                for test, result_value in results.get('Results', {}).items():
                    macro = macros.get(test)
                    if macro:
                        compiled_results[machine].setdefault(macro, []).append(result_value)
        
        # Fill missing values with NaN
        for machine, machine_data in compiled_results.items():
            for test in machine_data:
                if len(compiled_results[machine][test]) != len(compiled_results[machine]["Date"]):
                    compiled_results[machine][test].append(None)
        

            # Specify the file name
            csv_file = str(machine) + ' planar imaging baselines.csv'

            # Writing the data to CSV file
            with open(csv_file, 'w', newline='') as file:
                writer = csv.writer(file)

                # Write the header row
                writer.writerow(compiled_results[machine].keys())

                # Write the data rows
                writer.writerows(zip(*compiled_results[machine].values()))

            print(f'The CSV file "{csv_file}" has been created successfully.')


    def process_input_folder():
        
        test_list_results = {}
        print("Scanning files in input folder ({}).".format(str(PlanarImaging.input_path)))

        expected_test_lists = PlanarImaging.get_expected_test_lists()

        print("Processing has begun!")
        for machine in expected_test_lists:
            for date_key in expected_test_lists[machine]:
                for root, dirs, files in os.walk(PlanarImaging.input_path, topdown=False):
                    if "CBCT" in root:
                        continue
                    for file in files:
                        if ".dcm" in file:
                            file_path = os.path.join(root, file)
                            image = dicom.dcmread(file_path)
                            
                            # only process acquired images, not DRRs, plans, dose exports, etc...
                            if hasattr(image, "ImageType"):
                                if "DRR" not in image.ImageType[2]:
                                    if machine not in test_list_results:
                                        test_list_results[machine] = {}
    
                                    if date_key not in test_list_results[machine]:
                                        test_list_results[machine][date_key] = {}
                                        test_list_results[machine][date_key]["Acquisition Date"] = {}
                                        test_list_results[machine][date_key]["Results"] = {}
    
                                    if machine in image.StationName and date_key in image.AcquisitionDate: 
                                        file_info = PlanarImaging.get_file_info(file_path)
    
                                        if not file_info:
                                            continue
                                        else:
                                            test_results = PlanarImaging.process_image(file_info)
    
                                        if not test_results:
                                            continue
                                        else:
                                            for test_result in test_results:
                                                test_list_results[machine][date_key]["Results"][test_result] = test_results[test_result]
                                                test_list_results[machine][date_key]["Acquisition Date"] = qat.format_date(image)
    
                                            if PlanarImaging.archive_files == True:
                                                target_path = PlanarImaging.create_folders(file_info, PlanarImaging.processed_path)
                                                new_name = PlanarImaging.create_new_file_name(file_info, target_path)
                                                try:
                                                    os.rename(file_info['Directory'], new_name)
                                                    print("Processed: " + str(os.path.basename(new_name)))
                                                except:
                                                    print("Could not rename the following file:\n" + str(file_info["Directory"]))
                                else:
                                    os.remove(file_path)
                            else:
                                    os.remove(file_path)


        return test_list_results

    def get_expected_test_lists():
        expected_test_lists = {}
        for root, dirs, files in os.walk(PlanarImaging.input_path):
            if "CBCT" not in root:
                for file in files:
                    if ".dcm" in file:
                        try:
                            image = dicom.dcmread(os.path.join(root, file))
                            if hasattr(image, "ImageType"):
                                if "DRR" not in image.ImageType[2]:
                                    machine_name = image.StationName
                                    acquisition_date = image.AcquisitionDate

                                    # Initialize the nested dictionaries if they don't exist
                                    if machine_name not in expected_test_lists:
                                        expected_test_lists[machine_name] = {}

                                    if acquisition_date not in expected_test_lists[machine_name]:
                                        expected_test_lists[machine_name][acquisition_date.rstrip()[0:-2]] = {}

                        except Exception as e:
                            print("There was an error:\n{}".format(str(e)))

        return expected_test_lists
    
    def get_file_info(file_path):
        if isinstance(file_path, str):
            image = dicom.dcmread(file_path)

        if 'RTIMAGE' in image['Modality'].value:

            file_info = {}
            image_description = image['RTImageDescription'].value.lower()

            if "mv" in image_description:
                image_description = image_description.split(" ")
                file_info['Energy'] = image_description[0].strip("x")
                file_info['Energy Unit'] = 'mv'

                if "2.5" in file_info['Energy']:
                    file_info['Energy'] = "2"
                    file_info['Flood Field'] = PlanarImaging.check_for_phantom(image)

                else:
                    file_info['Flood Field'] = None
                    file_info['Rep Rate'] = "rr" + image_description[2]

            elif "kv" in image_description:
                file_info['Energy'] = image_description.split(" ")[0]
                file_info['Energy Unit'] = 'kv'
                file_info['Flood Field'] = PlanarImaging.check_for_phantom(image)
        
        file_info["Machine"] = image['RadiationMachineName'].value
        file_info["Date"] = datetime.datetime.strptime(image['AcquisitionDate'].value, "%Y%m%d")
        file_info["Directory"] = file_path
        
        return file_info
    
    def process_image(file_info):
        file = file_info['Directory']
        in_house_results = {}
        pylinac_results = []

        try:
            if file_info['Flood Field'] == True:
                in_house_results["Uniformity"] = PlanarImaging.get_uniformity(file)
                
            elif 'kv' in file_info['Energy Unit']:
                test = StandardImagingQCkV(file)
                test.analyze(low_contrast_threshold=0.01, high_contrast_threshold=0.5, ssd=test.image.sid-57)
                pylinac_results = test.results_data()
                in_house_results["Phantom Size"] = PlanarImaging.get_phantom_size_in_mm(file, test)

            elif 'mv' in file_info['Energy Unit']:
                test = StandardImagingQC3(file)
                test.analyze(low_contrast_threshold=0.01, high_contrast_threshold=0.5, ssd=test.image.sid-91)
                pylinac_results = test.results_data()
                if "2" in file_info["Energy"]:
                    in_house_results["Phantom Size"] = PlanarImaging.get_phantom_size_in_mm(file, test)

            return PlanarImaging.format_results_for_QATrack(file_info, pylinac_results, in_house_results)
         
        except Exception as e:
            image = dicom.dcmread(file).pixel_array
            if file_info['Flood Field'] == None:
                print('\nDid not process: "{}"\n'.format(str(file_info['Directory']).split("\\")[-1]) + 
                 "Flood field only required for 2.5x and kv.")

            else:   
                print('\nError with file: {}\n'.format(str(file_info['Directory']).split("\\")[-1]) + 
                '({} {}) '.format(file_info['Energy'], file_info['Energy Unit']) + str(e))

            if PlanarImaging.show_unprocessed_plots == True:
                print("Do you want to see the image? [Y/N]")
                user_input = input()
                if "y" in user_input or "Y" in user_input or "yes" in user_input or "Yes" in user_input:
                    plt.imshow(image, cmap= 'gray')
                    plt.title(str(file))
                    plt.show()
            
            return None
    
    def create_folders(file_info, processed_path_root):
        target_path = os.path.join(processed_path_root, file_info['Machine'], 'Planar Imaging', str(file_info["Date"].year), file_info["Date"].strftime("%Y-%m-%d"))

        if not os.path.exists(os.path.join(target_path)):
            os.makedirs(target_path)

        return target_path

    def create_new_file_name(file_info, target_path):

        if 'Rep Rate' in file_info and file_info["Flood Field"] == True:
            new_name = " ".join([file_info['Energy'], file_info['Energy Unit'], file_info['Rep Rate']]) + " (FF).dcm"
        
        elif 'Rep Rate' in file_info and file_info["Flood Field"] != True:
            new_name = " ".join([file_info['Energy'], file_info['Energy Unit'], file_info['Rep Rate']]) + ".dcm"

        elif 'Rep Rate' not in file_info and file_info["Flood Field"] == True:
            new_name = " ".join([file_info['Energy'], file_info['Energy Unit']]) + " (FF).dcm"
        else:
            new_name = " ".join([file_info['Energy'], file_info['Energy Unit']]) + ".dcm"

        new_name = os.path.join(target_path, new_name)

        new_name = PlanarImaging.ensure_unique_file_name(new_name)

        return new_name
    
    def ensure_unique_file_name(new_name):
        count = 0
        root, ext = os.path.splitext(new_name)
        while os.path.exists(new_name):
            count += 1
            new_name = f"{root}_{count}{ext}"
        return new_name
    
    def print_macros_from_test_list_results(test_list_results):
        for key in test_list_results:
            print(key)

    def check_for_phantom(file, window = 20, poly_order = 3):
        if "mv" in file['RTImageDescription'].value.lower():
            prominence = 0.003
        else:
            prominence = 0.15

        pixel_info = file.pixel_array
        search_row = int(pixel_info.shape[0]/2)
        search_array = pixel_info[search_row,:]
        rsd = PlanarImaging.get_rsd(search_array, window=100)
        rsd_smooth = savgol_filter(rsd, window, poly_order)

        ### Visualize data
        if PlanarImaging.show_plots == True:
            plt.plot(rsd_smooth)

            if len(find_peaks(rsd_smooth, prominence = prominence)[0]) == 2:
                plt.title("No phantom in image: indicated by 2 peaks")
            if len(find_peaks(rsd_smooth, prominence = prominence)[0]) > 2:
                plt.title("Phantom in image: indicated by > 2 peaks")

            plt.show()

        if len(find_peaks(rsd_smooth, prominence = prominence)[0]) == 2:
            return True
        else:
            return False

    def get_rsd(one_d_array, window = 10):
        rsd = []
        for pixel in range(len(one_d_array-window)):
            moving_std = np.std(one_d_array[pixel:pixel+window])
            moving_ave =np.mean(one_d_array[pixel:pixel+window])
            rsd.append(moving_std / moving_ave)
        return rsd

    def get_uniformity(file, roi_size_mm = 10, off_axis_rois_mm = 75):
        
        # initialize variables
        rois = {
            "Center": [],
            "Left": [],
            "Top": [],
            "Right": [],
            "Bottom": []
        }
        if isinstance(file, str):
            dicom_info = dicom.dcmread(file)
        else:
            dicom_info = file

        pixel_info = dicom_info.pixel_array
        pixel_center = {
                "Row": int(pixel_info.shape[0]/2),
                "Column": int(pixel_info.shape[1]/2)
            }
        pixel_spacing = dicom_info.ImagePlanePixelSpacing

        # Determine which pixels correspond to ROIs
        roi_length_pixels = int(round(roi_size_mm / pixel_spacing[0]))
        roi_pixel_offset = int(round(off_axis_rois_mm / pixel_spacing[0]))
        half_roi_pixels = int(round(roi_length_pixels/2))

        for roi in rois:
            rois[roi] = PlanarImaging.get_roi_pixels(roi, pixel_info, pixel_center, half_roi_pixels, roi_pixel_offset)
        
        if PlanarImaging.show_plots ==True:
            plt.imshow(pixel_info, cmap = 'gray', interpolation = 'nearest')
            plt.show()
        else:
            plt.close()

        return PlanarImaging.calculate_uniformity(rois)

    def calculate_uniformity(rois):
        roi_averages = []

        for roi in rois:
            roi_averages.append(np.mean(rois[roi]))

        max_ave = np.max(roi_averages)
        min_ave = np.min(roi_averages)

        uniformity = np.round((1 - ((max_ave - min_ave)/(max_ave + min_ave)))*100, 2) # Should this be divided by just max or min?
        return uniformity

    def get_roi_pixels(roi, pixel_info, pixel_center, half_roi_pixels, roi_pixel_offset):

        # Determine the pixel info for the ROIs
        if "Center" in roi:
            index = {"Top": pixel_center['Row'] - half_roi_pixels,
                     "Bottom": pixel_center['Row'] + half_roi_pixels,
                     "Left": pixel_center['Column'] - half_roi_pixels,
                     "Right": pixel_center['Column'] + half_roi_pixels
                     }

        elif "Left" in roi:
            index = {"Top": pixel_center['Row'] - half_roi_pixels,
                     "Bottom": pixel_center['Row'] + half_roi_pixels,
                     "Left": pixel_center['Column'] - half_roi_pixels - roi_pixel_offset,
                     "Right": pixel_center['Column'] + half_roi_pixels - roi_pixel_offset
                     }
            
        elif "Top" in roi:
            index = {"Top": pixel_center['Row'] - half_roi_pixels - roi_pixel_offset,
                     "Bottom": pixel_center['Row'] + half_roi_pixels - roi_pixel_offset,
                     "Left": pixel_center['Column'] - half_roi_pixels,
                     "Right": pixel_center['Column'] + half_roi_pixels
                     }
            
        elif "Right" in roi:
            index = {"Top": pixel_center['Row'] - half_roi_pixels,
                     "Bottom": pixel_center['Row'] + half_roi_pixels,
                     "Left": pixel_center['Column'] - half_roi_pixels + roi_pixel_offset,
                     "Right": pixel_center['Column'] + half_roi_pixels + roi_pixel_offset
                     }
            
        elif "Bottom" in roi:
            index = {"Top": pixel_center['Row'] - half_roi_pixels + roi_pixel_offset,
                     "Bottom": pixel_center['Row'] + half_roi_pixels + roi_pixel_offset,
                     "Left": pixel_center['Column'] - half_roi_pixels,
                     "Right": pixel_center['Column'] + half_roi_pixels
                     }
        
        if PlanarImaging.show_plots ==True:
            PlanarImaging.plot_rectangle(index)
        roi_pixels = pixel_info[index["Top"] : index["Bottom"], index["Left"] : index["Right"]]
        return(roi_pixels)
    
    def plot_rectangle(index):
        plt.plot([index['Left'], index['Right'], index['Right'], index['Left'], index['Left']],
                 [index['Top'], index['Top'], index['Bottom'], index['Bottom'], index['Top']], 
                 color='red')
    
    def measure_phantom_in_pixels(rotated_array, prominence, peak_window = 3, canny = True): # 3
        if canny == True:
            image_array = (rotated_array / np.max(rotated_array) * 255).astype(np.uint8)
            blurred_image = cv2.GaussianBlur(image_array, (5, 5), 0)
            edges = cv2.Canny(blurred_image, 5, 30)  # 30, 100 finds jaws, 20, 40 finds phantom sometimes

            if PlanarImaging.show_plots == True:
                overlay_image = cv2.cvtColor(image_array, cv2.COLOR_GRAY2BGR)
                overlay_image[:, :, 2] = edges  # Set blue channel to the Canny edges
                
                # Display the original grayscale image with edges overlaid
                cv2.imshow('Edge Detection', overlay_image)
                cv2.waitKey(0)
                cv2.destroyAllWindows()

            # Measure the length and width of the rectangle in pixels
            
            center_row = rotated_array.shape[0] // 2
            center_column = rotated_array.shape[1] // 2

            length_edges_ave = np.mean(edges[center_row - 10: center_row + 10, :], axis = 0)
            width_edges_ave = np.mean(edges[:, center_column - 10: center_column + 10], axis = 1)

            width_peaks, _ = find_peaks(width_edges_ave)
            length_peaks, _ = find_peaks(length_edges_ave)
            return {"Width [mm]": int(width_peaks[-1] - width_peaks[0]),
                    "Length [mm]": int(length_peaks[-1] - length_peaks[0])
                }

        else:
            center_row = rotated_array.shape[0] // 2
            length_array = rotated_array[center_row, :] 
            length_rsd = PlanarImaging.get_rsd(length_array)

            center_column = rotated_array.shape[1] // 2
            width_array = rotated_array[:, center_column]
            width_rsd = PlanarImaging.get_rsd(width_array)

            one_d_arrays = {"Length": length_rsd,
                    "Width": width_rsd}

            if PlanarImaging.show_plots == True:
                plt.plot(length_rsd)
                plt.show()
            num_pixels = []

            for array in one_d_arrays:
                peaks, _ = find_peaks(one_d_arrays[array], prominence=prominence)
                peaks_of_interest = [peaks[0], peaks[-1]]

                peak_centroids = []

                for peak in peaks_of_interest:
                    peak_1 = one_d_arrays[array][peak-peak_window:peak+peak_window]
                    x_values = np.arange(peak-peak_window, peak + peak_window)
                    peak_centroids.append(PlanarImaging.find_centroid_using_polynomial(peak_1, x_values))
                    #peak_centroids.append(General.find_centroid_using_gaussian(peak_1, x_values))
                num_pixels.append(peak_centroids[1] - peak_centroids[0])
                #num_pixels.append(peaks_of_interest[1] - peaks_of_interest[0]) # Calculates dimensions without fitting

            return { "Width [px]": num_pixels[1],
                    "Length [px]": num_pixels[0]
                }

    def polynomial(x, *coefficients):
        return np.polyval(coefficients, x)
    
    def find_centroid_using_polynomial(peak, x_values, degree=3):
        # Fit a polynomial to the data
        coefficients = np.polyfit(x_values, peak, degree)

        # Generate a higher-resolution array of x-values
        high_res_x_values = np.linspace(x_values[0], x_values[-1], 1000)

        # Evaluate the polynomial function at the higher-resolution points
        interpolated_fit_curve = PlanarImaging.polynomial(high_res_x_values, *coefficients)

        # Plot the original data and the interpolated polynomial curve
        if PlanarImaging.show_plots == True:
            plt.figure(20)
            plt.plot(x_values, peak, 'bo', label='Original Data')
            plt.plot(high_res_x_values, interpolated_fit_curve, 'r-', label=f'Interpolated Polynomial (Degree {degree}) Curve')
            plt.legend()
            plt.show()

        # Find peaks in the interpolated polynomial curve
        peaks, _ = find_peaks(interpolated_fit_curve)
        interpolated_peaks = high_res_x_values[peaks]

        return interpolated_peaks
    
    def get_phantom_size_in_mm(file_path, pylinac_results):
        dicom_info = dicom.dcmread(file_path)
        pixel_spacing_mm = dicom_info.ImagePlanePixelSpacing[0]
        magnification_factor = dicom_info.RadiationMachineSAD / dicom_info.RTImageSID
        pixel_spacing_mm = pixel_spacing_mm * magnification_factor
        
        if isinstance(pylinac_results, StandardImagingQCkV):
            crop_rows = 100
            crop_columns = 200
            prominence = 0.15
            angle = pylinac_results.phantom_angle - pylinac_results.phantom_ski_region.orientation 

        elif isinstance(pylinac_results, StandardImagingQC3):
            crop_rows = 275
            crop_columns = 275
            prominence = 0.003
            angle = pylinac_results.phantom_angle + pylinac_results.phantom_ski_region.orientation

        pixel_array = dicom_info.pixel_array

        cropped_pixel_array = pixel_array[crop_rows:-crop_rows, crop_columns:-crop_columns]

        # Using PIL to rotate the image
        pixel_array1 = Image.fromarray(np.array(cropped_pixel_array))
        rotated_image = pixel_array1.rotate(angle, expand= False)

        # Convert rotated image back to NumPy array
        rotated_array = np.array(rotated_image)
        if PlanarImaging.show_plots == True:
            plt.imshow(rotated_array, cmap='gray')
            plt.show()    

        phantom_size = PlanarImaging.measure_phantom_in_pixels(rotated_array, prominence)
        for dimension in phantom_size:
            phantom_size[dimension] = float(phantom_size[dimension] * pixel_spacing_mm)
        
        return phantom_size
             

    def format_results_for_QATrack(file_info, pylinac_results, in_house_results):
        results = {}
        if file_info['Flood Field'] == True:
            if 'Rep Rate' in file_info:
                macro_base = "_".join([file_info['Energy Unit'], file_info['Energy'], file_info['Rep Rate']])
            else:
                macro_base = "_".join([file_info['Energy Unit'], file_info['Energy']])
            
            results["_".join([macro_base, 'uniformity'])] = in_house_results["Uniformity"]

            return results
        
        elif 'Rep Rate' in file_info:
            macro_base = "_".join([file_info['Energy Unit'], file_info['Energy'], file_info['Rep Rate']])
        else:
            macro_base = "_".join([file_info['Energy Unit'], file_info['Energy']])

        results["_".join([macro_base, 'median_cnr'])] = round(pylinac_results.median_cnr, 2)
        results["_".join([macro_base, 'noise'])] = round(pylinac_results.median_contrast/pylinac_results.median_cnr, 4)
        results["_".join([macro_base, 'mtf_50'])] = round(list(pylinac_results.mtf_lp_mm[1].values())[0], 3)
        results["_".join([macro_base, 'contrast_rois'])] = round(pylinac_results.num_contrast_rois_seen, 0)

        if in_house_results != {}:
            results["_".join([macro_base, 'width'])] = round(in_house_results["Phantom Size"]["Width [mm]"], 1)
            results["_".join([macro_base, 'length'])] = round(in_house_results["Phantom Size"]["Length [mm]"], 1)

        return results