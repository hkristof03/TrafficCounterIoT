import os
import traceback

import numpy as np
import cv2

from tclib.tctools import tctools as tct

log = tct.log


def intersect(A, B, C, D):
    return ccw(A, C, D) != ccw(B, C, D) and ccw(A, B, C) != ccw(A, B, D)


def ccw(A, B, C):
    return (C[1] - A[1]) * (B[0] - A[0]) > (B[1] - A[1]) * (C[0] - A[0])


class TrafficDetector:

    base_path = os.path.dirname(__file__)

    def __init__(
        self,
        model_name: str,
        path_weights: str,
        path_model_config: str,
        path_classes: str,
        kafka_input_topic: str,
        kafka_output_topic_traffic_count: str,
        kafka_output_topic_object_detections: str,
        confidence_threshold: float,
        threshold_nms: float
    ) -> None:
        self.model_name = model_name
        self.path_weights = os.path.join(
            TrafficDetector.base_path, *path_weights)
        self.path_model_config = os.path.join(
            TrafficDetector.base_path, *path_model_config)
        self.path_classes = os.path.join(
            TrafficDetector.base_path, *path_classes)
        self.class_map = self.get_class_map()
        self.kafka_input_topic = kafka_input_topic
        self.kafka_output_topic_tc = kafka_output_topic_traffic_count
        self.kafka_output_topic_od = kafka_output_topic_object_detections
        self.kafka_helper = tct.kafka
        self.td_schema_helper = tct.schema.create_helper("TrafficDetection")
        self.tc_schema_helper = tct.schema.create_helper("TrafficCount")
        self.net, self.ln = self.load_model()
        self.confidence_threshold = confidence_threshold
        self.threshold_nms = threshold_nms

    def get_class_map(self) -> dict:
        """

        :return:
        """
        with open(self.path_classes, 'r') as file:
            classes = file.readlines()
        classes = list(map(lambda x: x.replace('\n', ''), classes))
        class_map = dict(zip(list(range(len(classes))), classes))

        return class_map

    def load_model(self) -> tuple:
        """"""
        log.info(f"Loading YOLO from path  {self.path_weights}")
        net = cv2.dnn.readNetFromDarknet(self.path_model_config,
                                         self.path_weights)
        ln = net.getLayerNames()
        ln = [ln[i[0] - 1] for i in net.getUnconnectedOutLayers()]

        return net, ln

    def detect_traffic(self, message: dict) -> None:
        """
        """
        try:
            log.info(f"Received message: {message}")
            path_image = os.path.join(message['imagePath'], message['imageID'])
            (W, H) = (None, None)
            # read the next frame from the file
            frame = cv2.imread(path_image)

            # if the frame dimensions are empty, grab them
            if W is None or H is None:
                (H, W) = frame.shape[:2]
            # construct a blob from the input frame and then perform a forward
            # pass of the YOLO object detector, giving us our bounding boxes
            # and associated probabilities
            blob = cv2.dnn.blobFromImage(frame, 1 / 255.0, (416, 416),
                                         swapRB=True, crop=False)
            self.net.setInput(blob)
            layer_outputs = self.net.forward(self.ln)
            # initialize our lists of detected bounding boxes, confidences,
            # and class IDs, respectively
            boxes = []
            confidences = []
            class_ids = []
            # loop over each of the layer outputs
            for output in layer_outputs:
                # loop over each of the detections
                for detection in output:
                    # extract the class ID and confidence (i.e., probability)
                    # of the current object detection
                    scores = detection[5:]
                    class_id = np.argmax(scores)
                    confidence = scores[class_id]
                    # filter out weak predictions by ensuring the detected
                    # probability is greater than the minimum probability
                    if confidence > self.confidence_threshold:
                        # scale the bounding box coordinates back relative to
                        # the size of the image, keeping in mind that YOLO
                        # actually returns the center (x, y)-coordinates of
                        # the bounding box followed by the boxes' width and
                        # height
                        box = detection[0:4] * np.array([W, H, W, H])
                        (centerX, centerY, width, height) = box.astype("int")
                        # use the center (x, y)-coordinates to derive the top
                        # left corner of the bounding box
                        x = int(centerX - (width / 2))
                        y = int(centerY - (height / 2))
                        # update our list of bounding box coordinates,
                        # confidences, and class IDs
                        boxes.append([x, y, int(width), int(height)])
                        confidences.append(float(confidence))
                        class_ids.append(class_id)
            # apply non-maxima suppression to suppress weak, overlapping
            # bounding boxes
            idxs = cv2.dnn.NMSBoxes(
                boxes, confidences, self.confidence_threshold,
                self.threshold_nms
            )
            dets = []
            class_ids_nms = []
            if len(idxs) > 0:
                # loop over the indexes we are keeping
                for i in idxs.flatten():
                    (x, y) = (boxes[i][0], boxes[i][1])
                    (w, h) = (boxes[i][2], boxes[i][3])
                    dets.append([x, y, x + w, y + h, confidences[i]])
                    class_ids_nms.append(class_ids[i])
            else:
                log.info(
                    "Model did not recognise object on the road! The road is "
                    "possibly empty."
                )
                return

            detections = {
                "detection": True if dets else False,
                "numberOfObjects": len(dets),
                "detectedClasses": [self.class_map[i] for i in class_ids_nms],
                "boundingBoxes": boxes,
                "confidenceScores": confidences
            }
            td_msg = self.get_object_detection_schema(message, detections)
            tc_msg = self.get_traffic_count_schema(td_msg)
            self.td_schema_helper.validate(td_msg)
            self.tc_schema_helper.validate(tc_msg)
            self.kafka_helper.publish(self.kafka_output_topic_od, td_msg)
            self.kafka_helper.publish(self.kafka_output_topic_tc, tc_msg)
            log.info(f"Traffic detection message: {td_msg}")
            log.info(f"Traffic count message: {tc_msg}")

        except:
            log.error(
                f"Unexpected event occurred! Error: {traceback.format_exc()}"
            )

    def get_object_detection_schema(
        self,
        message: dict,
        detections: dict
    ) -> dict:
        """"""
        traffic_detection_message = {
            "version": "1.0.0",
            "modelName": self.model_name,
            "cameraID": message["cameraID"],
            "imageID": message["imageID"],
            "imagePath": message["imagePath"],
            "createdTS": message["createdTS"],
            "detectionTS": tct.chrono.now_as_str(),
            "detection": None,
            "numberOfObjects": None,
            "detectedClasses": None,
            "boundingBoxes": None
        }
        traffic_detection_message.update(detections)

        return traffic_detection_message

    @staticmethod
    def get_traffic_count_schema(detections: dict) -> dict:
        """"""
        traffic_count_message = dict(filter(
            lambda x: x[0] in ["cameraID", "imageID", "createdTS",
                               "modelName", "detectionTS"],
            detections.items()
        ))
        traffic_count_message.update({
            "version": "1.0.0",
            "trafficCount": detections["numberOfObjects"]
        })
        return traffic_count_message

    def get_recorded_images(self) -> None:
        """"""
        self.kafka_helper.consume_forever(
            group_id=f'traffic_detector_{self.model_name}',
            topics=[self.kafka_input_topic],
            callback_functions=[self.detect_traffic]
        )


if __name__ == '__main__':
    cr = tct.conf
    app_conf = cr.parse_yaml(
        os.path.join(os.getcwd(), 'configs', 'app_config.yaml')
    )['traffic_detector']

    td = TrafficDetector(**app_conf)
    td.get_recorded_images()
