import sys
sys.path.append("/home/lemon/catkin_ws/src/aelos_smart_ros")

from leju import *

LIGHT_UP_LIMIT = 120


def main():
    nodes.node_initial()
    trigger = False
    try:
        while True:
          light_val = sensor_port.get_gpio(1)
          if light_val > LIGHT_UP_LIMIT:
            if not trigger:
              print(f"光敏值：{light_val}，准备执行下蹲动作")
              base_action.action('下蹲')
              trigger = True
          else:
            if trigger:
              print(f"光敏值：{light_val}，准备恢复站立")
              base_action.action('站立')
              trigger = False

    except Exception as e:
        nodes.serror(e)
        exit(2)
    finally:
        nodes.finishsend()


if __name__ == "__main__":
    print ("Run Leju - 11.2 - 光敏-下蹲站立")
    main()
