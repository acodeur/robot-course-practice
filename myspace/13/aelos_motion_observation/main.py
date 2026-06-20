import sys
sys.path.append("/home/lemon/catkin_ws/src/aelos_smart_ros")

from leju import *

leju_variable__E6_89_8B_E6_9F_84_E6_8C_89_E9_94_AE_E5_80_BC = None



def main():
    nodes.node_initial()
    try:


        while True:
            leju_variable__E6_89_8B_E6_9F_84_E6_8C_89_E9_94_AE_E5_80_BC = get_key.key()
            if leju_variable__E6_89_8B_E6_9F_84_E6_8C_89_E9_94_AE_E5_80_BC == 193:
                base_action.action('向前慢走3步')
                base_action.action('向左平移1步')
                base_action.action('向右平移1步')
                base_action.action('向后慢走1步')
                base_action.action('向后慢走1步')
                base_action.action('向后慢走1步')
                break

    except Exception as e:
        nodes.serror(e)
        exit(2)
    finally:
        nodes.finishsend()
if __name__ == "__main__":
    print ("Run custom project")
    main()
