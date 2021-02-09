"""Script to plot accelerometer traces."""

import matplotlib
matplotlib.use('Agg')
from accelerometer import accUtils
import argparse
from datetime import datetime, timedelta, time
import matplotlib.pyplot as plt
import matplotlib.lines as mlines
import matplotlib.patches as mpatches
import matplotlib.dates as dates

import numpy as np
import pandas as pd
import sys

# http://pandas-docs.github.io/pandas-docs-travis/whatsnew/v0.21.1.html#restore-matplotlib-datetime-converter-registration
from pandas.plotting import register_matplotlib_converters
register_matplotlib_converters()

DOHERTY_NatComms_COLOURS = {'sleep':'blue', 'sedentary':'red',
    'tasks-light':'darkorange', 'walking':'lightgreen', 'moderate':'green'}

WILLETS_SciReports_COLOURS = {'sleep':'blue', 'sit.stand':'red',
    'vehicle':'darkorange', 'walking':'lightgreen', 'mixed':'green',
    'bicycling':'purple'}

WALMSLEY_Nov2020_COLOURS = {'sleep':'blue', 'sedentary':'red',
    'light':'green', 'MVPA':'green'}


def main():
    """
    Application entry point responsible for parsing command line requests
    """

    parser = argparse.ArgumentParser(
        description="A script to plot acc time series data.", add_help=True)
    # required
    parser.add_argument('timeSeriesFile', metavar='input file', type=str,
                            help="input .csv.gz time series file to plot")
    parser.add_argument('plotFile', metavar='output file', type=str,
                            help="output .png file to plot to")
    parser.add_argument('--activityModel', type=str,
                            default="activityModels/walmsley-nov20.tar",
                            help="""trained activity model .tar file""")
    parser.add_argument('--useRecommendedImputation',
                            metavar='True/False', default=True, type=str2bool,
                            help="""Highly recommended method to show imputed
                            missing data (default : %(default)s)""")
    parser.add_argument('--imputedLabels',
                            metavar='True/False', default=False, type=str2bool,
                            help="""If activity classification during imputed
                            period will be displayed (default : %(default)s)""")
    parser.add_argument('--imputedLabelsHeight',
                            metavar='Proportion i.e. 0-1.0', default=0.9,
                            type=float, help="""Proportion of plot labels take
                            if activity classification during imputed
                            period will be displayed (default : %(default)s)""")
    parser.add_argument('--sleepDiary', default="", type=str)

    # check input is ok
    if len(sys.argv) < 3:
        msg = "\nInvalid input, please enter at least 2 parameters, e.g."
        msg += "\npython accPlot.py timeSeries.csv.gz plot.png \n"
        accUtils.toScreen(msg)
        parser.print_help()
        sys.exit(-1)
    args = parser.parse_args()

    # and then call plot function
    plotTimeSeries(args.timeSeriesFile, args.plotFile,
        activityModel=args.activityModel,
        useRecommendedImputation=args.useRecommendedImputation,
        imputedLabels=args.imputedLabels,
        diary=args.sleepDiary,
        imputedLabelsHeight=args.imputedLabelsHeight)



def plotTimeSeries(
        tsFile,
        plotFile,
        activityModel="activityModels/walmsley-nov20.tar",
        useRecommendedImputation=True,
        imputedLabels=False,
        diary="",
        imputedLabelsHeight=0.9):
    """Plot overall activity and classified activity types

    :param str tsFile: Input filename with .csv.gz time series data
    :param str tsFile: Output filename for .png image
    :param str activityModel: Input tar model file used for activity classification
    :param bool useRecommendedImputation: Highly recommended method to show
        imputed values for missing data
    :param bool imputedLabels: If activity classification during imputed period
        will be displayed
    :param float imputedLabelsHeight: Proportion of plot labels take up if
        <imputedLabels> is True

    :return: Writes plot to <plotFile>
    :rtype: void

    :Example:
    >>> import accPlot
    >>> accPlot.plotTimeSeries("sample-timeSeries.csv.gz", "sample-plot.png")
    <plot file written to sample-plot.png>
    """

    # read time series file to pandas DataFrame
    d = pd.read_csv(
        tsFile, index_col='time',
        parse_dates=['time'], date_parser=accUtils.date_parser
    )
    diary_df = ""
    if diary != "":
        diary_tz = 'Europe/London'
        diary_df = pd.read_csv(diary)
        diary_df['Time_in_bed'] = pd.to_datetime(diary_df['Time_in_bed'])
        diary_df['Time_in_bed'] = diary_df['Time_in_bed'].dt.tz_localize(diary_tz)
        diary_df['Time_out_of_bed'] = pd.to_datetime(diary_df['Time_out_of_bed'])
        diary_df['Time_out_of_bed'] = diary_df['Time_out_of_bed'].dt.tz_localize(diary_tz)
        in_markers = diary_df['Time_in_bed']
        in_markers = in_markers.sort_values()
        in_markers = in_markers.to_numpy()

        out_markers = diary_df['Time_out_of_bed']
        out_markers = out_markers.sort_values()
        out_markers = out_markers.to_numpy()

    d['acc'] = d['acc'].rolling(window=12, min_periods=1).mean() # smoothing
    d['time'] = d.index
    ymin = d['acc'].min()
    ymax = d['acc'].max()

    # infer labels
    labels = []
    for col in d.columns.tolist():
        if col not in [accUtils.TIME_SERIES_COL, 'imputed', 'acc', 'MET']:
            labels += [col]
    print(labels)
    if 'walmsley' in activityModel:
        labels_as_col = WALMSLEY_Nov2020_COLOURS
    elif 'doherty' in activityModel:
        labels_as_col = DOHERTY_NatComms_COLOURS
    elif 'willetts' in activityModel:
        labels_as_col = WILLETS_SciReports_COLOURS
    # add imputation label colour
    labels_as_col['imputed'] = '#fafc6f'

    convert_date = np.vectorize(lambda day, x: matplotlib.dates.date2num(datetime.combine(day, x)))

    # number of rows to display in figure (all days + legend)
    d['new_date'] = (d.index - timedelta(days=0.5)).date
    d['new_time'] = (d.index - timedelta(days=0.5))

    if not useRecommendedImputation:
        d = d[d['imputed']==0] # if requested, do not show imputed values

    if imputedLabels:
        labelsPosition = imputedLabelsHeight
    else:
        labelsPosition = 1

    groupedDays = d[['acc','time','imputed', 'new_time'] + labels].groupby(by=d['new_date'])
    nrows = len(groupedDays) + 1

    # create overall figure
    fig = plt.figure(1, figsize=(10,nrows), dpi=100)
    fig.canvas.set_window_title(tsFile)

    # create individual plot for each day
    i = 0
    j = 0 # in idx
    k = 0 # out idx
    ax_list = []
    for day, group in groupedDays:
        # set start and end to zero to avoid diagonal fill boxes
        group['imputed'].values[0] = 0
        group['imputed'].values[-1] = 0

        # retrieve time series data for this day
        mytime = group['time'].tolist()
        timeSeries = dates.date2num(mytime)

    # and then plot time series data for this day
        plt.subplot(nrows, 1, i+1)
        plt.plot(timeSeries, group['acc'], c='k')
        if imputedLabels:
            plt.fill_between(timeSeries,
                y1 = np.multiply(group['imputed'], ymax),
                y2 = np.multiply(group['imputed'], ymax * labelsPosition),
                color = labels_as_col['imputed'], alpha=1.0,
                where=group['imputed']==1)
        else:
            plt.fill(timeSeries, np.multiply(group['imputed'], ymax),
            labels_as_col['imputed'], alpha=1.0)

        # change display properties of this subplot
        ax = plt.gca()
        if len(labels)>0:
            ax.stackplot(timeSeries,
                [np.multiply(group[l], ymax * labelsPosition) for l in labels],
                colors=[labels_as_col[l] for l in labels],
                alpha=0.5, edgecolor="none")
        # add date label to left hand side of each day's activity plot
        nextday = day+timedelta(days=1)
        plt.title(
            day.strftime("%a,%d")+'-'+nextday.strftime("%a,%d\n%b"), weight='bold',
            x=-.2, y=0.5,
            horizontalalignment='left',
            verticalalignment='center',
            rotation='horizontal',
            transform=ax.transAxes,
            fontsize='medium',
            color='k'
        )
        # run gridlines for each hour bar
        ax.get_xaxis().grid(True, which='major', color='grey', alpha=0.5)
        ax.get_xaxis().grid(True, which='minor', color='grey', alpha=0.25)
        # set x and y-axes
        ax.set_xlim((datetime.combine(day,time(12, 0, 0, 0)),
            datetime.combine(day+timedelta(days=1), time(12, 0, 0, 0))))
        ax.set_xticks(pd.date_range(start=datetime.combine(day,time(12, 0, 0, 0)),
            end=datetime.combine(day+timedelta(days=1), time(12, 0, 0, 0)),
            freq='4H'))
        ax.set_xticks(pd.date_range(start=datetime.combine(day,time(12, 0, 0, 0)),
            end=datetime.combine(day+timedelta(days=1), time(12, 0, 0, 0)),
            freq='1H'), minor=True)
        ax.set_ylim((ymin, ymax))
        ax.get_yaxis().set_ticks([]) # hide y-axis lables
        # make border less harsh between subplots
        ax.spines['top'].set_color('#d3d3d3') # lightgray
        ax.spines['right'].set_visible(False)
        ax.spines['left'].set_visible(False)
        # set background colour to lightgray
        ax.set_facecolor('#d3d3d3')

        # add sleep diary marker if present
        if diary != "":
            x = []
            y_I = []
            y_II = []
            while j < len(in_markers) and (in_markers[j]-timedelta(days=0.5)).day == day.day:
                y_I.append(ymax)
                y_II.append(ymin)
                x.append(in_markers[j])
                j += 1
            ax.plot(x,y_I, 'vm', markersize=10, zorder=10, clip_on=False)
            ax.plot(x,y_II, '^m', markersize=10, zorder=10, clip_on=False)

            x = []
            y_I = []
            y_II = []
            while k < len(out_markers) and (out_markers[k]-timedelta(days=0.5)).day == day.day:
                y_I.append(ymax)
                y_II.append(ymin)
                x.append(out_markers[k])
                k += 1
            ax.plot(x,y_I, 'vc', markersize=10, zorder=10, clip_on=False)
            ax.plot(x,y_II, '^c', markersize=10, zorder=10, clip_on=False)

        # append to list and incrament list counter
        ax_list.append(ax)
        i += 1

    # create new subplot to display legend
    plt.subplot(nrows, 1, i+1)
    ax = plt.gca()
    ax.axis('off') # don't display axis information
    # create a 'patch' for each legend entry
    legend_patches = [mpatches.Patch(color=labels_as_col['imputed'],
                                     label='not recorded', alpha=1.0),
                      mlines.Line2D([],[],color='k',label='movement'),
                      mlines.Line2D([],[], marker='^',linestyle='None',color='m',label='time to bed'),
                      mlines.Line2D([],[], marker='^',linestyle='None',color='c',label='time out of bed')]
    # create lengend entry for each label
    ucl_labels = {
        'sleep': 'possible sleep',
        'imputed': 'not recorded',
        'acceleration': 'movement',
        'MVPA': 'moving a lot',
        "sedentary": 'not moving a lot'

    }
    for label in labels:
        col = labels_as_col[label]
        if label == 'light':
            continue
        legend_patches.append(mpatches.Patch(color=col, label=ucl_labels[label], alpha=0.5))
    # create overall legend
    plt.legend(handles=legend_patches, bbox_to_anchor=(0., 0., 1., 1.),
        loc='center', ncol=min(4,len(legend_patches)), mode="best",
        borderaxespad=0, framealpha=0.6, frameon=True, fancybox=True)

    # remove legend border
    ax.spines['left'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.spines['top'].set_visible(False)
    ax.spines['bottom'].set_visible(False)
    ax_list.append(ax)

    # format x-axis to show hours
    plt.gcf().autofmt_xdate()
    # add hour labels to top of plot
    hours2Display = range(0, 24, 4)
    hrLabels = ['00:00', '04:00', '08:00', '12:00', '16:00', '20:00', '24:00']
    hrLabels = ['12:00 PM', '04:00PM', '08:00PM', '12:00AM', '04:00AM', '08:00AM', '12:00PM']
    ax_list[0].set_xticklabels(hrLabels)
    ax_list[0].tick_params(labelbottom=False, labeltop=True, labelleft=False)

    plt.savefig(plotFile, dpi=200, bbox_inches='tight')
    print('Plot file written to:', plotFile)


def str2bool(v):
    """
    Used to parse true/false values from the command line. E.g. "True" -> True
    """

    return v.lower() in ("yes", "true", "t", "1")


if __name__ == '__main__':
    main()  # Standard boilerplate to call the main() function to begin the program.
