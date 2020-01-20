import json
from enum import Enum
from pathlib import Path
from typing import List
from ..util import DobotPosition, DobotController


class DobotCarrierMotion(Enum):
    PICK = "pick"
    MOVE = "move"
    RELEASE = "release"


class DobotCarrier(DobotController):

    def carry_by_suction_cup(self, source: DobotPosition, waypoints: List[DobotPosition], destination: DobotPosition):
        """
        Carry an item using the suction cup.

        :param source: Target item position. Dobot will pick the item up here.
        :param waypoints: Points where Dobot will pass
        :param destination: Carrying destination. Dobot will release the item here.
        """

        # Pick up
        self.__pick_up_by_suction_cup(target_position=source)

        # Carry
        for waypoint in waypoints:
            self.move(destination=waypoint)

        # Put down
        self.__release_from_suction_cup(release_position=destination)

    def playback(self, motions_json_path: Path):
        """
        Playback carrying motions taught by DobotCarrierTeacher.

        :param motions_json_path: Path to JSON file that records motions
        """

        # Load motions
        with motions_json_path.open(mode='r') as motions_json:
            motions: list = json.load(motions_json)
        assert type(motions) is list

        # Playback motions
        for motion in motions:
            destination = DobotPosition._make(motion["dest"])
            motion_mode = DobotCarrierMotion(motion["motion"])

            if motion_mode == DobotCarrierMotion.PICK:
                self.__pick_up_by_suction_cup(target_position=destination)
            elif motion_mode == DobotCarrierMotion.MOVE:
                self.move(destination=destination, wait=False)
            elif motion_mode == DobotCarrierMotion.RELEASE:
                self.__release_from_suction_cup(release_position=destination)
            else:
                assert False

    def __pick_up_by_suction_cup(self, target_position: DobotPosition):
        self.move(destination=target_position)
        self.set_suction_cup(is_on=True)
        self.wait(seconds=0.4)
    
    def __release_from_suction_cup(self, release_position: DobotPosition):
        self.move(destination=release_position)
        self.set_suction_cup(is_on=False)
        self.wait(seconds=0.2)
