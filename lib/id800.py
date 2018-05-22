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
        self.getTimebase = self.dll_lib.TDC_getTimebase
        self.getTimebase.restype = c_double
        self.timebase = self.getTimebase()
        self.timestamp_count = config.timestamp_count
        
        # Variable declarations
        self.channelMask = c_int8()
        self.coincWin = c_int(config.coincidence_window)
        self.expTime = c_int(config.exposure_time)
        
        c_array8 = c_int8*self.timestamp_count
        c_array64 = c_int64*self.timestamp_count
        self.timestamps = c_array64()
        self.channels = c_array8()
        self.valid = c_int32()
        
        
        # Activate
        rs = self.dll_lib.TDC_init(-1) # Accept every device
        print(">>> Init module")
        self.switch(rs)
        if rs != 0:
            self.connection = False
        else:
            self.connection = True
        
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
#        print(">>> Enabling channels (byte-wise) "+str(self.channels_enabled))
#        self.switch(rs)
        
        # Coincidence window and exposure time
        rs = self.dll_lib.TDC_setCoincidenceWindow(self.coincWin)
        self.switch(rs)
        rs = self.dll_lib.TDC_setExposureTime(self.expTime)
        self.switch(rs)
        
        # Set the buffer size
        self.dll_lib.TDC_setTimestampBufferSize(self.timestamp_count)
        
        self.setHistogramParams()
    
    def getTimebase(self):
        self.dll_lib.TDC_getTimebase.restype = c_double
        return self.dll_lib.TDC_getTimebase()
        
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
        
    def switchTermination(self,on=True):
        rs = self.dll_lib.TDC_switchTermination(on)
        return self.switch(rs)
    
    def getChannel(self,chan=0):
        dictionary = {0:None,1:(1,),2:(2,),3:(1,2),4:(3,),5:(1,3),6:(2,3),7:(1,2,3),
                      8:(4,),9:(1,4),10:(2,4),11:(1,2,4),12:(3,4),13:(1,3,4),
                      14:(2,3,4),15:(1,2,3,4)}
        return dictionary[chan]
    
    def configureSelfTest(self,test_channel,sg_period,sg_burst,burst_dist):
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
        
        print(">>> Getting {} timestamps".format(str(self.timestamp_count)))
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
        
    def setHistogramParams(self,numHists=1):
        self.dll_lib.TDC_clearAllHistograms()
        
        self.hist_bincount = config.hist_bincount
        self.binwidth = config.binwidth
        c_array32 = c_int32*self.hist_bincount
        for i in range(numHists):
            self.hist = c_array32()
        self.bins2ns = c_double(self.binwidth*(81*1e-6)) # r u sure?
        
        rs = self.dll_lib.TDC_setHistogramParams(self.binwidth,
                                                 self.hist_bincount)
#        print(">>> Setting histogram parameters")
        self.switch(rs)
            
    def getHistogram(self,hist=False,channel1=-1,channel2=-1):
        """ WIP if toobig or toosmall then you should change the expwindow
        """
        if not hist:
            hist = self.hist
        self.toobig = c_int32()
        self.toosmall = c_int32()
        self.datacount = c_int32()
        self.dll_lib.TDC_freezeBuffers(1)
        self.dll_lib.TDC_getHistogram(channel1,channel2,1,hist,
                                      self.datacount,self.toosmall,self.toobig,
                                      None,None,None)
        
        self.dll_lib.TDC_freezeBuffers(0)
        
    def getCoincCounters(self):
        self.data = (c_int32*19)()
        rs = self.dll_lib.TDC_getCoincCounters(self.data)
        if not rs:
            print("Coincidences calculated for {}ms".format(str(self.expTime.value)))
        else:
            self.switch(rs)
        
    def getDataLost(self):
        """ LED signalling
        """
        self.data_loss = c_int8()
        rs = self.dll_lib.TDC_getDataLost(self.data_loss)
        if not rs:
            return self.data_loss.value
        else:
            self.switch(rs)
    
    def experimentWindowSleep(self,sleep_time=1000):
        """ In milliseconds. Useless I think.
        """
        sleep(sleep_time/1000.0)
        
    def experimenWindowSignal(self):
        """ TBD - Get signal from LabJack control system, using signals
        I think I have to write a new class for the listener.
        """
    
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
            