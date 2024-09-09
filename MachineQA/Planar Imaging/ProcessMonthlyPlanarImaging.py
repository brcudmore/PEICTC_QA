import sys

sys.path.append("T:\\_Physics Team PEICTC\\Benjamin\\GitHub\\PEICTC_QA")
from Helpers.QATrackHelpers import QATrack as qat
from Helpers.PlanarImagingHelpers import PlanarImaging as pimg

### Author: Benjamin Cudmore

# Use the following to package into an application:
# pyinstaller -F --hiddenimport=pydicom.encoders.gdcm --hiddenimport=pydicom.encoders.pylibjpeg --hiddenimport=pylinac --hiddenimport=pyTQA.tqa --uac-admin --onefile --clean ProcessMonthlyPlanarImaging.py


# Makes it so files are not renamed or moved while testing
pimg.archive_files = True

# Set to true for helpful visualizations of what the code is doing.
pimg.show_plots = False

# Set to True if you want to see images that were not processed
pimg.show_unprocessed_plots = False

#    log_into_QATrack() checks for a QATrack API key associated with the Windows Username
#    of the person logged in. The user will be prompted if they do not have an API key.

qat.log_into_QATrack()

#    process_input_folder() does the following:
#    1. Sorts through files in "T:\QA\Data\Monthly Imaging\_Input Folder\Planar Imaging", 
#    2. Each image is processed one at a time
#    3. Processed images are renamed based on their acquisition parameters (uniqueness ensured) 
#    4. Files are organized into "T:\QA\Data\Monthly Imaging\_Processed" with sub-folders
#        reflecting linac, imaging system, and date acquired


test_list_results = pimg.process_input_folder()


#    Results are formatted to be posed for QATrack. 
#    Images acquired on different months will be uploaded to separate test lists
#    Results are uploaded to the test list associated with the linac the images were acquired on.

# Enable next line if you want to post results to QATrack
pimg.post_planar_results_to_qatrack(test_list_results)

input("Press Enter to exit...")



    

