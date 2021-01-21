#!/bin/bash
# ------------------------------------------------------------------
# [Aiden Doherty] Download sample data and activity models
# ------------------------------------------------------------------

downloadDir="http://gas.ndph.ox.ac.uk/aidend/accModels/"
# download sample data file
if ! [ -f "data/sample.cwa.gz" ]
then
    curl -L ${downloadDir}sample.cwa.gz -o data/sample.cwa.gz
fi

# delete and newly download activity model files
curl -L ${downloadDir}doherty-may20.tar --output activityModels/doherty-may20.tar
curl -L ${downloadDir}willetts-may20.tar --output activityModels/willetts-may20.tar
curl -L ${downloadDir}old-walmsley-nov20.tar --output activityModels/walmsley-nov20.tar

# download sample training file
#if ! [ -f "activityModels/labelled-acc-epochs.csv" ]
#then
#    wget ${downloadDir}labelled-acc-epochs.csv -P activityModels/
#fi