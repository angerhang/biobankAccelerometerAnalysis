#!/bin/bash

#$ -j y
#$ -P doherty.prjc -q short.qc
#$ -N Merge-labels_new_version
#$ -cwd
#$ -pe shmem 5

echo "------------------------------------------------"
echo "Run on host: "`hostname`
echo "Operating system: "`uname -s`
echo "Username: "`whoami`
echo "Started at: "`date`
echo "------------------------------------------------"

module load Python/3.7.2-GCCcore-8.2.0
source ~/.bashrc
conda activate raine_parsing
# source /well/doherty/users/cxx579/venv/bin/activate

python merge_label_raw.py
# python /well/doherty/users/cxx579/test_process/myBBAA/merge_label_raw.py

echo "------------------------------------------------"
echo "Done at: "`date`
echo "------------------------------------------------"
