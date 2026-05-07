import torch
import torch.nn.functional as F
from torch.distributions import Categorical
from .replay_buffer import ReplayBuffer
from .net import PolicyNet,ValueNet,ActorNetwork, CriticNetwork
from .rl_utils import *

''' PPO算法,采用截断方式 '''
class PPO2:
    def __init__(self, state_dim, hidden_dim, action_dim, actor_lr, critic_lr,
                 lmbda, epochs, eps, gamma, batch_size,device):
        self.actor = ActorNetwork(state_dim, hidden_dim, action_dim).to(device)
        self.critic = CriticNetwork(state_dim, hidden_dim).to(device)
        self.actor_lr = actor_lr
        self.critic_lr = critic_lr
        self.actor_optimizer = torch.optim.Adam(self.actor.parameters(),lr=actor_lr)
        self.critic_optimizer = torch.optim.Adam(self.critic.parameters(),lr=critic_lr)
        self.gamma = gamma
        self.lmbda = lmbda
        self.epochs = epochs  # 一条序列的数据用来训练轮数
        self.eps = eps  # PPO中截断范围的参数
        self.entropy_coef = 0.01 #策略熵系数
        self.batch_size = batch_size
        self.device = device

        # 更新次数
        self.steps = 0

        # 初始和终止学习率
        self.start_actor_lr = self.actor_lr
        self.end_actor_lr = 1e-6
        self.start_critic_lr = self.critic_lr
        self.end_critic_lr = 2e-6

    def take_action(self, state,memory):
        state = torch.tensor(state, dtype=torch.float).to(self.device)
        probs = self.actor(state)
        action_dist = torch.distributions.Categorical(probs)
        action = action_dist.sample() #采样获取动作

        memory.states.append(state)  # Store state in memory
        memory.actions.append(action)  # Store action in memory
        memory.logprobs.append(action_dist.log_prob(action))  # Store log probability of the action

        return action.item()

    #学习率衰减机制
    def lr_decay(self):
        #1.线性衰减
        actor_lr_decay = (self.start_actor_lr - self.end_actor_lr)/500
        critic_lr_decay = (self.start_critic_lr - self.end_critic_lr)/500
        self.actor_lr = max(self.end_actor_lr,self.actor_lr - actor_lr_decay)
        self.critic_lr = max(self.end_critic_lr,self.critic_lr - critic_lr_decay)
        self.actor_optimizer = torch.optim.Adam(self.actor.parameters(),lr=self.actor_lr)
        self.critic_optimizer = torch.optim.Adam(self.critic.parameters(),lr=self.critic_lr)

    def update(self, memory):
        # Convert memory to tensors
        old_states = torch.stack(memory.states).to(self.device).detach()  # Convert states to tensor
        next_states = torch.stack(memory.next_states).to(self.device).detach()  # Convert states to tensor
        old_actions = torch.stack(memory.actions).to(self.device).detach()  # Convert actions to tensor
        old_log_probs = torch.stack(memory.logprobs).to(self.device).detach()  # Convert log probabilities to tensor
        rewards = torch.stack(memory.rewards).to(self.device).detach()

        # td_target = rewards + self.gamma * self.critic(next_states) * (1 - dones)
        td_target = rewards + self.gamma * self.critic(next_states).detach().squeeze()
        #组装新的样本集合
        sample_dict = {'states':old_states, 'actions':old_actions, 'old_log_probs':old_log_probs,'td_target':td_target}
        total_samples  = len(sample_dict['states'])
        mini_batch_size = min(self.batch_size, total_samples)

        total_actor_loss = 0
        for _ in range(self.epochs):
            #每次抽取一批样本
            indices = np.random.choice(total_samples, size=mini_batch_size, replace=False)
            sample_states = sample_dict['states'][indices]
            sample_actions = sample_dict['actions'][indices]
            sample_old_log_probs = sample_dict['old_log_probs'][indices]
            sample_td_target = sample_dict['td_target'][indices]

            td_delta = sample_td_target - self.critic(sample_states).detach().squeeze()  #
            advantage = compute_advantage(self.gamma, self.lmbda, td_delta.cpu()).to(self.device)  #

            #计算策略熵和log_probs
            #TODO:
            action_probs = self.actor(sample_states)
            dist = Categorical(probs = action_probs)
            #TODO:sample_actions维度需为(样本数量,)，即必须是一维的
            log_probs = dist.log_prob(sample_actions)
            entropy = dist.entropy() # Compute entropy for exploration
            # log_probs = torch.log(self.actor(sample_states).gather(1, sample_actions))

            ratio = torch.exp(log_probs - sample_old_log_probs)
            surr1 = ratio * advantage
            surr2 = torch.clamp(ratio, 1 - self.eps,1 + self.eps) * advantage  # 截断
            # actor_loss =  - torch.mean(torch.min(surr1, surr2)) - self.entropy_coef * entropy.mean()
            actor_loss = - torch.mean(torch.min(surr1, surr2))
            critic_loss = torch.mean(
                F.mse_loss(self.critic(sample_states).squeeze(), sample_td_target))
            #
            total_actor_loss += actor_loss
            actor_loss.backward()
            critic_loss.backward()
            self.actor_optimizer.step()
            self.critic_optimizer.step()
            self.actor_optimizer.zero_grad()
            self.critic_optimizer.zero_grad()

        self.steps += 1
        return total_actor_loss / self.epochs


    # 保存模型
    def save_model(self, file:str):
        torch.save(self.actor.state_dict(), file)

    # 导入模型
    def load_model(self, file:str):
        state_dict = torch.load(file,map_location='cpu')
        self.actor.load_state_dict(state_dict)