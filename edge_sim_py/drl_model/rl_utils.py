'''
定义工具函数
'''
import numpy as np
import scipy.signal

#滑动平均滤波
def moving_average(a, window_size):
    cumulative_sum = np.cumsum(np.insert(a, 0, 0))
    middle = (cumulative_sum[window_size:] - cumulative_sum[:-window_size]) / window_size
    r = np.arange(1, window_size-1, 2)
    begin = np.cumsum(a[:window_size-1])[::2] / r
    end = (np.cumsum(a[:-window_size:-1])[::2] / r)[::-1]
    return np.concatenate((begin, middle, end))


#S-G滤波
def SG_Filter(a,window_size,n):
    a = scipy.signal.savgol_filter(a,window_size,n)
    return a