import hunahpy as IDQ
from ctypes import WinDLL,byref,c_int,c_int8,c_int32,c_int64,c_double
from os import path
import time
import pandas as pd

def get_sample(filename : str) -> tuple[pd.DataFrame, float]:
    """
    
    """
    if filename:
        delta_t = time.time()
        tagger.writeTimestamps(filename, binary= False)
        time.sleep(0.1)
        tagger.writeTimestamps(None)
        delta_t = time.time() - delta_t
        return pd.read_csv(filename), delta_t
    
    return None



# # Get Dark Counts
tagger = IDQ.TDC()
timestamps, period = get_sample('scan.csv')
events = list(timestamps.iloc[ : , 1])
num_events = events.count(1)
dark_counts = num_events/period
tagger.close()
print("Dark Count Rate = ", int(dark_counts))
# dll = WinDLL(path.join(path.dirname(__file__),
#                         'tdcbase.dll'))
# TDC_discover = dll.TDC_discover
# discover_input = c_int32()
# print(discover_input.value)
# TDC_discover(byref(discover_input))
# print(discover_input.value)