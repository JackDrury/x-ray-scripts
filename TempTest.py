"""
Be careful, because if you run this with the textfiles already in existence
it will append to them. Although, all entries have a time stamp, so it wouldn't
be the end of the world.

Each handler has to call write separately unfortunately. I mean I 
could use more global variables so that I only have to write to disk once every 
5 seconds....?


SO! When you add the extra channels! Don't forget adding the starts, middles and ends.

@author: dru03f
"""
import sys
import time
from time import ctime 
from Phidget22.Devices.TemperatureSensor import *
from Phidget22.PhidgetException import *
from Phidget22.Phidget import *
from Phidget22.Net import *
import numpy as np
import csv


tempslist0=np.asarray([])
tempslist1=np.asarray([])
tempslist2=np.asarray([])
tempslist3=np.asarray([])

try:
    ch0 = TemperatureSensor()
    ch1=TemperatureSensor()
    ch2=TemperatureSensor()
    ch3=TemperatureSensor()
    
except RuntimeError as e:
    print("Runtime Exception %s" % e.details)
    print("Press Enter to Exit...\n")
    readin = sys.stdin.read(1)
    exit(1)

def TemperatureSensorAttached(e):
    try:
        attached = e
        print("\nAttach Event Detected (Information Below)")
        print("===========================================")
        print("Library Version: %s" % attached.getLibraryVersion())
        print("Serial Number: %d" % attached.getDeviceSerialNumber())
        print("Channel: %d" % attached.getChannel())
        print("Channel Class: %s" % attached.getChannelClass())
        print("Channel Name: %s" % attached.getChannelName())
        print("Device ID: %d" % attached.getDeviceID())
        print("Device Version: %d" % attached.getDeviceVersion())
        print("Device Name: %s" % attached.getDeviceName())
        print("Device Class: %d" % attached.getDeviceClass())
        print("\n")

    except PhidgetException as e:
        print("Phidget Exception %i: %s" % (e.code, e.details))
        print("Press Enter to Exit...\n")
        readin = sys.stdin.read(1)
        exit(1)   
    
def TemperatureSensorDetached(e):
    detached = e
    try:
        print("\nDetach event on Port %d Channel %d" % (detached.getHubPort(), detached.getChannel()))
    except PhidgetException as e:
        print("Phidget Exception %i: %s" % (e.code, e.details))
        print("Press Enter to Exit...\n")
        readin = sys.stdin.read(1)
        exit(1)   

def ErrorEvent(e, eCode, description):
    print("Error %i : %s" % (eCode, description))


    
def AvgTemp(channel,tempslist,start):
#no global so can hopefully be channel agnostic...    

    avg=np.average(tempslist)

    with open('tempavg{0}.csv'.format(channel), 'a') as csvfile:
        filewriter = csv.writer(csvfile, delimiter=',',
                            quotechar='|', quoting=csv.QUOTE_MINIMAL)
        filewriter.writerow([str(avg),str(start)])
    print('avgtemp{0}: '.format(channel) +str(avg) +'  start: '+str(start))    





    

def TemperatureChangeHandler0(e, temperature):
    print('temp0   ' + str(temperature))   
    global tempslist0
    tempslist0=np.append(tempslist0,temperature)
    
    global start0
#if it has been 5s, calc an average and start again
    if time.time() >= start0+5:
        
        AvgTemp(0,tempslist0,start0)
        tempslist0=np.asarray([])
        start0+=5
        
        
        
    

def TemperatureChangeHandler1(e, temperature):
    print('temp1   ' + str(temperature))
   
    global tempslist1
    tempslist1=np.append(tempslist1,temperature)
    
    global start1
#if it has been 5s, calc an average and start again
    if time.time() >= start1+5:
        
        AvgTemp(1,tempslist1,start1)
        tempslist1=np.asarray([])
        start1+=5
        
    

def TemperatureChangeHandler2(e, temperature):
   
    global tempslist2
    tempslist2=np.append(tempslist2,temperature)
    
    global start2

    if time.time() >= start2+5:
        
        AvgTemp(2,tempslist2,start2)
        tempslist2=np.asarray([])
        start2+=5
        
    

def TemperatureChangeHandler3(e, temperature):
   
    global tempslist3
    tempslist3=np.append(tempslist3,temperature)
    
    global start3
#if it has been 5s, calc an average and start again
    if time.time() >= start3+5:
        
        AvgTemp(3,tempslist3,start3)
        tempslist3=np.asarray([])
        start3+=5
        
    
        


try:

    ch0.setOnAttachHandler(TemperatureSensorAttached)
    ch0.setOnDetachHandler(TemperatureSensorDetached)
    ch0.setOnErrorHandler(ErrorEvent)


    ch1.setOnAttachHandler(TemperatureSensorAttached)
    ch1.setOnDetachHandler(TemperatureSensorDetached)
    ch1.setOnErrorHandler(ErrorEvent)
    
    
    ch2.setOnAttachHandler(TemperatureSensorAttached)
    ch2.setOnDetachHandler(TemperatureSensorDetached)
    ch2.setOnErrorHandler(ErrorEvent)

    ch3.setOnAttachHandler(TemperatureSensorAttached)
    ch3.setOnDetachHandler(TemperatureSensorDetached)
    ch3.setOnErrorHandler(ErrorEvent)


    start0=time.time()
    start1=start0
    start2=start0
    start3=start0
    
    ch0.setOnTemperatureChangeHandler(TemperatureChangeHandler0)
    ch0.setChannel(0)
    
    ch1.setOnTemperatureChangeHandler(TemperatureChangeHandler1)
    ch1.setChannel(1)
    
    ch2.setOnTemperatureChangeHandler(TemperatureChangeHandler2)
    ch2.setChannel(2)
    
    ch3.setOnTemperatureChangeHandler(TemperatureChangeHandler3)
    ch3.setChannel(3)
    
    
    



    # Please review the Phidget22 channel matching documentation for details on the device
    # and class architecture of Phidget22, and how channels are matched to device features.

    # Specifies the serial number of the device to attach to.
    # For VINT devices, this is the hub serial number.
    #
    # The default is any device.
    #
    # ch.setDeviceSerialNumber(<YOUR DEVICE SERIAL NUMBER>) 

    # For VINT devices, this specifies the port the VINT device must be plugged into.
    #
    # The default is any port.
    #
    # ch.setHubPort(0)

    # Specifies which channel to attach to.  It is important that the channel of
    # the device is the same class as the channel that is being opened.
    #
    # The default is any channel.
    #
    # ch.setChannel(0)

    # In order to attach to a network Phidget, the program must connect to a Phidget22 Network Server.
    # In a normal environment this can be done automatically by enabling server discovery, which
    # will cause the client to discovery and connect to available servers.
    #
    # To force the channel to only match a network Phidget, set remote to 1.
    #
    # Net.enableServerDiscovery(PhidgetServerType.PHIDGETSERVER_DEVICE);
    # ch.setIsRemote(1)

    print("Waiting for the Phidget TemperatureSensor Object to be attached...")
    ch0.openWaitForAttachment(5000)
    ch1.openWaitForAttachment(5000)
    ch2.openWaitForAttachment(5000)
    ch3.openWaitForAttachment(5000)
    
#    ch0.setDataInterval(30)
    
#    print(str(ch0.getTemperatureChangeTrigger()))
#    print(str(ch0.getDataInterval()))
    
    
except PhidgetException as e:
    print("Phidget Exception %i: %s" % (e.code, e.details))
    print("Press Enter to Exit...\n")
    readin = sys.stdin.read(1)
    exit(1)

print("Gathering data for ?? seconds...")
time.sleep(21)



try:
    ch0.close()
    ch1.close()
    ch2.close()
    ch3.close()
except PhidgetException as e:
    print("Phidget Exception %i: %s" % (e.code, e.details))
    print("Press Enter to Exit...\n")
    readin = sys.stdin.read(1)
    exit(1) 
print("Closed TemperatureSensor device")
exit(0)
                     
