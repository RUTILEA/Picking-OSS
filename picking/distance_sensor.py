import re
from typing import List
from serial import Serial
from serial.tools import list_ports
from serial.tools.list_ports_common import ListPortInfo


class DistanceSensorError(Exception):
    pass


def acquire_distance(times: int = 1) -> List[int]:
    """
    Acquire the distance sensor value via Arduino. The sensor model is 'VL6180X'.

    :params times: The number of times to acquire value.
    :return: Distance value list returned from the sensor (Units: mm).
             The list size equals to the specified `times`.
    """

    # Find Arduino port
    arduino_port = __find_arduino_port()
    serial = Serial(port=arduino_port.device)

    # Acquire distance
    results = []
    while len(results) < times:
        serial_value = serial.readline()
        distance_search_result = re.search(pattern=r'\d+', string=str(serial_value))  # Extract distance value
        try:
            distance_str = distance_search_result.group()
            results.append(int(distance_str))
        except AttributeError:
            continue
    serial.close()
    assert len(results) == times
    return results


def __find_arduino_port() -> ListPortInfo:
    ports = list_ports.comports()
    arduino_pid = 67
    
    try:
        return next(port for port in ports if port.pid == arduino_pid)
    except StopIteration:
        raise DistanceSensorError("The distance sensor not found.")


if __name__ == "__main__":
    print(acquire_distance(times=10))
