# -*- coding: utf-8 -*-
"""
Created on Wed May 23 09:32:56 2018

This code requires the file "ReturnSpectWithExceptions" that is referred to in 
the argument of the "meas_spect" function and is found in the directory
referred to by the "acq_code_dir" argument.

"ReturnSpectWithExceptions" is an exe file that was written in C++ and assumes
the amptek detector is connected via USB. It has some dll dependencies in the
ampteksdk folder

Don't forget to calibrate your detector and ensure that the other settings are
correct.

Don't forget to change the save filename otherwise it will over write any files
with the same name (i.e. old files).

@author: dru03f
"""


import subprocess
import os
import numpy as np
import matplotlib.pyplot as plt
import pickle as pkl
import time

#at the moment will save in the Users "Documents" folder with the filename 
#entered by the user:
filename=input('type the filename for the data to be saved as and hit enter: ')
#The point of this prompt is to help ensure you don't overwrite any data by
# using the same filename (use the .p extension to identify it as a pickle file)

#Don't forget to change the filename, to prevent overwriting other files
#and losing data.
acq_number=2 # number of acquisitions to make
PRET=10 # number of seconds to acquire spectrum for
        #PRET is an amptek variable that is "Preset acquisition time"
        # might need to set Preset acquisition time on detector to True?

#returns the spectrum as an np.array which can be summed to give total slow cts
def meas_spect(PRET_var,plot=False,exe_file='ReturnSpectWithExceptions',acq_code_dir=r'C:\AmptekSDK\SDK\gccDppConsoleWin'):


#exe_file='ReturnSpectWithExceptions'
#PRET_var='6' # time to acquire spectrum for "PRESET ACQ TIME" PRET
#acq_code_dir=r'C:\AmptekSDK\SDK\gccDppConsoleWin' # directory where c++ code is
    print('Acquiring Spectra...')
    os.chdir(acq_code_dir)

    result = subprocess.run([str(exe_file),str(PRET_var)],stdout=subprocess.PIPE,shell=True);

    output_lines=str(result.stdout.decode('utf-8'))

    chars=['\r','\x0c','\t']

    for ch in chars:
        output_lines=output_lines.replace(ch,'')
    
    output_lines=output_lines.split('\n')



    spect=output_lines[-1].split(',')
    spect=np.asarray([int(i) for i in spect[:-1]]) #slicing removes a whitespace at the end

    if plot: #Just for reference
        plt.close('all')
        plt.figure(1)
        plt.plot(range(4096),spect)
        
    if len(spect)==0:
        print('Not acquiring spectra, check detector connection')
        raise ValueError('No spectra recorded, detector is probably unplugged, check and try again')            

    else:        
        
        print('TOTAL sum of measured spect: '+str(sum(spect)))
        return spect

stamp=time.time()    
data_dict = {"spect":np.asarray([meas_spect(PRET)]),"time_stamps":np.asarray([stamp])}
    
for i in range(acq_number-1):
    start_stamp=time.time()

    data_dict["spect"]=np.append(data_dict["spect"],[meas_spect(PRET)],axis=0)
    data_dict["time_stamps"]=np.append(data_dict["time_stamps"],start_stamp)


homedir=os.path.expanduser("~")

pkl.dump(data_dict,open(str(homedir+"\\Documents\\"+filename),"wb"))# saves dictionary to disk
