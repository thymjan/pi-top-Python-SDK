import pygame
from threading import Event, Thread
from time import sleep


class Simulatable:
    """Represents an object that can be simulated on a digital canvas."""

    def __del__(self):
        self.stop_simulation()

    def __init__(self, size=(780, 620)):
        self._sim_size = size
        self._sim_screen = None
        self._sim_stop_event = None

    def simulate(self):
        self.stop_simulation()
        self._sim_stop_event = Event()

        # pygame has to be set up in the same thread as it's render loop
        Thread(target=self.__run_sim, daemon=True).start()

    def stop_simulation(self):
        if self._sim_stop_event is not None:
            self._sim_stop_event.set()
            pygame.quit()
            self._sim_screen = None

    def __run_sim(self):
        pygame.init()
        clock = pygame.time.Clock()

        width, height = self._sim_size
        self._sim_screen = pygame.display.set_mode([width, height])
        self._sim_screen.fill((255, 255, 255))

        sprite = self._create_sprite()

        while not self._sim_stop_event.is_set():
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.stop_simulation()
                else:
                    self._handle_event(event)

            sprite.update()
            sprite.draw(self._sim_screen)
            pygame.display.flip()
            clock.tick(20)

    def _create_sprite(self):
        raise NotImplementedError(
            "_create_sprite must be implemented to use `simulate`"
        )

    def _handle_event(self, event):
        pass