import glob
import pandas as pd
from datetime import datetime, timedelta

import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from pandas.plotting import register_matplotlib_converters
from matplotlib.patches import Rectangle
from matplotlib.lines import Line2D
import matplotlib.patches as patches
import os
import numpy as np

print("Hello!")
# helper functions
LABEL_COLORS = {
    0: "#f95a5d",
    1: "#fda354",
    2: "#8c9d43",
    3: "#1c93b7",
    4: "#887ea5",
    5: "#3a3547"
}

def merge_rows(sleep_df, current_label):
    sleep_df = sleep_df[sleep_df['sleep_stage']==current_label]
    startTimes = []
    endTimes = []
    current_stage = []
    currentStartTime = None
    preTime = None
    labels = []

    for index, row in sleep_df.iterrows():
        currentTime = row['time']
        if preTime == None:
            currentStartTime = currentTime
        else:
            if currentTime - preTime > timedelta(seconds=30):
                startTimes.append(currentStartTime)
                endTimes.append(preTime+timedelta(seconds=30))
                currentStartTime = currentTime
                labels.append(current_label)
        preTime = currentTime


    startTimes.append(currentStartTime)
    endTimes.append(preTime+timedelta(seconds=30))
    labels.append(current_label)

    stage_blocks = {
        'start_time': startTimes,
        'end_time': endTimes,
        'label': labels
    }
    stage_df = pd.DataFrame(stage_blocks)
    return stage_df

def parse_file_name(file_path):
    file_name = file_path.split('/')[-1]
    file_name = file_name[:-4] # remove .csv extension
    subjectID = file_name.split('_')[-1]
    file_date = file_name.split('_')[0]

    first_day = datetime.strptime(file_date, '%d%m%Y')

    if subjectID == '942099' or subjectID == '687006':
        # labels start on the same day:
        second_day = first_day
    else:
        second_day = first_day + timedelta(days=1)

    first_day_str = first_day.strftime('%d%m%Y')
    second_day_str = second_day.strftime('%d%m%Y')
    return first_day_str, second_day_str, subjectID

def xDate2yDate(xDate):
    year = xDate[:4]
    month = xDate[5:7]
    date = xDate[-2:]
    return date + month + year

def xName2yName(x_name, label_root):
    full_file_name = x_name.split('/')[-1]
    full_file_name = full_file_name[:-7]
    subject_id = full_file_name.split('_')[0]
    date_str = full_file_name.split('_')[-1]
    yDate = xDate2yDate(date_str)

    return subject_id, os.path.join(label_root, yDate + '_' + subject_id + '.csv')

def updateTimes(first_day_str, second_day_str, x_df, y_df):
    current_date = first_day_str

    newtimes = []
    isSecondDay = False
    preHour = -1
    for index, row in y_df.iterrows():
        hour = int(row['time'].split(':')[0])
        if isSecondDay == False and ((hour < preHour and hour != 12) or (hour == 12 and preHour < hour)):
            isSecondDay = True
            current_date = second_day_str
        row_time = datetime.strptime(current_date+' '+row['time'], '%d%m%Y %I:%M:%S %p')
        newtimes.append(row_time)
        preHour = hour
    y_df['time'] = newtimes
    x_df['time']=x_df['time'].apply(lambda x: x[:-27])
    x_df['time']=x_df['time'].apply(lambda x: datetime.strptime(x, '%Y-%m-%d %H:%M:%S'))
    # y_df = y_df.join(x_df.set_index('time'), on='time')
    return x_df, y_df


def create_col(num_sample):
    cols = []
    for i in range(num_sample):
        cols.append('x'+str(i))
    for i in range(num_sample):
        cols.append('y'+str(i))
    for i in range(num_sample):
        cols.append('z'+str(i))
    return cols


def merge_xy(x_df, y_df, pid):
    # should return x_df in the format of
    # Time x y z pid
    # Size: 900 * N * 4
    # y_df: Time sleep_stage
    # Size: N * 2

    features = []
    times = []
    sleep_stages = []
    num_samples = 900
    epoch_length_sec = 30

    x_filter = pd.Series(False, index=x_df.index)
    y_filter = pd.Series(False, index=y_df.index)
    x_df['pid'] = pid

    for i in range(len(y_df)):
        startTime = y_df.iloc[i]['time']
        endTime = startTime+timedelta(seconds=epoch_length_sec)
        current_df = (x_df['time'] >= startTime) & (x_df['time'] < endTime)

        if current_df.sum() == num_samples:
            x_filter = x_filter | current_df
            y_filter[i] = True

    final_X = x_df.loc[x_filter]
    final_Y = y_df.loc[y_filter]
    return final_X, final_Y

def extract_xyz(raw_epoch):
    # given a row of xyz
    # separate xyz sepatately

    x = raw_epoch[0::3]
    y = raw_epoch[1::3]
    z = raw_epoch[2::3]
    return x, y, z

destSleepPath = '/well/doherty/projects/raine/gen1_26/sleepLabelsClean/allSleepTime.csv'
sleepTimePath = '/well/doherty/projects/raine/gen1_26/sleepLabelsClean/sleepTime.csv'
sleepDf = pd.read_csv(sleepTimePath,  index_col=0)
data_dir = '/well/doherty/projects/raine/gen1_26/gt3x/wrist/sleepNov3/raw'
file_desp = data_dir + '/*.csv.gz'
epoch_files = glob.glob(file_desp)

def get_subjectID(file_path):
    path2file = file_path.split('/')[-1]
    path2file = path2file.split('_')[0]
    return path2file

# fix file names for having two recordings for the same subject at different dates
# only the ones with postfix 1 have labels
# 2 files do have valid acc but no PSG data
# x_file_one =  os.path.join(data_dir, '563679_wrist_1.csv.gz')
# x_file_two =  os.path.join(data_dir, '563679_wrist_2.csv.gz')
# x_file_new =  os.path.join(data_dir, '563679_wrist_2016-04-01.csv.gz')
# os.rename(x_file_one, x_file_new)
# os.remove(x_file_two)
#
#
# x_file_one =  os.path.join(data_dir, '953536_wrist_1.csv.gz')
# x_file_two =  os.path.join(data_dir, '953536_wrist_2.csv.gz')
# x_file_new =  os.path.join(data_dir, '953536_wrist_2016-04-01.csv.gz')
# os.rename(x_file_one, x_file_new)
# os.remove(x_file_two)

# get file names
root_dir = '/well/doherty/projects/raine/gen1_26/'
epoch_dir = os.path.join(root_dir, 'gt3x/wrist/sleepNov3/epoch')
raw_dir = os.path.join(root_dir, 'gt3x/wrist/sleepNov3/raw')
label_dir = os.path.join(root_dir, 'sleepLabelsClean')
image_dir = os.path.join(root_dir, 'imgs')
master_x_file_path = os.path.join(root_dir, 'gt3x/wrist/sleepNov3/master_raw_x.csv.gz')
master_y_file_path = os.path.join(root_dir, 'gt3x/wrist/sleepNov3/master_raw_y.csv.gz')
good_file_list = os.path.join(root_dir, 'gt3x/wrist/sleepNov3', 'good_file_list.csv')
file_desp = raw_dir + '/*csv.gz'
file_list = glob.glob(file_desp)

ok_file_list = pd.read_csv(good_file_list)
ok_file_list = ok_file_list['file_name']
ok_file_list = ok_file_list.apply(lambda x: get_subjectID(x))
ok_file_list = ok_file_list.astype(int)



import traceback

files_with_NA = []
labels_with_NA = []
acc_without_labels = []
isPlotting = True
master_DF = None
i = 0

import traceback

files_with_NA = []
labels_with_NA = []
acc_without_labels = []
isPlotting = True
master_DF = None
i = 0

for x_file_path in file_list:
    i += 1

    if i % 50 == 0:
        print('Processing %d ' % i)

    subject_id, y_file_path = xName2yName(x_file_path, label_dir)
    image_save_path = os.path.join(image_dir, subject_id + 'raw.png')
    if int(subject_id) in ok_file_list is False:
        print("not in")
        print(subject_id)
        continue

    try:
        # 2. We find their sleep labels and merge them with x, together with their age info and subject_id
        if os.path.isfile(y_file_path) is False:
            acc_without_labels.append(y_file_path)
            continue

        x_df = pd.read_csv(x_file_path)
        y_df = pd.read_csv(y_file_path)
        if subject_id == '585573':
            # fix for strange file
            y_df = pd.read_csv(y_file_path, header=None)
            y_df.columns = ['idx', 'time', 'sleep_stage', '3']
            y_df = y_df[['idx', 'time', 'sleep_stage']]
        else:
            y_df.reset_index(inplace=True)
            y_df.columns = ['idx', 'time', 'sleep_stage']
        y_df = y_df[y_df.sleep_stage != 'NS']
        y_df = y_df.dropna()

        first_day_str, second_day_str, subjectID = parse_file_name(y_file_path)

        # 2.2 we need to add time to the y labels
        x_df, y_df = updateTimes(first_day_str, second_day_str, x_df, y_df)
        y_df = y_df.reset_index()
        y_df = y_df.drop(columns=['idx', 'index'])

        x_df, y_df = merge_xy(x_df, y_df, subject_id)

        if y_df.isnull().values.any():
            files_with_NA.append(x_file_path)
            labels_with_NA.append(y_file_path)


        x_time = y_df['time']
        y_df['sleep_stage'] = y_df['sleep_stage'] .astype(int)
        if i == 1:
            master_y = y_df
            master_X = x_df
        else:
            master_y = pd.concat([master_y, y_df])
            master_X = pd.concat([master_X, x_df])

        if isPlotting and len(x_df) > 0:
            x_df = x_df.drop(columns=['time', 'pid'])
            x_np = x_df.to_numpy()
            good_shape = x_np.reshape([-1, 2700])

            x_mean = []
            y_mean = []
            z_mean = []
            for k in range(len(good_shape)):
                x, y, z = extract_xyz(good_shape[k])
                x_mean.append(np.mean(x))
                y_mean.append(np.mean(y))
                z_mean.append(np.mean(z))

            # needs to change plotting for raw actigrahm
            # also change the visu for plotting
            ## plotting
            fig,ax = plt.subplots(1,1,sharex=False, sharey=False, figsize=(18,12))
            ax.grid(True)
            ax.set_title('Participant = ' + str(subject_id), fontsize=16, fontweight='bold')
            #format x-axis
            ax.xaxis.set_major_locator(mdates.HourLocator())
            ax.xaxis.set_major_formatter(mdates.DateFormatter('%H'))
            ax.xaxis.set_minor_locator(mdates.HourLocator())
            ax.tick_params(axis='x', which='major', labelsize=20)

            ax.tick_params(axis='y', which='major', labelsize=20)
            ax.set_ylabel('Mean acceleration (mg)', fontsize=24, fontweight='bold')
            #format plot area
            ax.spines['right'].set_visible(False)
            ax.spines['top'].set_visible(False)
            ax.xaxis.set_ticks_position('bottom')
            ax.yaxis.set_ticks_position('left')
            ytick_locs = [1.0, 0, -1, -1.25, -1.75, -2.25, -2.75, -3.25]
            ylabels = [1.0, 0, -1.0, 'awake', 'N1', 'N2', 'N3', 'REM']
            plt.yticks(ytick_locs, ylabels)
            ax.plot(x_time, x_mean, color='black', label='x')
            ax.plot(x_time, y_mean, color='yellow', label='y')
            ax.plot(x_time, z_mean, color='blue', label='z')


            # OVERLAY LABELS
            legendPatches = []
            legendLabels = []
            label_height = 0.5
            label_y_start = -.5

            start = mdates.date2num(y_df['time'].min())
            end = mdates.date2num(y_df['time'].max())
            #ax.add_patch(Rectangle((start, -3.5), end-start, 2.5, color='grey', hatch='x'))

            label_locs = {
                0: -1.5,
                1: -2,
                2: -2.5,
                3: -3,
                5: -3.5
            }
            label_name = {
                0: 'awake',
                1: 'N1',
                2: 'N2',
                3: 'N3',
                5: 'REM'
            }
            for label in sorted(y_df['sleep_stage'].unique()):
                if label not in LABEL_COLORS.keys():
                    continue
                legendPatches += [patches.Patch(color=LABEL_COLORS[label], label=label)]
                legendLabels += [label_name[label]]

                stage_blocks_df = merge_rows(y_df, label)
                for ix, row in stage_blocks_df.iterrows():
                    start = mdates.date2num(pd.to_datetime(row['start_time']))
                    end = mdates.date2num(pd.to_datetime(row['end_time']))
                    duration = (row['end_time'] - row['start_time'])
                    if duration.total_seconds() < 10 * 3600: #make sure less than 10hrs
                        ax.add_patch(Rectangle((start, label_locs[label]), end-start, label_height, color=LABEL_COLORS[label]))
            # print legend
            # ax.legend(legendPatches, legendLabels, fontsize=24)
            plt.savefig(image_save_path)
            # plt.show()
            plt.close()
    except Exception as e:
        print(e)
        print(traceback.format_exc())
        print("File not working " + x_file_path)

master_y.to_csv(master_y_file_path, compression='infer')
master_X.to_csv(master_x_file_path, compression='infer')



