from math import cos, radians, sin, sqrt

import pygame

from . import sprites as Sprites

# this is based on the inital further-link graphics area dimensions of 720x680
# multiplied by 2 to leave plenty space around our pi-top image of 435x573
PITOP_SIM_SIZE = (1560, 1240)
PMA_CUBE_SIM_SIZE = (122, 122)


class SimSprite:
    Size = PMA_CUBE_SIM_SIZE

    @classmethod
    def create_sprite_group(cls, sim_size, config, scale):
        sprite_group = pygame.sprite.Group()

        # create the main sprite
        sprite = cls(config, scale)
        sprite.name = "main"

        # position main sprite in center
        center = int(sim_size[0] / 2), int(sim_size[1] / 2)
        sprite.rect.x = center[0] - int(sprite.rect.width / 2)
        sprite.rect.y = center[1] - int(sprite.rect.height / 2)

        sprite_group.add(sprite)
        return sprite_group

    @staticmethod
    def handle_event(type, target_name, component):
        pass

    @staticmethod
    def _remove_alpha(image):
        # draw a white background behind image and convert it, losing transparency
        # this improves performance and ensures that snapshots are consistent
        new = image.copy()
        new.fill((255, 255, 255))
        new.blit(image, (0, 0))
        return new.convert()

    @staticmethod
    def _load_image(path, scale):
        image = pygame.image.load(path)
        size = [scale * x for x in image.get_size()]
        scaled = pygame.transform.scale(image, size)
        return SimSprite._remove_alpha(scaled)


class ComponentableSimSprite(SimSprite):
    Size = PITOP_SIM_SIZE

    @classmethod
    def create_sprite_group(cls, sim_size, config, scale):
        sprite_group = super().create_sprite_group(sim_size, config, scale)

        main_sprite_rect = sprite_group.sprites()[0].rect
        sprite_centres = cls._generate_sprite_centres(sim_size, main_sprite_rect)

        components = config.get("components", {})
        for component in components.values():
            sprite_class = getattr(Sprites, component.get("classname"), None)

            if not sprite_class:
                continue

            sprite = sprite_class(component, scale)
            if not sprite:
                continue

            sprite_centre = sprite_centres.get(component.get("port_name", None), (0, 0))

            sprite.rect.x = sprite_centre[0] - int(sprite.rect.width / 2)
            sprite.rect.y = sprite_centre[1] - int(sprite.rect.height / 2)

            sprite.name = component.get("name")
            sprite_group.add(sprite)

        return sprite_group

    @staticmethod
    def handle_event(type, target_name, component):
        for _, child in component.children_gen():
            sprite_class = getattr(Sprites, child.config.get("classname"), None)
            if not sprite_class:
                continue

            t_name = "main" if child.config.get("name") == target_name else None
            sprite_class.handle_event(type, t_name, child)

    @staticmethod
    def _generate_sprite_centres(sim_size, main_sprite_rect):
        # sprites for the digital and analog ports are positioned on a circle
        # around the pi-top, with 30 degrees between them

        canvas_centre = int(sim_size[0] / 2), int(sim_size[1] / 2)

        def pythag_hypot(a, b):
            return sqrt(a**2 + b**2)

        def point_on_circle(angle):
            center = canvas_centre
            angle = radians(angle)

            corner_padding = main_sprite_rect.width / 4
            center_to_corner = pythag_hypot(
                main_sprite_rect.width / 2, main_sprite_rect.height / 2
            )
            radius = center_to_corner + corner_padding

            x = center[0] + (radius * cos(angle))
            y = center[1] + (radius * sin(angle))

            return x, y

        # clockwise from top right
        ports = ["A1", "A0", "D3", "D2", "D1", "D0", "A3", "A2", "D7", "D6", "D5", "D4"]
        return {port: point_on_circle(-75 + 30 * i) for i, port in enumerate(ports)}