'''
定义工具函数
'''
import numpy as np
import scipy.signal
import torch
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



#优势函数计算
def compute_advantage(gamma, lmbda, td_delta):
    # if lmbda == 0:
    #     return td_delta
    td_delta = td_delta.detach().numpy()
    advantage_list = []
    advantage = 0.0
    for delta in td_delta[::-1]:
        advantage = gamma * lmbda * advantage + delta
        advantage_list.append(advantage)
    advantage_list.reverse()
    return torch.tensor(advantage_list, dtype=torch.float)
