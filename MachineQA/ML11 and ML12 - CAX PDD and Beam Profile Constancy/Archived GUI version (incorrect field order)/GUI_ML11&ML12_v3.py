# This code generates an GUI that can process ML11 and ML12 data for either the iX, TrueBeam3426, or TrueBeam5833.
# If the order of the fields change in the test patient they need to be updated in this code. 
# Each linac required a different number of .opg files and performs different calculations
# As such, code varies where required

# ML11 baseliness are generated in MatLab code. More information is provided at the corresponding sections of code in this file.

# Create updated executable (.exe) using pyinstaller

# Image paths will need to be updated and remain unchanged when .exe is created

# For QATrack log in window, need error messages to disappear after button is re pressed. Also, more informative error codes throughout the application.

# All button definitions are defined before the app is built.
from ctypes import resize
from tkinter import *
import tkinter as tk
from tkinter import filedialog
from tkinter import ttk
from turtle import left


import webbrowser
import requests
import numpy as np
import os as os
import time as time
import hashlib
from PIL import ImageTk, Image

all_baselines = {
    "iX": {
        # Baseline data for each beam energy at a particular depth were extracted 
        # from BeamData.mat (MatLab file) BeamData.Ph.Prof.Z100.A200.F100 
        # and EclipseCalcData.mat EclipseCalcData.El.Prof.(['Z', depth]).A200.F100
        # corresponding to the MatriXX test points. Values were /100 in the Matlab code (MatriXXMonthly.mat)
        "6MV, 10cm Depth": np.array([
            0.9830025, 0.994, 1, 1.005, 1.007, 1.0055225, 1.005, 1.007, 
            1.005, 1.003, 1, 1, 1.003, 1.005, 1.007, 1.005, 1.006, 1.0066175, 
            1.005, 1, 0.994, 0.9830025]),

        "18MV, 10cm Depth": np.array([
            1.01, 1.015, 1.018, 1.019, 1.0206175, 1.021, 1.018, 1.011, 
            1.006, 1.004, 1.002, 1.002, 1.004, 1.006, 1.011, 1.018, 1.021, 
            1.020745, 1.019, 1.018, 1.015, 1.01]),

        "6MeV, 1.45cm Depth": np.array([
            1.004845333, 1.00605884, 1.00514448, 1.004673479, 1.003584476, 
            1.002588009, 1.001942064, 1.001019051, 1.000360154, 0.999876131, 
            0.999938979, 0.999981134, 0.999878251, 1.000269156, 1.000929458, 
            1.001829256, 1.002538181, 1.003563625, 1.004706117, 1.005195994, 
            1.006297155, 1.005509438]),

        "9MeV, 2.4cm Depth": np.array([
            0.995555943932944, 1.00114875868632, 1.00232782876615, 1.00235221732701, 
            1.001920386, 1.001320068, 1.001407754, 1.000940856, 1.000517494, 1.000123018, 
            1.000002525, 1.000017664, 1.000152946, 1.000579844, 1.000989925, 1.001447442, 
            1.001161932, 1.001665088, 1.002008553, 1.001832231, 1.000207453, 0.993821187]),

        "12MeV, 2.3cm Depth": np.array([
            0.99882059105255, 1.00008481737684, 1.00052034800102, 1.0003506079456, 
            1.00033033435427, 1.0003381666586, 1.00044464258232, 1.00025992277262, 
            1.0002891907277, 1.00012984433311, 0.999997736364859, 1.00000118397688, 
            1.00013525062166, 1.00026318811267, 1.00027745970346, 1.00046532459484, 
            1.00025683872033, 1.00023749476644, 1.00023175208607,1.00032930903432, 
            0.999722869224345, 0.997902785393864]),

        "16MeV, 3.3cm Depth": np.array([
            1.005518287, 1.005366875, 1.004056844, 1.003271331, 1.002763133, 1.001953554, 
            1.001313473, 1.000435732, 1.00021134, 1.000019143, 0.999996529, 1.000000618,
            1.000005999, 1.000250075, 1.000497578, 1.001402453, 1.001992235, 1.002836075, 
            1.003295143, 1.004075517, 1.005292331, 1.005040491]),

        "20MeV, 2.2cm Depth": np.array([
            0.998086004752233,	0.997172806023987,	0.996196021020505,	0.996163881036106,	
            0.997171893251318,	0.998129081404947,	0.99851406710305,	0.999067619780219,	
            0.999610437945485,	0.999902444545391,	0.9999923218453,	0.9999923218453,	
            0.999902444545391,	0.999610437945486,	0.999067619780219,	0.998514067103051,
            0.998129081404948,	0.997171893251318,	0.996163881036106,	0.996196021020505,	
            0.997172806023987,	0.998086004752233])
        },
    "TB3426": {
        #   Baseline values for photons correspond to variable 'phAveBaselinesROI' and electrons corresponding to variable 'electronBaselineROI' generated using
        #   'T:\MATLAB\ML12_TB_Baselines.m'. The MATLAB code performs linear interpolation of commissioning data from OmniPro (100 SSD, 20x20 cm^2, 10cm depth) to 
        #   match detector positions in MatriXX. For photons, baselines points are derived for inline and crossline profiles separately then averaged.
        #   Electron baselines are only crossline.

        "6MV, 10cm Depth": np.array([
            0.981001,	0.99092925,	0.99785775,	1.003,	1.005,	1.004,	1.00364275,	1.005,	
            1.00452375,	1.0025,	1.001,	1.001,	1.0025,	1.00452375,	1.005,	1.00364275,	
            1.004,	1.005,	1.003,	0.99785775,	0.99092925,	0.981001]),

        "6MV FFF, 10cm Depth": np.array([
            0.81200175,	0.839478,	0.8657155,	0.89014375,	0.91366775,	0.93523875,	0.95500075,	
            0.9715005,	0.985405,	0.99385725,	1.0001905,	1.0001905, 0.99385725,	0.985405,	
            0.9715005,	0.95500075,	0.93523875,	0.91366775,	0.89014375,	0.8657155,	0.839478,	
            0.81200175]),

        "10MV, 10cm Depth": np.array([
            0.99350025,	1.00030975,	1.00585775,	1.00942875,	1.011,	1.0104045,	1.00914275,	
            1.007,	1.0055,	1.002,	1,	1,	1.002,	1.0055,	1.007, 1.00914275,	1.0104045,	
            1.011,	1.00942875,	1.00585775,	1.00030975,	0.99350025]),

        "10MV FFF, 10cm Depth": np.array([
            0.700002,	0.73190725,	0.76507325,	0.79843,	0.83264425,	0.866882,	0.901358,	
            0.934834,	0.96331,	0.98592875,	0.99859525,	0.99859525,	0.98592875,	0.96331,	
            0.934834,	0.901358,	0.866882,	0.83264425,	0.79843,	0.76507325,	0.73190725,	
            0.700002]),

        "18MV, 10cm Depth": np.array([
            1.01350025,	1.0185,	1.021,	1.022,	1.0225,	1.02145225,	1.0182855,	1.01149975,	
            1.00557125,	1.0025,	1,	1,	1.0025,	1.00557125,	1.01149975, 1.0182855,	1.02145225,	
            1.0225,	1.022,	1.021,	1.0185,	1.01350025]),

        "6MeV, 1.3cm Depth": np.array([
            0.966001,  0.9786195,	0.9862385,	0.9908575,	0.994,	0.997,	0.998,	0.999,	
            0.999,	1,	1,	1,	1,	0.999,	0.999,	0.998,	0.997,	0.994,	0.9908575,
            0.9862385,  0.9786195,	0.966001]),

        "9MeV, 2.1cm Depth": np.array([
            1.005001,  1.0126195,	1.013,	1.0121425,	1.01,	1.007,	1.005,	1.003,	
            1.002,	1.001,	1,	1,	1.001,	1.002,	1.003,	1.005,	1.007,	1.01,	1.0121425,	
            1.013,  1.0126195,	1.005001]),
            
        "12MeV, 2.0cm Depth": np.array([
            1.011, 1.011,	1.01,	1.0071425,	1.005,	1.003,	1.002,	1.001,	1,	1,	1,	1,
            1,	1,	1.001,	1.002,	1.003,	1.005,	1.0071425,	1.01,	1.011, 1.011])
    },
    "TB5833": {
        # Data found in T:\TrueBeam5833\Commissioning\Beam Scanning\MatriXX Baselines
        # 
        "6MV, 10cm Depth": np.array([
            0.981, 0.99062, 
            0.99724, 1.0019, 1.004, 1.004, 1.004, 1.0043, 1.004, 1.0024, 
            1, 1, 1.0024, 1.004, 1.0043, 1.004, 1.004, 1.004, 1.0019, 
            0.99724, 0.99062, 0.981]),

        "6MV FFF, 10cm Depth": np.array([
            0.813, 0.84086, 
            0.86695, 0.89157, 0.91543, 0.93629, 0.95614, 0.97267, 0.98591, 
            0.99557, 1, 1, 0.99557, 0.98591, 0.97267, 0.95614, 0.93629, 
            0.91543, 0.89157, 0.86695, 0.84086, 0.813]),

        "10MV, 10cm Depth": np.array([
            0.997, 1.0046, 1.0092, 
            1.012, 1.013, 1.012, 1.0103, 1.008, 1.005, 1.0024, 1, 1, 1.0024, 1.005, 
            1.008, 1.0103, 1.012, 1.013, 1.012, 1.0092, 1.0046, 0.997]),

        "10MV FFF, 10cm Depth": np.array([
            0.703, 0.73648, 
            0.76895, 0.80229, 0.83591, 0.87038, 0.90457, 0.93633, 0.96486, 0.98671, 
            0.99819, 0.99819, 0.98671, 0.96486, 0.93633, 0.90457, 0.87038, 0.83591, 
            0.80229, 0.76895, 0.73648, 0.703]),

        "18MV, 10cm Depth": np.array([
            1.013, 1.0176, 1.0202, 1.022, 
            1.022, 1.0219, 1.0183, 1.011, 1.005, 1.0024, 1.0008, 1.0008, 1.0024, 1.005, 
            1.011, 1.0183, 1.0219, 1.022, 1.022, 1.0202, 1.0176, 1.013]),

        "6MeV, 1.3cm Depth": np.array([
            0.97, 0.98124, 0.988, 0.992, 
            0.995, 0.9971, 0.999, 1, 1, 1, 1, 1, 1, 1, 1, 0.999, 0.9971, 0.995, 0.992, 
            0.988, 0.98124, 0.97]),

        "9MeV, 2.3cm Depth": np.array([
            1.005, 1.014, 1.015, 1.013, 
            1.011, 1.0089, 1.006, 1.004, 1.002, 1.001, 1, 1, 1.001, 1.002, 1.004, 1.006, 
            1.0089, 1.011, 1.013, 1.015, 1.014, 1.005]),

        "12MeV, 2.3cm Depth": np.array([
            1.015, 1.017, 1.015, 1.012, 1.009, 
            1.006, 1.004, 1.002, 1.001, 1, 1, 1, 1, 1.001, 1.002, 1.004, 1.006, 1.009, 
            1.012, 1.015, 1.017, 1.015]),
        "16MeV, 3.3cm Depth": np.array([
            1.01, 1.013, 1.011, 1.0081, 1.005, 
            1.0029, 1.001, 1, 1, 1, 1, 1, 1, 1, 1, 1.001, 1.0029, 1.005, 
            1.0081, 1.011, 1.013, 1.01]),
        "20MeV, 3.3cm Depth": np.array([
            0.999, 0.999, 0.997, 0.995, 0.993, 
            0.992, 0.992, 0.99333, 0.996, 0.998, 1, 1, 0.998, 0.996, 0.99333, 0.992, 0.992, 0.993, 
            0.995, 0.997, 0.999, 0.999])       
    }   
}

ML12_file_indices = {
    "iX": {
        "6MV, 10cm Depth": 3,
        "18MV, 10cm Depth": 4,
        "6MeV, 1.45cm Depth": 8,
        "9MeV, 2.4cm Depth": 10,
        "12MeV, 2.3cm Depth": 11,
        "16MeV, 3.3cm Depth": 14,
        "20MeV, 2.2cm Depth": 12
        },
    "TB3426": {
        "6MV, 10cm Depth": 9,
        "6MV FFF, 10cm Depth": 8,
        "10MV, 10cm Depth": 11,
        "10MV FFF, 10cm Depth": 12,
        "18MV, 10cm Depth": 10,
        "6MeV, 1.3cm Depth": 16,
        "9MeV, 2.1cm Depth": 18,
        "12MeV, 2.0cm Depth": 19
        },
    "TB5833": {
        "6MV, 10cm Depth": 12,
        "6MV FFF, 10cm Depth": 11,
        "10MV, 10cm Depth": 14,
        "10MV FFF, 10cm Depth": 15,
        "18MV, 10cm Depth": 13,
        "6MeV, 1.3cm Depth": 16,
        "9MeV, 2.3cm Depth": 18,
        "12MeV, 2.3cm Depth": 19,
        "16MeV, 3.3cm Depth": 21,
        "20MeV, 3.3cm Depth": 22
        }
    }

ML11_file_indices = {
        "iX": {
            "Nominator": [3, 4, 9, 13, 15, 16, 17],
            "Denominator": [2, 5, 8, 10, 11, 14, 12],
            "EDW": {
                "Nominator1": [0, 6],
                "Nominator2": [1, 7],
                "Denominator2": [2, 5]
            }
        },
        "TB3426": {
            "Nominator": [9, 8, 11, 12, 10, 17, 20, 21],
            "Denominator": [6, 7, 14, 13, 15, 16, 18, 19],
            "EDW": {
                "Nominator1": [0, 2, 4],
                "Nominator2": [1, 3, 5],
                "Denominator2": [6, 14, 15]
            }
        },
        "TB5833": {
            "Nominator": [12, 11, 14, 15, 13, 17, 20, 23, 24, 25],
            "Denominator": [0, 1, 9, 8, 10, 16, 18, 19, 21, 22],
            "EDW": {
                "Nominator1": [2, 4, 6],
                "Nominator2": [3, 5, 7],
                "Denominator2": [1, 9, 10]
            }
        }
    }

def get_baseline(baselines, file_indices, i):
    try:
        return get_value(baselines, get_key(file_indices, i))
    except Exception as e:
        print(e)
        return False

def get_key(dictionary, value):
    try:
        for key, val in dictionary.items():
            if val == value:
                return key
        return None
    except:
        return False

def get_value(dictionary, value):
    try:
        for key, val in dictionary.items():
            if key == value:
                return val
        return None
    except:
        return False

def get_normalized_profiles(openFile, testPositions, i):
    doseTable = []
    for line in openFile:
        for testPosition in testPositions:
            if testPosition in line and not 'X[cm]' in line:
                rowOfData=line.split()
                rowOfData=rowOfData[1:33]  # This gets rid of the test position from ASCII file
                rowOfData=[float(num) for num in rowOfData]
                doseTable.append(rowOfData)
    # Dose table is normalized using an average of the center values (four ion chambers)
    
    doseTable= np.array(doseTable,dtype=int)
    doseTable=doseTable*cGy[i]
    centralDose=(doseTable[15,15]+doseTable[15,16]+doseTable[16,15]+doseTable[16,16])/4
    normalizedDoseTable=doseTable/centralDose
    crossline=(normalizedDoseTable[15,:]+normalizedDoseTable[16,:])/2
    crossline=crossline[5:27]
    inline=np.flip((normalizedDoseTable[:,15]+normalizedDoseTable[:,16])/2)
    inline=inline[5:27]

    return crossline, inline

def clear_tables(tbl_files, tbl_results):
    rows = len(tbl_files.get_children())
    
    for i in range(rows):
        tbl_files.set([i],3,"")
        tbl_files.set([i],4,"")
    rows = len(tbl_results.get_children())
    for i in range(4):
        for j in range(rows):
            tbl_results.set([j],[i+1],"")
    
def show_tables():
    lbl_data.pack(anchor=N)
    pageBreak.pack(side='top', fill='x',padx=20,pady=(5,10))

    btn_import.pack(anchor=N)

    frm_files.pack(anchor=N,pady=10,padx=10,)
    tbl_files.pack(fill=BOTH,expand=1, anchor=N)

    btn_Calculate.pack(anchor=N)
    btn_Calculate['state']=DISABLED

    frm_results.pack(anchor=N,pady=10,padx=10)
    tbl_results.pack(fill=BOTH, expand=1, anchor=N)

    btn_sendToQATrack.pack(anchor=N,pady=(0,10))

    btn_sendToQATrack['state'] = DISABLED

def clickLinac(): # 

    btn_r1iX['state']=DISABLED
    btn_r2TB3426['state']=DISABLED
    btn_r3TB5833['state']=DISABLED

    global linacChoice
    global linac_name
    global num_files
    global tbl_files
    global tbl_results
    global frm_files
    global frm_results
    global lbl_data
    global btn_import
    global baselines
    global file_indices
    global energy_constancy

    linacChoice = linac.get()

    if linacChoice == 1: # Set up GUI for iX file import and calculations

        linac_name = "iX"
        num_files = "18"
        tbl_files = tbl_iXFiles
        tbl_results = tbl_iXResults
        frm_files = frm_iXFiles
        frm_results = frm_iXResults
        lbl_data = lbl_iXData
        btn_import = btn_iXImport
        baselines = all_baselines["iX"]
        file_indices = ML12_file_indices["iX"]
        energy_constancy = ML11_file_indices["iX"]

    elif linacChoice == 2:  # Set up GUI for TB3426 file import and calculations
        linac_name = "TB 3426"
        num_files = "22"
        tbl_files = tbl_TB3426_files
        tbl_results = tbl_TB3426_results
        frm_files = frm_TB3426_files
        frm_results = frm_TB3426_results
        lbl_data = lbl_TB3426_data
        btn_import = btn_TB3426_import
        baselines = all_baselines["TB3426"]
        file_indices = ML12_file_indices["TB3426"]
        energy_constancy = ML11_file_indices["TB3426"]
    
    elif linacChoice == 3:  # Set up GUI for TB5833 file import and calculations
        linac_name = "TB 5833"
        num_files = "26"
        tbl_files = tbl_TB5833_files
        tbl_results = tbl_TB5833_results
        frm_files = frm_TB5833_files
        frm_results = frm_TB5833_results
        lbl_data = lbl_TB5833_data
        btn_import = btn_TB5833_import
        baselines = all_baselines["TB5833"]
        file_indices = ML12_file_indices["TB5833"]
        energy_constancy = ML11_file_indices["TB5833"]

    show_tables()
     
def clickReset(): # Returns GUI to initial state
    
    linacChoice = linac.get()

    if linacChoice == 0:
        None

    else:
        lbl_data.pack_forget()
        btn_import.pack_forget()
        frm_files.pack_forget()
        tbl_files.pack_forget()
        frm_results.pack_forget()
        tbl_results.pack_forget()
        btn_Calculate.pack_forget() 
        btn_sendToQATrack.pack_forget()
        pageBreak.pack_forget()
        lbl_QADate.place_forget()

        btn_r1iX['state']=NORMAL
        btn_r2TB3426['state']=NORMAL
        btn_r3TB5833['state']=NORMAL

        clear_tables(tbl_files, tbl_results)
        linac.set(0)        

def clickSelectFiles(): # Ensure the correct number of files are chosen for the selected linac and displays relevant information in table
    global files
    global directory
    global fileName
    global cGy
    cGy=[]
    global QADate
    global lbl_QADate
    QADate=[]

    lbl_QADate.place_forget()
    clear_tables(tbl_files, tbl_results)
       
    files= filedialog.askopenfiles(initialdir="T:\\QA\Data\\Monthly CAX PDD and BPC\\" + linac_name, title="Select Files,",filetypes=[("opg files","*.opg")])
    
    if files == '':
        None
    
    elif len(files) !=int(num_files):  
        top=Toplevel(root)
        top.geometry("250x75")
        top.title("Error")
        top.configure(width=700,background=BG_top)
        top.iconphoto(False, icon_image)
        Label(top, text="Wrong number of files selected. \n Please select " + num_files + " files.",font=('Aerial 11'),pady=20,background=BG_top).pack(anchor=CENTER)
    else:
        directory=[]
        fileName=[]
        cGy=[]

        for file in files:
            directory.append(file.name)
            fileName.append(file.name.split('/')[-1].strip())
            
        for file in directory: 
            openFile = open(file, 'r').readlines()
            for line in openFile:
               if 'Data Factor' in line:
                    dosemGy = float((line.split(":")[-1].strip()))  
                    dosecGy=dosemGy*100
                    cGy.append(dosecGy)
            
        cGy=np.round(np.array(cGy,dtype=float),1)
            
        # Labels date for selected data in App
        lbl_QADate = Label(text="QA Date: " + str((time.strftime('%Y-%b-%d', time.localtime(os.path.getctime(os.path.dirname(directory[0])))))),font=("Cambria 11"), highlightthickness=1,highlightbackground=HLBG_QADate,bg=BG_frm)
        lbl_QADate.place(x=505,y=130,width=175)

        for i in range(int(num_files)): # Inserts file names and data factors into table
            tbl_files.set([i],3,fileName[i])
            tbl_files.set([i],4,cGy[i])

        btn_Calculate['state']=NORMAL

        for line in openFile:   # Checks to see if MatriXX Calibration File was used (The calibration is requiered for calculations)
            if 'Rel. Dose' in line:
                top=Toplevel(root)
                top.title("Potential Error")
                top.configure(width=700,background=BG_top)
                top.iconphoto(False, icon_image)
                Label(top, text="Warning",font=('Aerial 14'),fg=error_message,pady=2,bg=BG_top).pack(anchor=CENTER)
                Label(top,text="It appears a MatriXX calibration file was not used during data acquisition.\nThe resulting calculations are likely to be invalid.\nCheck the user parameters in OmniPro to ensure a MatriXX calibration file was used.",font=('Aerial 11'),anchor=N,pady=5,padx=10,bg=BG_top).pack(anchor=CENTER)
            else:
                None

        if time.strftime('%Y-%m-%d', time.localtime(os.path.getctime(os.path.dirname(directory[0])))) < "2022-05-04" and linac_name == "TB3426":
            lbl_QADate = Label(text="QA Date: " + str((time.strftime('%Y-%b-%d', time.localtime(os.path.getctime(os.path.dirname(directory[0])))))),font=("Cambria 11"), fg='#FF2222', highlightthickness=1,highlightbackground=HLBG_QADate,bg=BG_frm)
            lbl_QADate.place(x=505,y=130,width=175)
            top=Toplevel(root)
            top.title("Warning")
            top.configure(width=700,background=BG_top)
            top.iconphoto(False, icon_image)
            Label(top, text="Due to a change in field delivery order, TrueBeam3426 data acquired \nbefore 2022-May-04 must be processed with Version 1 of this application (v1).", padx=20,pady=5, font=fontDateWarning, bg=BG_main).pack()

    
        for line in openFile:   # Checks to see if MatriXX Calibration File was used (The calibration is requiered for calculations)
            if 'Rel. Dose' in line:
                top=Toplevel(root)
                top.title("Potential Error")
                top.configure(width=700,background=BG_top)
                top.iconphoto(False, icon_image)
                Label(top, text="Warning",font=('Aerial 14'),fg=error_message,pady=2,bg=BG_top).pack(anchor=CENTER)
                Label(top,text="It appears a MatriXX calibration file was not used during data acquisition.\nThe resulting calculations are likely to be invalid.\nCheck the user parameters in OmniPro to ensure a MatriXX calibration file was used.",font=('Aerial 11'),anchor=N,pady=5,padx=10,bg=BG_top).pack(anchor=CENTER)
            else:
                None 

def get_test_positions(directory):
    # Get test positions from first file in directory list
    # If Gantry angle was set for the QA, the lines will be shifted down one. This block is to account for that.
    testPositions = open(directory[0], 'r').readlines()
    if 'Gantry' in testPositions:
        testPositions= testPositions[30].split()
        testPositions=testPositions[1:33]
    else:
        testPositions=testPositions[29].split()
        testPositions=testPositions[1:33]

    return testPositions

def clickCalculate():
    global table
    global file_indices
    global baselines
    global energy_constancy

    table=[]
    global crosslineList
    crosslineList = []
    global inlineList
    inlineList = []
    testPositions =[]
    doseTable=[]
    crossline = []
    inline = []
    energyCheck = []
    EDW = []
    btn_sendToQATrack['state']=NORMAL

    test_positions = get_test_positions(directory)      

        # Files from file index are opened one at a time to get their dose table 

    for i in file_indices.values():
        openFile = open(directory[i], 'r').readlines()
        doseTable=[]
        crossline, inline = get_normalized_profiles(openFile, test_positions, i)

        baseline = get_baseline(baselines, file_indices, i)
        if isinstance(baseline, np.ndarray):
            constancyCrossLine=float(np.round(np.average((np.abs((crossline - baseline)/baseline))*100),2))
            crosslineList.append(constancyCrossLine)
            constancyInLine=float(np.round(np.average((np.abs((inline - baseline)/baseline))*100),2))
            inlineList.append(constancyInLine)
        else:
            print("The variable 'baseline' is of type " + str(type(baseline))) + (". No results were generated.")
            break

    rows = len(energy_constancy['Nominator'])
    for i in range(rows):
        energyCheck.append(np.round(cGy[energy_constancy['Nominator'][i]]/cGy[energy_constancy['Denominator'][i]],4))

    table=np.reshape(np.hstack(np.array((crosslineList,inlineList,energyCheck))),[3,rows])

    for i in range(len(energy_constancy['EDW']['Nominator1'])):
        EDW = (np.round((cGy[energy_constancy['EDW']['Nominator1']] + cGy[energy_constancy['EDW']['Nominator2']])/2/cGy[energy_constancy['EDW']['Denominator2']],4))
    
    
    #Fill result table
    if linacChoice ==1:
        for i in range(3):
            for j in range(rows):
                tbl_iXResults.set([j],[i+1],table[i][j])

            tbl_iXResults.set(0,4,EDW[0])
            tbl_iXResults.set(1,4,EDW[1])
    
    if linacChoice == 2:
        for i in range(3):
            for j in range(rows):
                tbl_TB3426_results.set([j],[i+1],table[i][j])

            tbl_TB3426_results.set(0,4,EDW[0])
            tbl_TB3426_results.set(2,4,EDW[1])
            tbl_TB3426_results.set(4,4,EDW[2])
    
    if linacChoice == 3:
        for i in range(3):
            for j in range(rows):
                tbl_TB5833_results.set([j],[i+1],table[i][j])

            tbl_TB5833_results.set(0,4,EDW[0])
            tbl_TB5833_results.set(2,4,EDW[1])
            tbl_TB5833_results.set(4,4,EDW[2])

def clickSubmit(): #Generates login window
    global top
    global ent_username
    global ent_password
    top=Toplevel(root)
    top.configure(width=700,background=BG_top)
    top.iconphoto(False, icon_image)
    top.title('Log in to QA Track')
    top.resizable(0, 0)
    top.grab_set()
    frm_description = Frame(top, bg=BG_top)
    frm_description.grid(column=0,row=0)

    frm_login = Frame(top, bg=BG_top)
    frm_login.columnconfigure(0, weight=3)
    frm_login.columnconfigure(1, weight=1)
    frm_login.grid(column=0,row=1)

    # username
    lbl_username = ttk.Label(frm_login, text="Username:",background=BG_top)
    lbl_username.grid(column=0, row=0, sticky=W, padx=5, pady=5)
    ent_username = ttk.Entry(frm_login)
    ent_username.grid(column=1, row=0, sticky=E, padx=5, pady=5)

    # password
    lbl_password = ttk.Label(frm_login, text="Password:",background=BG_top)
    lbl_password.grid(column=0, row=1, sticky=W, padx=5, pady=5)
    ent_password = ttk.Entry(frm_login,  show="*")
    ent_password.grid(column=1, row=1, sticky=E, padx=5, pady=5)

    # login button
    global btn_login
    btn_login = Button(frm_login, text="Submit Results", command=clickQATrack,bg=BG_btn,pady=1)
    btn_login.grid(column=1, row=3, sticky=E, padx=15, pady=10,ipadx=10)

    #Displaied Description
    lbl_description = ttk.Label(frm_description,background=BG_top, text=\
    '1.  Enter your QATrack login credentials and click "Submit Results".\n2.  An in progress test list will be generated in a new window of QATrack.\n3.  Review the in progress test list and enter a "Work completed" date.\n4.  Submit QA results in QATrack.')
    lbl_description.grid(row=4, sticky=E, padx=10, pady=10,columnspan=4)

def clickQATrack():
    loginError=Label(top,text="Trouble connecting. Please check your username and password and try again.", fg=error_message,bg=BG_top)
    password=ent_password.get()
    username=ent_username.get()

    root = "http://qatrack/api"
    token_url = root + "/get-token/"
    resp = requests.post(token_url, {'username': username, 'password': password})
    
    if resp.status_code == requests.codes.BAD:
        loginError.grid_forget()
        loginError.grid(row=5)
    else:
        loginError.grid_forget()
        token = resp.json()['token']
        headers = {"Authorization": "Token %s" % token}     # the request headers must include the API token

        if linacChoice ==1 and resp.status_code != requests.codes.BAD:
            resp = requests.get(root + '/qa/unittestcollections/?unit__name__icontains=Clinac iX&test_list__name__icontains=Relative Dosimetry', headers=headers)
            utc_url = resp.json()['results'][0]['url']

            # prepare the data to submit to the API.
            data = {
                'unit_test_collection': utc_url,

                'in_progress': True,  # optional, default is False
                'include_for_scheduling': True,
                'work_started': time.strftime('%Y-%m-%d %H:%M', time.localtime(os.path.getctime(os.path.dirname(directory[0])))),
                'work_completed': time.strftime('%Y-%m-%d %H:%M', time.localtime(os.path.getctime(os.path.dirname(directory[0])))),
                'user_key': hashlib.md5(open(directory[0], "rb").read()).hexdigest(),  # NOT PREVENTING DUPLICATE RESULTS
                    "tests": {

                        "Mat6Y1": {'value': cGy[1]},
                        "Mat6Y2": {'value': cGy[1]},
                        "Mat6Open": {'value': cGy[2]},
                        "Mat6Depth": {'value': cGy[3]},
                        "Mat18Depth": {'value': cGy[4]},
                        "Mat18Open": {'value': cGy[5]},
                        "Mat18Y1": {'value': cGy[6]},
                        "Mat18Y2": {'value': cGy[7]},

                        "Mat6eOpen": {'value': cGy[8]},
                        "Mat6eDepth": {'value': cGy[9]},
                        "Mat9eOpen": {'value': cGy[10]},
                        "Mat12eOpen": {'value': cGy[11]},
                        "Mat20eOpen": {'value': cGy[12]},
                        "Mat9eDepth": {'value': cGy[13]},
                        "Mat16eOpen": {'value': cGy[14]},
                        "Mat12eDepth": {'value': cGy[15]},
                        "Mat16eDepth": {'value': cGy[16]},
                        "Mat20eDepth": {'value': cGy[17]},

                        "BPC_6x_Crossline": {'value': crosslineList[0]},
                        "BPC_18x_Crossline": {'value': crosslineList[1]},
                        "BPC_6e_Crossline": {'value': crosslineList[2]},
                        "BPC_9e_Crossline": {'value': crosslineList[3]},
                        "BPC_12e_Crossline": {'value': crosslineList[4]},
                        "BPC_16e_Crossline": {'value': crosslineList[5]},
                        "BPC_20e_Crossline": {'value': crosslineList[6]},

                        "BPC_6x_Inline": {'value': inlineList[0]},
                        "BPC_18x_Inline": {'value': inlineList[1]},
                        "BPC_6e_Inline": {'value': inlineList[2]},
                        "BPC_9e_Inline": {'value': inlineList[3]},
                        "BPC_12e_Inline": {'value': inlineList[4]},
                        "BPC_16e_Inline": {'value': inlineList[5]},
                        "BPC_20e_Inline": {'value': inlineList[6]}
                        }
                    }

        elif linacChoice ==2 and resp.status_code != requests.codes.BAD:
            resp = requests.get(root + '/qa/unittestcollections/?unit__name__icontains=3426&test_list__name__icontains=CAX PDD Reproducibility and Beam Profile Constancy TrueBeam', headers=headers)
            utc_url = resp.json()['results'][0]['url']

            # prepare the data to submit to the API.
            data = {
                'unit_test_collection': utc_url,

                'in_progress': True,  # optional, default is False
                'include_for_scheduling': True,
                'work_started': time.strftime('%Y-%m-%d %H:%M', time.localtime(os.path.getctime(os.path.dirname(directory[0])))),
                'work_completed': time.strftime('%Y-%m-%d %H:%M', time.localtime(os.path.getctime(os.path.dirname(directory[0])))),
                'user_key': hashlib.md5(open(directory[0], "rb").read()).hexdigest(),  # NOT PREVENTING DUPLICATE RESULTS
                    "tests": {

                        "Mat6Y1": {'value': cGy[0]},
                        "Mat6Y2": {'value': cGy[1]},
                        "Mat10Y1": {'value': cGy[2]},
                        "Mat10Y2": {'value': cGy[3]},
                        "Mat18Y1": {'value': cGy[4]},
                        "Mat18Y2": {'value': cGy[5]},
                        "Mat6Open": {'value': cGy[6]},
                        "Mat6FFFOpen": {'value': cGy[7]},
                        "Mat6FFFDepth": {'value': cGy[8]},
                        "Mat6Depth": {'value': cGy[9]},
                        "Mat18Depth": {'value': cGy[10]},
                        "Mat10Depth": {'value': cGy[11]},
                        "Mat10FFFDepth": {'value': cGy[12]},
                        "Mat10FFFOpen": {'value': cGy[13]},
                        "Mat10Open": {'value': cGy[14]},
                        "Mat18Open": {'value': cGy[15]},

                        "Mat6eOpen": {'value': cGy[16]},
                        "Mat6eDepth": {'value': cGy[17]},
                        "Mat9eOpen": {'value': cGy[18]},
                        "Mat12eOpen": {'value': cGy[19]},
                        "Mat9eDepth": {'value': cGy[20]},
                        "Mat12eDepth": {'value': cGy[21]},

                        "BPC_6x_Crossline": {'value': crosslineList[0]},
                        "BPC_6xFFF_Crossline": {'value': crosslineList[1]},
                        "BPC_10x_Crossline": {'value': crosslineList[2]},
                        "BPC_10xFFF_Crossline": {'value': crosslineList[3]},
                        "BPC_18x_Crossline": {'value': crosslineList[4]},
                        "BPC_6e_Crossline": {'value': crosslineList[5]},
                        "BPC_9e_Crossline": {'value': crosslineList[6]},
                        "BPC_12e_Crossline": {'value': crosslineList[7]},

                        "BPC_6x_Inline": {'value': inlineList[0]},
                        "BPC_6xFFF_Inline": {'value': inlineList[1]},
                        "BPC_10x_Inline": {'value': inlineList[2]},
                        "BPC_10xFFF_Inline": {'value': inlineList[3]},
                        "BPC_18x_Inline": {'value': inlineList[4]},
                        "BPC_6e_Inline": {'value': inlineList[5]},
                        "BPC_9e_Inline": {'value': inlineList[6]},
                        "BPC_12e_Inline": {'value': inlineList[7]}
                    }
                }
            
        elif linacChoice == 3:
            resp = requests.get(root + '/qa/unittestcollections/?unit__name__icontains=5833&test_list__name__icontains=CAX PDD Reproducibility and Beam Profile Constancy', headers=headers)
            utc_url = resp.json()['results'][0]['url']
            data = {
                'unit_test_collection': utc_url,

                'in_progress': True,  # optional, default is False
                'include_for_scheduling': True,
                'work_started': time.strftime('%Y-%m-%d %H:%M', time.localtime(os.path.getctime(os.path.dirname(directory[0])))),
                'work_completed': time.strftime('%Y-%m-%d %H:%M', time.localtime(os.path.getctime(os.path.dirname(directory[0])))),
                'user_key': hashlib.md5(open(directory[0], "rb").read()).hexdigest(),  # NOT PREVENTING DUPLICATE RESULTS
                    "tests": {

                        "Mat6Open": {'value': cGy[0]},
                        "Mat6FFFOpen": {'value': cGy[1]},
                        "Mat6Y1": {'value': cGy[2]},
                        "Mat6Y2": {'value': cGy[3]},
                        "Mat10Y1": {'value': cGy[4]},
                        "Mat10Y2": {'value': cGy[5]},
                        "Mat18Y1": {'value': cGy[6]},
                        "Mat18Y2": {'value': cGy[7]},
                        "Mat10FFFOpen": {'value': cGy[8]},
                        "Mat10Open": {'value': cGy[9]},
                        "Mat18Open": {'value': cGy[10]},

                        "Mat6FFFDepth": {'value': cGy[11]},
                        "Mat6Depth": {'value': cGy[12]},
                        "Mat18Depth": {'value': cGy[13]},
                        "Mat10Depth": {'value': cGy[14]},
                        "Mat10FFFDepth": {'value': cGy[15]},

                        "Mat6eOpen": {'value': cGy[16]},
                        "Mat6eDepth": {'value': cGy[17]},
                        "Mat9eOpen": {'value': cGy[18]},
                        "Mat12eOpen": {'value': cGy[19]},
                        "Mat9eDepth": {'value': cGy[20]},
                        "Mat16eOpen": {'value': cGy[21]},
                        "Mat20eOpen": {'value': cGy[22]},
                        "Mat12eDepth": {'value': cGy[23]},
                        "Mat16eDepth": {'value': cGy[24]},
                        "Mat20eDepth": {'value': cGy[25]},

                        "BPC_6x_Crossline": {'value': crosslineList[0]},
                        "BPC_6xFFF_Crossline": {'value': crosslineList[1]},
                        "BPC_10x_Crossline": {'value': crosslineList[2]},
                        "BPC_10xFFF_Crossline": {'value': crosslineList[3]},
                        "BPC_18x_Crossline": {'value': crosslineList[4]},
                        "BPC_6e_Crossline": {'value': crosslineList[5]},
                        "BPC_9e_Crossline": {'value': crosslineList[6]},
                        "BPC_12e_Crossline": {'value': crosslineList[7]},
                        "BPC_16e_Crossline": {'value': crosslineList[8]},
                        "BPC_20e_Crossline": {'value': crosslineList[9]},

                        "BPC_6x_Inline": {'value': inlineList[0]},
                        "BPC_6xFFF_Inline": {'value': inlineList[1]},
                        "BPC_10x_Inline": {'value': inlineList[2]},
                        "BPC_10xFFF_Inline": {'value': inlineList[3]},
                        "BPC_18x_Inline": {'value': inlineList[4]},
                        "BPC_6e_Inline": {'value': inlineList[5]},
                        "BPC_9e_Inline": {'value': inlineList[6]},
                        "BPC_12e_Inline": {'value': inlineList[7]},
                        "BPC_16e_Inline": {'value': inlineList[8]},
                        "BPC_20e_Inline": {'value': inlineList[9]}
                        }
                    }
       
        resp = requests.post(root + "/qa/testlistinstances/", json=data, headers=headers)

        if resp.status_code == requests.codes.CREATED: # http code 201
            btn_login['state']=DISABLED
            completed_url = resp.json()['site_url']
            webbrowser.open(completed_url, new=0, autoraise=True)
        else:
            
            Label(top,text='Your request failed with the following response:\n "%s" ' % resp.reason,bg=BG_top).grid(row=5)

# Define theme of GUI
BG_btn = "white"
FG_btn = "black"
BG_frm= '#F8F8F8'
fontNormal = (5)
fontSelectLinac= ('Cambria 15')
fontLinac= ('Cambria 18')
fontDateWarning=('Cambria 14')
HLBG_frm = "#838383"
HLBG_QADate= "#838383"
BG_main = "white"#"#F8F8F8"
oddrow='#F1F1F1'
error_message="red"
BG_top='#F5F5F5'

# Set up the main window
root = Tk()
root.title("ML11 and ML12")
root.geometry("700x955+100+1")
root.resizable(FALSE,FALSE)
root.configure(width=700,background=BG_main)

# Set Background
icon_image = PhotoImage(file = "T:\_Physics Team PEICTC\Benjamin\_Test Development\GUI Images\icon1.png")
root.iconphoto(FALSE, icon_image)
bg_image =Image.open('T:\_Physics Team PEICTC\Benjamin\_Test Development\GUI Images\Slide3.PNG')
resized = bg_image.resize((700,955),Image.LANCZOS)
new_image=ImageTk.PhotoImage(resized)
lbl_background = Label(root, image=new_image)
lbl_background.place(x=0, y=0, relwidth=1, relheight=1)

# Select Linac Frame
selectLinac=Label(root, text="Select Linac", padx=20,pady=5, font=fontSelectLinac, bg=BG_main).pack(anchor=W)
frm_selectLinac=Frame(root,width=100, highlightthickness=1,highlightbackground=HLBG_frm, bg=BG_frm)
frm_selectLinac.pack(ipady=2, ipadx=0, padx=(20,70), pady=0,anchor=W)

linac = IntVar()

# Radiobuttons for linac selection

btn_r1iX = Radiobutton(frm_selectLinac, text="   Clinac iX", padx=10,pady=10, variable=linac, value=1, command=clickLinac,bg=BG_frm)
btn_r1iX.grid(row=0,column=3, columnspan=2, sticky=W)

btn_r2TB3426 = Radiobutton(frm_selectLinac, text="   TrueBeam3426", padx=10, variable=linac, value=2, comman=clickLinac, bg=BG_frm)
btn_r2TB3426.grid(row=0,column=1, columnspan=2, sticky=W)

btn_r3TB5833 = Radiobutton(frm_selectLinac, text="   TrueBeam5833", padx=10, variable=linac, value=3, comman=clickLinac, bg=BG_frm)
btn_r3TB5833.grid(row=1,column=1, columnspan=2, sticky=W)

btn_Reset = Button(frm_selectLinac, text="Reset Selection", pady=2, padx=00, command =clickReset, bg =BG_btn, fg ="black")
btn_Reset.grid( row=1,column=3, sticky=NE,padx=10,ipadx=5,pady=5)


# Remaining widgets after linac is chosen

global lbl_iXData
lbl_iXData=Label(text="Clinac iX", padx=10,pady=2, font=fontLinac,bg=BG_main)
global lbl_QADate
lbl_QADate = Label(text= "QA Date: ",bg=BG_main)
global lbl_TB3426_data
lbl_TB3426_data=Label(text="TrueBeam3426", padx=10,pady=2, font=fontLinac, bg=BG_main)

global lbl_TB5833_data
lbl_TB5833_data=Label(text="TrueBeam5833", padx=10,pady=2, font=fontLinac, bg=BG_main)

global pageBreak
pageBreak = Frame(root,padx=10,highlightbackground=HLBG_frm,bg=HLBG_frm)

# Import Button
btn_TB3426_import = Button(root, text="Select all Files (22)", pady=0,padx=70, command=clickSelectFiles, bg=BG_btn, fg=FG_btn)
btn_TB5833_import = Button(root, text="Select all Files (26)", pady=0,padx=70, command=clickSelectFiles, bg=BG_btn, fg=FG_btn)
btn_iXImport = Button(root, text="Select all Files (18)", pady=0,padx=70, command=clickSelectFiles, bg=BG_btn, fg=FG_btn)

btn_Calculate = Button(root, text="Calculate Results", pady=1,padx=73, command=clickCalculate, bg=BG_btn, fg=FG_btn)

# Send results to QA Track Button
btn_sendToQATrack = Button(root, text="Send Results to QATrack", pady=1,padx=55, command=clickSubmit, bg=BG_btn, fg=FG_btn)

# iX Data File Table
frm_iXFiles = Frame(root, bg=BG_main,highlightbackground=HLBG_frm)

tbl_iXFiles = ttk.Treeview(frm_iXFiles, height=18)
tbl_iXFiles['columns'] = ('Energy', 'Accessory', 'Solid Water (cm)', 'File', 'Dose (cGy)')
tbl_iXFiles.column("#0", width=0,  stretch=NO)
tbl_iXFiles.column("Energy",anchor=CENTER, width=80)
tbl_iXFiles.column("Accessory",anchor=CENTER,width=80)
tbl_iXFiles.column("Solid Water (cm)",anchor=CENTER,width=100)
tbl_iXFiles.column("File",anchor=CENTER,width=150)
tbl_iXFiles.column("Dose (cGy)",anchor=CENTER,width=80)
tbl_iXFiles.heading("#0",text="",anchor=CENTER)
tbl_iXFiles.heading("Energy",text="Energy",anchor=CENTER)
tbl_iXFiles.heading("Accessory",text="Accessory",anchor=CENTER)
tbl_iXFiles.heading("Solid Water (cm)",text="Solid Water (cm)",anchor=CENTER)
tbl_iXFiles.heading("File",text="File",anchor=CENTER)
tbl_iXFiles.heading("Dose (cGy)",text="Dose (cGy)",anchor=CENTER)

tbl_iXFiles.insert(parent='',index='end',iid=0,text='',tags="oddRow",
values=('6 MV','EDW60IN','1'))
tbl_iXFiles.insert(parent='',index='end',iid=1,text='',
values=('6 MV','EDW60OUT','1'))
tbl_iXFiles.insert(parent='',index='end',iid=2,text='',tags="oddRow",
values=('6 MV','','1'))
tbl_iXFiles.insert(parent='',index='end',iid=3,text='',
values=('6 MV','','9.7'))
tbl_iXFiles.insert(parent='',index='end',iid=4,text='',tags="oddRow",
values=('18 MV','','9.7',""))
tbl_iXFiles.insert(parent='',index='end',iid=5,text='',
values=('18 MV','','2',""))
tbl_iXFiles.insert(parent='',index='end',iid=6,text='',tags="oddRow",
values=('18 MV','EDW60IN','2',""))
tbl_iXFiles.insert(parent='',index='end',iid=7,text='',
values=('18 MV','EDW60OUT','2',""))
tbl_iXFiles.insert(parent='',index='end',iid=8,text='',tags="oddRow",
values=('6 MeV','','1',""))
tbl_iXFiles.insert(parent='',index='end',iid=9,text='',
values=('6 MeV','','2',""))
tbl_iXFiles.insert(parent='',index='end',iid=10,text='',tags="oddRow",
values=('9 MeV','','2',""))
tbl_iXFiles.insert(parent='',index='end',iid=11,text='',
values=('12 MeV','','2',""))
tbl_iXFiles.insert(parent='',index='end',iid=12,text='',tags="oddRow",
values=('20 MeV','','2',""))
tbl_iXFiles.insert(parent='',index='end',iid=13,text='',
values=('9 MeV','','3',""))
tbl_iXFiles.insert(parent='',index='end',iid=14,text='',tags="oddRow",
values=('16 MeV','','3',""))
tbl_iXFiles.insert(parent='',index='end',iid=15,text='',
values=('12 MeV','','4.7',""))
tbl_iXFiles.insert(parent='',index='end',iid=16,text='',tags="oddRow",
values=('16 MeV','','6.2',""))
tbl_iXFiles.insert(parent='',index='end',iid=17,text='',
values=('20 MeV','','8.2',""))
tbl_iXFiles.tag_configure('oddRow', background=oddrow)

# iX Result Table
frm_iXResults = Frame(root, bg=BG_main,highlightbackground=HLBG_frm)

tbl_iXResults = ttk.Treeview(frm_iXResults, height=7)
tbl_iXResults['columns'] = ('Energy', 'Crossline Profile Constancy', 'Inline Profile Constancy', 'Energy Constancy', 'EDW Factor Constancy')
tbl_iXResults.column("#0", width=0,  stretch=NO)
tbl_iXResults.column("Energy",anchor=CENTER, width=60)
tbl_iXResults.column("Crossline Profile Constancy",anchor=CENTER,width=160)
tbl_iXResults.column("Inline Profile Constancy",anchor=CENTER,width=150)
tbl_iXResults.column("Energy Constancy",anchor=CENTER,width=125,)
tbl_iXResults.column("EDW Factor Constancy",anchor=CENTER,width=130)

tbl_iXResults.heading("#0",text="",anchor=CENTER)
tbl_iXResults.heading("Energy",text="Energy",anchor=CENTER)
tbl_iXResults.heading("Crossline Profile Constancy",text="Crossline Profile Constancy",anchor=CENTER)
tbl_iXResults.heading("Inline Profile Constancy",text="Inline Profile Constancy",anchor=CENTER)
tbl_iXResults.heading("Energy Constancy",text="Energy Constancy",anchor=CENTER)
tbl_iXResults.heading("EDW Factor Constancy",text="EDW Factor Constancy",anchor=CENTER)

tbl_iXResults.insert(parent='',index='end',iid=0,text='',tags="oddRow",
values=("6 MV",'','',''))
tbl_iXResults.insert(parent='',index='end',iid=1,text='',
values=("18 MV",'','',''))
tbl_iXResults.insert(parent='',index='end',iid=2,text='',tags="oddRow",
values=("6 MeV",'','',''))
tbl_iXResults.insert(parent='',index='end',iid=3,text='',
values=("9 MeV",'','',''))
tbl_iXResults.insert(parent='',index='end',iid=4,text='',tags="oddRow",
values=("12 MeV",'','',''))
tbl_iXResults.insert(parent='',index='end',iid=5,text='',
values=("16 MeV",'','',''))
tbl_iXResults.insert(parent='',index='end',iid=6,text='',tags="oddRow",
values=("20 MeV",'','',''))
tbl_iXResults.tag_configure('oddRow', background=oddrow)

# TB Data File Table
frm_TB3426_files = Frame(root, bg=BG_main,highlightbackground=HLBG_frm)

tbl_TB3426_files = ttk.Treeview(frm_TB3426_files, height=22)
tbl_TB3426_files['columns'] = ('Energy', 'Accessory', 'Solid Water (cm)', 'File', 'Dose (cGy)')
tbl_TB3426_files.column("#0", width=0,  stretch=NO)
tbl_TB3426_files.column("Energy",anchor=CENTER, width=80)
tbl_TB3426_files.column("Accessory",anchor=CENTER,width=80)
tbl_TB3426_files.column("Solid Water (cm)",anchor=CENTER,width=100)
tbl_TB3426_files.column("File",anchor=CENTER,width=150)
tbl_TB3426_files.column("Dose (cGy)",anchor=CENTER,width=80)
tbl_TB3426_files.heading("#0",text="",anchor=CENTER)
tbl_TB3426_files.heading("Energy",text="Energy",anchor=CENTER)
tbl_TB3426_files.heading("Accessory",text="Accessory",anchor=CENTER)
tbl_TB3426_files.heading("Solid Water (cm)",text="Solid Water (cm)",anchor=CENTER)
tbl_TB3426_files.heading("File",text="File",anchor=CENTER)
tbl_TB3426_files.heading("Dose (cGy)",text="Dose (cGy)",anchor=CENTER)

tbl_TB3426_files.insert(parent='',index='end',iid=0,text='',tags="oddRow",
values=('6 MV','EDW60IN','1'))
tbl_TB3426_files.insert(parent='',index='end',iid=1,text='',
values=('6 MV','EDW60OUT','1'))
tbl_TB3426_files.insert(parent='',index='end',iid=2,text='',tags="oddRow",
values=('10 MV','EDW60IN','2',""))
tbl_TB3426_files.insert(parent='',index='end',iid=3,text='',
values=('10 MV','EDW60OUT','2',""))
tbl_TB3426_files.insert(parent='',index='end',iid=4,text='',tags="oddRow",
values=('18 MV','EDW60IN','2',""))
tbl_TB3426_files.insert(parent='',index='end',iid=5,text='',
values=('18 MV','EDW60OUT','2',""))
tbl_TB3426_files.insert(parent='',index='end',iid=6,text='',tags="oddRow",
values=('6 MV','','1'))
tbl_TB3426_files.insert(parent='',index='end',iid=7,text='',
values=('6 MV FFF','','1'))
tbl_TB3426_files.insert(parent='',index='end',iid=8,text='',tags="oddRow",
values=('6 MV FFF','','9.7'))
tbl_TB3426_files.insert(parent='',index='end',iid=9,text='',
values=('6 MV','','9.7'))
tbl_TB3426_files.insert(parent='',index='end',iid=10,text='',tags="oddRow",
values=('18 MV','','9.7',""))
tbl_TB3426_files.insert(parent='',index='end',iid=11,text='',
values=('10 MV','','9.7',""))
tbl_TB3426_files.insert(parent='',index='end',iid=12,text='',tags="oddRow",
values=('10 MV FFF','','9.7',""))
tbl_TB3426_files.insert(parent='',index='end',iid=13,text='',
values=('10 MV FFF','','2',""))
tbl_TB3426_files.insert(parent='',index='end',iid=14,text='',tags="oddRow",
values=('10 MV','','2',""))
tbl_TB3426_files.insert(parent='',index='end',iid=15, text='',
values=('18 MV','','2',""))
tbl_TB3426_files.insert(parent='',index='end',iid=16,text='',tags="oddRow",
values=('6 MeV','','1',""))
tbl_TB3426_files.insert(parent='',index='end',iid=17,text='',
values=('6 MeV','','2',""))
tbl_TB3426_files.insert(parent='',index='end',iid=18,text='',tags="oddRow",
values=('9 MeV','','2',""))
tbl_TB3426_files.insert(parent='',index='end',iid=19,text='',
values=('12 MeV','','2',""))
tbl_TB3426_files.insert(parent='',index='end',iid=20,text='',tags="oddRow",
values=('9 MeV','','3',""))
tbl_TB3426_files.insert(parent='',index='end',iid=21,text='',
values=('12 MeV','','4.7',""))

tbl_TB3426_files.tag_configure('oddRow', background=oddrow)

# TB Result Table
frm_TB3426_results = Frame(root, bg=BG_main,highlightbackground=HLBG_frm)

tbl_TB3426_results = ttk.Treeview(frm_TB3426_results, height=8)
tbl_TB3426_results['columns'] = ('Energy', 'Crossline Profile Constancy', 'Inline Profile Constancy', 'Energy Constancy', 'EDW Factor Constancy')
tbl_TB3426_results.column("#0", width=0,  stretch=NO)
tbl_TB3426_results.column("Energy",anchor=CENTER, width=70)
tbl_TB3426_results.column("Crossline Profile Constancy",anchor=CENTER,width=160)
tbl_TB3426_results.column("Inline Profile Constancy",anchor=CENTER,width=150)
tbl_TB3426_results.column("Energy Constancy",anchor=CENTER,width=125,)
tbl_TB3426_results.column("EDW Factor Constancy",anchor=CENTER,width=130)

tbl_TB3426_results.heading("#0",text="",anchor=CENTER)
tbl_TB3426_results.heading("Energy",text="Energy",anchor=CENTER)
tbl_TB3426_results.heading("Crossline Profile Constancy",text="Crossline Profile Constancy",anchor=CENTER)
tbl_TB3426_results.heading("Inline Profile Constancy",text="Inline Profile Constancy",anchor=CENTER)
tbl_TB3426_results.heading("Energy Constancy",text="Energy Constancy",anchor=CENTER)
tbl_TB3426_results.heading("EDW Factor Constancy",text="EDW Factor Constancy",anchor=CENTER)

tbl_TB3426_results.insert(parent='',index='end',iid=0,text='',tags="oddRow",
values=("6 MV",'','',''))
tbl_TB3426_results.insert(parent='',index='end',iid=1,text='',
values=("6 MV FFF",'','',''))
tbl_TB3426_results.insert(parent='',index='end',iid=2,text='',tags="oddRow",
values=("10 MV",'','',''))
tbl_TB3426_results.insert(parent='',index='end',iid=3,text='',
values=("10 MV FFF",'','',''))
tbl_TB3426_results.insert(parent='',index='end',iid=4,text='',tags="oddRow",
values=("18 MV",'','',''))
tbl_TB3426_results.insert(parent='',index='end',iid=5,text='',
values=("6 MeV",'','',''))
tbl_TB3426_results.insert(parent='',index='end',iid=6,text='',tags="oddRow",
values=("9 MeV",'','',''))
tbl_TB3426_results.insert(parent='',index='end',iid=7,text='',
values=("12 MeV",'','',''))

tbl_TB3426_results.tag_configure('oddRow', background=oddrow)

# TB Data File Table
frm_TB5833_files = Frame(root, bg=BG_main,highlightbackground=HLBG_frm)

tbl_TB5833_files = ttk.Treeview(frm_TB5833_files, height=20)
tbl_TB5833_files['columns'] = ('Energy', 'Accessory', 'Solid Water (cm)', 'File', 'Dose (cGy)')
tbl_TB5833_files.column("#0", width=0,  stretch=NO)
tbl_TB5833_files.column("Energy",anchor=CENTER, width=80)
tbl_TB5833_files.column("Accessory",anchor=CENTER,width=80)
tbl_TB5833_files.column("Solid Water (cm)",anchor=CENTER,width=100)
tbl_TB5833_files.column("File",anchor=CENTER,width=150)
tbl_TB5833_files.column("Dose (cGy)",anchor=CENTER,width=80)
tbl_TB5833_files.heading("#0",text="",anchor=CENTER)
tbl_TB5833_files.heading("Energy",text="Energy",anchor=CENTER)
tbl_TB5833_files.heading("Accessory",text="Accessory",anchor=CENTER)
tbl_TB5833_files.heading("Solid Water (cm)",text="Solid Water (cm)",anchor=CENTER)
tbl_TB5833_files.heading("File",text="File",anchor=CENTER)
tbl_TB5833_files.heading("Dose (cGy)",text="Dose (cGy)",anchor=CENTER)


tbl_TB5833_files.insert(parent='',index='end',iid=0,text='',tags="oddRow",
values=('6 MV','','1'))
tbl_TB5833_files.insert(parent='',index='end',iid=1,text='',
values=('6 MV FFF','','1'))
tbl_TB5833_files.insert(parent='',index='end',iid=2,text='',tags="oddRow",
values=('6 MV','EDW60IN','1'))
tbl_TB5833_files.insert(parent='',index='end',iid=3,text='',
values=('6 MV','EDW60OUT','1'))
tbl_TB5833_files.insert(parent='',index='end',iid=4,text='',tags="oddRow",
values=('10 MV','EDW60IN','2',""))
tbl_TB5833_files.insert(parent='',index='end',iid=5,text='',
values=('10 MV','EDW60OUT','2',""))
tbl_TB5833_files.insert(parent='',index='end',iid=6,text='',tags="oddRow",
values=('18 MV','EDW60IN','2',""))
tbl_TB5833_files.insert(parent='',index='end',iid=7,text='',
values=('18 MV','EDW60OUT','2',""))
tbl_TB5833_files.insert(parent='',index='end',iid=8,text='',tags="oddRow",
values=('10 MV FFF','','2',""))
tbl_TB5833_files.insert(parent='',index='end',iid=9,text='',
values=('10 MV','','2',""))
tbl_TB5833_files.insert(parent='',index='end',iid=10, text='', tags="oddRow",
values=('18 MV','','2',""))
tbl_TB5833_files.insert(parent='',index='end',iid=11,text='',
values=('6 MV FFF','','9.7'))
tbl_TB5833_files.insert(parent='',index='end',iid=12,text='', tags="oddRow",
values=('6 MV','','9.7'))
tbl_TB5833_files.insert(parent='',index='end',iid=13,text='',
values=('18 MV','','9.7',""))
tbl_TB5833_files.insert(parent='',index='end',iid=14,text='', tags="oddRow",
values=('10 MV','','9.7',""))
tbl_TB5833_files.insert(parent='',index='end',iid=15,text='',
values=('10 MV FFF','','9.7',""))
tbl_TB5833_files.insert(parent='',index='end',iid=16,text='',tags="oddRow",
values=('6 MeV','','1',""))
tbl_TB5833_files.insert(parent='',index='end',iid=17,text='',
values=('6 MeV','','2',""))
tbl_TB5833_files.insert(parent='',index='end',iid=18,text='',tags="oddRow",
values=('9 MeV','','2',""))
tbl_TB5833_files.insert(parent='',index='end',iid=19,text='',
values=('12 MeV','','2',""))
tbl_TB5833_files.insert(parent='',index='end',iid=20,text='',tags="oddRow",
values=('9 MeV','','3',""))
tbl_TB5833_files.insert(parent='',index='end',iid=21,text='',
values=('16 MeV','','3',""))
tbl_TB5833_files.insert(parent='',index='end',iid=22,text='', tags="oddRow",
values=('20 MeV','','3',""))
tbl_TB5833_files.insert(parent='',index='end',iid=23,text='',
values=('12 MeV','','4.7',""))
tbl_TB5833_files.insert(parent='',index='end',iid=24,text='', tags="oddRow",
values=('16 MeV','','6.2',""))
tbl_TB5833_files.insert(parent='',index='end',iid=25,text='',
values=('20 MeV','','8.2',""))


tbl_TB5833_files.tag_configure('oddRow', background=oddrow)

# TB Result Table
frm_TB5833_results = Frame(root, bg=BG_main,highlightbackground=HLBG_frm)

tbl_TB5833_results = ttk.Treeview(frm_TB5833_results, height=10)
tbl_TB5833_results['columns'] = ('Energy', 'Crossline Profile Constancy', 'Inline Profile Constancy', 'Energy Constancy', 'EDW Factor Constancy')
tbl_TB5833_results.column("#0", width=0,  stretch=NO)
tbl_TB5833_results.column("Energy",anchor=CENTER, width=70)
tbl_TB5833_results.column("Crossline Profile Constancy",anchor=CENTER,width=160)
tbl_TB5833_results.column("Inline Profile Constancy",anchor=CENTER,width=150)
tbl_TB5833_results.column("Energy Constancy",anchor=CENTER,width=125,)
tbl_TB5833_results.column("EDW Factor Constancy",anchor=CENTER,width=130)

tbl_TB5833_results.heading("#0",text="",anchor=CENTER)
tbl_TB5833_results.heading("Energy",text="Energy",anchor=CENTER)
tbl_TB5833_results.heading("Crossline Profile Constancy",text="Crossline Profile Constancy",anchor=CENTER)
tbl_TB5833_results.heading("Inline Profile Constancy",text="Inline Profile Constancy",anchor=CENTER)
tbl_TB5833_results.heading("Energy Constancy",text="Energy Constancy",anchor=CENTER)
tbl_TB5833_results.heading("EDW Factor Constancy",text="EDW Factor Constancy",anchor=CENTER)

tbl_TB5833_results.insert(parent='',index='end',iid=0,text='',tags="oddRow",
values=("6 MV",'','',''))
tbl_TB5833_results.insert(parent='',index='end',iid=1,text='',
values=("6 MV FFF",'','',''))
tbl_TB5833_results.insert(parent='',index='end',iid=2,text='',tags="oddRow",
values=("10 MV",'','',''))
tbl_TB5833_results.insert(parent='',index='end',iid=3,text='',
values=("10 MV FFF",'','',''))
tbl_TB5833_results.insert(parent='',index='end',iid=4,text='',tags="oddRow",
values=("18 MV",'','',''))
tbl_TB5833_results.insert(parent='',index='end',iid=5,text='',
values=("6 MeV",'','',''))
tbl_TB5833_results.insert(parent='',index='end',iid=6,text='',tags="oddRow",
values=("9 MeV",'','',''))
tbl_TB5833_results.insert(parent='',index='end',iid=7,text='',
values=("12 MeV",'','',''))
tbl_TB5833_results.insert(parent='',index='end',iid=8,text='', tags="oddRow",
values=("16 MeV",'','',''))
tbl_TB5833_results.insert(parent='',index='end',iid=9,text='',
values=("20 MeV",'','',''))

tbl_TB5833_results.tag_configure('oddRow', background=oddrow)

scrollbar = ttk.Scrollbar(frm_TB5833_files, orient= VERTICAL,command=tbl_TB5833_files.yview)
scrollbar.pack(side= RIGHT, fill= Y)

root.mainloop()