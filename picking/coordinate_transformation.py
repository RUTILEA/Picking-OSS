import joblib
import numpy as np
from pathlib import Path
from typing import Union
from sklearn.linear_model import LinearRegression


class CoordinateTransformer:

    def __init__(self, model_path: Path):
        self.model_path = model_path
        if self.model_path.is_file():
            self.converter: LinearRegression = joblib.load(filename=self.model_path)
        else:
            print(f"[WARNING] {self.__class__.__name__} has not been calibrated. Please call 'fit' method.")
            self.converter = LinearRegression()

    def fit(self,
            transforming_coordinate_samples: Union[list, tuple, np.ndarray],
            target_coordinate_samples: Union[list, tuple, np.ndarray]):
        """
        Calculate parameters of a liner model and save the model with them.

        :param transforming_coordinate_samples: [[x1, y1], [x2, y2], ..., [xn, yn]]
        :param target_coordinate_samples: [[x1, y1], [x2, y2], ..., [xn, yn]]
        """

        self.converter.fit(transforming_coordinate_samples, target_coordinate_samples)
        joblib.dump(value=self.converter, filename=self.model_path)

    def predict(self, transforming_coordinate: Union[list, tuple, np.ndarray]) -> np.ndarray:
        """
        Predict the coordinate transformation.

        :param transforming_coordinate: Transforming coordinate in an image: [x, y]
        :return: Transformed coordinate: np.array([x, y])
        """

        return self.converter.predict([transforming_coordinate])[0]


# Usage example
if __name__ == "__main__":
    model_path_str = input("Enter the coordinate transformer's model path.\n>> ")
    transformer = CoordinateTransformer(model_path=Path(model_path_str))
    X = ((368.555, 509.198), (467.708, 513.775), (470.173, 313.074), (414.469, 313.426), (469.962, 113.428),
         (371.723, 114.484))
    Y = [[257.2426, 110.0510], [198.8885, 109.9388], [197.7876, -6.8562], [227.5777, -5.1529], [197.9241, -118.6624],
         [253.8159, -119.4369]]
    transformer.fit(transforming_coordinate_samples=X, target_coordinate_samples=Y)
    target = (320.532, 112.577)
    result = transformer.predict(target)
    print(target, " -> ", result, "\n")
