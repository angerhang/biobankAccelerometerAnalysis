import pandas as pd
import numpy as np
import random
import time
import argparse
random.seed(time.time())


parser = argparse.ArgumentParser(
    description="""A tool to extract physical activity information from
            raw accelerometer files.""", add_help=True
)
# required
parser.add_argument('--raw_file_path',
                    type=str, help="""The pandas DF contains a path list to
                    all the files that should be extracted""")
parser.add_argument('--result_path',
                    type=str, help="""Where the result npz should be stored""")
parser.add_argument('--time_path',
                    type=str, help="""Where the time npz should be stored""")
args = parser.parse_args()


def extract(raw_file_path, result_path, time_path):
    print("Processing ", raw_file_path)
    epochDF = pd.read_csv(raw_file_path)
    epochDF['date'] = epochDF['time'].str[:19]
    epochDF['date'] = pd.to_datetime(epochDF['date'])
    epochDF['date'] = epochDF['date'].dt.date

    # select a random day
    date_list = np.unique(epochDF['date'])
    date_list = date_list[1:-2]  # excluding and first and the last day
    date_choice = random.choice(date_list)
    result_df = epochDF[epochDF['date'] == date_choice]
    ref_length = 30*60*60*24
    i = 0
    while len(result_df) != ref_length and i < 3:
        date_choice = random.choice(date_list)
        result_df = epochDF[epochDF['date'] == date_choice]
        i += 1
    result_df = result_df[['time', 'x', 'y', 'z']]

    test_np = result_df[['x', 'y', 'z']].to_numpy()
    times = result_df[['time']].to_numpy()
    times = times[::900]

    x = test_np[:, 0]
    y = test_np[:, 1]
    z = test_np[:, 2]
    new_x = x.reshape(-1, 1, 900)
    new_y = y.reshape(-1, 1, 900)
    new_z = z.reshape(-1, 1, 900)
    trans_data = np.concatenate((new_x, new_y, new_z), 1)
    with open(result_path, 'wb') as f:
        np.save(f, trans_data)
    with open(time_path, 'wb') as f:
        np.save(f, times)
    # result_df.to_csv(result_path, index=False)
    print("Written to ", result_path)
    print("Written to ", time_path)


if __name__ == '__main__':
    extract(args.raw_file_path, args.result_path, args.time_path)