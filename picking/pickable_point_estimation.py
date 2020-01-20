import cv2
import numpy as np
from typing import Optional, Union


class PickablePointEstimator:

    def estimate_pickable_points(self, bulk_image: np.ndarray, show_result: bool = False) -> np.ndarray:
        """
        Estimate pickable points in a bulk image.

        :param bulk_image: Image of items in bulk
        :param show_result: Whether to display the estimation result
        :return: Pickable point coordinates: np.array([[x1, y1], [x2, y2], ..., [xn, yn]])
        """

        # Convert the color to HSV
        hsv_image = cv2.cvtColor(src=bulk_image, code=cv2.COLOR_BGR2HSV)

        # Mask pixels that do not have the specified hue
        mask = self.__mask(source_image=hsv_image, hue_lower_limit=30, hue_upper_limit=120)

        # Execute canny components
        coordinates = self.__canny_components(source_image=bulk_image, mask=mask)

        if show_result:
            plot_image = self.__plot_image(source_image=bulk_image, coordinates=coordinates, max_num=10)
            cv2.imshow('result', plot_image)
            cv2.waitKey(0)

        return coordinates

    def __canny_components(self, source_image: np.ndarray, mask: np.ndarray) -> np.ndarray:
        # Canny edge detection
        processing_image = cv2.Canny(image=cv2.cvtColor(src=source_image, code=cv2.COLOR_BGR2GRAY),
                                     threshold1=100,
                                     threshold2=200,
                                     edges=3,
                                     L2gradient=False)

        # Color inversion
        processing_image = cv2.bitwise_not(src=processing_image)

        # 3x3 kernel
        kernel = np.ones(shape=(3, 3), dtype=np.uint8)

        # Morphological operations
        processing_image = cv2.erode(src=processing_image, kernel=kernel, iterations=1)
        processing_image = cv2.morphologyEx(src=processing_image, op=cv2.MORPH_CLOSE, kernel=kernel, iterations=1)
        processing_image = cv2.morphologyEx(src=processing_image, op=cv2.MORPH_CLOSE, kernel=kernel, iterations=1)
        processing_image = cv2.bitwise_and(src1=processing_image, src2=processing_image, mask=mask)  # mask
        processing_image = cv2.morphologyEx(processing_image, cv2.MORPH_OPEN, kernel, iterations=2)

        # Distance transformation
        dist_transform = cv2.distanceTransform(src=processing_image, distanceType=cv2.DIST_L2, maskSize=3)

        # Extract sure foreground area
        _, sure_fg = cv2.threshold(src=dist_transform, thresh=0.2 * dist_transform.max(), maxval=255, type=0)
        sure_fg = np.uint8(sure_fg)

        # Label (Number) for each 1 object in foreground
        _, _, stats, centroids = cv2.connectedComponentsWithStats(sure_fg)

        stats_areas_pair = np.insert(arr=stats[1:], obj=[5], values=centroids[1:], axis=1)

        sorted_stats_area = stats_areas_pair[np.argsort(stats_areas_pair[:, 4])[::-1]]

        return sorted_stats_area[:, 5:7]  # Array of barycentric coordinates

    def __mask(self, source_image: np.ndarray, hue_lower_limit: int, hue_upper_limit: int) -> np.ndarray:
        bgr_lower = np.array([hue_lower_limit, 0, 0])  # Lower limit of color to mask
        bgr_upper = np.array([hue_upper_limit, 255, 255])  # Upper limit of color to mask
        mask = cv2.inRange(src=source_image, lowerb=bgr_lower, upperb=bgr_upper)  # Generate the mask image
        return mask

    def adjust_estimated_point(self,
                               bulk_image: np.ndarray,
                               coordinate: np.ndarray,
                               picker_size: int = 20,
                               search_rate: int = 3,
                               step: int = 3,
                               show_result: bool = False) -> Optional[np.ndarray]:
        """
        Adjust an estimated point.

        :param bulk_image: Image of items in bulk
        :param coordinate: Estimated pickable point in bulk_image: np.array([x, y])
        :param show_result: Whether to display the estimation result
        :return: Adjusted coordinate: np.array([x, y]) or None if there is no pickable point
        """

        # Crop image for search
        search_image = bulk_image[coordinate[1]-picker_size*search_rate//2:coordinate[1]+picker_size*search_rate//2,
                                  coordinate[0]-picker_size*search_rate//2:coordinate[0]+picker_size*search_rate//2]

        # Canny edge detection
        canny_image = cv2.Canny(cv2.cvtColor(search_image, cv2.COLOR_BGR2GRAY), 100, 200, 3, L2gradient=False)

        # Mask pixels that do not have the specified hue
        hsv_image = cv2.cvtColor(search_image, cv2.COLOR_BGR2HSV)
        mask = cv2.bitwise_not(self.__mask(source_image=hsv_image, hue_lower_limit=30, hue_upper_limit=120))
        canny_image = cv2.bitwise_or(canny_image, mask)
        
        # Search crop image for pickable point
        for i in range(0, canny_image.shape[0]-picker_size+1, step):
            for j in range(0, canny_image.shape[1]-picker_size+1, step):
                rect = canny_image[i:picker_size+i+1, j:picker_size+j+1]
                if np.count_nonzero(rect > 0) <= 10:
                    new_coordinate = coordinate + np.array([j-(canny_image.shape[1]-picker_size)//2,
                                                            i-(canny_image.shape[0]-picker_size)//2])
                    if show_result:
                        plot_image = self.__plot_image(source_image=bulk_image, coordinates=[new_coordinate], max_num=1)
                        cv2.imshow('result', plot_image)
                        cv2.waitKey(0)
                    return new_coordinate
        return None

    def __plot_image(self, source_image: np.ndarray, coordinates: Union[list, tuple, np.ndarray], max_num: int) -> np.ndarray:
        num = min(len(coordinates), max_num)
        plot_image = np.copy(source_image)
        for i in range(num):
            coordinate = coordinates[i]
            plot_image = cv2.putText(plot_image,
                                     text=str(i+1),
                                     org=tuple(np.where(coordinate-10 > 0, coordinate-10, coordinate).astype('uint')),
                                     fontFace=cv2.FONT_HERSHEY_SIMPLEX,
                                     fontScale=0.4,
                                     color=(0, 0, 255),
                                     thickness=1)
            plot_image = cv2.drawMarker(plot_image,
                                        position=tuple(coordinate.astype('uint')),
                                        color=(0, 0, 255),
                                        markerType=cv2.MARKER_STAR,
                                        markerSize=10)
        return plot_image


if __name__ == '__main__':
    filename = input("Enter a path to an image you want to detect pickable positions.\n>> ")
    image = cv2.imread(filename=filename)
    pickable_point_estimator = PickablePointEstimator()
    estimated_points = pickable_point_estimator.estimate_pickable_points(bulk_image=image, show_result=True)
    index = int(input("Enter an index of the position to be adjusted in the estimated positions.\n>> "))
    pickable_point_estimator.adjust_estimated_point(bulk_image=image,
                                                    coordinate=estimated_points[index-1],
                                                    show_result=True)
