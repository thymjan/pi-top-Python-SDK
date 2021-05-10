import math

MAX_LINEAR_SPEED = 0.44
MAX_ANGULAR_SPEED = 5.12
MAX_SERVO_ANGLE = 90


def calculate_direction(degree):
    direction = degree - 90

    # keeps direction between -180 and 180
    if direction > 180:
        return -(360 - direction)

    return direction


def calculate_pan_tilt_angle(data):
    angle = data.get('angle', {})
    degree = angle.get('degree', 0)
    distance = data.get('distance', 0)
    magnitude = distance * MAX_SERVO_ANGLE / 100.0
    direction = calculate_direction(degree)

    return {
        'y': -math.cos(direction * math.pi / 180) * magnitude,
        'z': math.sin(direction * math.pi / 180) * magnitude,
    }


def calculate_velocity_twist(data):
    angle = data.get('angle', {})
    degree = angle.get('degree', 0)
    distance = data.get('distance', 0)
    linear_speed = distance * MAX_LINEAR_SPEED / 100.0
    angular_speed = distance * MAX_ANGULAR_SPEED / 100.0
    direction = calculate_direction(degree)

    return {
        'linear': math.cos(direction * math.pi / 180) * linear_speed,
        'angular': math.sin(direction * math.pi / 180) * angular_speed,
    }


MAX_LINEAR_SPEED_4WD = 0.596
MAX_ANGULAR_SPEED_4WD = 3.24


def calculate_linear_velocities_4wd(data):
    angle = data.get('angle', {})
    degree = angle.get('degree', 0)
    distance = data.get('distance', 0)
    direction = calculate_direction(degree)
    linear_speed_x = (distance * MAX_LINEAR_SPEED / 100.0) * math.cos(direction * math.pi / 180)
    linear_speed_y = (distance * MAX_LINEAR_SPEED / 100.0) * math.sin(direction * math.pi / 180)

    return {
        'linear_x': linear_speed_x,
        'linear_y': linear_speed_y,
    }
