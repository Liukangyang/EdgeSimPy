import torch
import torch.nn.functional as F
from torch.distributions import Categorical
from .replay_buffer import ReplayBuffer
from .net import PolicyNet,ValueNet,ActorNetwork,ActorNetwork2,CriticNetwork
from .rl_utils import *

''' PPO算法,采用截断方式 '''
class DoublePPO:
    def __init__(self, state_dim, hidden_dim, action_dim, actor1_lr,actor2_lr, critic_lr,
                 lmbda, epochs, eps, gamma, batch_size,device):
        self.actor1_lr = actor1_lr
        self.actor2_lr = actor2_lr
        self.critic_lr = critic_lr
        #两个actor网络
        self.actor1 = ActorNetwork(state_dim, hidden_dim, 2).to(device)
        self.actor2 = ActorNetwork2(state_dim + 1 , hidden_dim, action_dim).to(device)
        self.critic = CriticNetwork(state_dim, hidden_dim).to(device)
        self.actor1_optimizer = torch.optim.Adam(self.actor1.parameters(),lr=self.actor1_lr)
        self.actor2_optimizer = torch.optim.Adam(self.actor2.parameters(),lr=self.actor2_lr)
        self.critic_optimizer = torch.optim.Adam(self.critic.parameters(),lr=self.critic_lr)
        self.gamma = gamma
        self.lmbda = lmbda
        self.epochs = epochs  # 一条序列的数据用来训练轮数
        self.eps = eps  # PPO中截断范围的参数
        self.entropy_coef = 0.01 #策略熵系数
        self.batch_size = batch_size
        self.device = device

        # 更新次数
        self.steps = 0

        self.decay_ratio = 0.993 #2e-6=>  <1e-6 (200次迭代)
        self.end_lr = 1e-5

    def take_action(self, state):
        #第一个actor
        state = torch.tensor(state, dtype=torch.float).to(self.device)
        action1_probs = self.actor1(state)
        action1_dist = torch.distributions.Categorical(action1_probs)
        action1 = action1_dist.sample()
        action1 = torch.tensor([action1.item()])
        #第二个actor的输入
        action2,actor2_log_probs= self.actor2.get_action(action1,state)
        #返回组合动作
        return (int(action1.item()),int(action2.item()))

    #学习率衰减机制
    def lr_decay(self):
        #第2个actor网络学习率阶跃衰减
        self.actor2_lr = max(self.end_lr,self.actor2_lr * self.decay_ratio)
        self.actor2_optimizer = torch.optim.Adam(self.actor2.parameters(),lr=self.actor2_lr)

    def update(self, transition_dict):
        #TODO:transition_dict包含有(s,a1,a2,r,s')
        states = torch.tensor(transition_dict['states'],dtype=torch.float).to(self.device) #
        action1 = torch.tensor(transition_dict['action1']).view(-1, 1).to(self.device)
        action2 = torch.tensor(transition_dict['action2']).view(-1, 1).to(self.device)
        rewards = torch.tensor(transition_dict['rewards'],dtype=torch.float).view(-1, 1).to(self.device)
        next_states = torch.tensor(transition_dict['next_states'],
                                   dtype=torch.float).to(self.device)
        # dones = torch.tensor(transition_dict['dones'],dtype=torch.float).view(-1, 1).to(self.device)

        #actor1
        actor1_old_log_probs,_ = self.actor1.evaluate(states,action1)
        #actor2
        actor2_old_log_probs,_ = self.actor2.evaluate(states,action1,action2)

        td_target = rewards + self.gamma * self.critic(next_states)
        #组装新的样本集合
        sample_dict = {'states':states, 'action1':action1, 'actor1_old_log_probs':actor1_old_log_probs,
                       'action2':action2,'actor2_old_log_probs':actor2_old_log_probs,'td_target':td_target}
        total_samples  = len(sample_dict['states'])
        mini_batch_size = min(self.batch_size, total_samples)

        total_actor_loss = 0
        for _ in range(self.epochs):
            #每次抽取一批样本
            indices = np.random.choice(total_samples, size=mini_batch_size, replace=False)
            sample_states = sample_dict['states'][indices]
            sample_action1 = sample_dict['action1'][indices]
            sample_action2 = sample_dict['action2'][indices]
            sample_actor1_old_log_probs = sample_dict['actor1_old_log_probs'][indices]
            sample_actor2_old_log_probs = sample_dict['actor2_old_log_probs'][indices]
            sample_td_target = sample_dict['td_target'][indices]
            # TODO:advantage需要每次重新计算
            td_delta = sample_td_target - self.critic(sample_states)  #
            advantage = compute_advantage(self.gamma, self.lmbda, td_delta.cpu()).to(self.device).detach()  #

            #actor1
            actor1_log_probs,actor1_entropy = self.actor1.evaluate(sample_states,sample_action1)
            actor1_ratio = torch.exp(actor1_log_probs - sample_actor1_old_log_probs).detach()
            actor1_surr1 = actor1_ratio * advantage
            actor1_surr2 = torch.clamp(actor1_ratio, 1 - self.eps,1 + self.eps) * advantage  # 截断
            #actor1损失函数
            actor1_loss =  -torch.mean(torch.min(actor1_surr1, actor1_surr2)) - self.entropy_coef * actor1_entropy.mean()

            #actor2
            actor2_log_probs,actor2_entropy = self.actor2.evaluate(sample_states,sample_action1,sample_action2)
            actor2_ratio = torch.exp(actor2_log_probs - sample_actor2_old_log_probs).detach()
            actor2_surr1 = actor2_ratio * advantage
            actor2_surr2 = torch.clamp(actor2_ratio, 1 - self.eps,1 + self.eps) * advantage  # 截断
            #actor2损失函数
            actor2_loss =  -torch.mean(torch.min(actor2_surr1, actor2_surr2)) - self.entropy_coef * actor2_entropy.mean()

            #critic损失函数
            critic_loss = torch.mean(F.mse_loss(self.critic(sample_states), sample_td_target.detach()))
            #
            total_actor_loss += (actor1_loss.item()+actor2_loss.item())

            self.actor1_optimizer.zero_grad()
            actor1_loss.backward()
            self.actor1_optimizer.step()

            self.actor2_optimizer.zero_grad()
            actor2_loss.backward()
            self.actor2_optimizer.step()

            self.critic_optimizer.zero_grad()
            critic_loss.backward()
            self.critic_optimizer.step()

        '''
        for _ in range(self.epochs):
            # TODO:advantage需要每次重新计算
            td_delta = td_target - self.critic(states)  #
            advantage = compute_advantage(self.gamma, self.lmbda, td_delta.cpu()).to(self.device)  #

            log_probs = torch.log(self.actor(states).gather(1, actions))
            ratio = torch.exp(log_probs - old_log_probs)
            surr1 = ratio * advantage
            surr2 = torch.clamp(ratio, 1 - self.eps,1 + self.eps) * advantage  # 截断
            actor_loss = torch.mean(-torch.min(surr1, surr2))  # PPO损失函数
            critic_loss = torch.mean(
                F.mse_loss(self.critic(states), td_target.detach()))
            #
            total_actor_loss += actor_loss
            actor_loss.backward()
            critic_loss.backward()
            self.actor_optimizer.step()
            self.critic_optimizer.step()
            self.actor_optimizer.zero_grad()
            self.critic_optimizer.zero_grad()
        '''
        self.steps += 1
        self.lr_decay()
        return total_actor_loss / self.epochs

    # 保存模型
    def save_model(self, file):
        torch.save(self.actor1.state_dict(), file+'actor1.pth')
        torch.save(self.actor2.state_dict(), file+'actor2.pth')

    # 导入模型
    def load_model(self, file):
        actor1_state_dict = torch.load(file+'actor1.pth')
        actor2_state_dict = torch.load(file+'actor2.pth')
        self.actor1.load_state_dict(actor1_state_dict)
        self.actor2.load_state_dict(actor2_state_dict)