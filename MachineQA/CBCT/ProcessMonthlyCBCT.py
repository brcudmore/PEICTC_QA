import sys

sys.path.append("T:\\_Physics Team PEICTC\\Benjamin\\GitHub\\PEICTC_QA")
from Helpers.QATrackHelpers import QATrack as qat
from Helpers.SmariHelpers import SMARI as si

### Author: Benjamin Cudmore

# Use the following to package into an application:
# pyinstaller -F --hiddenimport=pydicom.encoders.gdcm --hiddenimport=pydicom.encoders.pylibjpeg --hiddenimport=pylinac --hiddenimport=pyTQA.tqa --uac-admin --onefile --clean ProcessMonthlyCBCT.py


# log_into_smari() checks for a SMARI API key associated with the Windows Username
# of the person logged in. The user will be prompted if they do not have an API key.
si.log_into_smari()

#   log_into_QATrack() does the same as above for QATrack.
qat.log_into_QATrack()

# process_input_folder() does the following:
#   1. Sorts through files in "T:\QA\Data\Monthly Imaging\_Input Folder\CBCT"
#       to determine acquisition details of each CBCT
#   2. Each CBCT is processed one at a time
#   3. Files are organized into "T:\QA\Data\Monthly Imaging\_Processed" with sub-folders
#       reflecting linac, imaging system, and date acquired
#   4. SMARI results of interest are returned formatted for QATrack 

qatrack_results = si.process_input_folder()
 
#    Results are formatted to be posed for QATrack. 
#    Images acquired on different months will be uploaded to separate test lists
#    Results are uploaded to the test list associated with the linac the images were acquired on.

si.post_smari_results_to_qatrack(qatrack_results)

input("Press Enter to exit...")


