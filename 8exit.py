import builtins
import math
import random
from pathlib import Path

from direct.actor.Actor import Actor
from panda3d.core import AntialiasAttrib, loadPrcFileData
from ursina import (
    Entity,
    Text,
    Ursina,
    application,
    camera,
    color,
    mouse,
    time,
)
from ursina.prefabs.first_person_controller import FirstPersonController


loadPrcFileData('', 'framebuffer-multisample 1')
loadPrcFileData('', 'multisamples 4')
loadPrcFileData('', 'render-mode forward')


app = Ursina()
mouse.visible = False
application.fonts_folder = Path('C:/Windows/Fonts')
builtins.render.setAntialias(AntialiasAttrib.MAuto)


PLAYER_START = (0, 2, -35)
CHASER_START = (0, 0.5, -48)
MAX_FLOOR = 8
KOREAN_FONT = 'malgun.ttf'


def flat_distance(a, b):
    return math.sqrt((a[0] - b[0]) ** 2 + (a[1] - b[1]) ** 2)


class CorridorNavigation:
    def __init__(self):
        self.segments = [
            ((0, -50), (0, 50)),
            ((0, 50), (0, 55)),
            ((0, 55), (-50, 55)),
            ((-50, 55), (-50, 105)),
            ((0, -50), (0, -55)),
            ((0, -55), (50, -55)),
            ((50, -55), (50, -105)),
        ]
        self.nodes = sorted({point for segment in self.segments for point in segment})
        self.base_graph = {node: [] for node in self.nodes}

        for start, end in self.segments:
            distance = flat_distance(start, end)
            self.base_graph[start].append((end, distance))
            self.base_graph[end].append((start, distance))

    def find_path(self, start_position, target_position):
        start_point, start_segment = self._nearest_point_on_path(start_position)
        target_point, target_segment = self._nearest_point_on_path(target_position)
        start_key = ('start', start_point)
        target_key = ('target', target_point)
        graph = {node: neighbors[:] for node, neighbors in self.base_graph.items()}
        graph[start_key] = []
        graph[target_key] = []

        self._connect_dynamic_point(graph, start_key, start_point, start_segment)
        self._connect_dynamic_point(graph, target_key, target_point, target_segment)

        if start_segment == target_segment:
            distance = flat_distance(start_point, target_point)
            graph[start_key].append((target_key, distance))
            graph[target_key].append((start_key, distance))

        return self._shortest_path(graph, start_key, target_key)

    def clamp_to_path(self, position, radius):
        nearest_point, _ = self._nearest_point_on_path(position)
        distance = flat_distance(position, nearest_point)

        if distance <= radius or distance == 0:
            return position

        dx = position[0] - nearest_point[0]
        dz = position[1] - nearest_point[1]
        return (
            nearest_point[0] + dx / distance * radius,
            nearest_point[1] + dz / distance * radius,
        )

    def _nearest_point_on_path(self, position):
        best_point = None
        best_segment_index = 0
        best_distance = float('inf')

        for index, segment in enumerate(self.segments):
            point = self._project_to_segment(position, *segment)
            distance = flat_distance(position, point)
            if distance < best_distance:
                best_point = point
                best_segment_index = index
                best_distance = distance

        return best_point, best_segment_index

    def _project_to_segment(self, position, start, end):
        px, pz = position
        ax, az = start
        bx, bz = end
        dx = bx - ax
        dz = bz - az
        length_squared = dx * dx + dz * dz

        if length_squared == 0:
            return start

        t = ((px - ax) * dx + (pz - az) * dz) / length_squared
        t = max(0, min(1, t))
        return (ax + dx * t, az + dz * t)

    def _connect_dynamic_point(self, graph, key, point, segment_index):
        start, end = self.segments[segment_index]
        for node in (start, end):
            distance = flat_distance(point, node)
            graph[key].append((node, distance))
            graph[node].append((key, distance))

    def _shortest_path(self, graph, start_key, target_key):
        distances = {start_key: 0}
        previous = {}
        unvisited = set(graph.keys())

        while unvisited:
            current = min(unvisited, key=lambda node: distances.get(node, float('inf')))
            if distances.get(current, float('inf')) == float('inf'):
                break

            unvisited.remove(current)
            if current == target_key:
                break

            for neighbor, edge_distance in graph[current]:
                new_distance = distances[current] + edge_distance
                if new_distance < distances.get(neighbor, float('inf')):
                    distances[neighbor] = new_distance
                    previous[neighbor] = current

        if target_key not in distances:
            return []

        path = []
        current = target_key
        while current != start_key:
            path.append(current)
            current = previous[current]
        path.append(start_key)
        path.reverse()

        return [self._node_position(node) for node in path]

    def _node_position(self, node):
        if isinstance(node, tuple) and len(node) == 2 and isinstance(node[0], str):
            return node[1]
        return node


class LevelManager:
    def __init__(self):
        self.navigation = CorridorNavigation()
        self.build_level()

    def build_level(self):
        self._main_corridor()
        self._front_corridor()
        self._back_corridor()
        self._signs()
        self._exit_gate()

    def _main_corridor(self):
        Entity(model='cube', position=(0, 0, 0), scale=(10, 1, 100), color=color.gray, collider='box')
        Entity(model='cube', position=(0, 10, 0), scale=(10, 1, 100), color=color.gray, collider='box')
        Entity(
            model='cube',
            position=(-5, 5, -5),
            scale=(1, 10, 110),
            collider='box',
            texture='assets/wall.jpg',
            texture_scale=(16, 10),
        )
        Entity(
            model='cube',
            position=(5, 5, 5),
            scale=(1, 10, 110),
            collider='box',
            texture='assets/wall.jpg',
            texture_scale=(16, 10),
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
        Entity(model='cube', position=(0, 9, 25), scale=(5.2, 1, 0.1), texture='assets/exit_8_ceiling.jpg')
        Entity(model='cube', position=(-54.4, 4.5, 55), scale=(0.1, 3.8, 2), texture='assets/exit_0_wall.jpg')
        Entity(model='cube', position=(-4.4, 4.5, -55), scale=(0.1, 3.8, 2), texture='assets/exit_0_wall.jpg')

    def _exit_gate(self):
        self.exit_gate = Entity(
            model='cube',
            position=(-24.5, 2.6, 55),
            scale=(0.1, 4.2, 7.5),
            color=color.rgba(40, 220, 170, 70),
            collider='box',
        )

    def wrap_player(self, player, quiz_is_active):
        if quiz_is_active:
            return

        if player.position.x < -25 and player.position.z > 50:
            player.set_position((50 + player.position.x, player.position.y, -110 + player.position.z))
        elif player.position.x > 25 and player.position.z < -50:
            player.set_position((-50 + player.position.x, player.position.y, 110 + player.position.z))

    def keep_player_in_corridor(self, player):
        safe_x, safe_z = self.navigation.clamp_to_path(
            (player.position.x, player.position.z),
            radius=4.05,
        )
        player.set_position((safe_x, player.position.y, safe_z))


class ChaserNPC:
    def __init__(self, player, navigation):
        self.player = player
        self.navigation = navigation
        self.base_speed = 5.4
        self.catch_radius = 2.1
        self.entity = Entity(position=CHASER_START, scale=(1.25, 1.25, 1.25), collider='box')
        self.actor = Actor('assets/npc.glb')
        self.actor.reparent_to(self.entity)
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
            if flat_distance((self.entity.position.x, self.entity.position.z), point) > 0.15:
                return point
        return path[-1]

    def caught_player(self):
        dx = self.player.position.x - self.entity.position.x
        dz = self.player.position.z - self.entity.position.z
        return math.sqrt(dx * dx + dz * dz) <= self.catch_radius


class QuizZone:
    def __init__(self, game):
        self.game = game
        self.active = False
        self.correct_index = None
        self.question = None
        self.choices = []
        self.player_speed_before_quiz = None

        self.panel = Entity(
            parent=camera.ui,
            model='quad',
            position=(0, 0.34),
            scale=(1.35, 0.24),
            color=color.rgba(0, 0, 0, 0),
            z=0.1,
            enabled=False,
        )
        self.text = Text(
            parent=camera.ui,
            text='',
            origin=(0, 0),
            position=(0, 0.35),
            z=-0.1,
            scale=1.0,
            color=color.black,
            font=KOREAN_FONT,
            enabled=False,
        )

    def update(self, player):
        if self.active:
            return

        if player.position.x < -22.5 and 50 < player.position.z < 60:
            self.open()

    def open(self):
        self.active = True
        self.player_speed_before_quiz = self.game.player.speed
        self.game.player.speed = 0
        mouse.locked = True
        mouse.visible = False
        self.question, self.choices, self.correct_index = self._make_question(self.game.floor)
        self._render()

    def close(self):
        self.active = False
        self.panel.enabled = False
        self.text.enabled = False
        if self.player_speed_before_quiz is not None:
            self.game.player.speed = self.player_speed_before_quiz
            self.player_speed_before_quiz = None
        mouse.visible = False

    def handle_input(self, key):
        key_to_index = {
            '1': 0,
            '2': 1,
            '3': 2,
            'numpad 1': 0,
            'numpad 2': 1,
            'numpad 3': 2,
        }
        if key not in key_to_index:
            return

        selected_index = key_to_index[key]
        if selected_index == self.correct_index:
            self.close()
            self.game.next_floor()
        else:
            self.close()
            self.game.wrong_answer()

    def _make_question(self, floor):
        left = random.randint(2 + floor, 7 + floor)
        right = random.randint(1 + floor, 5 + floor)
        answer = left + right
        choices = [answer, answer + random.randint(1, 3), max(0, answer - random.randint(1, 3))]
        random.shuffle(choices)
        correct_index = choices.index(answer)
        question = f'{floor}층 문제: {left} + {right} = ?'
        return question, choices, correct_index

    def _render(self):
        lines = [
            self.question,
            f'1. {self.choices[0]}    2. {self.choices[1]}    3. {self.choices[2]}',
            '뒤를 보면서 1, 2, 3 중 하나를 누르세요',
        ]
        self.text.text = '\n'.join(lines)
        self.panel.enabled = True
        self.text.enabled = True


class GameManager:
    def __init__(self):
        self.floor = 1
        self.message_timer = 0

        self.level = LevelManager()
        self.player = FirstPersonController()
        self.player.cursor.visible = False
        self.player.gravity = 0.5
        self.player.speed = 15
        self.player.set_position(PLAYER_START)

        self.hud = Text(
            parent=camera.ui,
            text='',
            position=(-0.86, 0.45),
            scale=1.35,
            color=color.white,
            font=KOREAN_FONT,
        )
        self.message_text = Text(
            parent=camera.ui,
            text='',
            origin=(0, 0),
            position=(0, -0.38),
            scale=1.25,
            color=color.yellow,
            font=KOREAN_FONT,
        )

        self.chaser = ChaserNPC(self.player, self.level.navigation)
        self.quiz_zone = QuizZone(self)
        self.show_message('초록색 출구로 가서 문제를 푸세요. 술래는 계속 따라옵니다.', 4)
        self._refresh_hud()

    def update(self):
        self.quiz_zone.update(self.player)
        self.level.wrap_player(self.player, self.quiz_zone.active)
        self.level.keep_player_in_corridor(self.player)
        self.chaser.update()

        if self.chaser.caught_player():
            self.player_caught()

        if self.message_timer > 0:
            self.message_timer -= time.dt
            if self.message_timer <= 0:
                self.message_text.text = ''

    def handle_input(self, key):
        if key == 'escape':
            application.quit()
            return

        if self.quiz_zone.active:
            self.quiz_zone.handle_input(key)

    def next_floor(self):
        if self.floor >= MAX_FLOOR:
            self.show_message('8번 출구 탈출 성공!', 6)
            self.reset_current_floor()
            return

        self.floor += 1
        self.reset_current_floor()
        self.show_message(f'정답입니다. {self.floor}층으로 이동합니다.', 3)
        self._refresh_hud()

    def wrong_answer(self):
        self.reset_current_floor()
        self.show_message('오답입니다. 현재 층을 다시 시작합니다.', 3)

    def player_caught(self):
        if self.quiz_zone.active:
            self.quiz_zone.close()
        self.reset_current_floor()
        self.show_message('술래에게 잡혔습니다. 현재 층을 다시 시작합니다.', 3)

    def reset_current_floor(self):
        self.player.enabled = True
        mouse.visible = False
        self.player.set_position(PLAYER_START)
        self.player.rotation_y = 0
        self.chaser.reset(self.floor)
        self._refresh_hud()

    def show_message(self, message, duration):
        self.message_text.text = message
        self.message_timer = duration

    def _refresh_hud(self):
        self.hud.text = f'{self.floor}/{MAX_FLOOR}층'


game = GameManager()


def update():
    game.update()


def input(key):
    game.handle_input(key)


app.run()
