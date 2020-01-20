import cv2
import numpy as np
from statistics import median
from typing import Tuple
from . import distance_sensor
from .coordinate_transformation import CoordinateTransformer
from .pickable_point_estimation import PickablePointEstimator
from .qr_detector import detect_qr
from ..carrying.carrier import DobotCarrier
from ..pyuvc import uvc
from ..util import DobotPosition


class DobotPickingError(Exception):
    pass


class DobotPicker(DobotCarrier):

    def __init__(self,
                 bulk_camera_pid: int,
                 coordinate_transformer: CoordinateTransformer,
                 distance_sensor_displacement: Tuple[float, float, float],
                 port_name: str = "",
                 home: DobotPosition = DobotCarrier.default_home):
        """
        :param bulk_camera_pid: Index of the camera that captures a bulk
        :param coordinate_transformer: Converter that transforms coordinates between the bulk camera image and Dobot
        :param distance_sensor_displacement: Position displacement (x, y, z) of the distance sensor with respect to the suction cup
        :param port_name:
        :param home:
        """

        super().__init__(port_name=port_name, home=home)

        devices = uvc.device_list()
        bulk_device = next(device for device in devices if device['idProduct'] == bulk_camera_pid)
        self.bulk_capture = uvc.Capture(bulk_device['uid'])

        self.distance_sensor_displacement = distance_sensor_displacement
        self.coordinate_transformer = coordinate_transformer

    def calibrate_coordinate_transformer(self):
        input("Place QR codes and press Enter. >> ")
        image = self.__capture_bulk()
        cv2.imshow("Bulk Area", image)
        cv2.waitKey(0)

        qr_centers = detect_qr(image)
        detected_qr_ids = qr_centers.keys()
        print("Detected QR IDs:", detected_qr_ids)

        dobot_positions = []
        for qr_id in detected_qr_ids:
            input(f"Move dobot above the QR code of No.{qr_id} and press Enter. >> ")
            current_position = self.current_position
            dobot_positions.append((current_position.x, current_position.y))

        self.coordinate_transformer.fit(transforming_coordinate_samples=list(qr_centers.values()),
                                        target_coordinate_samples=dobot_positions)
        print("Coordinate transformer has been calibrated.")

    def pick_from_bulk(self, distance_error: float, show_pickable_points: bool = False):
        """
        Pick up an item in bulk automatically.
        Raise DobotPickingError if there is no pickable items.
        """

        # Find a pickable point
        bulk_image = self.__capture_bulk()
        pickable_points_estimator = PickablePointEstimator()
        pickable_points = pickable_points_estimator.estimate_pickable_points(bulk_image=bulk_image,
                                                                             show_result=show_pickable_points)
        target_point = None
        for estimated_point in pickable_points:
            adjusted_point = pickable_points_estimator.adjust_estimated_point(bulk_image=bulk_image,
                                                                              coordinate=estimated_point,
                                                                              picker_size=30,
                                                                              show_result=show_pickable_points)
            if adjusted_point is not None:
                target_point = adjusted_point
                break
        if target_point is None:
            raise DobotPickingError("There are no pickable items.")

        # Transform the coordinate
        transformed_target_point = self.coordinate_transformer.predict(transforming_coordinate=target_point)
        above_target = DobotPosition(x=transformed_target_point[0],
                                     y=transformed_target_point[1],
                                     z=-25,
                                     r_head=0)

        # Measure the distance
        measuring_distance_position = self.__measuring_distance_position(above_target=above_target)
        self.move(destination=measuring_distance_position, wait=True)
        self.wait(seconds=0.5)
        distance_sensor_values = distance_sensor.acquire_distance(times=60)
        distance_sensor_values = (val for val in distance_sensor_values if val < 130)  # Remove the obvious outliers
        distance_sensor_value = median(distance_sensor_values)
        distance = distance_sensor_value + distance_error - self.distance_sensor_displacement[2]
        print(f"Distance: {distance}mm (sensor value: {distance_sensor_value}mm)")
        target_position = above_target._replace(z=above_target.z-distance)

        # Go to pick up
        self.move(destination=above_target, wait=False)
        self.move(destination=target_position, wait=False)
        self.set_suction_cup(is_on=True)
        self.wait(seconds=0.8)
        above_target = above_target._replace(z=85)
        self.move(destination=above_target)

    def __capture_bulk(self) -> np.ndarray:
        self.bulk_capture.frame_mode = (640, 480, 30)
        controls = {control.display_name: control for control in self.bulk_capture.controls}
        controls['Auto Exposure Mode'].value = 1
        controls['Absolute Exposure Time'].value = 500
        controls['White Balance temperature,Auto'].value = 0
        controls['White Balance temperature'].value = 3000
        controls['Saturation'].value = 60
        image = self.bulk_capture.get_frame_robust().img
        image = cv2.flip(image, 1)
        return image

    def __measuring_distance_position(self, above_target: DobotPosition) -> DobotPosition:
        """
        Returns a position to measure the distance between the hand and the target.

        :param above_target: Position directly above the target
        :return: Position for measuring distance.
                 When Dobot move here, the distance sensor will directly above the target.
        """

        dx, dy, _ = self.distance_sensor_displacement
        if (dx, dy) == (0, 0):
            return above_target

        xa, ya = above_target.x, above_target.y
        # Angle: counterclockwise from the x-axis
        sin = ya / (xa**2 + ya**2)**(1/2)
        cos = xa / (xa**2 + ya**2)**(1/2)

        transform = np.array([[-cos, sin],
                              [-sin, -cos]])
        x, y = (xa, ya) + np.dot(transform, (dx, dy))
        return above_target._replace(x=x, y=y)
