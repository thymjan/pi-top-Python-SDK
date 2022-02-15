from .blueprints import ControllerBlueprint, RoverControllerBlueprint
from .webserver import WebServer


class WebController(WebServer):
    def __init__(self, port=None, get_frame=None, message_handlers={}, blueprints=[], **kwargs):
        self.controller_blueprint = ControllerBlueprint(
            get_frame=get_frame, message_handlers=message_handlers
        )

        WebServer.__init__(
            self, port=port, blueprints=[self.controller_blueprint] + blueprints, **kwargs
        )

    def broadcast(self, message):
        self.controller_blueprint.broadcast(message)


class RoverWebController(WebServer):
    def __init__(
        self,
        port=None,
        get_frame=None,
        drive=None,
        pan_tilt=None,
        message_handlers={},
        blueprints=[],
        **kwargs
    ):
        self.rover_blueprint = RoverControllerBlueprint(
            get_frame=get_frame,
            drive=drive,
            pan_tilt=pan_tilt,
            message_handlers=message_handlers,
        )

        WebServer.__init__(
            self, port=port, blueprints=[self.rover_blueprint] + blueprints, **kwargs
        )

    def broadcast(self, message):
        self.rover_blueprint.broadcast(message)
