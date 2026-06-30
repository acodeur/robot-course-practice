#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import numpy as np
import rospy
from sensor_msgs.msg import Image
from std_msgs.msg import Float32MultiArray, MultiArrayDimension


class HoughCircleDetectorNode:
    def __init__(self):
        rospy.init_node("hough_circle_detector_node")

        self.publish_rate_limit = rospy.get_param("~publish_rate_limit", 15.0)
        self.min_period = 1.0 / max(self.publish_rate_limit, 1e-6)
        self.last_process_time = rospy.Time(0)

        self.hsv_lower = np.array(rospy.get_param("~hsv_lower", [5, 80, 80]), dtype=np.uint8)
        self.hsv_upper = np.array(rospy.get_param("~hsv_upper", [30, 255, 255]), dtype=np.uint8)
        self.blur_kernel = int(rospy.get_param("~blur_kernel", 7))
        self.dp = rospy.get_param("~dp", 1.2)
        self.min_dist = rospy.get_param("~min_dist", 30.0)
        self.param1 = rospy.get_param("~param1", 80.0)
        self.param2 = rospy.get_param("~param2", 12.0)
        self.min_radius = int(rospy.get_param("~min_radius", 4))
        self.max_radius = int(rospy.get_param("~max_radius", 80))
        self.publish_debug_image = rospy.get_param("~publish_debug_image", True)

        self.cv2 = None
        self.ready = self._load_cv2()

        self.pub = rospy.Publisher("vision/detections", Float32MultiArray, queue_size=10)
        self.debug_pub = rospy.Publisher("hough/debug_image", Image, queue_size=2)
        self.sub = rospy.Subscriber(
            "camera/image_raw", Image, self._image_callback, queue_size=1, buff_size=2**24
        )

    def _load_cv2(self):
        try:
            import cv2
        except ImportError as exc:
            rospy.logerr("OpenCV is not installed; Hough detector disabled: %s", exc)
            return False
        self.cv2 = cv2
        rospy.loginfo("hough_circle_detector_node: camera/image_raw -> vision/detections")
        return True

    def _image_callback(self, msg):
        if not self.ready:
            return

        now = rospy.Time.now()
        if (
            self.last_process_time != rospy.Time(0)
            and (now - self.last_process_time).to_sec() < self.min_period
        ):
            return
        self.last_process_time = now

        try:
            image = self._image_to_bgr8(msg)
        except Exception as exc:
            rospy.logwarn_throttle(1.0, "image conversion failed: %s", exc)
            return

        detection = self._detect_circle(image)
        if detection is None:
            if self.publish_debug_image:
                self.debug_pub.publish(self._image_from_bgr8(msg.header, image))
            return

        cx, cy, radius = detection
        height, width = image.shape[:2]

        msg_out = Float32MultiArray()
        msg_out.layout.dim.append(MultiArrayDimension(label="fields", size=6, stride=6))
        msg_out.data = [
            (cx - 0.5 * width) / (0.5 * width),
            (cy - 0.5 * height) / (0.5 * height),
            (2.0 * radius) / float(width),
            (2.0 * radius) / float(height),
            1.0,
            0.0,
        ]
        self.pub.publish(msg_out)

        if self.publish_debug_image:
            debug = image.copy()
            self.cv2.circle(debug, (int(cx), int(cy)), int(radius), (0, 255, 0), 2)
            self.cv2.circle(debug, (int(cx), int(cy)), 2, (0, 0, 255), 3)
            self.debug_pub.publish(self._image_from_bgr8(msg.header, debug))

    def _detect_circle(self, image):
        cv2 = self.cv2
        hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
        mask = cv2.inRange(hsv, self.hsv_lower, self.hsv_upper)
        if self.blur_kernel > 1:
            kernel = self.blur_kernel if self.blur_kernel % 2 == 1 else self.blur_kernel + 1
            mask = cv2.GaussianBlur(mask, (kernel, kernel), 0)

        circles = cv2.HoughCircles(
            mask,
            cv2.HOUGH_GRADIENT,
            dp=self.dp,
            minDist=self.min_dist,
            param1=self.param1,
            param2=self.param2,
            minRadius=self.min_radius,
            maxRadius=self.max_radius,
        )
        if circles is None:
            return None

        circles = np.round(circles[0, :]).astype("int")
        height, width = image.shape[:2]
        best = None
        best_score = -1.0

        for x, y, radius in circles:
            if x < 0 or y < 0 or x >= width or y >= height or radius <= 0:
                continue
            x1 = max(0, x - radius)
            x2 = min(width, x + radius)
            y1 = max(0, y - radius)
            y2 = min(height, y + radius)
            if x2 <= x1 or y2 <= y1:
                continue
            score = float(np.mean(mask[y1:y2, x1:x2])) * radius
            if score > best_score:
                best = (float(x), float(y), float(radius))
                best_score = score

        return best

    def _image_to_bgr8(self, msg):
        encoding = msg.encoding.lower()
        if encoding not in ("rgb8", "bgr8", "rgba8", "bgra8", "mono8", "8uc3"):
            raise ValueError("unsupported image encoding: {}".format(msg.encoding))

        channels = 1 if encoding == "mono8" else 3
        source_channels = 4 if encoding in ("rgba8", "bgra8") else channels
        expected = msg.step * msg.height
        data = np.frombuffer(msg.data, dtype=np.uint8, count=expected)
        rows = data.reshape((msg.height, msg.step))
        image = rows[:, : msg.width * source_channels]

        if source_channels == 1:
            image = image.reshape((msg.height, msg.width))
            return np.ascontiguousarray(np.repeat(image[:, :, None], 3, axis=2))

        image = image.reshape((msg.height, msg.width, source_channels))
        if source_channels == 4:
            image = image[:, :, :3]
        if encoding in ("rgb8", "rgba8"):
            image = image[:, :, ::-1]
        return np.ascontiguousarray(image)

    def _image_from_bgr8(self, header, image):
        msg = Image()
        msg.header = header
        msg.height = image.shape[0]
        msg.width = image.shape[1]
        msg.encoding = "bgr8"
        msg.is_bigendian = 0
        msg.step = msg.width * 3
        msg.data = np.ascontiguousarray(image).tobytes()
        return msg


if __name__ == "__main__":
    try:
        HoughCircleDetectorNode()
        rospy.spin()
    except rospy.ROSInterruptException:
        pass
