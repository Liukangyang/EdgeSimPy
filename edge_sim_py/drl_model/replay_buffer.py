import collections
import numpy as np
import random
class ReplayBuffer:
    ''' 经验回放池 '''
    def __init__(self, capacity):
        self.buffer = collections.deque(maxlen=capacity)  # 队列,先进先出
        self.counter = 0

    def add(self, state, action, reward, next_state,log_probe,next_v,done):  # 将数据加入buffer
        self.buffer.append((state, action, reward, next_state,log_probe, next_v,done))
        self.counter += 1

    def sample(self, batch_size):  # 从buffer中采样数据,数量为batch_size
        transitions = random.sample(self.buffer, batch_size)
        state, action, reward, next_state, log_probe,next_v,done = zip(*transitions)
        b_s, b_a, b_r, b_ns, b_probs,b_next_v,b_d = (np.array(state), np.array(action), reward,
                                            np.array(next_state),np.array(log_probe),np.array(next_v),done)
        # 转化为字典形式
        transition_dict = {
            'states': b_s,
            'actions': b_a,
            'next_states': b_ns,
            'rewards': b_r,
            'log_probs': b_probs,
            'next_vs': b_next_v,
            'dones': b_d
        }
        return transition_dict

    def size(self):  # 目前buffer中数据的数量
        return len(self.buffer)

    #清空经验池
    def clear(self):
        self.buffer.clear()
        self.counter = 0
