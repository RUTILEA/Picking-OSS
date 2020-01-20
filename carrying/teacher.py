import json
from pathlib import Path
from .carrier import DobotController, DobotCarrierMotion


class DobotCarrierTeacher(DobotController):

    def teach(self, motions_file_path: Path):
        """
        Teach DobotCarrier how to carry. The motion data will be saved as a JSON file.

        :param motions_file_path: A path to save the motion JSON file
        """

        motions = []
        fin_arg = "fin"
        adjust_arg = "adjust"
        yes_arg = "y"
        no_arg = "n"
        is_carrying = False

        while True:
            arg = input(f"\nPress Enter or type '{adjust_arg}' or '{fin_arg}'.\n"
                        f"  - Press Enter: Teach current position\n"
                        f"  - '{adjust_arg}': Manually adjust coordinates or angles\n"
                        f"  - '{fin_arg}': End teaching\n"
                        f">> ")
            if arg == fin_arg:
                print("--- end teaching")
                break
            elif arg == adjust_arg:
                print(f"Current pose:\n  {self.current_position}\n  {self.current_joint_angles}")
                adjustment = input("Specify the new value with the target name(x, y, z, r, j1, j2, j3, j4).\n"
                                   "  e.g.) x 60\n"
                                   ">> ")
                self.__adjust_pose(adjustment=adjustment)
                continue
            if is_carrying:
                wanna_release_arg = input(f"Wanna release the item here? [{yes_arg}/{no_arg}] >> ")
                if wanna_release_arg == yes_arg:
                    motions.append(self.__motion_data(DobotCarrierMotion.RELEASE))
                    is_carrying = False
                    self.set_suction_cup(is_on=is_carrying)
                    print("--- will move and release")
                elif wanna_release_arg == no_arg:
                    motions.append(self.__motion_data(DobotCarrierMotion.MOVE))
                    print("--- will move")
                else:
                    print("--- skip")
            else:
                wanna_pick_arg = input(f"Wanna pick an item up here? [{yes_arg}/{no_arg}] >> ")
                if wanna_pick_arg == yes_arg:
                    motions.append(self.__motion_data(DobotCarrierMotion.PICK))
                    is_carrying = True
                    self.set_suction_cup(is_on=is_carrying)
                    print("--- will move and pick up")
                elif wanna_pick_arg == no_arg:
                    motions.append(self.__motion_data(DobotCarrierMotion.MOVE))
                    print("--- will move")
                else:
                    print("--- skip")

        with motions_file_path.open(mode='w') as motions_file:
            json.dump(motions, motions_file)

    def __motion_data(self, motion: DobotCarrierMotion) -> dict:
        return {
            "dest": self.current_position,
            "motion": motion.value
        }

    def __adjust_pose(self, adjustment: str):
        """
        Adjust the pose of Dobot with the specified value.

        :param adjustment: Specified adjustment in the form of '<target> <value>'.
                           Possible targets: x, y, z, r, j1, j2, j3, j4.
        """

        try:
            target, value_str = adjustment.split()
            value = float(value_str)
        except ValueError:
            print("--- error: invalid arguments")
            return
        if target == 'x':
            self.move(destination=self.current_position._replace(x=value))
        elif target == 'y':
            self.move(destination=self.current_position._replace(y=value))
        elif target == 'z':
            self.move(destination=self.current_position._replace(z=value))
        elif target == 'r':
            self.move(destination=self.current_position._replace(r_head=value))
        elif target == 'j1':
            self.set_joint_angles(angles=self.current_joint_angles._replace(joint1=value))
        elif target == 'j2':
            self.set_joint_angles(angles=self.current_joint_angles._replace(joint2=value))
        elif target == 'j3':
            self.set_joint_angles(angles=self.current_joint_angles._replace(joint3=value))
        elif target == 'j4':
            self.set_joint_angles(angles=self.current_joint_angles._replace(joint4=value))
        else:
            print(f"--- error: unknown target {target}")
