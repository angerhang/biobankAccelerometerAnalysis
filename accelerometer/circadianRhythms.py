"""Module to support calculation of metrics of circadian rhythm from acc data"""

import gzip
import numpy as np
import pandas as pd
import pytz
import sys
import scipy as sp
from scipy import fftpack
from datetime import timedelta
import datetime

# to compute average time
from cmath import rect, phase
from math import radians, degrees


def calculatePSD(e, epochPeriod, fourierWithAcc, labels, summary):
    """Calculate the power spectral density from fourier analysis of a 1 day frequency
    
    :param pandas.DataFrame e: Pandas dataframe of epoch data
    :param int epochPeriod: Size of epoch time window (in seconds)
    :param bool fourierWithAcc:True calculates fourier done with acceleration data instead of sleep data
    :param list(str) labels: Activity state labels
    :param dict summary: Output dictionary containing all summary metrics

    :return: Write dict <summary> keys 'PSD-<W/Hz>'
    """
    if fourierWithAcc:
        y = e['accImputed'].values
    else:
        cols = [label+'Imputed' for label in labels]  # 'sleepImputed', 'sedentaryImputed', etc...
        y = e[cols].idxmax(axis=1) == 'sleepImputed'  # is sleepImputed highest?
        y = y.values.astype('int')  # e.g. [0,0,0,1,1,0,0,1,...]
        y = 2 * y - 1  # center the signal, [0,1] -> [-1,1]
        
    n = len(y)
    k = len(y)*epochPeriod/(60*60*24)
    a = -2.j * np.pi * k * np.arange(n) / n
    # Find the power spectral density for a one day cycle using fourier analysis 
    res = np.sum(np.exp(a) * y) / n
    PSD = np.abs(res)**2
    summary['PSD'] = PSD



def calculateFourierFreq(e, epochPeriod, fourierWithAcc, labels, summary):
    """Calculate the most prevalent frequency in a fourier analysis 
    
    :param pandas.DataFrame e: Pandas dataframe of epoch data
    :param int epochPeriod: Size of epoch time window (in seconds)
    :paran bool fourierWithAcc: True calculates fourier done with acceleration data instead of sleep data
    :param list(str) labels: Activity state labels
    :param dict summary: Output dictionary containing all summary metrics

    :return: Write dict <summary> keys 'fourier frequency-<1/days>'
    """
    if fourierWithAcc:
        y = e['accImputed'].values
    else:
        cols = [label+'Imputed' for label in labels]  # 'sleepImputed', 'sedentaryImputed', etc...
        y = e[cols].idxmax(axis=1) == 'sleepImputed'  # is sleepImputed highest?
        y = y.values.astype('int')  # e.g. [0,0,0,1,1,0,0,1,...]
        y = 2 * y - 1  # center the signal, [0,1] -> [-1,1]
        
    # Fast fourier transform of the sleep column 
    fft_y = np.abs(fftpack.fft(y))
    
    i =  np.arange(1,len(fft_y)) 
    k_max = np.argmax(fft_y[i]) + 1
    n = len(y)
    # Maximise the fourier transform function (func) using the fft_y as a first esitmate 
    func = lambda k: -np.abs(np.sum(np.exp(-2.j * np.pi * k * np.arange(n) / n) * y) / n)
    res = sp.optimize.minimize_scalar(func, bracket=(k_max-1,k_max+1)) 
    # Adjust the frequency to have the units 1/days
    freq_mx = float(res.x)/(len(y)*epochPeriod/(60*60*24))
    summary['fourier-frequency'] = freq_mx


def mean_angle(deg):
    return degrees(phase(sum(rect(1, radians(d)) for d in deg)/len(deg)))


def mean_time(times):
    """Compute the radian average of times in a format of HH:MM:SS.
    A simple average won't work for timestamps for instance, the
    mean between 23:00:00, 01:00:00 would be far from 00:00:00.

    See https://stackoverflow.com/questions/12033905/using-python-to-create-an-average-out-of-a-list-of-times?answertab=votes#tab-top
    for more info.

    :param times: a list of times
    :return: the mean time in str
    """

    t = (time.split(':') for time in times)
    seconds = ((float(s) + int(m) * 60 + int(h) * 3600)
               for h, m, s in t)
    day = 24 * 60 * 60
    to_angles = [s * 360. / day for s in seconds]
    mean_as_angle = mean_angle(to_angles)
    mean_seconds = mean_as_angle * day / 360.
    if mean_seconds < 0:
        mean_seconds += day
    h, m = divmod(mean_seconds, 3600)
    m, s = divmod(m, 60)
    return '%02i:%02i:%02i' % (h, m, s)


def min2hour(time):
    h = time//60
    m = (time-h*60)
    return '%02i:%02i:00' % (h, m)


def calculatISIV(e, summary):
    """  IS and IV are computed using hourly means according to the link below
    https://www.ncbi.nlm.nih.gov/pmc/articles/PMC4890079/

    :param pandas.DataFrame e: Pandas dataframe of epoch data
    :param int epochPeriod: Size of epoch time window (in seconds)
    :param dict summary: Output dictionary containing all summary metrics

    :return: Write dict <summary> keys 'IS', 'IV'
    """
    N = (e.index[-1] - e.index[0]).seconds//3600
    X_bar = np.mean(e['accImputed'])  # grand mean
    P = 24
    time_format = "%H:%M"

    mean_hourly_rate = []
    base_time = datetime.datetime(2020, 1, 1)
    for i in range(P):
        start_time = base_time+timedelta(hours=i)
        end_time = base_time+timedelta(hours=i+1)

        this_hour = e.between_time(start_time.strftime(time_format), end_time.strftime(time_format))
        mean_hourly_rate.append(np.mean(this_hour['accImputed']))

    mean_hourly_rate = np.array(mean_hourly_rate)
    mean_hourly_rate = mean_hourly_rate - X_bar
    var_daily = np.sum(np.square(mean_hourly_rate))*N

    start_time = e.index[0]
    final_time = e.index[-1]
    total_var = 0
    k = 0
    pre_x_i = -1
    total_hour_diff = 0
    while start_time <= final_time:
        end_time = start_time+timedelta(hours=1)
        this_hour = e.between_time(start_time.strftime(time_format), end_time.strftime(time_format))
        x_i = np.mean(this_hour['accImputed'])
        total_var += (x_i-X_bar)**2
        if k > 0:
            total_hour_diff += (x_i-pre_x_i)**2*N
        k += 1
        pre_x_i = x_i
        start_time = end_time
    summary['circadianRhythms_IS'] = var_daily/(total_var*P)
    summary['circadianRhythms_IV'] = total_hour_diff/(total_hour_diff*(N-1))


def calculateM10L5(e, epochPeriod, summary):
    """Calculates the M10 L5 relative amplitude from the average acceleration from
    the ten most active hours and 5 least most active hours 
    
    :param pandas.DataFrame e: Pandas dataframe of epoch data
    :param int epochPeriod: Size of epoch time window (in seconds)
    :param dict summary: Output dictionary containing all summary metrics

    :return: Write dict <summary> keys 'M10 L5-<rel amp>', 'M10, L5 onset and average'
    """
    TEN_HOURS = int(10*60*60/epochPeriod)
    FIVE_HOURS = int(5*60*60/epochPeriod)
    num_days = (e.index[-1] - e.index[0]).days+1  # add the last day
           
    days_split = []
    for n in range(num_days+1):
        # creates a new list which is used to identify the 24 hour periods in the data frame
        days_split += [n for x in e.index if (e.index[0] + timedelta(days=n)).date() == x.date()]
    day_start_idx = np.where(np.roll(days_split, 1) != days_split)[0]

    dct = {}
    for i in range(num_days+1):
        # create new lists with the acceleration data from each 24 hour period
        dct['day_%s' %i] = [e.loc[:,'accImputed'][n] for n in range(len(days_split)) if days_split[n]==i]    
    dct_10 = {}
    dct_5 = {}

    for i in dct:
        #  sums each 10 or 5 hour window with steps of 30s for each day
        dct_10['%s' % i] = [sum(dct['%s' % i][j:j+TEN_HOURS]) for j in range(len(dct['%s' % i])-TEN_HOURS)]
        dct_5['%s' % i] = [sum(dct['%s' % i][j:j+FIVE_HOURS]) for j in range(len(dct['%s' % i])-FIVE_HOURS)]
    avg_10 = {}
    m10_onsets = []
    avg_5 = {}
    l5_onsets = []

    # Average acceleration (for each 30s) for the max and min windows
    k = 0
    for i in dct:
        m10_day_list = dct_10['%s' % i]
        max_idx = np.argmax(m10_day_list) + day_start_idx[k]
        m10_onsets.append(e.index[max_idx])
        avg_10['%s' % i] = (np.max(m10_day_list))/TEN_HOURS

        l5_day_list = dct_5['%s' % i]
        max_idx = np.argmin(l5_day_list) + day_start_idx[k]
        l5_onsets.append(e.index[max_idx])
        avg_5['%s' % i] = (np.min(l5_day_list))/FIVE_HOURS
        k += 1

    if num_days > 0:
        m10 = sum(avg_10.values())/len(dct_10)
        l5 = sum(avg_5.values())/len(dct_5)
        rel_amp = (m10-l5)/(m10+l5)
    else:
        rel_amp = 'NA_too_few_days'

    l5_onsets = [min2hour(onset.hour*60 + onset.minute) for onset in l5_onsets]
    m10_onsets = [min2hour(onset.hour*60 + onset.minute) for onset in m10_onsets]

    summary['circadianRhythms_M10L5_Rel_AMP'] = rel_amp
    summary['circadianRhythms_M10AVG'] = m10
    summary['circadianRhythms_L5AVG'] = l5
    summary['circadianRhythms_M10_Onset'] = mean_time(m10_onsets)
    summary['circadianRhythms_L5_Onset'] = mean_time(l5_onsets)
