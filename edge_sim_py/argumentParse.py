import argparse


def parse_Args():
    # 创建解析器
    parser = argparse.ArgumentParser(description='Params for RL-PPO')

    # 添加参数
    # 训练 or 测试
    parser.add_argument('--train', action='store_true', default=False, help='Work for train')
    parser.add_argument('--test', action='store_true', default=False, help='Work for test')

    # 选择模型
    parser.add_argument('-m', '--model', type=str, default='none', help='强化学习模型[ppo,dqn,....]')

    # 选择策略
    parser.add_argument('-s', '--strategy', type=str, default='random', help='strategy[EFT,EDA,EES,DRL,random]')

    # 训练/测试迭代次数
    parser.add_argument('-e', '--episodes', type=int, default=100, help='train/test episodes')

    # 最大任务数量
    parser.add_argument('-t', '--max_tasks', type=int, default=300, help='max num of tasks for one episode')

    # 选择设备
    parser.add_argument('-d', '--device', type=str, default='cpu', help='device')

    # 导入文件
    # 配置文件
    parser.add_argument('--configfile', type=str, default='Test/config.yaml', help='config file')
    # 参数文件
    parser.add_argument('--paramsfile', type=str, default='Test/file/params.json', help='params file')
    # 拓扑文件
    parser.add_argument('--topofile', type=str, default='Test/file/test1.json', help='topo file')

    # 保存结果文件路径
    parser.add_argument('--modelparams', type=str, default='params.pth',
                        help='The file path for saving model params dict')
    parser.add_argument('--reward', type=str, default='reward.pkl', help='The file path for saving reward result')
    parser.add_argument('--loss', type=str, default='loss.pkl', help='The file path for saving loss result')

    # 加载模型参数文件路径
    parser.add_argument('--model_dict_file', type=str, default='', help='The file path for model params dict')

    args = parser.parse_args()

    return args