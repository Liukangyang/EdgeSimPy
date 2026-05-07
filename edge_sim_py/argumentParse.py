import argparse

def parse_args():
    #创建解析器
    parser = argparse.ArgumentParser(description='Params for RL-PPO')

    #添加参数
    #训练 or 测试
    parser.add_argument('--train',action='store_true',default=False)
    parser.add_argument('--test', action='store_true', default=True)

    #选择模型
    parser.add_argument('-m','--model',type=str, default='none',help='强化学习模型')

    #选择策略
    parser.add_argument('-s','--strategy',type=str, default='dynamic')

    #训练/测试迭代次数
    parser.add_argument('-e','--episodes',type=int, default=100)

    #选择设
    parser.add_argument('-d','--device',type=str,default='cpu')

    #导入文件
    #配置文件
    parser.add_argument('--configfile',type=str, default='Test/config.yaml')
    #参数文件
    parser.add_argument('--paramsfile',type=str, default='Test/file/params.json')
    #拓扑文件
    parser.add_argument('--topofile', type=str, default='Test/file/test1.json')

    #保存结果文件路径
    parser.add_argument('--modelparams',type=str, default='params.pth')
    parser.add_argument('--reward',type=str, default='reward.pkl')
    parser.add_argument('--loss',type=str,default = 'loss.pkl')

    args = parser.parse_args()

    return args