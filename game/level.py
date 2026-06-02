from ursina import Entity, color

from .constants import PLAYER_CORRIDOR_RADIUS
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
        self.gate_portal_front = None
        self.gate_portal_back = None
        self.poster = None

        self.build_level()

    def build_level(self):
        self._main_corridor()
        self._front_corridor()
        self._back_corridor()
        self._signs()
        self._exit_gate()
        self._poster()

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
        Entity(name='front_floor_1', model='cube', position=(-25, 0, 55), scale=(60, 1, 10), color=color.gray, collider='box')
        Entity(name='front_ceiling_1', model='cube', position=(-25, 10, 55), scale=(60, 1, 10), color=color.gray, collider='box')

        Entity(
            name='front_wall_z50',
            model='cube',
            position=(-30, 5, 50),
            scale=(50, 10, 1),
            collider='box',
            texture='assets/wall.jpg',
            texture_scale=(16, 10),
        )

        Entity(
            name='front_wall_z60',
            model='cube',
            position=(-20, 5, 60),
            scale=(50, 10, 1),
            collider='box',
            texture='assets/wall.jpg',
            texture_scale=(16, 10),
        )

        Entity(name='front_floor_2', model='cube', position=(-50, 0, 80), scale=(10, 1, 60), color=color.gray, collider='box')
        Entity(name='front_ceiling_2', model='cube', position=(-50, 10, 80), scale=(10, 1, 60), color=color.gray, collider='box')

        Entity(
            name='front_wall_x55',
            model='cube',
            position=(-55, 5, 75),
            scale=(1, 10, 50),
            collider='box',
            texture='assets/wall.jpg',
            texture_scale=(16, 10),
        )

        Entity(
            name='front_wall_x45',
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
            name='exit_gate_trigger_panel',
            model='cube',
            position=(-24.5, 2.7, 55),
            scale=(0.12, 4.4, 8.0),
            visible=False,
            collider='box',
        )

        self.gate_portal_front = Entity(
            name='gate_portal_front',
            model='quad',
            texture='assets/portal.png',
            position=(-24.25, 3.05, 55),
            rotation_y=90,
            scale=(5.8, 5.8),
            color=color.white,
            double_sided=True,
        )

        self.gate_portal_back = Entity(
            name='gate_portal_back',
            model='quad',
            texture='assets/portal.png',
            position=(-24.75, 3.05, 55),
            rotation_y=-90,
            scale=(5.8, 5.8),
            color=color.white,
            double_sided=True,
        )


    def _poster(self):
        self.poster = Entity(
            name='poster',
            model='quad',
            texture='assets/poster.png',
            position=(-4.48, 4.2, -10),
            rotation_y=90,
            scale=(3.0, 2.2),
            texture_scale=(-1, 1),   # 좌우 반전 보정
            color=color.white,
            double_sided=True,
        )

        self.gate_portal_front = Entity(
            name='gate_portal_front',
            model='quad',
            texture='assets/portal.png',
            position=(-24.25, 3.05, 55),
            rotation_y=90,
            scale=(5.8, 5.8),
            color=color.white,
        )

        self.gate_portal_back = Entity(
            name='gate_portal_back',
            model='quad',
            texture='assets/portal.png',
            position=(-24.75, 3.05, 55),
            rotation_y=-90,
            scale=(5.8, 5.8),
            color=color.white,
        )

    def apply_anomaly(self, anomaly_type):
        self.reset_anomaly()

        if anomaly_type is None:
            return
        if anomaly_type == 'sign_wrong':
            self.ceiling_sign.texture = 'assets/exit_0_wall.jpg'

        elif anomaly_type == 'gate_red':
            self.gate_portal_front.color = color.rgb(255, 80, 80)
            self.gate_portal_back.color = color.rgb(255, 80, 80)

        elif anomaly_type == 'wall_dark':
            self.left_wall.color = color.rgb(150, 150, 150)
            self.right_wall.color = color.rgb(150, 150, 150)

        elif anomaly_type == 'poster_changed':
            self.poster.texture = 'assets/poster2.png'

    def reset_anomaly(self):
        self.ceiling_sign.texture = 'assets/exit_8_ceiling.jpg'
        self.ceiling_sign.color = color.white

        self.gate_portal_front.color = color.white
        self.gate_portal_back.color = color.white

        self.left_wall.color = color.white
        self.right_wall.color = color.white

        self.poster.texture = 'assets/poster.png'

    def get_anomaly_hint(self, anomaly_type):
        if anomaly_type == 'sign_wrong':
            return '힌트: 출구 표지판의 숫자를 확인하세요.'
        if anomaly_type == 'gate_red':
            return '힌트: 출구문의 색깔을 확인하세요.'
        if anomaly_type == 'wall_dark':
            return '힌트: 양쪽 벽의 밝기를 확인하세요.'
        if anomaly_type == 'poster_changed':
            return '힌트: 벽에 붙은 포스터를 확인하세요.'

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
            radius=PLAYER_CORRIDOR_RADIUS,
        )

        player.set_position((safe_x, player.position.y, safe_z))
