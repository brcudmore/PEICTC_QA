import requests
import os as os
import datetime as datetime
import time
import sys
from PIL import Image as Image
import pandas as pd

import pydicom as dicom
from pyTQA import tqa
import json


sys.path.append("T:\\_Physics Team PEICTC\\Benjamin\\GitHub\\PEICTC_QA")
from Helpers.QATrackHelpers import QATrack as qat

class SMARI:
    client_key = ''
    client_id = ''
    input_path = "T:\\QA\\Data\\Monthly Imaging\\_Input Folder\\CBCT"
    output_path = "T:\\QA\\Data\\Monthly Imaging\\_Processed\\"

    machines = {
        "TrueBeam3426":                       # Update string to unique portion of machine name from SMARI
        {
            'Machine ID': '',
            "Tests": 
            {
                '1. CTP504 - Head': 
                {          
                    'kvp': '100',       # Update value to test acquisition parameter
                    'mA': '15',
                },
                '2. CTP504 - Pelvis': 
                {
                    'kvp': '125',
                    'mA': '60',
                },
                '3. CTP504 - Thorax': 
                {
                    'kvp': '125',
                    'mA': '15',
                }
                }
            },

        "TrueBeam5833":  
        {
            'Machine ID': '',   
            'Tests': 
            {   
                '1. CTP504 - Head': 
                {           
                    'kvp': '100',       
                    'mA': '15',       
                },
                '2. CTP504 - Pelvis': 
                {
                    'kvp': '125',
                    'mA': '60',
                },
                '3. CTP504 - Thorax': 
                {
                    'kvp': '125',
                    'mA': '15',
                }
            }
        },
    "iX": 
    {
        'Machine ID': '',
        'Tests': 
        {
            'Pelvis CNR': 
            {
            
                'kvp': '125',
                'mA': '80'
            },
            'Low Thorax CNR': 
            {
            
                'kvp': '110',
                'mA': '20'
            },
            'STD Head CNR': 
            {
            
                'kvp': '100',
                'mA': '20'
            },
            'HQ Head CNR': 
            {
            
                'kvp': '100',
                'mA': '80'
            },
        }
    },
    "DiscoveryRT": 
    {
        'Machine ID': '',
        'Tests': 
        {
            'D3 - D4 - CT number for water - Noise and Uniformity': 
            {
                'kvp': '120',
                'mA': '250'
            },
            'GE water phantom': 
            {
                'kvp': '120',
                'mA': '3100' ### temp
            }
        }
    }
    }

    def log_into_smari():

        user = os.getlogin()
        key_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'Not in GitHub', 'LoginInfo_smari.xlsx') # Can only access with Physicist login
        keys = pd.read_excel(key_path)

        for _, row in keys.iterrows():
            if row["user"] == user:
                tqa.client_key = row["key"]
                tqa.client_id = f"418:{row['id']}"
                tqa.set_tqa_token()
                return
            
        print(user + " does not have a SMARI token set. Contact Ben Cudmore to get set up.")


    def post_results_from_rsid(head = '', pelvis = '', thorax = ''):
        
        rsids = {"TrueBeam3426": {
                    "Head": head,
                    "Pelvis": pelvis,
                    "Thorax": thorax
                }
            }

        SMARI.machines = {}
        for machine in rsids:
            for scan in rsids[machine]:
                if rsids[machine][scan] != '':
                    date = qat.format_date(tqa.get_report_data(rsids[machine][scan])['json']['reportData']['collectedOn']['date'])
                    date_key = date[0:7]

                    if machine not in SMARI.machines:
                        SMARI.machines[machine] = {}

                    if date_key not in SMARI.machines[machine]:
                        SMARI.machines[machine][date_key] = {}

                    SMARI.machines[machine][date_key][scan] = {}
                    SMARI.machines[machine][date_key][scan]["Acquisition Date"] = date

        SMARI.set_expected_linac_results()

        for machine in SMARI.machines:
            for date_key in SMARI.machines[machine]:
                for scan in SMARI.machines[machine][date_key]:
                    SMARI.get_results_from_result_set_id(rsids[machine][scan], machine, date_key, scan)

        qatrack_results = SMARI.compile_test_list_results() 

        SMARI.post_smari_results_to_qatrack(qatrack_results)

    def compile_test_list_results():
        qatrack_results = {}
        for machine in SMARI.machines:
            qatrack_results[machine] = {}
            for date_key in SMARI.machines[machine]:
                if hasattr(qatrack_results[machine], date_key) == False:
                    qatrack_results[machine][date_key] = {}
                    qatrack_results[machine][date_key]["Acquisition Date"] = ""
                    qatrack_results[machine][date_key]["Results"] = {}
                for test in SMARI.machines[machine][date_key]:
                    for result in SMARI.machines[machine][date_key][test]["Results"]:
                        qatrack_results[machine][date_key]["Results"][result] = SMARI.machines[machine][date_key][test]["Results"][result]
                qatrack_results[machine][date_key]["Acquisition Date"] = SMARI.machines[machine][date_key][test]["Acquisition Date"]
        
        return qatrack_results

    def post_smari_results_to_qatrack(qatrack_results):
        for machine in qatrack_results:
            for date_key in qatrack_results[machine]:
                if "3426" in machine or "5833" in machine:
                    test_list = "Monthly CBCT"
                elif "GE Discovery":
                    test_list = None

                unit_test_collection_url, macros = qat.get_unit_test_collection(machine, test_list)

                if type(unit_test_collection_url) != None:
                    formatted_results = qat.format_results(macros, qatrack_results[machine][date_key]["Results"])

                    date = qatrack_results[machine][date_key]["Acquisition Date"]

                    qat.post_results(unit_test_collection_url, formatted_results, date)

    def process_input_folder():
        folder_content = SMARI.determine_input_path_contents()
        SMARI.initialize_result_list(folder_content)
        if 'DiscoveryRT' in SMARI.machines.keys():
            SMARI.set_expected_ct_sim_results()
        else:
            SMARI.set_expected_linac_results()

        for machine in SMARI.machines:
            for date_key in SMARI.machines[machine]:
                for test in SMARI.machines[machine][date_key]:
                    schedule_id = SMARI.machines[machine][date_key][test]['Schedule ID']
                    acquisition_date = SMARI.machines[machine][date_key][test]["Acquisition Date"]
                    try:
                        target_folder = SMARI.create_processed_path(machine, acquisition_date, test)
                    except:
                        pass

                    try:
                        SMARI.upload_to_smari(schedule_id, machine, test, date_key, target_folder)
                        SMARI.analyze_image_set(schedule_id)
                        SMARI.set_report_date(schedule_id, acquisition_date)
                        resp = tqa.finalize_report(schedule_id)

                        if resp.status_code >= 200 or resp.status_code < 300:
                            result_set_id = resp.json()['reportId']
                            SMARI.machines[machine][date_key][test]['Result Set ID'] = result_set_id
                            SMARI.get_results_from_result_set_id(result_set_id, machine, date_key, test)
                    except Exception as e:
                        print ("There was an error:\n" + str(e))
                        break
        
        qatrack_results = SMARI.compile_test_list_results() 

        return qatrack_results

    def create_processed_path(machine, date, test):
        target_folder = os.path.join(SMARI.output_path, machine, "CBCT", date.split("-")[0], date.split(" ")[0], test)
        if not os.path.exists(target_folder):
            os.makedirs(target_folder)

        return target_folder
    
    def determine_input_path_contents():
        print("Scanning files in input folder (" + str(SMARI.input_path) + ").")
        series_instance_id_dict = {}

        for root, dirs, files in os.walk(SMARI.input_path):
            for file in files:
                if '.dcm' in file:
                    try:
                        image = dicom.dcmread(os.path.join(root, file))
                        if hasattr(image, 'SeriesInstanceUID'):
                            machine_name = image.StationName
                            series_instance_uid = image.SeriesInstanceUID
                            if 'DiscoveryRT' in machine_name:
                                acquisition_date = image.AcquisitionDate
                            else:
                                # Do not want the date of acquisiion for monthly QA so that CBCTs can be acquired on separate days
                                acquisition_date = image.AcquisitionDate[:6]

                            # Initialize the nested dictionaries if they don't exist
                            if machine_name not in series_instance_id_dict:
                                series_instance_id_dict[machine_name] = {}

                            if acquisition_date not in series_instance_id_dict[machine_name]:
                                series_instance_id_dict[machine_name][acquisition_date.rstrip()] = {}

                            if series_instance_uid not in series_instance_id_dict[machine_name]:
                                series_instance_id_dict[machine_name][acquisition_date][series_instance_uid] = {}

                            # Populate the nested dictionary
                            series_instance_id_dict[machine_name][acquisition_date][series_instance_uid] = {
                                "kvp": str(image.KVP),
                                "mA": str(image.XRayTubeCurrent),
                                "Acquisition Date": qat.format_date(image)
                            }
            
                    except Exception as e:
                        print("There was an error:\n" + str(e))

        if len(series_instance_id_dict.keys()) < 1:
            print("There were no files in the input folder.\n")

        return series_instance_id_dict
        
    def initialize_result_list(folder_content):

        updated_folder_content = {}

        for machine in folder_content:
            updated_folder_content[machine] = {}

            for date_key in folder_content[machine]:
                updated_folder_content[machine][date_key] = {}

                for uid in folder_content[machine][date_key]:
                    for expected_machine in SMARI.machines:
                        if machine in expected_machine:
                            for test in SMARI.machines[machine]['Tests']:
                                if folder_content[machine][date_key][uid]['kvp'] == SMARI.machines[machine]['Tests'][test]['kvp'] and folder_content[machine][date_key][uid]['mA'] == SMARI.machines[machine]['Tests'][test]['mA']: 
                                    updated_folder_content[machine][date_key][test] = {
                                        "UID": uid,
                                        "Schedule ID": tqa.get_schedule_id_from_string(test, tqa.get_machine_id_from_str(machine.replace("ryRT", "ry RT"))),
                                        "Acquisition Date": folder_content[machine][date_key][uid]["Acquisition Date"],
                                        "Result Set ID": []
                                    }

        SMARI.machines = updated_folder_content
    
    def set_expected_ct_sim_results():
        for machine in SMARI.machines:
            for date_key in SMARI.machines[machine]:
                for test in SMARI.machines[machine][date_key]:
                    if hasattr(SMARI.machines[machine][date_key][test], 'Results') == False:
                        SMARI.machines[machine][date_key][test]['Results'] = {}
                    if 'D3 - D4 - CT number for water - Noise and Uniformity' in test:
                        macro_prefix = 'water'

                    else:
                        macro_prefix = ""
                    SMARI.machines[machine][date_key][test]['Results']["_".join([macro_prefix, "cbct_geometric_distortion"])] = "Geometric distortion"
                    SMARI.machines[machine][date_key][test]['Results']["_".join([macro_prefix, "cbct_spatial_resolution"])] = "Spatial resolution"
                    SMARI.machines[machine][date_key][test]['Results']["_".join([macro_prefix, "cbct_hu_constancy"])] = "HU constancy"
                    SMARI.machines[machine][date_key][test]['Results']["_".join([macro_prefix, "cbct_uniformity"])] = "Uniformity"
                    SMARI.machines[machine][date_key][test]['Results']["_".join([macro_prefix, "cbct_noise"])] = "Noise"
                    SMARI.machines[machine][date_key][test]['Results']["_".join([macro_prefix, "cbct_cnr"])] = "Low Contrast- CNR"
                    SMARI.machines[machine][date_key][test]['Results']["_".join([macro_prefix, "cbct_slice_thickness"])] = "Average"

    def set_expected_linac_results():
        for machine in SMARI.machines:
            for date_key in SMARI.machines[machine]:
                for test in SMARI.machines[machine][date_key]:
                    if hasattr(SMARI.machines[machine][date_key][test], 'Results') == False:
                        SMARI.machines[machine][date_key][test]['Results'] = {}
                    if "Thorax" in test:
                        macro_prefix = "thorax"
                    elif "Head" in test:
                        macro_prefix = "head"
                    elif "Pelvis" in test:
                        macro_prefix = "pelvis"
                    else:
                        macro_prefix = ""
                    SMARI.machines[machine][date_key][test]['Results']["_".join([macro_prefix, "cbct_geometric_distortion"])] = "Geometric distortion"
                    SMARI.machines[machine][date_key][test]['Results']["_".join([macro_prefix, "cbct_spatial_resolution"])] = "Spatial resolution"
                    SMARI.machines[machine][date_key][test]['Results']["_".join([macro_prefix, "cbct_hu_constancy"])] = "HU constancy"
                    SMARI.machines[machine][date_key][test]['Results']["_".join([macro_prefix, "cbct_uniformity"])] = "Uniformity"
                    SMARI.machines[machine][date_key][test]['Results']["_".join([macro_prefix, "cbct_noise"])] = "Noise"
                    SMARI.machines[machine][date_key][test]['Results']["_".join([macro_prefix, "cbct_cnr"])] = "Low Contrast- CNR"
                    SMARI.machines[machine][date_key][test]['Results']["_".join([macro_prefix, "cbct_slice_thickness"])] = "Average"

    def get_results_from_result_set_id(result_set_id, machine, date_key, test):

        smari_results = tqa.get_report_data(result_set_id)['json']['reportData']['values']

        for result in SMARI.machines[machine][date_key][test]['Results']:
            restart_loop = False
            for variable_id in smari_results:
                for result_id in smari_results[variable_id]:
                    if SMARI.machines[machine][date_key][test]['Results'][result] in smari_results[variable_id][result_id]['variableName']:
                        SMARI.machines[machine][date_key][test]['Results'][result] = smari_results[variable_id][result_id]['value']
                        restart_loop = True
                        break
                if restart_loop == True:
                    break


    
    def upload_to_smari(schedule_id, machine, test, date_key, target_folder):
        
        uid = SMARI.machines[machine][date_key][test]['UID']

        print("Uploading files for {} {} to SMARI for analysis.".format(machine, test))
        
        # Ensures that only images with the same SeriesInstanceID are uploaded together
        for root, dirs, files in os.walk(SMARI.input_path):
            for file in files:
                    file_directory = os.path.join(root, file)
                    image = dicom.dcmread(file_directory)
                    if hasattr(image, 'SeriesInstanceUID'):
                        series_id = image.SeriesInstanceUID
                        if series_id in uid:
                            resp = tqa.upload_analysis_file(schedule_id, file_directory)
                            if resp.status_code <200 or resp.status_code > 299:
                                print(resp.json()) #:" + str(resp.text.split(":")[-1]))
                            else:
                                if os.path.exists(os.path.join(target_folder, file)):
                                    os.rename(file_directory, os.path.join(target_folder, "repeat_" + file))
                                else:
                                    os.rename(file_directory, os.path.join(target_folder, file))

    def analyze_image_set(schedule_id):
        tqa.start_processing(schedule_id)
        print("Processing has begun.")
        
        # Wait for processing to finish before moving on to next step
        for i in range(360):
            time.sleep(10)
            processing_status = tqa.get_upload_status(schedule_id)
            if "finished" in processing_status['json']['scans'][0]['status']:
                print("Processing finished.\n")
                break
    
    def set_report_date(schedule_id, report_date):

        output_dict = {'date': report_date, 'finalize': 0}
        headers = tqa.get_standard_headers()
        url_ext = ''.join(['/schedules/', str(schedule_id), '/add-results'])
        url_process = ''.join([tqa.base_url, url_ext])
        json_data = json.dumps(output_dict)
        response = requests.post(url_process, headers = headers, data = json_data)
        return {'json': response.json(),
                'status': response.status_code,
                'raw': response
                }
