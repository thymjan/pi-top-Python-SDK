from time import sleep
from unittest.mock import patch

import pygame
import pytest


@pytest.fixture
def pitop_mocks(oled_mocks, fonts_mock):
    mocks = {}

    mocks["supports_battery"] = patch("pitop.system.pitop.SupportsBattery")
    mocks["supports_battery"].start()

    from pitop.common.common_names import DeviceName

    mocks["device_type"] = patch(
        "pitop.core.mixins.supports_miniscreen.device_type",
        return_value=DeviceName.pi_top_4.value,
    )
    mocks["device_type"].start()

    mocks["encoder_motor_controller"] = patch(
        "pitop.pma.encoder_motor.EncoderMotorController"
    )
    mocks["encoder_motor_controller"].start()

    from pitop.pma import EncoderMotor

    mocks["rotation_counter"] = patch.object(EncoderMotor, "rotation_counter")
    mocks["rotation_counter"].start()

    mocks["braking_type"] = patch.object(EncoderMotor, "braking_type").start()
    mocks["braking_type"].start()

    mocks["set_target_speed"] = patch.object(EncoderMotor, "set_target_speed")
    mocks["set_target_speed"].start()

    yield mocks

    mocks["supports_battery"].stop()
    mocks["device_type"].stop()
    mocks["encoder_motor_controller"].stop()
    mocks["rotation_counter"].stop()
    mocks["braking_type"].stop()
    mocks["set_target_speed"].stop()


@pytest.fixture
def pitop(pitop_mocks):
    from pitop import Pitop

    pitop = Pitop()

    yield pitop

    pitop.close()
    Pitop.instance = None
    del pitop


@pytest.fixture
def rover(pitop_mocks):
    from pitop import BlockPiRover

    rover = BlockPiRover()

    yield rover

    rover.close()
    BlockPiRover.instance = None
    del rover


def test_pitop(pitop):
    from pitop.pma import LED
    from pitop.robotics.drive_controller import DriveController

    drive = DriveController()
    pitop.add_component(drive)
    led = LED("D0")
    pitop.add_component(led)

    assert pitop.config == {
        "classname": "Pitop",
        "components": {
            "drive": {
                "classname": "DriveController",
                "left_motor_port": "M3",
                "module": "pitop.robotics.drive_controller",
                "name": "drive",
                "right_motor_port": "M0",
                "version": "0.17.0",
            },
            "led": {
                "classname": "LED",
                "color": "red",
                "module": "pitop.pma.led",
                "name": "led",
                "port_name": "D0",
                "version": "0.17.0",
            },
        },
        "module": "pitop.system.pitop",
        "version": "0.17.0",
    }

    assert not pitop.state["led"]["is_lit"]

    pitop.led.on()

    assert pitop.state["led"]["is_lit"]

    pitop.drive.forward(50)

    pitop.drive.left_motor.set_target_speed.assert_called()
    pitop.drive.right_motor.set_target_speed.assert_called()


def test_blockpi_rover(rover):
    assert rover.config == {
        "classname": "BlockPiRover",
        "components": {
            "drive": {
                "classname": "DriveController",
                "left_motor_port": "M3",
                "module": "pitop.robotics.drive_controller",
                "name": "drive",
                "right_motor_port": "M0",
                "version": "0.17.0",
            },
        },
        "module": "pitop.robotics.blockpi_rover",
        "version": "0.17.0",
    }

    rover.forward(50)

    rover.drive.left_motor.set_target_speed.assert_called()
    rover.drive.right_motor.set_target_speed.assert_called()


def test_pitop_simulate(pitop, mocker, create_sim, snapshot, analog_sensor_mocks):
    mocker.patch(
        "pitop.simulation.sprites.is_virtual_hardware",
        return_value=True,
    )

    from pitop.pma import (
        LED,
        Button,
        Buzzer,
        LightSensor,
        Potentiometer,
        SoundSensor,
        UltrasonicSensor,
    )

    pitop.add_component(LED("D0"))
    pitop.add_component(Button("D1"))
    pitop.add_component(Buzzer("D2"))
    pitop.add_component(UltrasonicSensor("D3"))
    pitop.add_component(LightSensor("A0"))
    pitop.add_component(SoundSensor("A1"))
    pitop.add_component(Potentiometer("A3"))

    def on_button_press():
        pitop.led.on()
        pitop.buzzer.on()
        analog_sensor_mocks.get("light_sensor").return_value = 100
        analog_sensor_mocks.get("sound_sensor").return_value = 100
        analog_sensor_mocks.get("potentiometer").return_value = 100
        analog_sensor_mocks.get("ultrasonic_sensor").return_value = 2

    def on_button_release():
        pitop.led.off()
        pitop.buzzer.off()
        analog_sensor_mocks.get("light_sensor").return_value = 0
        analog_sensor_mocks.get("sound_sensor").return_value = 0
        analog_sensor_mocks.get("potentiometer").return_value = 0
        analog_sensor_mocks.get("ultrasonic_sensor").return_value = 0

    pitop.button.when_pressed = on_button_press
    pitop.button.when_released = on_button_release

    sim = create_sim(pitop)

    # give time for the screen and sprites to be set up
    sleep(2)
    snapshot.assert_match(sim.snapshot(), "default.png")

    # simulate a button click
    sim.event(pygame.MOUSEBUTTONDOWN, pitop.button.name)

    # these events are a bit slow
    sleep(0.5)
    snapshot.assert_match(sim.snapshot(), "button_pressed.png")

    sim.event(pygame.MOUSEBUTTONUP, pitop.button.name)

    sleep(0.5)
    snapshot.assert_match(sim.snapshot(), "default.png")


def test_pitop_visualize(pitop, create_sim, mocker, snapshot):
    # with is_virtual_hardware False, pygame button events will not be handled
    mocker.patch(
        "pitop.simulation.sprites.is_virtual_hardware",
        return_value=False,
    )

    from pitop.pma import LED, Button, Buzzer

    pitop.add_component(LED("D0"))
    pitop.add_component(Button("D1"))
    pitop.add_component(Buzzer("D2"))

    pitop.button.when_pressed = lambda: (pitop.led.on(), pitop.buzzer.on())
    pitop.button.when_released = lambda: (pitop.led.off(), pitop.buzzer.off())

    sim = create_sim(pitop)

    # give time for the screen and sprites to be set up
    sleep(2)
    snapshot.assert_match(sim.snapshot(), "default.png")

    # simulate a button click
    sim.event(pygame.MOUSEBUTTONDOWN, pitop.button.name)

    # these events are a bit slow
    sleep(0.5)
    # should not have changed
    snapshot.assert_match(sim.snapshot(), "default.png")

    pitop.button.pin.drive_low()
    sleep(0.1)
    snapshot.assert_match(sim.snapshot(), "button_pressed.png")

    pitop.button.pin.drive_high()
    sleep(0.1)
    snapshot.assert_match(sim.snapshot(), "default.png")


def test_pitop_sim_miniscreen(pitop, create_sim, mocker, snapshot):
    sim = create_sim(pitop)

    # give time for the screen and sprites to be set up
    sleep(2)
    snapshot.assert_match(sim.snapshot(), "default.png")

    pitop.miniscreen.display_multiline_text("are we in a simulation?")

    sleep(0.1)
    snapshot.assert_match(sim.snapshot(), "text.png")

    from pitop.simulation.images import Pitop

    sample_image_path = Pitop
    pitop.miniscreen.display_image_file(sample_image_path)

    sleep(0.1)
    snapshot.assert_match(sim.snapshot(), "image.png")


def test_pitop_simulate_scale(pitop, mocker, create_sim, snapshot, analog_sensor_mocks):
    mocker.patch(
        "pitop.simulation.sprites.is_virtual_hardware",
        return_value=True,
    )

    from pitop.pma import (
        LED,
        Button,
        Buzzer,
        LightSensor,
        Potentiometer,
        SoundSensor,
        UltrasonicSensor,
    )

    pitop.add_component(LED("D0"))
    pitop.add_component(Button("D1"))
    pitop.add_component(Buzzer("D2"))
    pitop.add_component(UltrasonicSensor("D3"))
    pitop.add_component(Potentiometer("A0"))
    pitop.add_component(SoundSensor("A1"))
    pitop.add_component(LightSensor("A2"))

    def on_button_press():
        pitop.led.on()
        pitop.buzzer.on()
        analog_sensor_mocks.get("light_sensor").return_value = 200
        analog_sensor_mocks.get("sound_sensor").return_value = 400
        analog_sensor_mocks.get("potentiometer").return_value = 600
        analog_sensor_mocks.get("ultrasonic_sensor").return_value = 3

    def on_button_release():
        pitop.led.off()
        pitop.buzzer.off()
        analog_sensor_mocks.get("light_sensor").return_value = 0
        analog_sensor_mocks.get("sound_sensor").return_value = 0
        analog_sensor_mocks.get("potentiometer").return_value = 0
        analog_sensor_mocks.get("ultrasonic_sensor").return_value = 0

    pitop.button.when_pressed = on_button_press
    pitop.button.when_released = on_button_release

    sim = create_sim(pitop, 0.5, (700, 700))

    # give time for the screen and sprites to be set up
    sleep(2)
    snapshot.assert_match(sim.snapshot(), "default.png")

    # simulate a button click
    sim.event(pygame.MOUSEBUTTONDOWN, pitop.button.name)

    # these events are a bit slow
    sleep(0.5)
    snapshot.assert_match(sim.snapshot(), "button_pressed.png")

    sim.event(pygame.MOUSEBUTTONUP, pitop.button.name)

    sleep(0.5)
    snapshot.assert_match(sim.snapshot(), "default.png")


def test_pitop_simulate_add_component(
    pitop, mocker, create_sim, snapshot, analog_sensor_mocks
):
    mocker.patch(
        "pitop.simulation.sprites.is_virtual_hardware",
        return_value=True,
    )

    from pitop.pma import LED, Button

    pitop.add_component(LED("D0"))

    sim = create_sim(pitop)

    # give time for the screen and sprites to be set up
    sleep(2)
    snapshot.assert_match(sim.snapshot(), "default.png")

    pitop.add_component(Button("D1"))
    sleep(0.5)  # some time for button to be added
    snapshot.assert_match(sim.snapshot(), "with_button.png")

    pitop.add_component(Button("D2"), name="button2")
    print(pitop.config)
    sleep(0.5)  # some time for button to be added
    snapshot.assert_match(sim.snapshot(), "with_2_button.png")
