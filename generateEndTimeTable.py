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
parser.add_argument('--timeShift', dest='timeshift', default=7, type=int, help='How many days to shift')

args = parser.parse_args()
## input arguments
# data_dir = '/well/doherty/users/cxx579/project_data/test_raine'
# timeshift = timedelta(days=7)
# script_dir = '/well/doherty/users/cxx579/test_process/myBBAA/process-raine-cmds.txt'
# dest_script_dir = '/well/doherty/users/cxx579/test_process/myBBAA/process-raine-cmds-final.txt'
data_dir = args.data_dir
script_dir = args.script_dir
dest_script_dir = args.dest_script_dir
timeshift = timedelta(days=args.timeshift)


endTimeFilePath = data_dir + '/endTime.csv'
file_desp = data_dir + '/*.gt3x'
tmp_dir = data_dir + '/tmp'
info_txt_dir = tmp_dir + '/info.txt'
file_list = glob.glob(file_desp)
if os.path.exists(tmp_dir):
    print(tmp_dir + " exists! Removing....")
    rmtree(tmp_dir) 
os.mkdir(tmp_dir)


def obtain_start_date(txt_dir):

    f = open(txt_dir, "r")
    start_date = "0"
    for x in f:
        substrs = x.split(": ")
        if (substrs[0] == 'Start Date'):
            start_date = substrs[1]
            start_date = start_date[:-1] # remove line break'
            return int(start_date)

    return int(start_date)


def GT3XfromTickToMillisecond(mydate):
    mydate = mydate - 621355968000000000
    mydate /= 10000000
    mydate = int(mydate)
    return datetime.utcfromtimestamp(mydate)

startTimes = []
endTimes = []
fileNames = []

for current_file in file_list:
    with zipfile.ZipFile(current_file, 'r') as zip_ref:
        zip_ref.extractall(tmp_dir)
    
    start_date = obtain_start_date(info_txt_dir)
    localDateTime = GT3XfromTickToMillisecond(start_date)
    endTime = localDateTime + timeshift
    startTime = localDateTime.strftime('%Y-%m-%dT%H:%M')
    endTime = endTime.strftime('%Y-%m-%dT%H:%M')
    fileName = current_file.split('/')[-1]
    
    fileNames.append(fileName)
    startTimes.append(startTime)
    endTimes.append(endTime)


if os.path.exists(endTimeFilePath):
    os.remove(endTimeFilePath)
    
with open(endTimeFilePath, mode='w') as csv_file:
    fieldnames = ['file_name', 'startTime', 'endTime']
    writer = csv.DictWriter(csv_file, fieldnames=fieldnames)
    writer.writeheader()

    for i in range(len(fileNames)):
        writer.writerow({'file_name': fileNames[i], 
                         'startTime': startTimes[i], 
                         'endTime': endTimes[i]})    


# # Modify command line script
def extract_file_name(command_str):
    file_path = command_str.split(' ')
    file_path = file_path[2]
    file_path = file_path[1:]
    file_path = file_path[:-1] # remove quotation marks

    return file_path.split("/")[-1]

# Input for this one should be the script paths and endTime table. 
# We will add the adaptive endTime to each file.
endTimeDf = pd.read_csv(endTimeFilePath)

f = open(script_dir, "r")
k = 0

if os.path.exists(dest_script_dir):
    os.remove(dest_script_dir)

with open(dest_script_dir, 'a') as dest_f:
    for x in f:
        my_file_name = extract_file_name(x)
        my_end_time = endTimeDf.loc[endTimeDf['file_name'] == my_file_name]['endTime'].item()
        x = x[:-1] # remove line break    
        x = x + ' --endTime ' + my_end_time + '\n'
        dest_f.write(x)
        
f.close()

