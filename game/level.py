from ursina import Entity, color

from .constants import KOREAN_FONT
from .navigation import CorridorNavigation


class LevelManager:
    def __init__(self):
        self.navigation = CorridorNavigation()

        self.left_wall = None
        self.right_wall = None
        self.ceiling_sign = None
        self.front_sign = None
        self.back_sign = None
        self.exit_gate = None
        self.anomaly_object = None

        self.build_level()

    def build_level(self):
        self._main_corridor()
        self._front_corridor()
        self._back_corridor()
        self._signs()
        self._exit_gate()
        self._anomaly_object()

    def _main_corridor(self):
        Entity(
            model='cube',
            position=(0, 0, 0),
            scale=(10, 1, 100),
            color=color.gray,
            collider='box',
        )

        Entity(
            model='cube',
            position=(0, 10, 0),
            scale=(10, 1, 100),
            color=color.gray,
            collider='box',
        )

        self.left_wall = Entity(
            model='cube',
            position=(-5, 5, -5),
            scale=(1, 10, 110),
            collider='box',
            texture='assets/wall.jpg',
            texture_scale=(16, 10),
            color=color.white,
        )

        self.right_wall = Entity(
            model='cube',
            position=(5, 5, 5),
            scale=(1, 10, 110),
            collider='box',
            texture='assets/wall.jpg',
            texture_scale=(16, 10),
            color=color.white,
        )

        for i in range(-90, 90):
            Entity(
                model='cube',
                position=(0, 0.5, i * 0.5),
                scale=(0.5, 0.02, 0.5),
                texture='assets/yellow_tile.jpg',
            )

    def _front_corridor(self):
        Entity(model='cube', position=(-25, 0, 55), scale=(60, 1, 10), color=color.gray, collider='box')
        Entity(model='cube', position=(-25, 10, 55), scale=(60, 1, 10), color=color.gray, collider='box')

        Entity(
            model='cube',
            position=(-30, 5, 50),
            scale=(50, 10, 1),
            collider='box',
            texture='assets/wall.jpg',
            texture_scale=(16, 10),
        )

        Entity(
            model='cube',
            position=(-20, 5, 60),
            scale=(50, 10, 1),
            collider='box',
            texture='assets/wall.jpg',
            texture_scale=(16, 10),
        )

        Entity(model='cube', position=(-50, 0, 80), scale=(10, 1, 60), color=color.gray, collider='box')
        Entity(model='cube', position=(-50, 10, 80), scale=(10, 1, 60), color=color.gray, collider='box')

        Entity(
            model='cube',
            position=(-55, 5, 75),
            scale=(1, 10, 50),
            collider='box',
            texture='assets/wall.jpg',
            texture_scale=(16, 10),
        )

        Entity(
            model='cube',
            position=(-45, 5, 85),
            scale=(1, 10, 50),
            collider='box',
            texture='assets/wall.jpg',
            texture_scale=(16, 10),
        )

    def _back_corridor(self):
        Entity(model='cube', position=(25, 0, -55), scale=(60, 1, 10), color=color.gray, collider='box')
        Entity(model='cube', position=(25, 10, -55), scale=(60, 1, 10), color=color.gray, collider='box')

        Entity(
            model='cube',
            position=(30, 5, -50),
            scale=(50, 10, 1),
            collider='box',
            texture='assets/wall.jpg',
            texture_scale=(16, 10),
        )

        Entity(
            model='cube',
            position=(20, 5, -60),
            scale=(50, 10, 1),
            collider='box',
            texture='assets/wall.jpg',
            texture_scale=(16, 10),
        )

        Entity(model='cube', position=(50, 0, -80), scale=(10, 1, 60), color=color.gray, collider='box')
        Entity(model='cube', position=(50, 10, -80), scale=(10, 1, 60), color=color.gray, collider='box')

        Entity(
            model='cube',
            position=(55, 5, -75),
            scale=(1, 10, 50),
            collider='box',
            texture='assets/wall.jpg',
            texture_scale=(16, 10),
        )

        Entity(
            model='cube',
            position=(45, 5, -85),
            scale=(1, 10, 50),
            collider='box',
            texture='assets/wall.jpg',
            texture_scale=(16, 10),
        )

    def _signs(self):
        self.ceiling_sign = Entity(
            model='cube',
            position=(0, 9, 25),
            scale=(5.2, 1, 0.1),
            texture='assets/exit_8_ceiling.jpg',
            color=color.white,
        )

        self.front_sign = Entity(
            model='cube',
            position=(-54.4, 4.5, 55),
            scale=(0.1, 3.8, 2),
            texture='assets/exit_0_wall.jpg',
            color=color.white,
        )

        self.back_sign = Entity(
            model='cube',
            position=(-4.4, 4.5, -55),
            scale=(0.1, 3.8, 2),
            texture='assets/exit_0_wall.jpg',
            color=color.white,
        )

    def _exit_gate(self):
        self.exit_gate = Entity(
            model='cube',
            position=(-24.5, 2.6, 55),
            scale=(0.1, 4.2, 7.5),
            color=color.rgba(40, 220, 170, 70),
            collider='box',
        )

    def _anomaly_object(self):
        self.anomaly_object = Entity(
            model='sphere',
            position=(0, 3.2, 5),
            scale=(1.1, 1.1, 1.1),
            color=color.red,
            enabled=False,
        )

    def apply_anomaly(self, anomaly_type):
        self.reset_anomaly()

        if anomaly_type is None:
            return

        if anomaly_type == 'sign_wrong':
            self.ceiling_sign.texture = 'assets/exit_0_wall.jpg'

        elif anomaly_type == 'gate_red':
            self.exit_gate.color = color.rgba(220, 40, 40, 90)

        elif anomaly_type == 'wall_dark':
            self.left_wall.color = color.rgb(150, 150, 150)
            self.right_wall.color = color.rgb(150, 150, 150)

        elif anomaly_type == 'red_sphere':
            self.anomaly_object.enabled = True

    def reset_anomaly(self):
        self.ceiling_sign.texture = 'assets/exit_8_ceiling.jpg'
        self.ceiling_sign.color = color.white

        self.exit_gate.color = color.rgba(40, 220, 170, 70)

        self.left_wall.color = color.white
        self.right_wall.color = color.white

        self.anomaly_object.enabled = False

    def get_anomaly_hint(self, anomaly_type):
        if anomaly_type == 'sign_wrong':
            return '힌트: 출구 표지판의 숫자를 확인하세요.'
        if anomaly_type == 'gate_red':
            return '힌트: 출구문의 색깔을 확인하세요.'
        if anomaly_type == 'wall_dark':
            return '힌트: 양쪽 벽의 밝기를 확인하세요.'
        if anomaly_type == 'red_sphere':
            return '힌트: 복도 중앙에 이상한 물체가 있는지 확인하세요.'

        return '힌트: 이번 층은 특별한 이상현상이 없을 수 있습니다.'

    def wrap_player(self, player, quiz_is_active):
        if quiz_is_active:
            return

        if player.position.x < -25 and player.position.z > 50:
            player.set_position(
                (
                    50 + player.position.x,
                    player.position.y,
                    -110 + player.position.z,
                )
            )

        elif player.position.x > 25 and player.position.z < -50:
            player.set_position(
                (
                    -50 + player.position.x,
                    player.position.y,
                    110 + player.position.z,
                )
            )

    def keep_player_in_corridor(self, player):
        safe_x, safe_z = self.navigation.clamp_to_path(
            (player.position.x, player.position.z),
            radius=4.05,
        )

        player.set_position((safe_x, player.position.y, safe_z))
