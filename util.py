import struct
from typing import NamedTuple
from pydobot.dobot import Dobot, MODE_PTP_MOVJ_XYZ, MODE_PTP_MOVJ_ANGLE
from pydobot.message import Message


class DobotPosition(NamedTuple):
    x: float
    y: float
    z: float
    r_head: float


class DobotJointAngles(NamedTuple):
    joint1: float
    joint2: float
    joint3: float
    joint4: float


class DobotActivationError(Exception):
    pass


class DobotController:

    default_home = DobotPosition(x=250, y=0, z=100, r_head=0)
    default_ptp_mode = MODE_PTP_MOVJ_XYZ

    def __init__(self, port_name: str = "", home: DobotPosition = default_home):
        self.dobot = Dobot(port=port_name)
        self.port_name = port_name
        self.home = home

    def activate(self):
        """
        Connect Dobot, set up parameters and start queued commands.
        Raise DobotActivationError if failed to connect.
        """

        self.dobot.lock.acquire()
        if not self.dobot._on:
            self.dobot.ser.open()
        self.dobot.lock.release()

        if self.dobot.ser.isOpen():
            self.dobot._on = True
            self.dobot._set_queued_cmd_start_exec()
        else:
            raise DobotActivationError(f"Failed to connect on port {self.port_name}")

        self.dobot._set_queued_cmd_clear()
        self.set_home(home=self.home)
        self.dobot._set_ptp_joint_params(400, 400, 400, 400, 400, 400, 400, 400)
        self.dobot._set_ptp_common_params(velocity=400, acceleration=400)

    def deactivate(self):
        """
        Stop queued commands and disconnect Dobot.
        """

        self.dobot._set_queued_cmd_stop_exec()
        self.dobot.close()

    # ---------- Setups ---------- #

    def set_home(self, home: DobotPosition):
        message = Message()
        message.id = 30
        message.ctrl = 0x03
        message.params = bytearray([])
        message.params.extend(bytearray(struct.pack('f', home.x)))
        message.params.extend(bytearray(struct.pack('f', home.y)))
        message.params.extend(bytearray(struct.pack('f', home.z)))
        message.params.extend(bytearray(struct.pack('f', home.r_head)))
        self.dobot._send_message(message)
        self.home = home

    def set_conveyor_connected(self, is_connected: bool):
        message = Message()
        message.id = 3
        message.ctrl = 0x03
        message.params = bytearray([is_connected])
        self.dobot._send_command(message, wait=True)

    def set_io_multiplexing(self, address: int, multiplex: int):
        message = Message()
        message.id = 130
        message.ctrl = 0x03
        assert False  # TODO: Implement

    # ---------- Readers ---------- #

    @property
    def current_position(self) -> DobotPosition:
        x, y, z, r, _, _, _, _ = self.dobot.pose()
        return DobotPosition(x=x, y=y, z=z, r_head=r)

    @property
    def current_joint_angles(self) -> DobotJointAngles:
        _, _, _, _, j1, j2, j3, j4 = self.dobot.pose()
        return DobotJointAngles(joint1=j1, joint2=j2, joint3=j3, joint4=j4)

    def io_adc(self, address: int) -> int:
        """
        Read the I/O analog-digital conversion value.

        :param address: I/O port address(1~20)
        :return: I/O analog-digital conversion value
        """

        message = Message()
        message.id = 134
        message.params = bytearray([address])
        response = self.dobot._send_command(message, wait=True)
        assert False  # TODO: Return correct value

    # ---------- Instructions ---------- #

    def calibrate(self):
        message = Message()
        message.id = 31
        message.ctrl = 0x03
        self.dobot.lock.acquire()
        self.dobot._send_message(message)
        self.dobot.lock.release()

    def move(self, destination: DobotPosition, ptp_mode=default_ptp_mode, wait: bool = True):
        self.dobot._set_ptp_cmd(x=destination.x,
                                y=destination.y,
                                z=destination.z,
                                r=destination.r_head,
                                mode=ptp_mode,
                                wait=wait)

    def shift(self,
              x: float = 0,
              y: float = 0,
              z: float = 0,
              r_head: float = 0,
              ptp_mode=default_ptp_mode,
              wait: bool = True):
        current_position = self.current_position
        destination = DobotPosition(x=current_position.x + x,
                                    y=current_position.y + y,
                                    z=current_position.z + z,
                                    r_head=current_position.r_head + r_head)
        self.move(destination=destination, ptp_mode=ptp_mode, wait=wait)

    def move_with_conveyor(self,
                           destination: DobotPosition,
                           conveyor_position: int,
                           ptp_mode=default_ptp_mode):
        message = Message()
        message.id = 86
        message.ctrl = 0x03
        message.params = bytearray([])
        message.params.extend(bytearray([ptp_mode]))
        message.params.extend(bytearray(struct.pack('f', destination.x)))
        message.params.extend(bytearray(struct.pack('f', destination.y)))
        message.params.extend(bytearray(struct.pack('f', destination.z)))
        message.params.extend(bytearray(struct.pack('f', destination.r_head)))
        message.params.extend(bytearray(struct.pack('f', conveyor_position)))
        self.dobot._send_command(message, wait=True)

    def move_conveyor(self, conveyor_position: int, ptp_mode=default_ptp_mode):
        self.move_with_conveyor(destination=self.current_position,
                                conveyor_position=conveyor_position,
                                ptp_mode=ptp_mode)

    def set_joint_angles(self, angles: DobotJointAngles, ptp_mode=MODE_PTP_MOVJ_ANGLE, wait: bool = True):
        self.dobot._set_ptp_cmd(x=angles.joint1,
                                y=angles.joint2,
                                z=angles.joint3,
                                r=angles.joint4,
                                mode=ptp_mode,
                                wait=wait)

    def set_suction_cup(self, is_on: bool):
        self.dobot.suck(enable=is_on)

    def set_gripper(self, is_on: bool):
        self.dobot.grip(enable=is_on)

    def wait(self, seconds: float):
        from time import sleep
        sleep(seconds)
