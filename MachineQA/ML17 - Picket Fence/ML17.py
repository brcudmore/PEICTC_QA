import pydicom as dicom
from pylinac.picketfence import PicketFence, MLCArrangement

from tkinter import *
from tkinter import filedialog, ttk

# import webbrowser
import requests
import numpy as np
import os as os
import datetime as datetime
import datetime
from PIL import ImageTk, Image
import sys

sys.path.append("T:\\_Physics Team PEICTC\\Benjamin\\GitHub\\PEICTC_QA")
from Helpers.QATrackHelpers import QATrack as qat

# Written by Ben Cudmore
# One of my first apps... Please don't judge but by all means make better as needed ;P


# This code was written before the QATrackHelperClass was developed. It has since been updated to use it but I left some things as is so as to not break it BRC
# This code generates an GUI that can process Picket Fence Images using Pylinac.
# 
#
# Create updated executable (.exe) using the following in terminal:
# pyinstaller -F --hiddenimport=pydicom.encoders.gdcm --hiddenimport=pydicom.encoders.pylibjpeg --consol --clean ML17.py
#
# make sure all dependencies are installed on your local environment using 
# pip install gdcm
#
#
# Image paths will need to be updated and remain unchanged when .exe is created

# All button definitions are defined before the app is built.


# Declare variables and lists

pf = []
PF_tests = (
    "Static Gantry 0°",
    "Static Gantry 90°",
    "Static Gantry 180°",
    "Static Gantry 270°",
    "Rapid Arc",
    "Rapid Arc with Error"
    )

processed_image_data = {
    "Static Gantry 0°": {},
    "Static Gantry 90°": {},
    "Static Gantry 180°": {},
    "Static Gantry 270°": {},
    "Rapid Arc": {},
    "Rapid Arc w/ Errors": {}
    }

unprocessed_image_data = {
    "File_Name": [],
    "Modality":[],
    "Machine_Name": [],
    "Acquisition_Date": []
    } 
incomplete_tests = {"Missing_PF_test": []}

# GUI functions

def double_click(event):
    item = tbl_Results.selection()[0]
    value = tbl_Files.item(item)['values']
    processed_image_data[value[0]]['Pylinac_Data'].plot_analyzed_image()

def run_pylinac_picket_fence(image, test):
 
    pf = PicketFence(image, mlc = mlc_type, filter = 3, crop_mm = 0.8)

    pf.image.array = np.flipud(pf.image.array)  # Flip image array to correspond to varian display w/ collimator set to 0°


    # Nominal gap determined iteratively adjusting nominal_gap value to minimizing median leaf error.
        #h:\_Test Development\Pylinac\Picket Fence\Code\Determine nominal gap.py

    pf.analyze(tolerance = 0.50, action_tolerance = 0.50, separate_leaves=True, nominal_gap_mm=1.84) #1.841
    
    # Calculate std of all leaves absolute positing errors
    individual_leaf_results = []
    for m in  pf.mlc_meas:
        individual_leaf_results.append(m.error)
    
    leaf_std = np.std(np.abs(individual_leaf_results))

    # append all results in dictionary
    processed_image_data[test]["Abs._Median_Error_(mm)"] = float(np.round(pf.abs_median_error,2))
    processed_image_data[test]["Standard_Deviation"] = float(np.round(leaf_std, 2))
    processed_image_data[test]["Max Error_(mm)"] = float(np.round(pf.max_error, 2))
    corrected_max_leaf_location = correct_MLC_Bank_Letter(pf.max_error_leaf)
    processed_image_data[test]["Max_Error_Leaf_Location"] = corrected_max_leaf_location
    processed_image_data[test]["Leaves_Passing"] = float(np.round(pf.percent_passing, 1))

    return pf

def correct_MLC_Bank_Letter(max_error_leaf_location):
    # The Picket Fence module mixes up MLC leaf banks A and B and the numbering is off by 1.
    # This was discovered by analyzing the Varian PF plan with intentional errors
    if "A" in max_error_leaf_location:
        corrected_max_leaf_location = 'B' + str(int(max_error_leaf_location[1:])+1)
    elif "B" in max_error_leaf_location:
        corrected_max_leaf_location = 'A' + str(int(max_error_leaf_location[1:])+1)
    return corrected_max_leaf_location

def reset_dictionaries():
    global processed_image_data
    for key in processed_image_data:
        processed_image_data[key] = {}

    unprocessed_image_data["File_Name"] = []

    unprocessed_image_data["Machine_Name"] = []
    unprocessed_image_data["Acquisition_Date"] = []

    incomplete_tests["Missing_PF_test"] = []

def clickLinac(): # 

    btn_r1TB3426['state']=DISABLED
    btn_r2TB5833['state']=DISABLED

    global linacChoice
    global mlc_type
    linacChoice = linac.get()

    if linacChoice == 1:
        mlc_type = MLCArrangement(leaf_arrangement=[(14, 5), (32, 2.5), (14, 5)])
        lbl_MachineTB3426.pack(anchor=N)
    
    if linacChoice == 2:
        mlc_type = MLCArrangement(leaf_arrangement=[(10, 10), (40, 5), (10, 10)])
        lbl_MachineTB5833.pack(anchor=N)
    
    pageBreak.pack(side='top', fill='x',padx=20,pady=(5,10))

    btn_Import.pack(anchor=N)

    frm_Files.pack(anchor=N,pady=10,padx=10,)
    tbl_Files.pack(fill=BOTH,expand=1, anchor=N)

    btn_Calculate.pack(anchor=N)
    btn_Calculate['state']=DISABLED

    frm_Results.pack(anchor=N,pady=10,padx=10)
    tbl_Results.pack(fill=BOTH, expand=1, anchor=N)
    lbl_Double_Click_Results.pack(anchor=NW)

    btn_sendToQATrack.pack(anchor=N,pady=(10))

    btn_sendToQATrack['state'] = DISABLED

def clickReset(): # Returns GUI to initial state
    
    linacChoice = linac.get()
    
    if linacChoice == 0:
        None

    else:
        lbl_MachineTB3426.pack_forget()
        lbl_MachineTB5833.pack_forget()
        btn_Import.pack_forget()
        frm_Files.pack_forget()
        tbl_Files.pack_forget()
        frm_Results.pack_forget()
        tbl_Results.pack_forget()
        btn_Calculate.pack_forget() 
        lbl_Double_Click_Results.pack_forget()

        btn_sendToQATrack.pack_forget()
        pageBreak.pack_forget()
        lbl_QADate.place_forget()
        btn_r1TB3426['state']=NORMAL
        btn_r2TB5833['state']=NORMAL

        linac.set(0)

        for i in range(6):
            for j in range(4):
                tbl_Files.set([i],j,"")
            for j in range(6):
                tbl_Results.set([i],[j],"")
        
        reset_dictionaries()


def clickSelectFiles(): # Ensure the correct number of files are chosen for the selected linac and displays relevant information in table

    for i in range(6):
        for j in range(4):
            tbl_Files.set([i],j,"")
        for j in range(6):
            tbl_Results.set([i],j,"")
    
    reset_dictionaries()
    
    for i in range(4):
        for j in range(7):
            tbl_Results.set([j],[i+1],"")

    if linacChoice == 1:
        files= filedialog.askopenfiles(initialdir="T:\\QA\\Data\\Monthly Picket Fence\\TrueBeam3426",title="Select Files,",filetypes=[("opg files","*.dcm")])
        linac = '3426'
    if linacChoice == 2:
        files= filedialog.askopenfiles(initialdir="T:\\QA\\Data\\Monthly Picket Fence\\TrueBeam5833",title="Select Files,",filetypes=[("opg files","*.dcm")])
        linac = '5833'

    if files == '':
        None
    
    elif len(files) >6:  
        top=Toplevel(root)
        top.geometry("250x75")
        top.title("Error")
        top.configure(width=700,background=BG_top)
        top.iconphoto(False, icon_image)
        Label(top, text="Wrong number of files selected. \n Please select 6 files or less.",font=('Aerial 11'),pady=20,background=BG_top).pack(anchor=CENTER)
    else:
        reset_dictionaries()
        count = 0
        for file in files:
            fileInfo = dicom.read_file(file.name)
            modality = fileInfo.Modality
            fileName = file.name.split('/')[-1].strip()

            if modality == 'RTIMAGE':
                gantry_angle = fileInfo.GantryAngle
                processed = True

                if gantry_angle > 358 or gantry_angle <2:
                    test = "Static Gantry 0°"

                elif gantry_angle > 88 and gantry_angle < 92:
                    test = "Static Gantry 90°"

                elif gantry_angle > 178 and gantry_angle < 182:
                    test = "Static Gantry 180°"

                elif (gantry_angle > 268 and gantry_angle < 272):
                    test = "Static Gantry 270°"

                elif gantry_angle > 185 and gantry_angle < 189 or  (gantry_angle > 226 and gantry_angle < 231):
                    count += 1
                    if count == 1:
                        test = "Rapid Arc"
                    else:
                        test = "Rapid Arc w/ Errors"

                elif gantry_angle > 60 and gantry_angle < 64:
                    test = "Rapid Arc w/ Errors"

                else:
                    processed = False
                
                if processed == True:
                    acquisition_date = datetime.datetime.strptime(fileInfo.AcquisitionDate, '%Y%m%d').strftime('%b %d/%y')
                    treatment_machine = fileInfo.RadiationMachineName
                    processed_image_data[test]["Directory"] = file.name
                    processed_image_data[test]["File_Name"] = fileName
                    processed_image_data[test]["Machine_Name"] = treatment_machine
                    processed_image_data[test]["Acquisition_Date"] = acquisition_date
                    
                else:
                    unprocessed_image_data["File_Name"].append(fileName)
                    unprocessed_image_data["Machine_Name"].append(treatment_machine)
                    unprocessed_image_data["Acquisition_Date"].append(acquisition_date)

            else:
                top=Toplevel(root)
                top.geometry("500x75")
                top.title("Error")
                top.configure(width=700,background=BG_top)
                top.iconphoto(False, icon_image)
                Label(top, text="The following file(s) are not RT images and cannot be processed: \n \n" + fileName, font=('Aerial 12'),pady=20,background=BG_top).pack(anchor=CENTER)


        for test_type in PF_tests:
            if test_type in processed_image_data[test]:
                pass
            else:
                incomplete_tests["Missing_PF_test"].append(test)

        # start count at -1 so index starts at 0
        count = -1
        can_process = True
        wrong_machine = ""

        for i in (processed_image_data): # Inserts file names and data factors into table
            count +=1
            if len(processed_image_data[i]) > 0:
                tbl_Files.set([count],0, i)
                tbl_Files.set([count],1,processed_image_data[i]["File_Name"])
                tbl_Files.set([count],2,processed_image_data[i]["Machine_Name"])
                tbl_Files.set([count],3,processed_image_data[i]["Acquisition_Date"])
        
                if linac not in processed_image_data[i]["Machine_Name"]:
                    wrong_machine = processed_image_data[i]["Machine_Name"]
                    can_process = False
        
        if can_process:
            btn_Calculate['state']=NORMAL
            
        else:
            top=Toplevel(root)
            top.geometry("700x75")
            top.title("Error")
            Label(top, text="At lease one dicom header indicated {} but you have TrueBeam{} selected.\nPlease verify you have the correct linac selected.".format(wrong_machine, linac),font=('Aerial 11'),pady=20,background=BG_top).pack(anchor=CENTER)
           

def clickCalculate():
    
    btn_sendToQATrack['state']=NORMAL

    for test in processed_image_data:
        if len(processed_image_data[test]) > 0:
            pf = run_pylinac_picket_fence(processed_image_data[test]['Directory'], test)
            processed_image_data[test]['Pylinac_Data'] = pf

    count = 0
    for test in processed_image_data: # Inserts file names and data factors into table
        if len(processed_image_data[test]) > 0:
            count += 1
            tbl_Results.set([count - 1],0, test)
            tbl_Results.set([count - 1],1, processed_image_data[test]["Leaves_Passing"])
            tbl_Results.set([count - 1],2, processed_image_data[test]["Abs._Median_Error_(mm)"])
            tbl_Results.set([count - 1],3, processed_image_data[test]["Standard_Deviation"])
            tbl_Results.set([count - 1],4, processed_image_data[test]["Max Error_(mm)"])
            tbl_Results.set([count - 1],5, processed_image_data[test]["Max_Error_Leaf_Location"])

def clickQATrack():
    tests = {
        "gant_0_percent_leaves_passing": {'skipped': True},
        "gant_0_abs_median_error": {'skipped': True},
        "gant_0_leaf_error_std": {'skipped': True},
        "gant_0_max_error": {'skipped': True},
        
    
        "gant_90_percent_leaves_passing": {'skipped': True},
        "gant_90_abs_median_error": {'skipped': True},
        "gant_90_leaf_error_std": {'skipped': True},
        "gant_90_max_error": {'skipped': True},

        "gant_180_percent_leaves_passing": {'skipped': True},
        "gant_180_abs_median_error": {'skipped': True},
        "gant_180_leaf_error_std": {'skipped': True},
        "gant_180_max_error": {'skipped': True},

        "gant_270_percent_leaves_passing": {'skipped': True},
        "gant_270_abs_median_error": {'skipped': True},
        "gant_270_leaf_error_std": {'skipped': True},
        "gant_270_max_error": {'skipped': True},

        "arc_percent_leaves_passing": {'skipped': True},
        "arc_abs_median_error": {'skipped': True},
        "arc_leaf_error_std": {'skipped': True},
        "arc_max_error": {'skipped': True},
    
        "arc_errors_percent_leaves_passing": {'skipped': True},
        "arc_errors_abs_median_error": {'skipped': True},
        "arc_errors_leaf_error_std": {'skipped': True},
        "arc_errors_max_error": {'skipped': True}
    }
    
    if "Static Gantry 0°" in processed_image_data:
        tests ["gant_0_percent_leaves_passing"] = {'value': processed_image_data['Static Gantry 0°']['Leaves_Passing']}
        tests ["gant_0_abs_median_error"] = {'value': processed_image_data['Static Gantry 0°']["Abs._Median_Error_(mm)"]}
        tests ["gant_0_leaf_error_std"] = {'value': processed_image_data['Static Gantry 0°']['Standard_Deviation']}
        tests ["gant_0_max_error"]= {'value': processed_image_data['Static Gantry 0°']['Max Error_(mm)']}
        
    if "Static Gantry 90°" in processed_image_data:
        tests ["gant_90_percent_leaves_passing"] = {'value': processed_image_data['Static Gantry 90°']['Leaves_Passing']}
        tests ["gant_90_abs_median_error"] = {'value': processed_image_data['Static Gantry 90°']["Abs._Median_Error_(mm)"]}
        tests ["gant_90_leaf_error_std"] = {'value': processed_image_data['Static Gantry 90°']['Standard_Deviation']}
        tests ["gant_90_max_error"]= {'value': processed_image_data['Static Gantry 90°']['Max Error_(mm)']}

    if "Static Gantry 180°" in processed_image_data:
        tests ["gant_180_percent_leaves_passing"] = {'value': processed_image_data['Static Gantry 180°']['Leaves_Passing']}
        tests ["gant_180_abs_median_error"] = {'value': processed_image_data['Static Gantry 180°']["Abs._Median_Error_(mm)"]}
        tests ["gant_180_leaf_error_std"] = {'value': processed_image_data['Static Gantry 180°']['Standard_Deviation']}
        tests ["gant_180_max_error"]= {'value': processed_image_data['Static Gantry 180°']['Max Error_(mm)']}

    if "Static Gantry 270°" in processed_image_data:
        tests ["gant_270_percent_leaves_passing"] = {'value': processed_image_data['Static Gantry 270°']['Leaves_Passing']}
        tests ["gant_270_abs_median_error"] = {'value': processed_image_data['Static Gantry 270°']["Abs._Median_Error_(mm)"]}
        tests ["gant_270_leaf_error_std"] = {'value': processed_image_data['Static Gantry 270°']['Standard_Deviation']}
        tests ["gant_270_max_error"]= {'value': processed_image_data['Static Gantry 270°']['Max Error_(mm)']}

    if "Rapid Arc" in processed_image_data:
        tests ["arc_percent_leaves_passing"] = {'value': processed_image_data['Rapid Arc']['Leaves_Passing']}
        tests ["arc_abs_median_error"] = {'value': processed_image_data['Rapid Arc']["Abs._Median_Error_(mm)"]}
        tests ["arc_leaf_error_std"] = {'value': processed_image_data['Rapid Arc']['Standard_Deviation']}
        tests ["arc_max_error"]= {'value': processed_image_data['Rapid Arc']['Max Error_(mm)']}
    
    if "Rapid Arc w/ Errors" in processed_image_data:
        tests ["arc_errors_percent_leaves_passing"] = {'value': processed_image_data['Rapid Arc w/ Errors']['Leaves_Passing']}
        tests ["arc_errors_abs_median_error"] = {'value': processed_image_data['Rapid Arc w/ Errors']["Abs._Median_Error_(mm)"]}
        tests ["arc_errors_leaf_error_std"] = {'value': processed_image_data['Rapid Arc w/ Errors']['Standard_Deviation']}
        tests ["arc_errors_max_error"]= {'value': processed_image_data['Rapid Arc w/ Errors']['Max Error_(mm)']}

    qat.log_into_QATrack()
    
    first_test = next(iter(processed_image_data))
    date = datetime.datetime.strptime(processed_image_data[first_test]['Acquisition_Date'], "%b %d/%y")
    formatted_date = date.strftime('%Y-%m-%d %H:%M')
    machine = processed_image_data[first_test]['Machine_Name']

    utc_url, _ = qat.get_unit_test_collection(machine, "Picket Fence")

    qat.post_results(utc_url, tests, formatted_date)

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
root.title("ML17 - Dynamic Leaf Position Accuracy (Picket Fence)")
root.geometry("800x955+100+1")
root.resizable(FALSE,FALSE)
root.configure(width=1000,background=BG_main)

# Set Background
try:
    icon_image = PhotoImage(file = 'T:\\_Physics Team PEICTC\\Benjamin\\_Test Development\\GUI Images\\icon1.png')
    root.iconphoto(FALSE, icon_image)
    bg_image =Image.open('T:\\_Physics Team PEICTC\\Benjamin\\_Test Development\\GUI Images\\Slide3.PNG')
    resized = bg_image.resize((800,955),Image.LANCZOS)
    new_image=ImageTk.PhotoImage(resized)
    lbl_background = Label(root, image=new_image)
    lbl_background.place(x=0, y=0, relwidth=1, relheight=1)
except:
    top=Toplevel(root)
    top.geometry("600x75")
    top.title("Error")
    top.configure(width=700,background=BG_top)
    Label(top, text="The GUI images 'icon1.png' and/or 'Slide3.png' are not located in\n T:\\_Physics Team PEICTC\\Benjamin\\_Test Development\\GUI Images\\\nThe app may look different.",font=('Aerial 11'),pady=20,background=BG_top).pack(anchor=CENTER)



# Select Linac Frame
selectLinac=Label(root, text="Select Linac", padx=20,pady=5, font=fontSelectLinac, bg=BG_main).pack(anchor=W)
frm_selectLinac=Frame(root,width=100, highlightthickness=1,highlightbackground=HLBG_frm, bg=BG_frm)
frm_selectLinac.pack(ipady=2, ipadx=0, padx=(20,70), pady=0,anchor=W)

linac = IntVar()

# Radiobuttons for linac selection

btn_r1TB3426 = Radiobutton(frm_selectLinac, text="   TrueBeam3426", padx=10,pady=10, variable=linac, value=1, command=clickLinac,bg=BG_frm)
btn_r1TB3426.grid(row=0,column=1, columnspan=2, sticky=W)

btn_r2TB5833 = Radiobutton(frm_selectLinac, text="   TrueBeam5833", padx=10, variable=linac, value=2, comman=clickLinac, bg=BG_frm)
btn_r2TB5833.grid(row=1,column=1, columnspan=2, sticky=W)


btn_Reset = Button(frm_selectLinac, text="Reset Selection", pady=2, padx=00, command =clickReset, bg =BG_btn, fg ="black")
btn_Reset.grid( row=1,column=3, sticky=NE,padx=10,ipadx=5,pady=5)


# Remaining widgets after linac is chosen

global lbl_MachineTB3426
global lbl_MachineTB5833
global lbl_Double_Click_Results
lbl_Double_Click_Results = Label(text = "Double-click on a row of results to view the picket fence image.", padx = 20, pady=1,bg=BG_main)
lbl_MachineTB3426=Label(text="TrueBeam 3426", padx=10,pady=2, font=fontLinac,bg=BG_main)
lbl_MachineTB5833=Label(text="TrueBeam 5833", padx=10,pady=2, font=fontLinac,bg=BG_main)
global lbl_QADate
lbl_QADate = Label(text= "QA Date: ",bg=BG_main)
global lbl_TB5833Data

global pageBreak
pageBreak = Frame(root,padx=10,highlightbackground=HLBG_frm,bg=HLBG_frm)

# Import Button
btn_Import = Button(root, text="Select all Files (6)", pady=0,padx=70, command=clickSelectFiles, bg=BG_btn, fg=FG_btn)

btn_Calculate = Button(root, text="Calculate Results", pady=1,padx=73, command=clickCalculate, bg=BG_btn, fg=FG_btn)

# Send results to QA Track Button
btn_sendToQATrack = Button(root, text="Send Results to QATrack", pady=1,padx=55, command=clickQATrack, bg=BG_btn, fg=FG_btn)

# File Data Table
frm_Files = Frame(root, bg=BG_main,highlightbackground=HLBG_frm)

tbl_Files = ttk.Treeview(frm_Files, height=6)
tbl_Files['columns'] = ('Picket Fence Test', 'File Name', 'Treatment Machine', 'Acquisition Date')
tbl_Files.column("#0", width=0,  stretch=NO)
tbl_Files.column("Picket Fence Test",anchor=CENTER, width=140)
tbl_Files.column("File Name", anchor=W, width=260)
tbl_Files.column("Treatment Machine",anchor=CENTER,width=120)
tbl_Files.column("Acquisition Date",anchor=CENTER,width=120)

tbl_Files.heading("#0",text="",anchor=CENTER)
tbl_Files.heading("Picket Fence Test",text="Picket Fence Test",anchor=CENTER)
tbl_Files.heading("File Name",text="File Name",anchor=CENTER)
tbl_Files.heading("Treatment Machine",text="Treatment Machine",anchor=CENTER)
tbl_Files.heading("Acquisition Date",text="Acquisition Date",anchor=CENTER)


tbl_Files.insert(parent='',index='end',iid=0,text='',tags="oddRow",
values=('','','',''))
tbl_Files.insert(parent='',index='end',iid=1,text='',
values=('','','',''))
tbl_Files.insert(parent='',index='end',iid=2,text='',tags="oddRow",
values=('','','',''))
tbl_Files.insert(parent='',index='end',iid=3,text='',
values=('','','',''))
tbl_Files.insert(parent='',index='end',iid=4,text='',tags="oddRow",
values=('','','',''))
tbl_Files.insert(parent='',index='end',iid=5,text='',
values=('','','','',''))
tbl_Files.tag_configure('oddRow', background=oddrow)
tbl_Files.tag_configure('redText', foreground='red')

# Result Table
frm_Results = Frame(root, bg=BG_main, highlightbackground=HLBG_frm)

tbl_Results = ttk.Treeview(frm_Results, height=6)
tbl_Results['columns'] = ('Picket Fence Test', 'Leaves Passing (%)', 'Abs. Median Error (mm)', 'Abs. Standard Deviation (mm)', 'Max Error (mm)', 'Max Error Leaf')
tbl_Results.column("#0", width=0,  stretch=NO)
tbl_Results.column('Picket Fence Test',anchor=CENTER, width=115)
tbl_Results.column('Leaves Passing (%)',anchor=CENTER,width=110)
tbl_Results.column('Abs. Median Error (mm)',anchor=CENTER,width=140)
tbl_Results.column('Abs. Standard Deviation (mm)',anchor=CENTER,width=170)
tbl_Results.column('Max Error (mm)',anchor=CENTER,width=95,)
tbl_Results.column('Max Error Leaf',anchor=CENTER,width=95)

tbl_Results.heading("#0",text="",anchor=CENTER)
tbl_Results.heading('Picket Fence Test',text='Picket Fence Test',anchor=CENTER)
tbl_Results.heading('Leaves Passing (%)',text='Leaves Passing (%)',anchor=CENTER)
tbl_Results.heading('Abs. Median Error (mm)',text='Abs. Median Error (mm)',anchor=CENTER)
tbl_Results.heading('Abs. Standard Deviation (mm)', text ='Abs. Standard Deviation (mm)',anchor=CENTER)
tbl_Results.heading('Max Error (mm)',text='Max Error (mm)',anchor=CENTER)
tbl_Results.heading('Max Error Leaf',text='Max Error Leaf',anchor=CENTER)

tbl_Results.insert(parent='',index='end',iid=0,text='',tags="oddRow",
values=('','','',''))
tbl_Results.insert(parent='',index='end',iid=1,text='',
values=('','','',''))
tbl_Results.insert(parent='',index='end',iid=2,text='',tags="oddRow",
values=('','','','',''))
tbl_Results.insert(parent='',index='end',iid=3,text='',
values=('','','',''))
tbl_Results.insert(parent='',index='end',iid=4,text='',tags="oddRow",
values=('','','',''))
tbl_Results.insert(parent='',index='end',iid=5,text='',
values=('','','',''))
tbl_Results.insert(parent='',index='end',iid=6,text='',tags="oddRow",
values=('','','',''))
tbl_Results.tag_configure('oddRow', background=oddrow)

tbl_Results.bind('<Double-1>',double_click)

root.mainloop()