import webbrowser
import requests
import os as os
import pandas as pd
import datetime as datetime
import time
import pydicom as dicom

# Author:   Benjamin Cudmore, PEICTC

class QATrack:

    """
    1.  qat.log_into_QATrack()
    2.  utc_url, macros = qat.get_unit_test_collection(machine, "Jaw Position Accuracy")
    3.  tests = qat.format_results(macros, all_results)
            # all_results must be structured in your as {"QATrack_test_marco": result}
    4.  qat.post_results(utc_url, tests, date)
    5.  evaluate_MPC_position0(use_bb = True)

    """
    root = "http://qatrack/api"
    headers = ""
    login = {
        "token": "",
        "username": "",
        "password": ""
    }

    def log_into_QATrack():

        user = os.getlogin()
        key_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))), 'Not in GitHub', 'LoginInfo_qatrack.xlsx')
        keys = pd.read_excel(key_path)

        for index, row in keys.iterrows():
            if row["user"] == user:
                QATrack.login['token'] = row["key"]
                QATrack.set_headers()
                return
            
        print(user + " does not have a QATrack token set. Contact Ben Cudmore to get set up.")
        

    def set_headers():
        if QATrack.login['token'] != "":
            QATrack.headers = {"Authorization": "Token %s" % QATrack.login['token']}
        else:
            token_url = QATrack.root + "/get-token/"
            resp = requests.post(token_url, {'username': QATrack.login['username'], 'password': QATrack.login['password']})
            if resp.status_code == requests.codes.BAD:
                print(resp)
            else:
                token = resp.json()['token']
                QATrack.headers = {"Authorization": "Token %s" % token} # the request headers must include the API token

    def get_unit_test_collection(unit, test_list):
        test_lists = requests.get(
            QATrack.root +
            '/qa/unittestcollections/?unit__name__icontains=' +
            unit +'&test_list__name__icontains=' +
            test_list, headers=QATrack.headers)
        
        test_lists = test_lists.json()['results']
        number_of_test_lists = len(test_lists)

        if number_of_test_lists != 1:
            if number_of_test_lists > 1:
                print("\nThe following tests lists match the string you entered:\n")
                for i in range(len(test_lists)):
                    print(test_lists[i]['name'])
                print("\nRefine test_list name to reduce the number of test list results.")
            elif number_of_test_lists == 0:
                print("No test lists found on {} containing '{}'.".format(unit, test_list))
                return None, None
        else:
            utc_url = test_lists[0]['url']
            test_list_url = test_lists[0]['tests_object']
            macros = QATrack.get_macros_from_unit_test_collection(test_list_url)
            return utc_url, macros

    def get_macros_from_unit_test_collection(test_list_url):
        macros = {}
        tests_resp = requests.get(test_list_url, headers=QATrack.headers).json()
        for test in tests_resp['tests']:
            test_resp = requests.get(test, headers=QATrack.headers).json()
            macros[test_resp['name']] = test_resp['slug']
        return macros
    
    def format_results(macros, results):
        tests = {}
        for macro in macros:
            tests[macros[macro]] = {'skipped': True}

        for test in tests:
            for result in results:
                if test == result:
                    try:
                        tests[test] = {'value': float(results[result])}
                    except:
                        tests[test] = {'skipped': True}
        return tests
    
    def format_date(date_source):
        date_format = '%Y-%m-%d %H:%M'

        if isinstance(date_source, dicom.FileDataset):
            acquisition_date = date_source.AcquisitionDate
            acquisition_time = date_source.AcquisitionTime

            if acquisition_date and acquisition_time:
                # Combine date and time and convert to a datetime object
                date_string = f"{acquisition_date}{acquisition_time}"
                date_string = date_string[:12]
                datetime_object = datetime.datetime.strptime(date_string, "%Y%m%d%H%M")

            # Format the datetime object
            formatted_date = datetime_object.strftime(date_format)
            return formatted_date

        elif isinstance(date_source, datetime.datetime):
            date = date_source.strftime(date_format)

        elif ".dcm" in date_source:
            date = datetime.datetime.strptime(date_source['Acquisition_Date'], "%b %d/%y")
            date.strftime(date_format)
        else:
            date = datetime.datetime.strptime(date_source, '%Y-%m-%d %H:%M:%S.%f')
            date = str(date.strftime(date_format))


        return date
    
    def post_results(utc_url, tests, date, in_progress = True):
        
        data = {
            'unit_test_collection': utc_url,
            'in_progress': in_progress,  # optional, default is False
            'include_for_scheduling': True,
            'work_started': date,
            'work_completed': date,
            #'comment': "Results imported using API (GUI v2)",  # optional
                "tests": tests      
    }       
        resp = requests.post(QATrack.root + "/qa/testlistinstances/", json=data, headers=QATrack.headers)

        if resp.status_code == requests.codes.CREATED: # http code 201
            print('POSTED!! The test list will open in a few seconds.')
            completed_url = resp.json()['site_url']
            time.sleep(2)
            webbrowser.open(completed_url, new=0, autoraise=True)

        else:
            print('Your request failed with the following response:\n "%s" ' % resp.reason)