import os
import glob
import traceback
import uuid
import time

import cv2
import imutils

from tclib.tctools import tctools as tct

log = tct.log


class CameraProducer:

    base_path = os.path.dirname(__file__)

    def __init__(
        self,
        camera_id: int,
        path_video: str,
        path_save: str,
    ) -> None:
        self.camera_id = camera_id
        self.path_video = os.path.join(
            CameraProducer.base_path,
            path_video,
            os.listdir(os.path.join(CameraProducer.base_path, path_video))[0]
        )
        self.path_save = os.path.join(CameraProducer.base_path, path_save)
        self.kafka_helper = tct.kafka
        self.scheduler = tct.chrono
        self.kafka_topic = tct.conf.get('kafka', 'camera_producer')['topic']
        self.schema_helper = tct.schema.create_helper('CameraImage')

    def record_publish_images(self) -> None:
        """Extracts images from the video at the configured path and publishes
        them to the configured kafka topic.

        :return:
        """
        self.create_destination_dir()

        cap = cv2.VideoCapture(self.path_video)
        # try to determine the total number of frames in the video file
        try:
            prop = (
                cv2.cv.CV_CAP_PROP_FRAME_COUNT if imutils.is_cv2()
                else cv2.CAP_PROP_FRAME_COUNT
            )
            total = int(cap.get(prop))
            print("[INFO] {} total frames in video".format(total))

        # an error occurred while trying to determine the total
        # number of frames in the video file
        except:
            print("[INFO] could not determine # of frames in video")
            print("[INFO] no approx. completion time can be provided")
            total = -1

        # loop over frames from the video file stream
        while cap.isOpened():
            # read the next frame from the file
            (grabbed, frame) = cap.read()
            # if the frame was not grabbed, then we have reached the end
            # of the stream
            if not grabbed:
                break

            img_id = f'{self.camera_id}_' + str(uuid.uuid4()) + '.jpg'
            log.info(
                f"CameraProducer - {self.camera_id} - recorded an image "
                f"with ID: {img_id}"
            )
            file_name = os.path.join(self.path_save, img_id)
            cv2.imwrite(file_name, frame)
            camera_message = self.get_camera_image_schema(img_id)
            log.info(camera_message)
            # validate the message before publishing
            self.schema_helper.validate(camera_message)
            self.kafka_helper.publish(self.kafka_topic, camera_message)
            time.sleep(2)

        log.info(f"CameraProducer - {self.camera_id} - finished recording!")

    def create_destination_dir(self) -> None:
        """

        :return:
        """
        if os.path.isdir(self.path_save):
            return
        else:
            os.mkdir(self.path_save)

    def get_camera_image_schema(self, image_id: str) -> dict:
        """Returns an empty camera image schema.

        :param image_id: ID of the scanned image
        :return: filled camera image schema represented by a dictionary
        """
        camera_image = {
            "version": "1.0.0",
            "cameraID": self.camera_id,
            "createdTS": self.scheduler.now_as_str(),
            "imageID": image_id,
            "imagePath": self.path_save
        }
        return camera_image


if __name__ == '__main__':

    cr = tct.conf
    app_conf = cr.parse_yaml(
        os.path.join(os.getcwd(), 'configs', 'app_config.yaml')
    )['camera_producer']
    cp = CameraProducer(**app_conf)
    cp.record_publish_images()

