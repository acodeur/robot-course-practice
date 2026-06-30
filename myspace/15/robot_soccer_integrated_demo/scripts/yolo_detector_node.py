#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import re

import numpy as np
import rospy
import rospkg
from sensor_msgs.msg import Image
from std_msgs.msg import Float32MultiArray, MultiArrayDimension


def _resolve_ros_find(path):
    pattern = re.compile(r"\$\(find\s+([A-Za-z0-9_]+)\)")
    rospack = rospkg.RosPack()
    this_package_path = None

    def replace(match):
        package_name = match.group(1)
        try:
            return rospack.get_path(package_name)
        except rospkg.ResourceNotFound:
            nonlocal this_package_path
            if this_package_path is None:
                this_package_path = rospack.get_path("robot_soccer_integrated_demo")
            sibling_path = os.path.join(os.path.dirname(this_package_path), package_name)
            if os.path.isdir(sibling_path):
                return sibling_path
            raise

    return pattern.sub(replace, path)


class YoloDetectorNode:
    def __init__(self):
        rospy.init_node("yolo_detector_node")

        self.model_path = _resolve_ros_find(
            rospy.get_param(
                "~model_path",
                "$(find robot_soccer_integrated_demo)/models/yolo11n.pt",
            )
        )
        self.confidence = rospy.get_param("~confidence", 0.10)
        self.imgsz = rospy.get_param("~imgsz", 320)
        self.target_class = rospy.get_param("~target_class", "sports ball")
        self.accept_any_ball_class = rospy.get_param("~accept_any_ball_class", True)
        self.debug_all_classes = rospy.get_param("~debug_all_classes", True)
        self.publish_debug_image = rospy.get_param("~publish_debug_image", True)
        self.fallback_color_circle = rospy.get_param("~fallback_color_circle", True)
        self.publish_rate_limit = rospy.get_param("~publish_rate_limit", 10.0)
        self.min_period = 1.0 / max(self.publish_rate_limit, 1e-6)
        self.last_predict_time = rospy.Time(0)
        self.last_image_log_time = rospy.Time(0)

        self.hsv_lower = np.array(rospy.get_param("~fallback_hsv_lower", [5, 80, 80]), dtype=np.uint8)
        self.hsv_upper = np.array(rospy.get_param("~fallback_hsv_upper", [30, 255, 255]), dtype=np.uint8)
        self.fallback_min_radius = int(rospy.get_param("~fallback_min_radius", 4))
        self.fallback_max_radius = int(rospy.get_param("~fallback_max_radius", 80))

        self.cv2 = None
        self.model = None
        self.model_ready = False

        self.pub = rospy.Publisher("vision/detections", Float32MultiArray, queue_size=10)
        self.debug_pub = rospy.Publisher("yolo/debug_image", Image, queue_size=2)
        self.sub = rospy.Subscriber(
            "camera/image_raw", Image, self._image_callback, queue_size=1, buff_size=2**24
        )

        self._load_cv2()
        self._load_model()

    def _load_cv2(self):
        try:
            import cv2
        except ImportError as exc:
            rospy.logwarn("OpenCV unavailable; YOLO debug/fallback disabled: %s", exc)
            return
        self.cv2 = cv2

    def _load_model(self):
        try:
            from ultralytics import YOLO
        except ImportError as exc:
            rospy.logerr("Ultralytics is not installed; YOLO detector disabled: %s", exc)
            return

        if not os.path.exists(self.model_path):
            rospy.logerr("YOLO model not found; detector disabled: %s", self.model_path)
            return

        self.model = YOLO(self.model_path)
        self.model_ready = True
        rospy.loginfo("YOLO model loaded: %s", self.model_path)
        rospy.loginfo(
            "YOLO params: conf=%.2f imgsz=%s target_class=%s accept_any_ball=%s fallback=%s",
            self.confidence,
            self.imgsz,
            self.target_class,
            self.accept_any_ball_class,
            self.fallback_color_circle,
        )

    def _image_callback(self, msg):
        now = rospy.Time.now()
        if (
            self.last_predict_time != rospy.Time(0)
            and (now - self.last_predict_time).to_sec() < self.min_period
        ):
            return
        self.last_predict_time = now

        try:
            image = self._image_to_bgr8(msg)
        except Exception as exc:
            rospy.logwarn_throttle(1.0, "image conversion failed: %s", exc)
            return

        rospy.loginfo_throttle(
            2.0,
            "YOLO received image: %dx%d encoding=%s",
            msg.width,
            msg.height,
            msg.encoding,
        )

        best = None
        detections = []
        if self.model_ready:
            best, detections = self._run_yolo(image)

        debug = image.copy() if self.publish_debug_image else None
        if debug is not None:
            self._draw_yolo_debug(debug, detections)

        if best is not None:
            self._publish_detection(best, image.shape[1], image.shape[0])
            if debug is not None:
                self._draw_detection(debug, best, (0, 255, 0), "YOLO")
                self.debug_pub.publish(self._image_from_bgr8(msg.header, debug))
            return

        rospy.logwarn_throttle(
            2.0,
            "YOLO found no accepted ball detection; raw detections=%s",
            ", ".join(["{}:{:.2f}".format(d[1], d[0]) for d in detections[:5]]) or "none",
        )

        fallback = self._fallback_circle(image) if self.fallback_color_circle else None
        if fallback is not None:
            self._publish_detection(fallback, image.shape[1], image.shape[0])
            if debug is not None:
                self._draw_detection(debug, fallback, (0, 200, 255), "FALLBACK")
        elif debug is not None:
            self.cv2.putText(debug, "NO BALL", (20, 40), self.cv2.FONT_HERSHEY_SIMPLEX, 1.0, (0, 0, 255), 2)

        if debug is not None:
            self.debug_pub.publish(self._image_from_bgr8(msg.header, debug))

    def _run_yolo(self, image):
        try:
            results = self.model.predict(
                source=image,
                imgsz=self.imgsz,
                conf=self.confidence,
                verbose=False,
            )
        except Exception as exc:
            rospy.logwarn_throttle(1.0, "YOLO inference failed: %s", exc)
            return None, []

        if not results:
            return None, []

        result = results[0]
        names = result.names
        best = None
        detections = []

        for box in result.boxes:
            cls_id = int(box.cls[0])
            class_name = names.get(cls_id, str(cls_id))
            confidence = float(box.conf[0])
            x1, y1, x2, y2 = [float(v) for v in box.xyxy[0]]
            detections.append((confidence, class_name, cls_id, x1, y1, x2, y2))

            class_ok = class_name == self.target_class
            if self.accept_any_ball_class and "ball" in class_name.lower():
                class_ok = True
            if not class_ok:
                continue
            if best is None or confidence > best[0]:
                best = (confidence, class_name, cls_id, x1, y1, x2, y2)

        rospy.loginfo_throttle(
            2.0,
            "YOLO raw detections: %s",
            ", ".join(["{}:{:.2f}".format(d[1], d[0]) for d in detections[:5]]) or "none",
        )
        return best, detections

    def _fallback_circle(self, image):
        if self.cv2 is None:
            return None
        cv2 = self.cv2
        hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
        mask = cv2.inRange(hsv, self.hsv_lower, self.hsv_upper)
        mask = cv2.GaussianBlur(mask, (7, 7), 0)
        circles = cv2.HoughCircles(
            mask,
            cv2.HOUGH_GRADIENT,
            dp=1.2,
            minDist=30.0,
            param1=80.0,
            param2=12.0,
            minRadius=self.fallback_min_radius,
            maxRadius=self.fallback_max_radius,
        )
        if circles is None:
            return None

        height, width = image.shape[:2]
        best = None
        best_score = -1.0
        for x, y, radius in np.round(circles[0, :]).astype("int"):
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
                best = (1.0, "fallback_circle", -1, float(x - radius), float(y - radius), float(x + radius), float(y + radius))
                best_score = score
        return best

    def _publish_detection(self, detection, width, height):
        confidence, _class_name, cls_id, x1, y1, x2, y2 = detection
        cx = 0.5 * (x1 + x2)
        cy = 0.5 * (y1 + y2)
        box_w = max(0.0, x2 - x1)
        box_h = max(0.0, y2 - y1)

        msg_out = Float32MultiArray()
        msg_out.layout.dim.append(MultiArrayDimension(label="fields", size=6, stride=6))
        msg_out.data = [
            (cx - 0.5 * width) / (0.5 * width),
            (cy - 0.5 * height) / (0.5 * height),
            box_w / float(width),
            box_h / float(height),
            confidence,
            float(cls_id),
        ]
        self.pub.publish(msg_out)

    def _draw_yolo_debug(self, image, detections):
        if self.cv2 is None or not self.debug_all_classes:
            return
        for confidence, class_name, _cls_id, x1, y1, x2, y2 in detections:
            color = (180, 180, 180)
            if class_name == self.target_class or "ball" in class_name.lower():
                color = (255, 0, 0)
            self._draw_box(image, x1, y1, x2, y2, color, "{} {:.2f}".format(class_name, confidence))

    def _draw_detection(self, image, detection, color, label):
        confidence, class_name, _cls_id, x1, y1, x2, y2 = detection
        self._draw_box(image, x1, y1, x2, y2, color, "{} {} {:.2f}".format(label, class_name, confidence))

    def _draw_box(self, image, x1, y1, x2, y2, color, label):
        if self.cv2 is None:
            return
        cv2 = self.cv2
        p1 = (int(x1), int(y1))
        p2 = (int(x2), int(y2))
        cv2.rectangle(image, p1, p2, color, 2)
        cv2.putText(image, label, (p1[0], max(20, p1[1] - 6)), cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 1)

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
        YoloDetectorNode()
        rospy.spin()
    except rospy.ROSInterruptException:
        pass
