# -*- coding: utf-8 -*-

"""

Takes .mca file as input and returns a dictionary the same as 
DATA from Analyse_Slurry.py

The .mca files are not quite all standard 
(i.e. AuFoil_DETcrystal_smallplug_smallcollimator.mca and 
As_DETcrystal_Cwindow_1h_50_0p2.mca have 16 and 12 line preambles respectively) 
so this code is  more generalisable at the expense of some speed (hopefully not
a noticeable difference).

@author: dru03f
"""

import re
import numpy as np

#define function
def m2D(filename):

    # define regex used to strip strings of all non-numeric and non-'.' chars
    non_decimal = re.compile(r'[^\d.]+');
    #create empty dictionary
    
    #open file read-only     
    f=open(filename,'r');


    #create list of all lines in file
    linelist=f.readlines();

    #Realtime and livetime should always remain on the same line between files                        
    DATA={'RealTimeMs':np.float(non_decimal.sub('',linelist[8])),
          'LiveTimeMs':np.float(non_decimal.sub('',linelist[7]))};


    #finds indices within linelist at which the raw data starts and finishes
    data_start=linelist.index('<<DATA>>\n')+1;#+1 because it starts the line after
    data_end=linelist.index('<<END>>\n');

    #list comprehension to put all raw data into an array
    DATA['RawSpectrum'] =np.asarray([np.int32(non_decimal.sub('',val)) for val in linelist[data_start:data_end]]); 
    RawSpectrumError = np.sqrt(DATA['RawSpectrum']);
    RawSpectrumError[RawSpectrumError < 1] = 1; # set min error to one
    DATA['RawSpectrumError']=RawSpectrumError;
    

    config_start=linelist.index('<<DP5 CONFIGURATION>>\n')+1;                            
#   config_end=linelist.index('<<DP5 CONFIGURATION END>>\n');
    DATA['TPEA'] = np.float(non_decimal.sub('',linelist[config_start+2]));
    DATA['TFLA'] = np.float(non_decimal.sub('',linelist[config_start+6]));                       
    DATA['TPFA'] = np.int32(non_decimal.sub('',linelist[config_start+7]));
    PURE_STRING=linelist[config_start+8];
    if 'ON' in PURE_STRING:
         DATA['PURE'] ='ON';
    else:
         DATA['PURE'] ='OFF';
    DATA['NumChan'] = np.int32(non_decimal.sub('',linelist[config_start+11]));
    DATA['THSL'] = np.float(non_decimal.sub('',linelist[config_start+18]));
         
          
 #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~   
                        





        
#Calculating the live time using CalcLiveTime function

    status_start=linelist.index('<<DPP STATUS>>\n')+1;
                               
#If fast count is available use to calc Live Time
    if np.int32(non_decimal.sub('',linelist[status_start+4]))>0: 
        CalcLiveTimeMs = CalcLiveTime(SlowCount = np.int64(non_decimal.sub('',linelist[status_start+5])), 
                                      RealTimeMs= np.float64(non_decimal.sub('',linelist[8])) , 
                                      FastCount=np.int64(non_decimal.sub('',linelist[status_start+4])), 
                                      TPFA=np.int64(non_decimal.sub('',linelist[config_start+7])) );
    else:# if no fastcount available
        CalcLiveTimeMs = CalcLiveTimeNoFast( RealTimeMs=np.float64(non_decimal.sub('',linelist[8])),
        TFLA= np.float64(non_decimal.sub('',linelist[config_start+6])),
        TPEA=np.float64(non_decimal.sub('',linelist[config_start+2])), 
        PURE= DATA['PURE'], 
        NumChan=np.int64(non_decimal.sub('',linelist[config_start+11])), 
        THSL=np.float64(non_decimal.sub('',linelist[config_start+18])), 
        RawSpectrum=np.asarray([np.int32(non_decimal.sub('',val)) for val in linelist[data_start:data_end]])  );
        
    DATA['CalcLiveTimeMs'] = CalcLiveTimeMs;
        
 
    DATA['chan'] = np.add(np.asarray(range(0,DATA['NumChan'])),0.5) ;       
   

    
    return DATA

















'''
This is used for the live time calculation from CalcLiveTime.py
Putting it here so this file can be standalone.


Created on Wed Apr  6 11:14:40 2016

This function takes the settings and some measured counts to calculatethe Amptek 
as true as can be livetime


@author: Yves Van Haarlem 
@Date: 6/4/2016

'''
import math as m
#import numpy as np

# Function definition is here
def CalcLiveTime( SlowCount = 0 ,RealTimeMs = 0, FastCount = 0, TPFA = 0 ):
    # fastcount is available
    DeadFast = TPFA*m.pow(10,-9)
    print(str(FastCount))
    print(str(TPFA))
    print(str(DeadFast))
    R_out = FastCount/RealTimeMs*1000 #1000 puts it into seconds
    R_in = R_out;
    print(str(R_in))
    for i in range(10):
        print(str(type(R_in)))
        print(str(R_in))
        R_in = R_out*m.exp(R_in*DeadFast)
    R_out_s = SlowCount/RealTimeMs*1000
    CalcLiveTimeMs = R_out_s/R_in * RealTimeMs 
    return CalcLiveTimeMs;


def CalcLiveTimeNoFast( RawSpectrum, RealTimeMs = 0, TFLA = 0, TPEA = 0, PURE = 'ON', NumChan = 0, THSL = 0 ):
   # fastcount is not available 
   Cpeak = np.dot(RawSpectrum.astype('int64'),np.arange(4096)+1) / np.sum(RawSpectrum) 
   C_LLD = THSL/100*NumChan;
   F_PD = C_LLD/Cpeak;
   if (PURE == 'ON'):
       N = 2;
   else:
       N = 1;
   DeadSlow = N*(1+F_PD)*(TPEA+TFLA)*m.pow(10,-6);
   R_out_s =  np.sum(RawSpectrum) / RealTimeMs*1000;
   R_in_s = R_out_s;
   for i in range(10):
       R_in_s = R_out_s*m.exp(R_in_s*DeadSlow);
   CalcLiveTime = R_out_s/R_in_s * RealTimeMs 
   return CalcLiveTime;
