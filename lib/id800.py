# -*- coding: utf-8 -*-
"""
Created on Tue Mar 20 15:08:31 2018

@author: Luis Villegas
"""

from ctypes import WinDLL,byref,c_int,c_int8,c_int32,c_int64,c_double
from time import sleep
from os import path
import config


class TDC:
    def __init__(self, libpath = None):
        if libpath is not None:
            self._libpath = libpath
        else:
            self._libpath = path.join(path.dirname(__file__),
                                        'tdcbase.dll')
        self.dll_lib = WinDLL(self._libpath)
        

        # Timebase
        self.timebase = c_double()
        self.timebase.value = self.dll_lib.TDC_getTimebase()
        self.timestamp_count = config.timestamp_count
        
        # Variable declarations
        self.channelMask = c_int8()
        self.coincWin = c_int()
        self.expTime = c_int()
        
        c_array8 = c_int8*self.timestamp_count
        c_array64 = c_int64*self.timestamp_count
        self.timestamps = c_array64()
        self.channels = c_array8()
        self.valid = c_int32()
        
        
        # Activate
        rs = self.dll_lib.TDC_init(-1) # Accept every device
        print(">>> Init module")
        self.switch(rs)
        
        # Select channels to use (id800 userguide)
        # 0 = none         8 = 4
        # 1 = 1            9 = 1,4
        # 2 = 2           10 = 2,4
        # 3 = 1,2         11 = 1,2,4
        # 4 = 3           12 = 3,4
        # 5 = 1,3         13 = 1,3,4
        # 6 = 2,3         14 = 2,3,4
        # 7 = 1,2,3       15 = 1,2,3,4
        
        self.channels_enabled = config.channels_enabled # All
        rs = self.dll_lib.TDC_enableChannels(self.channels_enabled)
        print(">>> Enabling channels (byte-wise) "+str(self.channels_enabled))
        self.switch(rs)
        
        print(">>> Setting coincidence window and exposure time")
        rs = self.dll_lib.TDC_setCoincidenceWindow(self.coincWin)
        self.switch(rs)
        rs = self.dll_lib.TDC_setExposureTime(self.expTime)
        self.switch(rs)
        
        # Set the buffer size
        self.dll_lib.TDC_setTimestampBufferSize(self.timestamp_count)
        
        self.setHistogram()
        
    def close(self):
        rs = self.dll_lib.TDC_deInit()
        return self.switch(rs)
        
    def switch(self,rs):
        """ For debugging, refer to tdcbase.h
        """
        if rs == 0: #TDC_Ok
            print("Success")
        elif rs == -1: #TDC_Error
            print("Unspecified error")
        elif rs == 1: #TDC_Timeout
            print("Receive timed out")
        elif rs == 2: #TDC_NotConnected
            print("No connection was established")
        elif rs == 3: #TDC_DriverError
            print("Error accessing the USB driver")
        elif rs == 7: #TDC_DeviceLocked
            print("Can't connect device beause already in use")
        elif rs == 8: #TDC_Unknown
            print("Unknown error")
        elif rs == 9: #TDC_NoDevice
            print("Invalid device number used in call")
        elif rs == 10: #TDC_OutOfRange
            print("Parameter in func. call is out of range")
        elif rs == 11: #TDC_CantOpen
            print("Failed to open specified file")
        else:
            print("????")
        return
    
    def getTimebase(self):
        print(self.timebase.value)
    
    def selfTest(self,test_channel,sg_period,sg_burst,burst_dist):
        rs = self.dll_lib.TDC_configureSelftest(test_channel,
                                                sg_period,
                                                sg_burst,
                                                burst_dist)
        return self.switch(rs)
    
    def getDeviceParams(self):
        return self.dll_lib.TDC_getDeviceParams(byref(self.channelMask),
                                                byref(self.coincWin),
                                                byref(self.expTime))
    
    def getLastTimestamps(self,freeze=True,output=False,*args):
        """ WIP
        """
        if freeze:
            self.dll_lib.TDC_freezeBuffers(1)
        rs = self.dll_lib.TDC_getLastTimestamps(1,byref(self.timestamps),
                                                byref(self.channels),
                                                byref(self.valid))
        
        print(">>> Getting last {} timestamps".format(str(self.timestamp_count)))
        self.switch(rs)
        if not rs:
            print("Timestamps: buffered {}".format(str(self.valid.value)))
        if output:
            self.saveTimestamps(*args)
            print("Saving to file...")
        if freeze:
            self.dll_lib.TDC_freezeBuffers(0)
            
    def saveTimestamps(self,filenamet="timestamps",filenamec="channels",
                       filesuffix=".bin"):
        timefile = open(filenamet+filesuffix,"w")
        for item in self.timestamps:
            timefile.write("%s\n" % item)
        timefile.close()
        
        channelfile = open(filenamec+filesuffix,"w")
        for item in self.channels:
            channelfile.write("%s\n" % item)
        channelfile.close()
    
    def experimentWindowSleep(self,sleep_time=1000):
        """ In milliseconds. Useless I think.
        """
        sleep(sleep_time/1000.0)
        
    def experimenWindowSignal(self):
        """ TBD - Get signal from LabJack control system, using signals
        I think I have to write a new class for the listener
        """
        
    def setHistogram(self,numHists=1):
        self.dll_lib.TDC_clearAllHistograms()
        
        self.hist_bincount = config.hist_bincount
        self.binwidth = config.binwidth
        c_array32 = c_int32*self.hist_bincount
        self.hist1 = c_array32()
        self.hist2 = c_array32()
        self.bins2ns = c_double(self.binwidth*self.timebase*1e9) # r u sure?
        
        rs = self.dll_lib.TDC_setHistogramParams(self.binwidth,
                                                 self.hist_bincount)
        print(">>> Setting histogram parameters")
        self.switch(rs)
            
    def getHistogram(self):
        """ TBD
        """
        self.dll_lib.TDC_freezeBuffers(1)
        
        
        self.dll_lib.TDC_freezeBuffers(0)
    
    def run(self,signal,filename="timestamps",filesuffix=".bin",out=1):
        """ Idea for signal: index of experiment run = 0,1,2,3,...,n
        If first, only open new file.
        If last, only close file.
        Else, close last and open new file.
        
        WIP until I know how to implement signalling from LabJack, but it
        should pretty much be something like this. Can't work much more until
        I know how.
        """
        if signal == ("last"): # If last: close and end call
            try:
                self.dll_lib.TDC_writeTimestamps(None,c_int(out))
            except:
                print(">>> Couldn't initiate run")
        else: # If not last: check if first or else
            if signal == ("else"): # If else: close then open
                try:
                    self.dll_lib.TDC_writeTimestamps(None,c_int(out))
                except:
                    print(">>> Couldn't initiate run")
            # If first: ignore closing and only open
            try: 
                # Start writing to file
                text = str.encode(filename+filesuffix)
                rs = self.dll_lib.TDC_writeTimestamps(text,c_int(out))
                print(">>> Writing to file "+filename+filesuffix)
                self.switch(rs)                    
            except:
                print(">>> Couln't initiate run")
            