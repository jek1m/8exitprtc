import math

from direct.actor.Actor import Actor
from ursina import Entity, color, time

from .constants import CHASER_START


class ChaserNPC:
    def __init__(self, player, navigation):
        self.player = player
        self.navigation = navigation
        self.base_speed = 5.4
        self.catch_radius = 2.1

        self.entity = Entity(
            position=CHASER_START,
            scale=(1.25, 1.25, 1.25),
            collider='box',
        )

        self.actor = Actor('assets/npc.glb')
        self.actor.reparent_to(self.entity)
        self.actor.setH(180)

        self.marker = Entity(
            parent=self.entity,
            model='sphere',
            position=(0, 2.4, 0),
            scale=(0.35, 0.35, 0.35),
            color=color.yellow,
            always_on_top=True,
            render_queue=1,
        )

        self._play_first_animation()
        self.reset(1)

    def _play_first_animation(self):
        animations = self.actor.getAnimNames()

        if animations:
            self.actor.loop(animations[0])

    def reset(self, floor):
        self.floor = floor
        self.speed = self.base_speed + (floor - 1) * 0.6
        self.entity.set_position(CHASER_START)

    def add_pressure(self):
        self.speed += 1.2

    def update(self):
        path = self.navigation.find_path(
            (self.entity.position.x, self.entity.position.z),
            (self.player.position.x, self.player.position.z),
        )

        if len(path) < 2:
            return

        target_x, target_z = self._next_path_point(path)

        dx = target_x - self.entity.position.x
        dz = target_z - self.entity.position.z

        distance = math.sqrt(dx * dx + dz * dz)

        if distance <= 0.05:
            return

        step = min(self.speed * time.dt, distance)

        self.entity.x += dx / distance * step
        self.entity.z += dz / distance * step
        self.entity.rotation_y = math.degrees(math.atan2(dx, dz))

    def _next_path_point(self, path):
        for point in path[1:]:
            if math.sqrt((self.entity.position.x - point[0]) ** 2 + (self.entity.position.z - point[1]) ** 2) > 0.15:
                return point

        return path[-1]

    def caught_player(self):
        return self.distance_to_player() <= self.catch_radius

    def distance_to_player(self):
        dx = self.player.position.x - self.entity.position.x
        dz = self.player.position.z - self.entity.position.z

        return math.sqrt(dx * dx + dz * dz)
