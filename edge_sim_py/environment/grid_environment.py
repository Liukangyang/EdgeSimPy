import torch
# import gym
import numpy as np


class GridEnvironment():
    '''
    环境定义
    '''
    def __init__(self,grid=None,destination=None):
        self.state = None

        self.action = None

        # 网格定义,1表示有障碍物
        if grid:
            self.grid = grid
        else:
            self.grid=[
                [0,0,0,0,0,0,0,0],
                [0,0,0,0,0,0,1,0],
                [0,0,1,0,0,0,0,0],
                [0,1,0,0,1,0,0,0],
                [0,0,0,0,0,1,0,0],
                [0,1,0,0,0,0,0,2],
            ]
        #动作映射:上下左右
        self.action_mapping = {
            0:[-1,0],  #上
            1:[1,0],   #下
            2:[0,-1],  #左
            3:[0,1],   #右
        }
        #目的地坐标
        if destination:
            self.destination = destination
        else:
            self.destination = [ len(self.grid)-1,len(self.grid[0])-1]

        # 状态和动作维度
        self.state_dim = 2
        self.action_dim = len(self.action_mapping)

        #惩罚系数
        self.p1= -20  #超出边界的惩罚
        self.p2= -20  #遇到障碍物的惩罚
        self.target_reward = +50
        #奖励值 :与当前网格距离目的地的距离成反比
        self.reward = 0

    '''
    重置初始位置
    '''
    def reset(self):
        init_row = 0
        init_col = 0

        #TODO:增加随机性
        if np.random.random() > 0.5:
            init_col = np.random.randint(1,len(self.grid[0]))
        else:init_row = np.random.randint(1,len(self.grid))

        state = [init_row,init_col]
        self.state=state
        return state


    def step(self,action):
        # 将动作进行映射
        row_action,col_action = self.action_mapping[action]
        ori_row,ori_col = self.state
        new_row,new_col = ori_row+row_action,ori_col+col_action

        reward = 0
        new_state = None
        done = False

        # 判断是否超出边界
        if new_row < 0 or new_row >= len(self.grid) or new_col < 0 or new_col >= len(self.grid[0]):
                reward = self.p1
                new_state = [ori_row,ori_col]
        else:
                # 是否遇到障碍物
                if self.grid[new_row][new_col]==1:
                    reward = self.p2
                    new_state = [ori_row,ori_col]
                # 是否到达目的地
                elif self.grid[new_row][new_col]==2:
                    reward = self.target_reward
                    new_state = [new_row,new_col]
                    done = True
                else: #0
                    # reward = -self.get_Distance([new_row,new_col]) #以距离作为惩罚
                    reward = -5 + 5/self.get_Distance([new_row,new_col])#正常格子固定惩罚
                    new_state = [new_row,new_col]

        self.state=new_state
        self.reward=reward
        return new_state,reward,done

    def get_Distance(self,state):
        return np.sqrt((state[0]-self.destination[0])**2+
                (state[1]-self.destination[1])**2)
    '''
    打印当前位置
    '''
    def render(self):
        print(f"current pos:[{self.state[0]},{self.state[1]}]")