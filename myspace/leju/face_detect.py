# #!/usr/bin/env python
# #-*- coding:utf-8 -*-
# # ********************
# # Author : KKKK
# # Last Modification : 
# # Comment : 
# #   定义基本 人脸检测 接口
# #   接口数据定义格式请参考 smart_face_pkg/接口文档说明.md
# # ********************


import rospy
from aelos_smart_ros.srv import smart_face, smart_faceRequest, smart_faceResponse

# 调试开关
DEBUG = False

# 性别列表
gender_list = ["male", "female"]

# 儿童、少年、青年、中年、老年
age_list = ["children", "teenager", "youth", "middle-aged", "elderly"]

# 表情列表
emotion_list = ["neutral", "angry", "disgust", "fear", "happy", "sad", "surprise", "pouty", "grimace"]

# ****************************************
#                  服务调用
# ****************************************
def face_server_detect(camera_id=0, wait_time=0):
    rospy.wait_for_service('smart_face_server')
    val = rospy.ServiceProxy('smart_face_server', smart_face)
    resp1 = val(camera_id, wait_time)
    return resp1

# ****************************************
#                  check检查范围
# ****************************************
def age_check(age):
    if 0 < age <= 10:
        return "children"     # 儿童
    elif 11 <= age <= 20:
        return "teenager"     # 少年
    elif 21 <= age <= 40:
        return "youth"        # 青年
    elif 41 <= age <= 60:
        return "middle-aged"  # 中年
    else:
        return "elderly"      # 老年

# ****************************************
#            单个类别————接口调用  
# ****************************************
def face_gender_detect(x_seconds=1, gender="male", camera_string="head"):

    global gender_list

    start_time = rospy.get_time()
    elapsed_time = 0

    result = False

    if gender in gender_list:
        
        while elapsed_time < x_seconds:
            
            face_list = face_server_detect(camera_string, 0)

            # 符合条件
            if (face_list.is_face) and (gender == face_list.gender):
                result = True
                break 
            else:
                rospy.sleep(1)
                elapsed_time = rospy.get_time() - start_time
        
    return result

def face_age_detect(x_seconds=1, age="children", camera_string="head"):

    global age_list

    start_time = rospy.get_time()
    elapsed_time = 0

    result = False

    if age in age_list:
        
        while elapsed_time < x_seconds:
            
            face_list = face_server_detect(camera_string, 0)
            pre_target = age_check(face_list.age)

            # 符合条件
            if (face_list.is_face) and (age == pre_target):
                result = True
                break 
            else:
                rospy.sleep(1)
                elapsed_time = rospy.get_time() - start_time

    return result

def face_emotion_detect(x_seconds=1, emotion="neutral", camera_string="head"):

    global emotion_list 

    result = False
    
    start_time = rospy.get_time()
    elapsed_time = 0
    
    if emotion in emotion_list:
        
        while elapsed_time < x_seconds:
            
            face_list = face_server_detect(camera_string, 0)

            # 符合条件
            if (face_list.is_face) and (emotion == face_list.emotion):
                result = True
                break 
            else:
                rospy.sleep(1)
                elapsed_time = rospy.get_time() - start_time
    
    return result

# ****************************************
#            所有类别————接口调用  
# ****************************************

def is_desired_face(response, desired_gender=None, desired_age=None, desired_emotion=None):
    if not response.is_face:
        return False
    
    if desired_gender is not None and desired_gender.lower() != response.gender.lower():
        return False
    
    if desired_age is not None and age_check(response.age) != desired_age:
        return False
    
    if desired_emotion is not None and desired_emotion.lower() != response.emotion.lower():
        return False
    
    return True

def face_all_detect(x_seconds, desired_gender=None, desired_age=None, desired_emotion=None, camera_string="head"):
    
    start_time = rospy.get_time()
    elapsed_time = 0

    result = False

    while elapsed_time < x_seconds:
        face_list = face_server_detect(camera_string, 0)

        if is_desired_face(face_list, desired_gender, desired_age, desired_emotion):
            if DEBUG:
                print("Desired face detected!")
                print(f"Age: {face_list.age}")
                print(f"Gender: {face_list.gender}")
                print(f"Emotion: {face_list.emotion}")
                print(" -------- ")
            
            result = True
            break
        else:
            rospy.sleep(1)
            elapsed_time = rospy.get_time() - start_time

    return result

if __name__ == "__main__":

    rospy.init_node("leju_smart_face")
    
    # # 以下为单例测试
    # result_gender_id = face_gender_detect(5, "male", "head")
    # print("result_gender_id : ", result_gender_id)

    # result_age_id = face_age_detect(5, "Children", "head")
    # print("result_age_id : ", result_gender_id)

    # result_emotion_id = face_emotion_detect(5, "happy", "head")
    # print("result_emotion_id : ", result_emotion_id)

    # result_all_id_1 = face_all_detect(3, None, None, None, "head")
    # print("result_all_id_1 : ", result_all_id_1)

    # result_all_id_2 = face_all_detect(5, "male", None, "happy", "head")
    # print("result_all_id_2 : ", result_all_id_2)

    # result_all_id_3 = face_all_detect(2, "male", "Teenager", None, "head")
    # print("result_all_id_3 : ", result_all_id_3)