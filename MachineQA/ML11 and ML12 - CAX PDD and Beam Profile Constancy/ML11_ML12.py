print("~ Monthly Energy and Beam Profile Constancy ~\n")
print("Please wait while the app loads.\n")

# from matplotlib import pyplot as plt
# from scipy.signal import medfilt2d

import numpy as np
import os as os
import time as time
import os
import sys
from datetime import datetime
sys.path.append("T:\\_Physics Team PEICTC\\Benjamin\\GitHub\\PEICTC_QA")
from Helpers.QATrackHelpers import QATrack as qat

###

# Created by Ben Cudmore
# create executable by running the following while in the directory of the .py file
# pyinstaller -F --hiddenimport=pydicom.encoders.gdcm --hiddenimport=pydicom.encoders.pylibjpeg --consol --clean ML11_ML12.py

###


# Any time the field order changes for one of the plans you have to update the field order in the file_indices variable
#   To do this, add a new date key when the change took place in yyyy-mm-dd format, then add ALL linacs.

# To add a new linac (e.g. future TreBeam) to this test list, A new linac key will have to be added.
# search this code for "### Needs to be updated when new linac added ###" to find areas which need to be updated for the addition of a new linac.


### Needs to be updated when new linac added ###
file_indices = {

    '2022-05-04': 
        {
        'TB3426': 
            {
            '6MV 1.3cm' : 6,
            '6MV 1.3cm EDW in': 0,
            '6MV 1.3cm EDW out': 1,
            '6MV FFF 1.3cm': 7,
            '10MV 2.3cm': 14,
            '10MV 2.3cm EDW in': 2,
            '10MV 2.3cm EDW out': 3,
            '10MV FFF 2.3cm': 13, 
            '18MV 2.3cm': 15,
            '18MV 2.3cm EDW in': 4,
            '18MV 2.3cm EDW out': 5,

            '6MV 10cm': 9,
            '6MV FFF 10cm': 8,
            '10MV 10cm': 11,
            '10MV FFF 10cm': 12,
            '18MV 10cm': 10,

            '6MeV 1.3cm': 16,
            '6MeV 2.3cm': 17,
            '9MeV 2.1cm': 18, # measured with MatriXX at 2.3 cm but baseline at 2.1 cm
            '12MeV 2.0cm': 19, # measured with MatriXX at 2.3 cm but baseline at 2.0 cm
            '9MeV 3.3cm': 20,
            '12MeV 5.0cm': 21
            },

        'TB5833': 
            {
            '6MV 1.3cm': 0,
            '6MV 1.3cm EDW in': 2,
            '6MV 1.3cm EDW out': 3,
            '6MV FFF 1.3cm': 1,
            '10MV 2.3cm': 9,
            '10MV 2.3cm EDW in': 4,
            '10MV 2.3cm EDW out': 5,
            '10MV FFF 2.3cm': 8,
            '18MV 2.3cm': 10,
            '18MV 2.3cm EDW in': 6,
            '18MV 2.3cm EDW out': 7,

            '6MV 10cm': 12,
            '6MV FFF 10cm': 11,
            '10MV 10cm': 14,
            '10MV FFF 10cm': 15,
            '18MV 10cm': 13,

            '6MeV 1.3cm': 16,
            '6MeV 2.3cm': 17,
            '9MeV 2.3cm': 18,
            '12MeV 2.3cm': 19,
            '9MeV 3.3cm': 20,
            '16MeV 3.3cm': 21,
            '20MeV 3.3cm': 22,
            '12MeV 5.0cm': 23,
            '16MeV 6.5cm': 24,
            '20MeV 8.5cm': 25
            }
        },

    '2024-09-01': 
        {
        'TB3426': 
            {
            '6MV 1.3cm' : 0,
            '6MV 1.3cm EDW in': 1,
            '6MV 1.3cm EDW out': 2,
            '6MV FFF 1.3cm': 3,
            '10MV 2.3cm': 4,
            '10MV 2.3cm EDW in': 5,
            '10MV 2.3cm EDW out': 6,
            '10MV FFF 2.3cm': 7, 
            '18MV 2.3cm': 8,
            '18MV 2.3cm EDW in': 9,
            '18MV 2.3cm EDW out': 10,

            '6MV 10cm': 11,
            '6MV FFF 10cm': 12,
            '10MV 10cm': 13,
            '10MV FFF 10cm': 14,
            '18MV 10cm': 15,

            '6MeV 1.3cm': 16,
            '6MeV 2.3cm': 17,
            '9MeV 2.1cm': 18, # measured with MatriXX at 2.3 cm but baseline at 2.1 cm
            '12MeV 2.0cm': 19, # measured with MatriXX at 2.3 cm but baseline at 2.0 cm
            '9MeV 3.3cm': 20,
            '12MeV 5.0cm': 21
            },

        'TB5833': 
            {
            '6MV 1.3cm': 0,
            '6MV 1.3cm EDW in': 1,
            '6MV 1.3cm EDW out': 2,
            '6MV FFF 1.3cm': 3,
            '10MV 2.3cm': 4,
            '10MV 2.3cm EDW in': 5,
            '10MV 2.3cm EDW out': 6,
            '10MV FFF 2.3cm': 7,
            '18MV 2.3cm': 8,
            '18MV 2.3cm EDW in': 9,
            '18MV 2.3cm EDW out': 10,

            '6MV 10cm': 11,
            '6MV FFF 10cm': 12,
            '10MV 10cm': 13,
            '10MV FFF 10cm': 14,
            '18MV 10cm': 15,

            '6MeV 1.3cm': 16,
            '6MeV 2.3cm': 17,
            '9MeV 2.3cm': 18,
            '12MeV 2.3cm': 19,
            '9MeV 3.3cm': 20,
            '16MeV 3.3cm': 21,
            '20MeV 3.3cm': 22,
            '12MeV 5.0cm': 23,
            '16MeV 6.5cm': 24,
            '20MeV 8.5cm': 25
        }
    
    }
}

### Needs to be updated when new linac added ###
all_baselines = {
    'TB3426': {
        #   Baseline values for photons correspond to variable 'phAveBaselinesROI' and electrons corresponding to variable 'electronBaselineROI' generated using
        #   'T:\MATLAB\ML12_TB_Baselines.m'. The MATLAB code performs linear interpolation of commissioning data from OmniPro (100 SSD, 20x20 cm^2, 10cm depth) to 
        #   match detector positions in MatriXX. For photons, baselines points are derived for inline and crossline profiles separately then averaged.
        #   Electron baselines are only crossline.

        '6MV 10cm': np.array([
            0.981001,	0.99092925,	0.99785775,	1.003,	1.005,	1.004,	1.00364275,	1.005,	
            1.00452375,	1.0025,	1.001,	1.001,	1.0025,	1.00452375,	1.005,	1.00364275,	
            1.004,	1.005,	1.003,	0.99785775,	0.99092925,	0.981001]),

        '6MV FFF 10cm': np.array([
            0.81200175,	0.839478,	0.8657155,	0.89014375,	0.91366775,	0.93523875,	0.95500075,	
            0.9715005,	0.985405,	0.99385725,	1.0001905,	1.0001905, 0.99385725,	0.985405,	
            0.9715005,	0.95500075,	0.93523875,	0.91366775,	0.89014375,	0.8657155,	0.839478,	
            0.81200175]),

        '10MV 10cm': np.array([
            0.99350025,	1.00030975,	1.00585775,	1.00942875,	1.011,	1.0104045,	1.00914275,	
            1.007,	1.0055,	1.002,	1,	1,	1.002,	1.0055,	1.007, 1.00914275,	1.0104045,	
            1.011,	1.00942875,	1.00585775,	1.00030975,	0.99350025]),

        '10MV FFF 10cm': np.array([
            0.700002,	0.73190725,	0.76507325,	0.79843,	0.83264425,	0.866882,	0.901358,	
            0.934834,	0.96331,	0.98592875,	0.99859525,	0.99859525,	0.98592875,	0.96331,	
            0.934834,	0.901358,	0.866882,	0.83264425,	0.79843,	0.76507325,	0.73190725,	
            0.700002]),

        '18MV 10cm': np.array([
            1.01350025,	1.0185,	1.021,	1.022,	1.0225,	1.02145225,	1.0182855,	1.01149975,	
            1.00557125,	1.0025,	1,	1,	1.0025,	1.00557125,	1.01149975, 1.0182855,	1.02145225,	
            1.0225,	1.022,	1.021,	1.0185,	1.01350025]),

        '6MeV 1.3cm': np.array([
            0.966001,  0.9786195,	0.9862385,	0.9908575,	0.994,	0.997,	0.998,	0.999,	
            0.999,	1,	1,	1,	1,	0.999,	0.999,	0.998,	0.997,	0.994,	0.9908575,
            0.9862385,  0.9786195,	0.966001]),

        '9MeV 2.1cm': np.array([
            1.005001,  1.0126195,	1.013,	1.0121425,	1.01,	1.007,	1.005,	1.003,	
            1.002,	1.001,	1,	1,	1.001,	1.002,	1.003,	1.005,	1.007,	1.01,	1.0121425,	
            1.013,  1.0126195,	1.005001]),
            
        '12MeV 2.0cm': np.array([
            1.011, 1.011,	1.01,	1.0071425,	1.005,	1.003,	1.002,	1.001,	1,	1,	1,	1,
            1,	1,	1.001,	1.002,	1.003,	1.005,	1.0071425,	1.01,	1.011, 1.011])
    },
    'TB5833': {
        # Data found in T:\TrueBeam5833\Commissioning\Beam Scanning\MatriXX Baselines
        # 
        '6MV 10cm': np.array([
            0.981, 0.99062, 
            0.99724, 1.0019, 1.004, 1.004, 1.004, 1.0043, 1.004, 1.0024, 
            1, 1, 1.0024, 1.004, 1.0043, 1.004, 1.004, 1.004, 1.0019, 
            0.99724, 0.99062, 0.981]),

        '6MV FFF 10cm': np.array([
            0.813, 0.84086, 
            0.86695, 0.89157, 0.91543, 0.93629, 0.95614, 0.97267, 0.98591, 
            0.99557, 1, 1, 0.99557, 0.98591, 0.97267, 0.95614, 0.93629, 
            0.91543, 0.89157, 0.86695, 0.84086, 0.813]),

        '10MV 10cm': np.array([
            0.997, 1.0046, 1.0092, 
            1.012, 1.013, 1.012, 1.0103, 1.008, 1.005, 1.0024, 1, 1, 1.0024, 1.005, 
            1.008, 1.0103, 1.012, 1.013, 1.012, 1.0092, 1.0046, 0.997]),

        '10MV FFF 10cm': np.array([
            0.703, 0.73648, 
            0.76895, 0.80229, 0.83591, 0.87038, 0.90457, 0.93633, 0.96486, 0.98671, 
            0.99819, 0.99819, 0.98671, 0.96486, 0.93633, 0.90457, 0.87038, 0.83591, 
            0.80229, 0.76895, 0.73648, 0.703]),

        '18MV 10cm': np.array([
            1.013, 1.0176, 1.0202, 1.022, 
            1.022, 1.0219, 1.0183, 1.011, 1.005, 1.0024, 1.0008, 1.0008, 1.0024, 1.005, 
            1.011, 1.0183, 1.0219, 1.022, 1.022, 1.0202, 1.0176, 1.013]),

        '6MeV 1.3cm': np.array([
            0.97, 0.98124, 0.988, 0.992, 
            0.995, 0.9971, 0.999, 1, 1, 1, 1, 1, 1, 1, 1, 0.999, 0.9971, 0.995, 0.992, 
            0.988, 0.98124, 0.97]),

        '9MeV 2.3cm': np.array([
            1.005, 1.014, 1.015, 1.013, 
            1.011, 1.0089, 1.006, 1.004, 1.002, 1.001, 1, 1, 1.001, 1.002, 1.004, 1.006, 
            1.0089, 1.011, 1.013, 1.015, 1.014, 1.005]),

        '12MeV 2.3cm': np.array([
            1.015, 1.017, 1.015, 1.012, 1.009, 
            1.006, 1.004, 1.002, 1.001, 1, 1, 1, 1, 1.001, 1.002, 1.004, 1.006, 1.009, 
            1.012, 1.015, 1.017, 1.015]),
        '16MeV 3.3cm': np.array([
            1.01, 1.013, 1.011, 1.0081, 1.005, 
            1.0029, 1.001, 1, 1, 1, 1, 1, 1, 1, 1, 1.001, 1.0029, 1.005, 
            1.0081, 1.011, 1.013, 1.01]),
        '20MeV 3.3cm': np.array([
            0.999, 0.999, 0.997, 0.995, 0.993, 
            0.992, 0.992, 0.99333, 0.996, 0.998, 1, 1, 0.998, 0.996, 0.99333, 0.992, 0.992, 0.993, 
            0.995, 0.997, 0.999, 0.999])       
    }   
}


def get_test_positions(directory):
    # Get test positions from first file in directory list
    # If 'Gantry angle' was set for the QA, the lines will be shifted down one. This block is to account for that.
    testPositions = open(directory, 'r').readlines()
    
    if 'Gantry' in testPositions:
        testPositions= testPositions[30].split()
    else:
        testPositions=testPositions[29].split()
    
    testPositions=testPositions[1:33]

    return testPositions

def organize_data(input_folder):         
    files = []
    global acquisition_date
    global file_indices
    
    # file indicies need to be sorted newest to oldest order. This next line ensure that happens regardless of how date keys are added to file_indices
    sorted_file_indices = dict(sorted(file_indices.items(), key=lambda item: datetime.strptime(item[0], '%Y-%m-%d'), reverse = True))

    for dir_path, dir_names, file_names in os.walk(input_folder):
        if len(file_names) <1:
            continue
        # can only process files if the file order at the time of acquisition is known
        file_creation_date = datetime.fromtimestamp(os.path.getctime(os.path.join(dir_path, file_names[0])))
        acquisition_date = qat.format_date(file_creation_date) # for QATrack
        can_process = False

        for field_order_date in sorted_file_indices:
            if file_creation_date > datetime.strptime(field_order_date, '%Y-%m-%d'):
                file_indices = sorted_file_indices[field_order_date]
                can_process = True
                break
                
        if can_process == False:
            print("\nUnsure of field order because data was acquired before {}".format(field_order_date)) ###
            return None, None, None

        for file in file_names:
            if ".opg" in file:
                file_path = os.path.join(dir_path, file)
                files.append(file_path)

    test_positions = get_test_positions(os.path.join(dir_path, file))

    return files, file_indices, test_positions

def get_normalized_profiles(open_file, cGy, testPositions):
    
    matrixx_data = []
    for line in open_file:
        for testPosition in testPositions:
            if testPosition in line and not 'X[cm]' in line:
                matrixx_row = line.split()[1:33] # This gets rid of the test position from ASCII file
                matrixx_data.append(matrixx_row)
                
    # Dose table is normalized using an average of the center values (four ion chambers)
    
    matrixx_data = np.array(matrixx_data, dtype= float)
    matrixx_data = matrixx_data * cGy
    centralDose=(matrixx_data[15, 15] + matrixx_data[15, 16]+matrixx_data[16, 15] + matrixx_data[16,16])/4
    normalized_matrixx_data=matrixx_data / centralDose
    crossline = (normalized_matrixx_data[15, :] + normalized_matrixx_data[16, :]) / 2
    crossline = crossline[5:27]
    inline= np.flip((normalized_matrixx_data[:, 15] + normalized_matrixx_data[:, 16]) / 2)
    inline= inline[5:27]

    return crossline, inline

def get_scaling_factor(open_file):
    for line in open_file:
        if 'Data Factor' in line:
            mGy = float((line.split(":")[-1].strip()))  
            cGy = round(mGy * 100, 1)
            return cGy


input_folder = input("Drag and drop the folder containing the files to be processed (ONE COMPLETE DATASET ONLY).\n").replace("& ", "").strip("'").strip('"')
acquisition_date = ''

files, file_indices, test_positions = organize_data(input_folder)

process = True

if files is None:
    process = False

### Needs to be updated when new linac added ###
# add elif statement for new linac and updated file_indices and all_baselines accordingly

elif '3426' in input_folder:
    machine = 'TrueBeam3426'
    file_indices = file_indices['TB3426']
    baselines = all_baselines['TB3426']

elif '5833' in input_folder:
    machine = 'TrueBeam5833'
    file_indices = file_indices['TB5833']
    baselines = all_baselines['TB5833']

else:
    process = False
    print("This executable is currently only set up to process files from the TrueBeam3426 and TrueBeam5833 folders.")

if process == True:
    print("Processing files.")
    file_data = {}

    for i in range(len(files)):
        file_data[i] = {}

        open_file = open(files[i], 'r').readlines()
        file_data[i]['cGy'] = get_scaling_factor(open_file)
        file_data[i]['crossline'], file_data[i]['inline']  = get_normalized_profiles(open_file, file_data[i]['cGy'], test_positions)


    for acquisition in file_indices:
        if acquisition in baselines.keys():
            i = file_indices[acquisition]
            baseline = baselines[acquisition]
            file_data[i]['crossline constancy'] = float(np.round(np.average((np.abs((file_data[i]['crossline'] - baseline)/baseline)) * 100), 2))
            file_data[i]['inline constancy'] = float(np.round(np.average((np.abs((file_data[i]['inline'] - baseline)/baseline)) * 100), 2))


    all_results = {}

    ### Needs to be updated when new linac added ###
    # Differences between baseline acquisition and available energies constituted IF statements for machines.
    # update accordingly for new linac

    all_results['Mat6Y1'] = file_data[file_indices['6MV 1.3cm EDW in']]['cGy']
    all_results['Mat6Y2'] = file_data[file_indices['6MV 1.3cm EDW out']]['cGy']
    all_results['Mat6Open'] = file_data[file_indices['6MV 1.3cm']]['cGy']
    all_results['Mat6Depth'] = file_data[file_indices['6MV 10cm']]['cGy']
    all_results['BPC_6x_Crossline'] = file_data[file_indices['6MV 10cm']]['crossline constancy']
    all_results['BPC_6x_Inline'] = file_data[file_indices['6MV 10cm']]['inline constancy']

    all_results['Mat6FFFOpen'] = file_data[file_indices['6MV FFF 1.3cm']]['cGy']
    all_results['Mat6FFFDepth'] = file_data[file_indices['6MV FFF 10cm']]['cGy']
    all_results['BPC_6xFFF_Crossline'] = file_data[file_indices['6MV FFF 10cm']]['crossline constancy']
    all_results['BPC_6xFFF_Inline'] = file_data[file_indices['6MV FFF 10cm']]['inline constancy']

    all_results['Mat10Y1'] = file_data[file_indices['10MV 2.3cm EDW in']]['cGy']
    all_results['Mat10Y2'] = file_data[file_indices['10MV 2.3cm EDW out']]['cGy']
    all_results['Mat10Open'] = file_data[file_indices['10MV 2.3cm']]['cGy']
    all_results['Mat10Depth'] = file_data[file_indices['10MV 10cm']]['cGy']
    all_results['BPC_10x_Crossline'] = file_data[file_indices['10MV 10cm']]['crossline constancy']
    all_results['BPC_10x_Inline'] = file_data[file_indices['10MV 10cm']]['inline constancy']

    all_results['Mat10FFFOpen'] = file_data[file_indices['10MV FFF 2.3cm']]['cGy']
    all_results['Mat10FFFDepth'] = file_data[file_indices['10MV FFF 10cm']]['cGy']
    all_results['BPC_10xFFF_Crossline'] = file_data[file_indices['10MV FFF 10cm']]['crossline constancy']
    all_results['BPC_10xFFF_Inline'] = file_data[file_indices['10MV FFF 10cm']]['inline constancy']

    all_results['Mat18Y1'] = file_data[file_indices['18MV 2.3cm EDW in']]['cGy']
    all_results['Mat18Y2'] = file_data[file_indices['18MV 2.3cm EDW out']]['cGy']
    all_results['Mat18Open'] = file_data[file_indices['18MV 2.3cm']]['cGy']
    all_results['Mat18Depth'] = file_data[file_indices['18MV 10cm']]['cGy']
    all_results['BPC_18x_Crossline'] = file_data[file_indices['18MV 10cm']]['crossline constancy']
    all_results['BPC_18x_Inline'] = file_data[file_indices['18MV 10cm']]['inline constancy']

    all_results['Mat6eOpen'] = file_data[file_indices['6MeV 1.3cm']]['cGy']
    all_results['Mat6eDepth'] = file_data[file_indices['6MeV 2.3cm']]['cGy']
    all_results['BPC_6e_Crossline'] = file_data[file_indices['6MeV 1.3cm']]['crossline constancy']
    all_results['BPC_6e_Inline'] = file_data[file_indices['6MeV 1.3cm']]['inline constancy']

    if '3426' in machine:
        all_results['Mat9eOpen'] = file_data[file_indices['9MeV 2.1cm']]['cGy']
        all_results['Mat9eDepth'] = file_data[file_indices['9MeV 3.3cm']]['cGy']
        all_results['BPC_9e_Crossline'] = file_data[file_indices['9MeV 2.1cm']]['crossline constancy']
        all_results['BPC_9e_Inline'] = file_data[file_indices['9MeV 2.1cm']]['inline constancy']

        all_results['Mat12eOpen'] = file_data[file_indices['12MeV 2.0cm']]['cGy']
        all_results['Mat12eDepth'] = file_data[file_indices['12MeV 5.0cm']]['cGy']
        all_results['BPC_12e_Crossline'] = file_data[file_indices['12MeV 2.0cm']]['crossline constancy']
        all_results['BPC_12e_Inline'] = file_data[file_indices['12MeV 2.0cm']]['inline constancy']

    if '5833' in machine:
        all_results['Mat9eOpen'] = file_data[file_indices['9MeV 2.3cm']]['cGy']
        all_results['Mat9eDepth'] = file_data[file_indices['9MeV 3.3cm']]['cGy']
        all_results['BPC_9e_Crossline'] = file_data[file_indices['9MeV 2.3cm']]['crossline constancy']
        all_results['BPC_9e_Inline'] = file_data[file_indices['9MeV 2.3cm']]['inline constancy']

        all_results['Mat12eOpen'] = file_data[file_indices['12MeV 2.3cm']]['cGy']
        all_results['Mat12eDepth'] = file_data[file_indices['12MeV 5.0cm']]['cGy']
        all_results['BPC_12e_Crossline'] = file_data[file_indices['12MeV 2.3cm']]['crossline constancy']
        all_results['BPC_12e_Inline'] = file_data[file_indices['12MeV 2.3cm']]['inline constancy']

        all_results['Mat16eOpen'] = file_data[file_indices['16MeV 3.3cm']]['cGy']
        all_results['Mat16eDepth'] = file_data[file_indices['16MeV 6.5cm']]['cGy']
        all_results['BPC_16e_Crossline'] = file_data[file_indices['16MeV 3.3cm']]['crossline constancy']
        all_results['BPC_16e_Inline'] = file_data[file_indices['16MeV 3.3cm']]['inline constancy']

        all_results['Mat20eOpen'] = file_data[file_indices['20MeV 3.3cm']]['cGy']
        all_results['Mat20eDepth'] = file_data[file_indices['20MeV 8.5cm']]['cGy']
        all_results['BPC_20e_Crossline'] = file_data[file_indices['20MeV 3.3cm']]['crossline constancy']
        all_results['BPC_20e_Inline'] = file_data[file_indices['20MeV 3.3cm']]['inline constancy']

    qat.log_into_QATrack()
    utc_url, macros = qat.get_unit_test_collection(machine, "CAX PDD Reproducibility and Beam Profile Constancy")
    tests = qat.format_results(macros, all_results)
    qat.post_results(utc_url, tests, acquisition_date)
        