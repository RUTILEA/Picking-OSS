import numpy as np
from typing import Dict
from cv2 import aruco


def detect_qr(image: np.ndarray) -> Dict[int, tuple]:
    """
    Detects QR codes in the specified image and returns those IDs and center positions.

    :param image: Detecting image
    :return: IDs and center coordinates of detected QR codes in the form of {ID: (center.x, center.y)}
    """

    aruco_dictionary = aruco.getPredefinedDictionary(aruco.DICT_6X6_250)
    corners, qr_ids, _ = aruco.detectMarkers(image, aruco_dictionary)

    qr_centers = {}  # {ID: (center.x, center.y)}
    for qr_id, corner in zip(qr_ids, corners):
        qr_id = int(qr_id[0])
        corner = corner[0]
        center = (corner[:, 0].mean(), corner[:, 1].mean())
        qr_centers[qr_id] = center

    return qr_centers


if __name__ == '__main__':
    import cv2
    path_str = input("Enter an image path showing some QR codes.\n>> ")
    img = cv2.imread(path_str)
    QR_CENTERS = detect_qr(img)
    print("--- IDs and center positions of Detected QR codes:\n", QR_CENTERS, "\n")
