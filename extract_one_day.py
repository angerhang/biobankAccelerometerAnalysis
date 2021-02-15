# 1. path to data
import pandas as pd
import numpy as np
import random
import time
import argparse
import os
random.seed(time.time())

parser = argparse.ArgumentParser(
    description="""A tool to extract physical activity information from
            raw accelerometer files.""", add_help=True
)
# required
parser.add_argument('--file_list',
                    type=str, help="""The pandas DF contains a path list to
                    all the files that should be extracted""")
parser.add_argument('--raw_dir',
                    type=str, help="""Where the raw file is stored""")
parser.add_argument('--result_dir',
                    type=str, help="""Where the result csv should be stored""")
parser.add_argument('--cmdFile',
                    type=str, help="""The command line file""")
args = parser.parse_args()


def main():
    file_list_df = pd.read_csv(args.file_list)
    file_list = file_list_df['file_name'].to_numpy()
    cmdFile = args.cmdFile

    with open(cmdFile, 'w') as f:
        for file_path in file_list:
            file_name = file_path.split('/')[-1][:-7]
            file_name = file_name + '.csv.gz'
            path2load = os.path.join(args.raw_dir, file_name)

            cmd = [
                'python3 ss_extraction.py',
                '--raw_file_path "{:s}"'.format(path2load),
                '--result_path "{:s}"'.format(os.path.join(args.result_dir, file_name))
            ]

            cmd = ' '.join(cmd)
            f.write(cmd)
            f.write('\n')

    print('Processing list written to ', cmdFile)

if __name__ == '__main__':
    main()  # Standard boilerplate to call the main() function to begin the program.
