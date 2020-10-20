import glob
from datetime import timedelta, datetime
import os
from shutil import rmtree
import csv 
import pandas as pd
import zipfile
import argparse


parser = argparse.ArgumentParser(description='---Add end time dynamically to gt3x files---')
parser.add_argument('--dataDir', dest='data_dir',  help='Path to gt3x files')
parser.add_argument('--script', dest='script_dir',  help='Path to the baseline script')
parser.add_argument('--destScript', dest='dest_script_dir',  help='Path to the updated script')
parser.add_argument('--sleepDir', dest='sleep_dir',  help='Path sleep time table')

args = parser.parse_args()
## input arguments
# data_dir = '/well/doherty/users/cxx579/project_data/test_raine'
# timeshift = timedelta(days=7)
# script_dir = '/well/doherty/users/cxx579/test_process/myBBAA/process-raine-cmds.txt'
# dest_script_dir = '/well/doherty/users/cxx579/test_process/myBBAA/process-raine-cmds-final.txt'
# destSleepPath = '/well/doherty/users/cxx579/project_data/raine/gen1_26/allSleepTime.csv'
data_dir = args.data_dir
script_dir = args.script_dir
dest_script_dir = args.dest_script_dir
sleep_time_dir = args.sleep_dir


## Modify command line script
def extract_file_name(command_str):
    file_path = command_str.split(' ')
    file_path = file_path[2]
    file_path = file_path[1:]
    file_path = file_path[:-1] # remove quotation marks

    return file_path.split("/")[-1]


def get_subjectID(file_name):
    return file_name.split('_')[0]


sleepDf = pd.read_csv(sleep_time_dir)
f = open(script_dir, "r")
k = 0

if os.path.exists(dest_script_dir):
    os.remove(dest_script_dir)

with open(dest_script_dir, 'a') as dest_f:
    for x in f:
        my_file_name = extract_file_name(x)
        my_id = get_subjectID(my_file_name)
        result = sleepDf[sleepDf['subject_id'] == int(my_id)]

        my_start_time = result.iloc[0]['start_time']
        my_end_time = result.iloc[0]['end_time']

        my_start_time = datetime.strptime(my_start_time, '%Y-%m-%d %H:%M:%S')
        my_end_time = datetime.strptime(my_end_time, '%Y-%m-%d %H:%M:%S')
        my_end_time = my_end_time + timedelta(minutes=2)

        my_start_time = my_start_time.strftime('%Y-%m-%dT%H:%M')
        my_end_time = my_end_time.strftime('%Y-%m-%dT%H:%M')
        x = x[:-1] # remove line break
        x = x + ' --startTime ' + my_start_time
        x = x + ' --endTime ' + my_end_time + '\n'
        dest_f.write(x)
        
f.close()
