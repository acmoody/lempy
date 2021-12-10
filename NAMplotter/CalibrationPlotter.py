# -*- coding: utf-8 -*-
"""
Ever evolving calibration results plotter for NAM rainfall runoff results

Created on Wed Aug 18

@author: AMoody
"""
# Standard pacakges
import os
import sys
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
# DHI packages
from mikeio import Dfs0


# VVVVVVVVVVVVVVVVVVVVVVVVVVV SET YOUR PATH TO DROPBOX HERE
dropbox_dir = r"D:\Dropbox\Dropbox\LRBM"  #TODO

#VVVVVVVVVVVVVVVVVVVVVVV Set your working directory here.
wd = r"D:\Lemhi\NAM\AgencyAggCal"  #TODO

os.chdir(wd)

# Custom scripts. Change this directory to a working diretory with objectivefunctions.py
# sys.path.append(r'D:\code\utils')
from objectivefunctions import calculate_all_functions

# Matplotlib plot style options
plt.style.use(['fivethirtyeight','seaborn-talk','seaborn-ticks'])
plt.rcParams.update({'lines.linewidth':1.2})

#%% Define some helper functions
def COM(s):
    """Calculate Center of Mass and return date"""
    return ((np.cumsum(s)/np.sum(s))>0.5).idxmax().date()

def calcPercentDiff(MET,NAM):
    """Calculate percent different of each row between two series"""
    res = []
    for i,s in MET.iteritems():
        spd = pd.concat([s,NAM],1).apply(lambda x:(x[1]-x[0])/x[0],axis=1)
        spd.name = i
        res.append(spd)
    return pd.concat(res,1)

def wateryear(index):
    if isinstance(index,pd.DatetimeIndex):
        return (index + pd.DateOffset(months=3)).year
    else:
        print('Index object is not a pandas datetime index')

#%% Observed discharge name as it appears in the NAM input dfs0
nam_name = "Agency_cms"  #TODO

# Catchment name as it appears in the file ET_METRIC_AllCatchments.csv in dropbox
catchment_name = "Agency_Upper" #TODO
#%% DIRECTORIES
# Directory for retrieving observed flows
datadir = os.path.join(dropbox_dir,r"Cal Agency Agg\ContractedGages2021.dfs0")

# METRIC ETa for comparison
etafile=os.path.join(dropbox_dir,r"NAM Data\LRBM NAM Inputs 2021v3.xlsx")

# NAM Results File directory
NAMresults = os.path.join(wd,r"AgencyCal2.mhydro - Result Files\RainfallRunoff_Agency_AddNAM.dfs0")

# Calibration File
mhydro_file = os.path.join(wd,r"AgencyCal2.mhydro")

# Potential ET input dfs0
pet_file = os.path.join(dropbox_dir,r"Cal Agency Agg\PET.dfs0")

#%% Read in METRIC ET from Ryan Warden
ETa=pd.read_excel(etafile,sheet_name="ETa METRIC (in)",engine='openpyxl',header=None,skiprows=2,
              usecols="A,CI",index_col=0)
ETa=ETa.mean(1).dropna().mul(25.4).rename('METRIC-Warden')

#%% Read input PET
dfs = Dfs0(pet_file)
PET = dfs.to_dataframe()
#%% Open mhydro file and read in parameter string
with open(mhydro_file,'r') as f:
    lineno = 0
    while lineno < 1764:
        f.readline()
        lineno +=1
    param_string = f.readline()
    param_list = param_string.split(':')[1].split('>')[0].split(',')
# Read observed flow and NAM results
dfs0_obs = Dfs0(datadir)
dfobs = dfs0_obs.to_dataframe()
# print(dfobs.head())

# Read in model results
dfs0_res = Dfs0(NAMresults)
dfres = dfs0_res.to_dataframe()
# print(dfres.head())

# Group by Catchment. Catchment string is the last three places in the column name
# If you have run multiple dummy catchments with different parameter sets,
# this would make as many groups as you have catchments.
gb = dfres.groupby(dfres.columns.str[-3:],axis=1)

# Empty list for objective function results
metrics_l = []

# Loop through each catchment, plot results
for group, df in gb:
    # Clean item/column names
    df.columns = df.columns.str.replace(' ; '+ group,'')

    # Subset NAM results and combine with observed flow. For plotting
    data=pd.concat([dfobs[nam_name],
                    df[['TotalRunOff', 'OverlandFlow', 'InterFlow',
                        'BaseFlow']]],1).dropna(how='all')

    # Calculate center of mass for discharges
    com_mod=data['TotalRunOff'].dropna().groupby(wateryear(data['TotalRunOff'].dropna().index)).apply(COM)
    com_obs=data[nam_name].dropna().groupby(wateryear(data[nam_name].dropna().index)).apply(COM)
    # Subset results and observed. For model metrics
    X = pd.concat([dfobs[nam_name],df['TotalRunOff']],1).dropna()
    # print(X.head())

    # Calculate metrics, rename with catchment name, and add to metric list
    metrics = pd.Series(dict(calculate_all_functions(X.iloc[:,0],X.iloc[:,1]))).round(2);
    metrics.name='metrics_'+group
    metrics = metrics.drop(['decomposed_mse','kge','log_p','pbias','rsr'])
    metrics_l.append(metrics)

    # -------------------------
    # Initiatilize figure
    fig=plt.figure()

    # Initiate GridSpec of 3 rows, 1 col(allows subplots to be different sizes)
    gs=plt.GridSpec(3,1)
    # Add axis to row 1, all columns (trivial here, it's just one column)
    ax1=fig.add_subplot(gs[0,:])

    # Add axis to rows 2,3
    ax2 = fig.add_subplot(gs[1:,:])
    #Plot precip in first axis
    pcp = df['ActualRainfall'].mul(1000*86400).plot(ax=ax1,ds='steps')
    ax1.invert_yaxis()
    ax1.set_xticklabels('')
    ax1.set_ylabel('P (mm)',size='small')
    # -------------------------
    # Plot Actual ET
    ax1b = ax1.twinx()
    df['ActualEvaporation'].mul(86400*1000).plot(ax=ax1b,color='slategrey',label='NAM ETa')
    #METRIC
    ETa.plot(ax=ax1b,color='olive',label='METRIC ETa')
    ax1b.legend(frameon=True)
    ax1b.set_ylabel('ET (mm)',size='small')
    ax1.sharex(ax2) # X axes share same values. Aligns times

    # -------------------------
    # Plot Modeled and Observed Q
    # Area plot of columns 5,4,and 3 (python is 0-based indexing).
    # These columns are baseflow,interflow, and overland flow
    data.iloc[:,[4,3,2]].plot(kind='area',stacked=True,ax=ax2)
    # Plot observations
    ax2.plot(data[nam_name],c='k',label='Obs')

    # Plot Center of mass
    ax2.vlines(com_mod.values,*ax2.get_ylim(),color='k',linestyle='dashdot',label='Sim. COM')
    ax2.vlines(com_obs.values,*ax2.get_ylim(),color='k',linestyle='dotted',label='Obs. COM')
    # Zoom to modeled period
    ax2.set_xlim((mdates.date2num(df.first_valid_index()),
                  mdates.date2num(df.last_valid_index())))
    ax2.legend(ncol=2,frameon=True)

    info_str = \
        f"NS = {metrics.nashsutcliffe}\n" \
        f"Vol. Err = {metrics.volume_error}\n"\
        f"Avg. COM diff. = {(com_obs - com_mod).dropna().mean().days} days"

    ax2.text(0.45,0.8, info_str,transform=ax2.transAxes)
    ax2.set_ylabel('Q (cms)',size='small')
    # Format figure margins
    fig.tight_layout()
    fig.subplots_adjust(hspace=0)
    # fig.suptitle(group)
    fig.savefig('results.png')

    # -------------------------------------------------------------------
    # Write parameters and metrics to a csv in the working directory
    metrics_and_params = metrics.append(pd.Series(param_list))

    if os.path.exists(os.path.join(wd,'cal_metrics.csv')):
        writeheader=False
    else:
        writeheader=True
    with open(os.path.join(wd,'cal_metrics.csv'),'a+',newline=None) as f:

        metrics_and_params.to_frame().T.to_csv(f,line_terminator='\n',index=False,
                                               header=writeheader)


# Compare NAM ETa with METRIC seasonal values
metric_fname = os.path.join(dropbox_dir,r"ET_METRIC_AllCatchments.csv")
dfmet = pd.read_csv(metric_fname,index_col=0,parse_dates=True,infer_datetime_format=True)
dfmet = dfmet.filter(regex=catchment_name)
dfmet=dfmet.resample('M').mean()
dfmet = dfmet.mean(1).rename(catchment_name).to_frame()
# Irrigation season annual values
METRIC_annual=dfmet[dfmet.index.month.isin(range(4,11))].resample('A').sum().replace(0,np.nan)

# Model ETa
NAMETa = dfres.filter(regex='Evap').mul(1000*86400) # m/sec to mm/d
NAMETa_mo = NAMETa.resample('M').sum().squeeze()
NAMETa_ann = NAMETa[NAMETa.index.month.isin(range(4,11))].resample('A').sum().squeeze()

# Do percent diff calculations
pd_mo=calcPercentDiff(*dfmet.dropna().align(NAMETa_mo,join='inner',axis=0))
pd_ann = calcPercentDiff(*METRIC_annual.align(NAMETa_ann,join='inner',axis=0))

print('Monthly % Diff:')
print(pd_mo.groupby(pd_mo.index.month).describe().iloc[:,1:])
print('Annual % Diff:')
print(pd_ann)

# #%%
# fig,ax=plt.subplots(2,1)
# ax[0].fill_between(dfres.index,y1=10e-8,where=dfres.filter(regex='Temp').mean(1)<0,color='grey',alpha=.5)
# f1 = dfres.filter(regex='Evap').plot(ax=ax[0])
# ax[0].set_title('Grey when mean temp < 0 F')
# f2 = dfres.filter(regex='Temp').plot(ax=ax[1])
# fig.tight_layout()
# # fig.savefig('NAM_ETa_vs_NAM_temp.png')
# #%%
# pd.concat([PET,ETa/25.4],1).resample('M').sum().plot()
# plt.ylabel('mm/month')
# # fig.savefig('ET.png')