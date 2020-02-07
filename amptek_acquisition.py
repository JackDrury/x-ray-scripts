# -*- coding: utf-8 -*-
"""
Created on Thu Aug  3 17:38:56 2017

Whatever you do, don't run this code without having calibrated the positions
of the stages. If they have been moved manually (rather than through the box or
through the computer) the CRASH_LIMITS will be completely wrong and you could
break something (I am worried about this happening even with it calibrated...)

The idea of this code is to execute my C++ code that controls the AMPTEK SDD
via USB and returns the total slow counts.

This code will pass the C++ code an integer time in seconds, that will be the
preset acquisition time (PRET). This code will then wait while the C++ code
executes and will grab the integer output of the C++ code.

The integer output of the C++ code is the total slow counts measured.

I could and probably should do some altering of the C++ to return counts in an
energy calibrated ROI or something like that. Probably of around 11.45 keV.

This code then uses Yves' StageControl code to move the stages and optimise
alignment based on the output of the amptek detector.

Make sure you have the correct detector settings before using...



UG1config1="RESC=Y;CLCK=80;TPEA=1.600;GAIF=1.0710;GAIN=47.470;RESL=204;TFLA=0.200;"
UG1config2="TPFA=50;PURE=ON;RTDE=OFF;MCAS=NORM;MCAC=4096;SOFF=OFF;AINP=POS;"
UG1config3="INOF=DEF;GAIA=18;CUSP=50;PDMD=NORM;THSL=7.031;TLLD=OFF;THFA=41.43;"
UG1config4="DACO=SHAPED;DACF=50;RTDS=0;RTDT=0.00;BLRM=1;BLRD=3;BLRU=2;GATE=OFF;"
UG1config5="AUO1=SCA8;PRET=;PRER=600.000;PREC=OFF;PRCL=1;PRCH=8191;HVSE=-110;"
UG1config6="TECS=220;PAPS=ON;SCOE=FA;SCOT=12;SCOG=1;MCSL=1;MCSH=8191;MCST=0.01;"
UG1config7="AUO2=ICR;TPMO=OFF;GPED=RI;GPIN=AUX1;GPME=ON;GPGA=ON;GPMC=ON;MCAE=ON;BOOT=ON;"

Will get this running from the command line to make it take up less memory as 
the poor little X-Ray lab laptop is struggling with ORAC and the webcam and
this etc...

using the --ignoreposfile arg with the StageControl code and a query for position
(i.e. include JackPos.txt) will change the pfile to the correct value without moving
the stage if you have moved it by "hand"*** previously.


~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
It would be best to do roughly by "hand"*** at first, as otherwise the stage might
be just running around in "countless" positions and therefore optimise itself
based off of noise.
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
***by hand I mean using the electronic box and buttons as moving them pysically
will change the axis limit settings.

Code will hang and do nothing if the stages aren't connected to the little electronic box
or if the box is not set to computer control. Because the StageControl code just sits and waits.

C:\\ProgramData\\Anaconda3\\python.exe C:\\Users\\dru03f\\Documents\\mycodes\\amptek_acquisition.py

May need to fine-tune, while looking at the spectra as there is quite a bit of hysteresis
in these stages

Make sure your detector is calibrated and you have selected the correct ch_to_sum
(channels to sum) otherwise you will be optimising position based on the wrong X-ray energy.

If you don't have an Xray tube switched on, obviously it is not going to work.


@author: dru03f
"""



import subprocess
import os
import numpy as np
import matplotlib.pyplot as plt

#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

# I have moved everything I initialised at the start of the code into the start 
# of the auto align function so that I could import things without running the
# code.................... Hopefully it still works......
# 

#!~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~!!!!

#Break it into parts so that less bytes are sent to det, for some reason
# it can't take many
#returns the spectrum as an np.array which can be summed to give total slow cts
def meas_spect(PRET_var,plot=False,exe_file='ReturnSpectWithExceptions',acq_code_dir=r'C:\AmptekSDK\SDK\gccDppConsoleWin'):


#exe_file='ReturnSpect'
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

#    total_slow_counts=int(output_lines[-2])

    spect=output_lines[-1].split(',')
    spect=np.asarray([int(i) for i in spect[:-1]]) #slicing removes a whitespace at the end

    if plot: #Just for reference
        plt.close('all')
        plt.figure(1)
        plt.plot(range(4096),spect)
        
    if len(spect)==0:
        print('Not acquiring spectra, check detector connection')
        print('perhaps detector is connected in amptek software, make sure to disconnect it there')
        raise ValueError('No spectra recorded, detector is probably unplugged, check and try again')            

    else:        
        
        print('TOTAL sum of measured spect: '+str(sum(spect)))
        return spect


#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
#instead of checkpos, might need to --ignoreposfile as I may have moved
        #the stages from the box, meaning that the code will hang forever
def check_pos():# Need to add a condition in case pfile is different or switched off....
    # don't forget that pos4 is always relative
    sf=['-cfile', r'..\input\JackConfig.txt', '-pfile', r'..\input\JackPos.txt']#StageControl files
    print('Checking Position...')
    os.chdir(r'c:\StageControl\bin')
    result=subprocess.run(['StageControl',sf[0],sf[1],sf[2],sf[3]],stdout=subprocess.PIPE,shell=True);
    output_lines=str(result.stdout.decode('utf-8'))
    chars=['\r','\x0c','\t']
    for ch in chars:
        output_lines=output_lines.replace(ch,'')
        
    output_lines=output_lines.split('\n')
    pos1=float(((output_lines[-9]).split(' ')[-4]).replace('mm','')) # this many mm from "home"
    pos2=float(((output_lines[-8]).split(' ')[-4]).replace('mm',''))
    pos3=float(((output_lines[-7]).split(' ')[-4]).replace('mm',''))  
    
    return np.asarray([pos1,pos2,pos3]) # Tells you how far from 'home' each stage is



def reset_pfile():# If stage has been moved using the electric box, this will set the pfile to
    #the correct values
    print('Resetting pfile...')
    sf=['-cfile', r'..\input\JackConfig.txt', '-pfile', r'..\input\JackPos.txt']#StageControl files    
    os.chdir(r'c:\StageControl\bin')
    result=subprocess.run(['StageControl','--ignoreposfile',sf[0],sf[1],sf[2],sf[3]],stdout=subprocess.PIPE,shell=True);
    output_lines=str(result.stdout.decode('utf-8'))
    chars=['\r','\x0c','\t']
    for ch in chars:
        output_lines=output_lines.replace(ch,'')
   # print(output_lines)    
    output_lines=output_lines.split('\n')
    pos1=float(((output_lines[-9]).split(' ')[-4]).replace('mm','')) # this many mm from "home"
    pos2=float(((output_lines[-8]).split(' ')[-4]).replace('mm',''))
    pos3=float(((output_lines[-7]).split(' ')[-4]).replace('mm',''))  
    
    return np.asarray([pos1,pos2,pos3]) # Tells you how far from 'home' each stage is






# Moves the arm, sets Global 'setposn' and 'absposn' to the new values
# and passes them back ~~~~as long as you call it by saying globaldict=move...    
def move(axis,new_pos,Global_dict,speed=3,sf=['-cfile', r'..\input\JackConfig.txt', '-pfile', r'..\input\JackPos.txt']):#~~~~~~~~~~~~~~~~~~~~~~~~~~ ADD THE CRASH CHECK!!!!
    print('Moving axis # '+ str(axis)+' to '+ str(new_pos)+' mm from home')
          
    Global_dict['set_posn'][axis-1]=new_pos# set it to the new desired pos

#~~~~~~~~~~~~~~Should probably handle these errors such that it stops moving in that direction
#~~~~~~~~~~~~~~ and then continues with the process rather than halting the program    
    if  (Global_dict['Axis_Limits'][axis-1])[1]==-1:#If it is a lower limit
        if new_pos < (Global_dict['Axis_Limits'][axis-1])[0]:
            print('Uh-oh, the stage is trying to go beyond its limits, there might be a crash')
            raise ValueError('Trying to move stage beyond crash limit... dont do this. or check your limits and try again')
    
    if  (Global_dict['Axis_Limits'][axis-1])[1]==1:#If it is an upper limit
        if new_pos > (Global_dict['Axis_Limits'][axis-1])[0]:
            print('Uh-oh, the stage is trying to go beyond its limits, there might be a crash')
            raise ValueError('Trying to move stage beyond crash limit... dont do this. or check your limits and try again')
        
    
    
    os.chdir(r'c:\StageControl\bin')
    result=subprocess.run(['StageControl',sf[0],sf[1],sf[2],sf[3],'-abs',str(axis),str(new_pos),str(speed)],stdout=subprocess.PIPE,shell=True);

    output_lines=str(result.stdout.decode('utf-8'))
    chars=['\r','\x0c','\t']
    for ch in chars:
        output_lines=output_lines.replace(ch,'')
        
    output_lines=output_lines.split('\n')
    
#    print(output_lines)
    
#The below should have the same format as in check_pos, but double check in 
#case you return dumb values.
# if you get a strange error about string conversions here, it is probably because
# the stage is trying to move somewhere beyond its range as defined in the jack_config.txt file
# This changes the textual output from the stage control program and therefore ruins my slicing.
#The error could be an attempt at feeding the stages NEGATIVE numbers    
    pos1=float(((output_lines[-9]).split(' ')[-4]).replace('mm','')) # this many mm from "home"
    pos2=float(((output_lines[-8]).split(' ')[-4]).replace('mm',''))
    pos3=float(((output_lines[-7]).split(' ')[-4]).replace('mm','')) 
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~    
    Global_dict['abs_posn']=np.asarray([pos1,pos2,pos3])
#Just moved this here from below the if setpos!=abs pos cond.
#Why was the code working at all with it below????? This is the next thing to check!!!!    
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~    
    
    #Check that the stage has actually gone where you want it to go... otherwise could crash into things
    # np.allclose checks that they are element-wise equal within float precision (so there is a tolerance defined)
    if not np.allclose(Global_dict['set_posn'],Global_dict['abs_posn']):#if the set posn is different to the measured pos an error is raised... could lead to collisions
        print('For some reason the set axis posn on Axis number:'+str(axis)+' (or maybe crosstalk between axes?) is not the same as the measured value')
        print('perhaps the step size is too small? or the config is incorrect?')
        print('set pos1 === ' +str((Global_dict['set_posn'])[0])+'\n')
        print('set pos2 === ' +str((Global_dict['set_posn'])[1])+'\n')        
        print('set pos3 === ' +str((Global_dict['set_posn'])[2])+'\n')        
        print('abs pos1 === ' +str((Global_dict['abs_posn'])[0])+'\n')
        print('abs pos2 === ' +str((Global_dict['abs_posn'])[1])+'\n')        
        print('abs pos3 === ' +str((Global_dict['abs_posn'])[2])+'\n')        
        raise ValueError('The set position is not equal to the measured position of the stage. Pls try to fix this.')
    
    print('Finished a move...')
    print('set pos === ' +str(Global_dict['set_posn'])+'\n')
    print('abs pos === ' +str(Global_dict['abs_posn'])+'\n')
           

    
    return Global_dict 

#1= in and out  (Z)
#2 = up and down (Y)
 #3 = L&R (X)
   #4 = rotational
   
#~~~~~~CHECK THE MAXIMUM DISTANCE POSITIONS YOU ARE WILLING TO GO TO
#(TO PREVENT CRASHES)   
   
#First check the starting stage positions and measure the signal there:   

# What we will do is first use a big step size and then use small steps
# to look in between the 2 largest values... start with 5 mm? then 1 mm? OK!  
                        
def step_thru_pos(axis,stepsize,Global_dict):
    
    print('Stepping through different positions to optimise signal...')
    
    lower_ch=(Global_dict['ch_to_sum'])[0]
    upper_ch=(Global_dict['ch_to_sum'])[1]
                        
    while 1==1: # Move in first direction until no longer increasing spect
        
        new_pos=Global_dict['abs_posn'][axis-1]+stepsize #move by stepsize mm
#Check that these are the same after moving
        
        print('just set new_pos within while loop...')
        print('set pos === ' +str(Global_dict['set_posn']))
        print('abs pos === ' +str(Global_dict['abs_posn']))        
        print('new_pos === ' +str(new_pos))        
        
        
#        print('moving axis # '+str(axis)+' to '+str(new_pos)+' mm from home') this is already printed in move
        Global_dict=move(axis,new_pos,Global_dict)
        
        print('just finished move within while loop... about to measure spect...')
        print('set pos === ' +str(Global_dict['set_posn']))
        print('abs pos === ' +str(Global_dict['abs_posn']))        
        print('new_pos === ' +str(new_pos))            
        


        spect=meas_spect(Global_dict['PRET_var']) # Now we are in new position measure the spect
        
        sum_of_chans=sum(spect[lower_ch:upper_ch])
                         
        print('Sum counts in channels of interest ===  '+str(sum_of_chans))
        
        Global_dict['spect_log{0}'.format(str(axis))]=np.append(Global_dict['spect_log{0}'.format(str(axis))],sum_of_chans) #These logs are our important arrays
                                                #Their indices correspond to eachother
        
        Global_dict['posn_log{0}'.format(str(axis))]=np.append(Global_dict['posn_log{0}'.format(str(axis))],[Global_dict['abs_posn']],axis=0)# this is our important array   

#Now check whether signal is increasing... A bit complex because we jump around with the stages
# So we can't just check against the last recorded signal... or what I could do is append
# the starting signal each time we jump around and then remove it before checking for the maximum?? Good idea
        
        if Global_dict['spect_log{0}'.format(str(axis))][-1] < Global_dict['spect_log{0}'.format(str(axis))][-2]: # BE WARY OF THIS CONDITION! IT COULD MEAN
            print('counts not increasing, finishing movements') #THAT IF IT HAS ALREADY MOVED ONE DIRECTION AND THEN
            break                                       # SWAPS DIRECTION THAT IT WILL BE COMPARING 2 OPPOSITE ENDS
                                                    # OF THE STAGE'S POSITIONS
                                                    # Probably should make a copy and sort it to check
            
            
            
    return Global_dict

def max_2_inds(axis,Global_dict):

   ###Now we just need to find the two adjacent maxima in  spect_log:
    #(at least I really hope they are adjacent)
    max_inds=np.argpartition(Global_dict['spect_log{0}'.format(str(axis))],-2)[-2:]
    #sort so we can pick the larger of the two:
    max_inds=max_inds[np.argsort((Global_dict['spect_log{0}'.format(str(axis))])[max_inds])]
    
    if  (Global_dict['spect_log{0}'.format(str(axis))])[max_inds[1]]==(Global_dict['spect_log{0}'.format(str(axis))])[max_inds[0]]:
        print('This is either outrageously unlikely, or they are points in irrelevant "zero-count" space')
        print('or you have somehow not removed duplicates!')
        raise ValueError('The counts in the 2 max spectra are exactly equal. Most likely an error. Check posn of detector.')
        
    return max_inds        





# this is just a useful module for calling move externally
# so you can move the stage without needing a global dictionary
def external_move(axis,new_pos,speed=3,sf=['-cfile', r'..\input\JackConfig.txt', '-pfile', r'..\input\JackPos.txt']):#~~~~~~~~~~~~~~~~~~~~~~~~~~ ADD THE CRASH CHECK!!!!
    print('Moving axis # '+ str(axis)+' to '+ str(new_pos)+' mm from home')
    print('be careful in the value you choose, you dont want anything to crash')
          

    
    os.chdir(r'c:\StageControl\bin')
    result=subprocess.run(['StageControl',sf[0],sf[1],sf[2],sf[3],'-abs',str(axis),str(new_pos),str(speed)],stdout=subprocess.PIPE,shell=True);

    output_lines=str(result.stdout.decode('utf-8'))
    chars=['\r','\x0c','\t']
    for ch in chars:
        output_lines=output_lines.replace(ch,'')
        
    output_lines=output_lines.split('\n')
    
#    print(output_lines)
    
#The below should have the same format as in check_pos, but double check in 
#case you return dumb values.
# if you get a strange error about string conversions here, it is probably because
# the stage is trying to move somewhere beyond its range as defined in the jack_config.txt file
# This changes the textual output from the stage control program and therefore ruins my slicing.
#The error could be an attempt at feeding the stages NEGATIVE numbers    
    pos1=float(((output_lines[-9]).split(' ')[-4]).replace('mm','')) # this many mm from "home"
    pos2=float(((output_lines[-8]).split(' ')[-4]).replace('mm',''))
    pos3=float(((output_lines[-7]).split(' ')[-4]).replace('mm','')) 

    print('finished a move')
    print('final positions:')
    print('axis 1 = ' + str(pos1))
    print('axis 2 = ' + str(pos2))
    print('axis 3 = ' + str(pos3))


    return np.asarray([pos1,pos2,pos3])




        
def auto_align(axis_list=[1,2,3]):
    
    for axe in axis_list:
        if axe not in range(1,4):
            print('Your axis list has invalid axes only axes 1 to 3 inclusive, must do rotational separately')
            return 0
    #Make sure you haven't messed anything up along the way...
    #The main thing to look for will be variables that have not been defined inside
    #This function and are called upon.
    #Always check the axis limits!!!!!
    
    #Which Channels would you like to sum / maximise:
    
    ch_to_sum=(2625,2701)# current numbers based on most recent calib corresp to 11.25 keV to 11.65 keV
    #Perhaps should make it narrower? e.g. 1788 to 1819 corresp to 11.35 - 11.55 
    #decides which channels to sum and therefor which to maximise. After calibrating your detector based on it's ideal settings
    #you should choose these so that they correspond to the energy you are interested in (for me that is 11.45 keV) so I will
    #probably choose channels that go from 11.35ish to 11.55ish or 11.3 to 11.6
    
    
    verbosity=1; #1 = debug, anything else = no debug
    #Haven't set this up either....
    
    PRET_var='300'#preset acquisition time, how many seconds to acquire spectra on each acquisition
                #Must be string!
    
    num_of_stepsizes=2;#how deep to go into stepsizes, 1 = only big step
                        # 2 = big then small
                        # 3 = big then small then smallest
                        #have not implemented this just yet.....
    big_stepsize=5#in mm
    small_stepsize=0.5# in mm
    smallest_stepsize=0.05#in mm
    
    Rotational=False# whether to check rotational alignment (in the horizontal plane, havent figured out how to move it in the vert plane yet...)
    
    print('Acquisition times are set to: '+str(PRET_var))
    print('big stepsize is set to: ' + str(big_stepsize))
    print('small stepsize is set to: ' +str(small_stepsize))
    print('channels of interest: ' +str(ch_to_sum))
    
    sf=['-cfile', r'..\input\JackConfig.txt', '-pfile', r'..\input\JackPos.txt']#StageControl files
    print('')
    Global_dict={'Axis_Limits':((40,-1),(10.8,-1),(50.7,1)),'ch_to_sum':ch_to_sum,'sf':sf,'PRET_var':PRET_var}# This will make it much easier to pass and return things from functions
    print('Axis Limits ==  '+str(Global_dict['Axis_Limits']))

    #first value is posn in mm from home, second value indicates which direction not to move in
    # -1 implies do not go lower than this
    # +1 implies do not go higher than this 
    
     # rather than just limits, may
    #need to make combined limits, i.e. if y is below a certain level then z can't
    #be past another level. etc...
    
    print("don't forget to check your detector settings in the amptek software...")
    print("Don't forget to have the correct Axis Limits set, so nothing crashes into anything else")
    
    
    start_pos=check_pos()
    print('starting posn is: '+ str(start_pos))   
    Global_dict['abs_posn']=start_pos
    Global_dict['set_posn']=Global_dict['abs_posn']
    spect=meas_spect(PRET_var)
    
    
    
    
    Global_dict['posn_log1']=np.asarray([Global_dict['abs_posn']])# this is our important array
                                #We will probably be using the sum.
                                #Might just want specific channels though....
                                #i.e. sum(spect[1000:4000])
    start_spect=sum(spect[ch_to_sum[0]:ch_to_sum[1]])   # sum corresp to the above posn 

    print('Sum counts in channels of interest ===  '+str(start_spect))                        
       
    Global_dict['spect_log1']=np.asarray(start_spect)
    
    for axis in axis_list:#not including rotational stage yet as that needs different
                            # treatment since it only takes -rel inputs not -abs

        try:
            print(str(Global_dict['posn_log{0}'.format(str(axis))]))#if it doesn't exist it means you are starting
                                                                    # from axis 2 or 3 so you just need to create them
    
        except KeyError:
            
                 Global_dict['posn_log{0}'.format(str(axis))]=np.asarray([Global_dict['abs_posn']])
                 Global_dict['spect_log{0}'.format(str(axis))]=np.asarray(start_spect)
    
        print('Starting for axis {0}...'.format(str(axis)))
        print('set pos === ' +str(Global_dict['set_posn']))
        print('abs pos === ' +str(Global_dict['abs_posn']))
    
        #first move in 5mm steps from starting posn until spect does not increase
        Global_dict=step_thru_pos(axis,big_stepsize,Global_dict)
    
        print('Finished first step_thru_pos call...')
        print('set pos === ' +str(Global_dict['set_posn']))
        print('abs pos === ' +str(Global_dict['abs_posn']))
        
        
        
        #Then move back to start pos:
        print('Moving back to initial pos...')
    
        print('posn_log{0}[0]=== '.format(str(axis))+str((Global_dict['posn_log{0}'.format(str(axis))])[0]))
        ###############~~~~~ SINCE MOVE IS PRINTING NEW_POS AS 113, MAYBE START_POS[AXIS-1] HAS CHANGED??????
    
    
        Global_dict=move(axis,(Global_dict['posn_log{0}'.format(str(axis))])[0][axis-1],Global_dict)#Moving to initial pos
                                                            # It needs to be there before starting in the opp dir
        print('Finished moving back to initial pos...')
        print('set pos === ' +str(Global_dict['set_posn']))
        print('abs pos === ' +str(Global_dict['abs_posn']))
                                                            
                                                            
                                                            
        ## Now append the starting spect to reflect the move back to the centre:
        # just to ensure the "is it increasing?" checks perform correctly in step_thru_pos
        ####~~~~~ BUt be careful!!! You don't want to offset the spect indices from the posn_log indices
    
        Global_dict['spect_log{0}'.format(str(axis))]=np.append(Global_dict['spect_log{0}'.format(str(axis))],start_spect)
    
        duplicate_index=len(Global_dict['spect_log{0}'.format(str(axis))])-1
        #This makes the check as to whether our signal is increasing far easier.
        
        
                                                            
        #Then move in 5mm steps in the opposite direction until it no longer increases
        Global_dict=step_thru_pos(axis,-big_stepsize,Global_dict)
    
        print('Finished 2nd direction stepthru...')
        print('set pos === ' +str(Global_dict['set_posn']))
        print('abs pos === ' +str(Global_dict['abs_posn']))
        
        
        #now remove the added starting positions as the duplicates WILL ruin
        # our search for the maxima
        
        Global_dict['spect_log{0}'.format(str(axis))]=np.delete(Global_dict['spect_log{0}'.format(str(axis))],duplicate_index)
       
        #find indices that corresp to 2 largest spectra (and sorted)
        max_inds=max_2_inds(axis,Global_dict)
    
    #Now we find the positions of the 2 maxima:
    
        maxpos1=(Global_dict['posn_log{0}'.format(str(axis))])[max_inds[1]]#largest
        maxpos2=(Global_dict['posn_log{0}'.format(str(axis))])[max_inds[0]]#2nd largest
        
    #Now we move to the largest location and then we start stepping through towards 
        #2nd largest
    
        Global_dict=move(axis,maxpos1[axis-1],Global_dict)      
    
        print('Finished move to maxima at end of first axis iteration...')
        print('set pos === ' +str(Global_dict['set_posn']))
        print('abs pos === ' +str(Global_dict['abs_posn']))
        
        
        
    # Add the values from this max pos to the logs so that the greater than/less than 
    # checks perform correctly
    
        Global_dict['spect_log{0}'.format(str(axis))]=np.append(Global_dict['spect_log{0}'.format(str(axis))],(Global_dict['spect_log{0}'.format(str(axis))])[max_inds[1]])
        duplicate_index=len(Global_dict['spect_log{0}'.format(str(axis))])-1
    
            
    #decide the correct direction to step in and begin:
        if maxpos1[axis-1] > maxpos2[axis-1]:
            Global_dict=step_thru_pos(axis,-small_stepsize,Global_dict)
            print('Finished small stepthru...')
            print('set pos === ' +str(Global_dict['set_posn']))
            print('abs pos === ' +str(Global_dict['abs_posn']))
                
            
        else:
            Global_dict=step_thru_pos(axis,small_stepsize,Global_dict)
            
            print('Finished small stepthru...')
            print('set pos === ' +str(Global_dict['set_posn']))
            print('abs pos === ' +str(Global_dict['abs_posn']))
                        
            
    #Removing the duplicate entry.            
        Global_dict['spect_log{0}'.format(str(axis))]=np.delete(Global_dict['spect_log{0}'.format(str(axis))],duplicate_index)
        
       #Now move detector to the maximum position and make sure everything is
       # ready to loop through for the next axis:
    
    #New maximums?   
        max_inds=max_2_inds(axis,Global_dict)
        maxpos1=(Global_dict['posn_log{0}'.format(str(axis))])[max_inds[1]]#largest
    #Move to maximum    
        Global_dict=move(axis,maxpos1[axis-1],Global_dict)  
        print('Finished moving to small steps maximum!')
        print('set pos === ' +str(Global_dict['set_posn']))
        print('abs pos === ' +str(Global_dict['abs_posn']))
                    
        
    #Log this value and intialise the log for the next axis! 
        
        
        
        
        start_pos=maxpos1
        start_spect=np.asarray([(Global_dict['spect_log{0}'.format(str(axis))])[max_inds[1]]])    
        
        Global_dict['spect_log{0}'.format(str(axis+1))]=start_spect
        Global_dict['posn_log{0}'.format(str(axis+1))]=np.asarray([maxpos1])# I believe this is the desired format
        
        
        # now we are ready for the next axis?? I believe so.
    #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~    
    
    
        # Now we have maximised each axis separately. What do we do??
        # Do we run once more to see if one axis got sucked into a slightly weak
        # spot while the other axes were out of alignment? e.g. run again except
        # with small_stepsize and then smallest_stepsize (no big_stepsize)?
        
        #What do we want to return? Anything? Perhaps an acknowledgement of completion
        # Along with some spectra values, max, min and median and sd? just to make sure 
        # the spread seems normal or there is not like a difference of 3 counts
        # between max and min.
        
        # Do we run something to check the angular alignment??? i.e. the rotational stage
        
        # Do we make this code executable so I can run it from cmd, rather than
        # memory consuming spyder.
        
        # Hopefully that's everything.
        
        #Don't forget to measure and record the axis limits.
    
        
        
        
        
        
        
    #~~~~~~~~~~~~~~~    #start_pos=final pos before starting next loop....
        
        
    print('cool, all done, detector should be in the nicest position')    
    print('dont forget about the rotational stage though.....')
    print('Change the end of this code if you want it to return something next time...')
    print('dont forget that all stages are prone to hysteresis')
    print('so it is likely that the optimal position is not exactly where the stage has ended up')
    print('but hopefully it is close enough')
    

























































