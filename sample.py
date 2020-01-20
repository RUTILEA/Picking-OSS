from pathlib import Path
from util import DobotPosition
from picking.picker import CoordinateTransformer, DobotPicker


BULK_CAMERA_PID = 0
COORD_TRANS_MODEL_PATH = Path('coord_trans_model.joblib')
DISTANCE_SENSOR_DISPLACEMENT = (50, 0, 40)

# Dobot configuration
PICKER_PORT = '/dev/ttyXXXX'
PICKER_HOME = DobotPosition(x=250, y=0, z=100, r_head=0)
ABOVE_BULK = DobotPosition(x=200, y=100, z=100, r_head=0)
RELEASE_POSITION = DobotPosition(x=200, y=0, z=0, r_head=0)


if __name__ == "__main__":
    picker = DobotPicker(bulk_camera_pid=BULK_CAMERA_PID,
                         coordinate_transformer=CoordinateTransformer(model_path=COORD_TRANS_MODEL_PATH),
                         distance_displacement=DISTANCE_SENSOR_DISPLACEMENT,
                         port_name=PICKER_PORT,
                         home=PICKER_HOME)
    picker.move(destination=ABOVE_BULK)
    picker.pick_from_bulk(distance_error=0, show_pickable_points=True)
    picker.move(destination=RELEASE_POSITION)
    picker.set_suction_cup(is_on=False)
