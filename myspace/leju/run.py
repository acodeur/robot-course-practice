# ********************
# Author : z2h
# Last Modification : 
# Comment : 
#   默认配置，暂定就是开启一些业务相关结点
# ********************

from . import nodes

__all__ = ["run"]

def run():
    """默认的运行函数
    启动一些具体任务相关的结点
    定义一些动作？
    """
    nodes.init_nodes()
