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
    window,
)
from ursina.prefabs.first_person_controller import FirstPersonController


loadPrcFileData('', 'framebuffer-multisample 1')
loadPrcFileData('', 'multisamples 4')
loadPrcFileData('', 'render-mode forward')


app = Ursina()

# 오른쪽 디버그 숫자 숨기기
window.fps_counter.enabled = False
window.entity_counter.enabled = False
window.collider_counter.enabled = False

mouse.visible = False
application.fonts_folder = Path('C:/Windows/Fonts')
builtins.render.setAntialias(AntialiasAttrib.MAuto)


PLAYER_START = (0, 2, -35)
CHASER_START = (0, 0.5, -48)

MAX_FLOOR = 8
KOREAN_FONT = 'malgun.ttf'

BASE_FLOOR_TIME = 40
MIN_FLOOR_TIME = 18


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
            if flat_distance((self.entity.position.x, self.entity.position.z), point) > 0.15:
                return point

        return path[-1]

    def caught_player(self):
        return self.distance_to_player() <= self.catch_radius

    def distance_to_player(self):
        dx = self.player.position.x - self.entity.position.x
        dz = self.player.position.z - self.entity.position.z

        return math.sqrt(dx * dx + dz * dz)


class QuizZone:
    def __init__(self, game):
        self.game = game
        self.active = False
        self.correct_index = None
        self.question = None
        self.choices = []
        self.question_type = None
        self.hint_text = ''
        self.player_speed_before_quiz = None

        self.panel = Entity(
            parent=camera.ui,
            model='quad',
            position=(0, 0.34),
            scale=(1.35, 0.32),
            color=color.rgba(0, 0, 0, 190),
            z=0.2,
            enabled=False,
        )

        self.text = Text(
            parent=camera.ui,
            text='',
            origin=(0, 0),
            position=(0, 0.36),
            z=-0.2,
            scale=1.0,
            color=color.white,
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

        self.question, self.choices, self.correct_index, self.question_type = self._make_question()
        self.hint_text = ''
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

        if selected_index >= len(self.choices):
            return

        if selected_index == self.correct_index:
            self.close()
            self.game.next_floor()
        else:
            self.close()
            self.game.wrong_answer()

    def use_hint(self):
        if not self.active:
            return False

        if self.question_type == 'math':
            answer = self.choices[self.correct_index]
            if answer % 2 == 0:
                self.hint_text = '힌트: 정답은 짝수입니다.'
            else:
                self.hint_text = '힌트: 정답은 홀수입니다.'

        elif self.question_type == 'anomaly_yes_no':
            self.hint_text = self.game.level.get_anomaly_hint(self.game.current_anomaly)

        elif self.question_type == 'sign_number':
            self.hint_text = '힌트: 천장에 있는 노란 출구 표지판을 확인하세요.'

        elif self.question_type == 'gate_color':
            self.hint_text = '힌트: 초록색 출구문 색이 바뀌었는지 확인하세요.'

        self._render()
        return True

    def _make_question(self):
        question_types = ['math', 'anomaly_yes_no', 'sign_number', 'gate_color']
        question_type = random.choice(question_types)

        if question_type == 'math':
            return self._make_math_question(question_type)

        if question_type == 'anomaly_yes_no':
            return self._make_anomaly_question(question_type)

        if question_type == 'sign_number':
            return self._make_sign_question(question_type)

        return self._make_gate_color_question(question_type)

    def _make_math_question(self, question_type):
        floor = self.game.floor

        left = random.randint(2 + floor, 7 + floor)
        right = random.randint(1 + floor, 5 + floor)
        answer = left + right

        choices = [
            answer,
            answer + random.randint(1, 3),
            max(0, answer - random.randint(1, 3)),
        ]

        random.shuffle(choices)

        correct_index = choices.index(answer)
        question = f'{floor}층 문제: {left} + {right} = ?'

        return question, choices, correct_index, question_type

    def _make_anomaly_question(self, question_type):
        question = '이번 층에 이상현상이 있었습니까?'

        choices = ['있었다', '없었다']
        answer = '있었다' if self.game.current_anomaly is not None else '없었다'

        correct_index = choices.index(answer)

        return question, choices, correct_index, question_type

    def _make_sign_question(self, question_type):
        question = '천장 출구 표지판의 숫자는 무엇입니까?'

        answer = 0 if self.game.current_anomaly == 'sign_wrong' else 8
        choices = [8, 0, 9]

        random.shuffle(choices)
        correct_index = choices.index(answer)

        return question, choices, correct_index, question_type

    def _make_gate_color_question(self, question_type):
        question = '출구문의 색깔은 무엇입니까?'

        answer = '빨강' if self.game.current_anomaly == 'gate_red' else '초록'
        choices = ['초록', '빨강', '노랑']

        random.shuffle(choices)
        correct_index = choices.index(answer)

        return question, choices, correct_index, question_type

    def _render(self):
        choice_lines = []

        for index, choice in enumerate(self.choices):
            choice_lines.append(f'{index + 1}. {choice}')

        lines = [
            self.question,
            '',
            '     '.join(choice_lines),
            '',
            '1, 2, 3 중 하나를 누르세요',
            'H 키: 힌트 사용 / 남은 시간 5초 감소',
        ]

        if self.hint_text:
            lines.append('')
            lines.append(self.hint_text)

        self.text.text = '\n'.join(lines)
        self.panel.enabled = True
        self.text.enabled = True


class GameManager:
    def __init__(self):
        self.floor = 1
        self.state = 'start'

        self.message_timer = 0
        self.floor_timer = BASE_FLOOR_TIME
        self.total_play_time = 0

        self.current_anomaly = None

        self.wrong_count = 0
        self.caught_count = 0
        self.timeout_count = 0
        self.hint_count = 0
        self.clear_count = 0
        self.event_logs = []

        self.level = LevelManager()

        self.player = FirstPersonController()
        self.player.cursor.visible = False
        self.player.gravity = 0.5
        self.player.speed = 15
        self.player.set_position(PLAYER_START)
        self.player.enabled = False

        self.chaser = ChaserNPC(self.player, self.level.navigation)
        self.quiz_zone = QuizZone(self)

        self._create_game_ui()
        self._create_start_ui()
        self._create_clear_ui()

        self.setup_floor()
        self.show_start_screen()
        self._refresh_hud()

    def _create_game_ui(self):
        self.hud_panel = Entity(
            parent=camera.ui,
            model='quad',
            position=(-0.65, 0.38),
            scale=(0.58, 0.25),
            color=color.rgba(0, 0, 0, 150),
            z=0.2,
            enabled=False,
        )

        self.hud_text = Text(
            parent=camera.ui,
            text='',
            position=(-0.90, 0.47),
            z=-0.2,
            scale=1.05,
            color=color.white,
            font=KOREAN_FONT,
            enabled=False,
        )

        self.timer_text = Text(
            parent=camera.ui,
            text='',
            position=(-0.90, 0.41),
            z=-0.2,
            scale=1.0,
            color=color.white,
            font=KOREAN_FONT,
            enabled=False,
        )

        self.status_text = Text(
            parent=camera.ui,
            text='',
            position=(-0.90, 0.35),
            z=-0.2,
            scale=0.95,
            color=color.yellow,
            font=KOREAN_FONT,
            enabled=False,
        )

        self.objective_panel = Entity(
            parent=camera.ui,
            model='quad',
            position=(0.42, 0.42),
            scale=(1.02, 0.12),
            color=color.rgba(0, 0, 0, 130),
            z=0.2,
            enabled=False,
        )

        self.objective_text = Text(
            parent=camera.ui,
            text='목표: 초록색 출구로 이동',
            position=(-0.04, 0.445),
            z=-0.2,
            scale=0.95,
            color=color.white,
            font=KOREAN_FONT,
            enabled=False,
        )

        self.message_panel = Entity(
            parent=camera.ui,
            model='quad',
            position=(0, -0.38),
            scale=(1.15, 0.12),
            color=color.rgba(0, 0, 0, 170),
            z=0.2,
            enabled=False,
        )

        self.message_text = Text(
            parent=camera.ui,
            text='',
            origin=(0, 0),
            position=(0, -0.38),
            z=-0.2,
            scale=1.05,
            color=color.white,
            font=KOREAN_FONT,
            enabled=False,
        )

        self.warning_overlay = Entity(
            parent=camera.ui,
            model='quad',
            position=(0, 0),
            scale=(2, 1.2),
            color=color.rgba(255, 0, 0, 0),
            z=0.5,
            enabled=False,
        )

    def _create_start_ui(self):
        self.start_panel = Entity(
            parent=camera.ui,
            model='quad',
            position=(0, 0),
            scale=(1.35, 0.85),
            color=color.rgba(0, 0, 0, 220),
            z=0.2,
            enabled=False,
        )

        self.start_title = Text(
            parent=camera.ui,
            text='8 CHASER',
            origin=(0, 0),
            position=(0, 0.23),
            z=-0.2,
            scale=3.0,
            color=color.yellow,
            font=KOREAN_FONT,
            enabled=False,
        )

        self.start_guide = Text(
            parent=camera.ui,
            text=(
                '8번 출구를 모티브로 한 추격형 탈출 게임\n\n'
                '초록색 출구로 이동해서 문제를 푸세요.\n'
                '제한시간 안에 답하지 못하거나 술래에게 잡히면 현재 층을 다시 시작합니다.\n\n'
                'WASD : 이동\n'
                '마우스 : 시점 이동\n'
                '1, 2, 3 : 정답 선택\n'
                'H : 힌트 사용\n'
                'ESC : 종료\n\n'
                '[ SPACE ] 게임 시작'
            ),
            origin=(0, 0),
            position=(0, -0.09),
            z=-0.2,
            scale=1.05,
            color=color.white,
            font=KOREAN_FONT,
            enabled=False,
        )

    def _create_clear_ui(self):
        self.clear_panel = Entity(
            parent=camera.ui,
            model='quad',
            position=(0, 0),
            scale=(1.35, 0.85),
            color=color.rgba(0, 0, 0, 225),
            z=0.2,
            enabled=False,
        )

        self.clear_title = Text(
            parent=camera.ui,
            text='탈출 성공!',
            origin=(0, 0),
            position=(0, 0.23),
            z=-0.2,
            scale=2.5,
            color=color.yellow,
            font=KOREAN_FONT,
            enabled=False,
        )

        self.clear_guide = Text(
            parent=camera.ui,
            text='',
            origin=(0, 0),
            position=(0, -0.08),
            z=-0.2,
            scale=1.05,
            color=color.white,
            font=KOREAN_FONT,
            enabled=False,
        )

    def setup_floor(self):
        self.floor_timer = max(MIN_FLOOR_TIME, BASE_FLOOR_TIME - (self.floor - 1) * 2)

        anomaly_list = [None, 'sign_wrong', 'gate_red', 'wall_dark', 'red_sphere']
        self.current_anomaly = random.choice(anomaly_list)

        self.level.apply_anomaly(self.current_anomaly)

    def update(self):
        if self.state != 'playing':
            return

        self.total_play_time += time.dt
        self.floor_timer -= time.dt

        if self.floor_timer <= 0:
            self.timeout()
            return

        self.quiz_zone.update(self.player)
        self.level.wrap_player(self.player, self.quiz_zone.active)
        self.level.keep_player_in_corridor(self.player)
        self.chaser.update()

        if self.chaser.caught_player():
            self.player_caught()
            return

        self._refresh_hud()
        self._update_message_timer()
        self._update_warning_overlay()

    def handle_input(self, key):
        if key == 'escape':
            application.quit()
            return

        if self.state == 'start' and key == 'space':
            self.start_game()
            return

        if self.state == 'clear' and key == 'r':
            self.restart_game()
            return

        if self.state == 'playing' and key == 'h':
            self.use_hint()
            return

        if self.state == 'playing' and self.quiz_zone.active:
            self.quiz_zone.handle_input(key)

    def start_game(self):
        self.state = 'playing'

        self.start_panel.enabled = False
        self.start_title.enabled = False
        self.start_guide.enabled = False

        self.clear_panel.enabled = False
        self.clear_title.enabled = False
        self.clear_guide.enabled = False

        self.hud_panel.enabled = True
        self.hud_text.enabled = True
        self.timer_text.enabled = True
        self.status_text.enabled = True
        self.objective_panel.enabled = True
        self.objective_text.enabled = True

        self.player.enabled = True
        mouse.locked = True
        mouse.visible = False

        self.show_message('초록색 출구로 이동하세요. 술래가 따라옵니다.', 4)

    def show_start_screen(self):
        self.state = 'start'

        self.start_panel.enabled = True
        self.start_title.enabled = True
        self.start_guide.enabled = True

        self.clear_panel.enabled = False
        self.clear_title.enabled = False
        self.clear_guide.enabled = False

        self._hide_game_ui()

        self.player.enabled = False

        mouse.locked = False
        mouse.visible = True

    def show_clear_screen(self):
        self.state = 'clear'

        self.clear_count += 1
        self.player.enabled = False
        self.quiz_zone.close()
        self.level.reset_anomaly()

        self._hide_game_ui()

        result_text = self._make_result_text()

        self.clear_guide.text = result_text

        self.clear_panel.enabled = True
        self.clear_title.enabled = True
        self.clear_guide.enabled = True

        mouse.locked = False
        mouse.visible = True

    def restart_game(self):
        self.floor = 1
        self.total_play_time = 0

        self.wrong_count = 0
        self.caught_count = 0
        self.timeout_count = 0
        self.hint_count = 0
        self.event_logs = []

        self.clear_panel.enabled = False
        self.clear_title.enabled = False
        self.clear_guide.enabled = False

        self.reset_current_floor()
        self.start_game()

    def next_floor(self):
        self.event_logs.append(f'{self.floor}층 성공')

        if self.floor >= MAX_FLOOR:
            self.show_clear_screen()
            return

        self.floor += 1
        self.reset_current_floor()
        self.show_message(f'정답입니다. {self.floor}층으로 이동합니다.', 3)
        self._refresh_hud()

    def wrong_answer(self):
        self.wrong_count += 1
        self.event_logs.append(f'{self.floor}층 오답')

        self.reset_current_floor()
        self.show_message('오답입니다. 현재 층을 다시 시작합니다.', 3)

    def player_caught(self):
        self.caught_count += 1
        self.event_logs.append(f'{self.floor}층 술래에게 잡힘')

        if self.quiz_zone.active:
            self.quiz_zone.close()

        self.reset_current_floor()
        self.show_message('술래에게 잡혔습니다. 현재 층을 다시 시작합니다.', 3)

    def timeout(self):
        self.timeout_count += 1
        self.event_logs.append(f'{self.floor}층 시간 초과')

        if self.quiz_zone.active:
            self.quiz_zone.close()

        self.reset_current_floor()
        self.show_message('시간 초과입니다. 현재 층을 다시 시작합니다.', 3)

    def use_hint(self):
        if not self.quiz_zone.active:
            self.show_message('문제가 열렸을 때만 힌트를 사용할 수 있습니다.', 2)
            return

        used = self.quiz_zone.use_hint()

        if used:
            self.hint_count += 1
            self.floor_timer = max(0, self.floor_timer - 5)
            self.chaser.add_pressure()
            self.show_message('힌트를 사용했습니다. 남은 시간이 5초 감소하고 술래가 빨라집니다.', 3)

    def reset_current_floor(self):
        self.setup_floor()

        self.player.enabled = True
        mouse.visible = False

        self.player.set_position(PLAYER_START)
        self.player.rotation_y = 0

        self.chaser.reset(self.floor)

        self._refresh_hud()

    def show_message(self, message, duration):
        self.message_text.text = message
        self.message_timer = duration

        self.message_panel.enabled = True
        self.message_text.enabled = True

    def _update_message_timer(self):
        if self.message_timer > 0:
            self.message_timer -= time.dt

            if self.message_timer <= 0:
                self.message_text.text = ''
                self.message_panel.enabled = False
                self.message_text.enabled = False

    def _refresh_hud(self):
        distance = self.chaser.distance_to_player()
        remaining_time = max(0, int(self.floor_timer))

        if distance > 30:
            danger_text = '안전'
            self.status_text.color = color.green
        elif distance > 15:
            danger_text = '주의'
            self.status_text.color = color.yellow
        else:
            danger_text = '위험'
            self.status_text.color = color.red

        self.hud_text.text = f'현재 층: {self.floor} / {MAX_FLOOR}'
        self.timer_text.text = f'남은 시간: {remaining_time}초'
        self.status_text.text = f'술래 거리: {danger_text}'

        if remaining_time <= 10:
            self.timer_text.color = color.red
        else:
            self.timer_text.color = color.white

        if self.quiz_zone.active:
            self.objective_text.text = '목표: 문제를 풀어 다음 층으로 이동'
        else:
            self.objective_text.text = '목표: 초록색 출구로 이동'

    def _update_warning_overlay(self):
        distance = self.chaser.distance_to_player()

        if distance <= 15:
            blink = int(time.time() * 4) % 2

            if blink == 0:
                self.warning_overlay.color = color.rgba(255, 0, 0, 45)
            else:
                self.warning_overlay.color = color.rgba(255, 0, 0, 0)

            self.warning_overlay.enabled = True
        else:
            self.warning_overlay.enabled = False

    def _hide_game_ui(self):
        self.hud_panel.enabled = False
        self.hud_text.enabled = False
        self.timer_text.enabled = False
        self.status_text.enabled = False
        self.objective_panel.enabled = False
        self.objective_text.enabled = False
        self.message_panel.enabled = False
        self.message_text.enabled = False
        self.warning_overlay.enabled = False

    def _make_result_text(self):
        minutes = int(self.total_play_time // 60)
        seconds = int(self.total_play_time % 60)

        recent_logs = self.event_logs[-6:]

        if recent_logs:
            log_text = '\n'.join([f'- {log}' for log in recent_logs])
        else:
            log_text = '- 기록 없음'

        return (
            f'총 플레이 시간: {minutes}분 {seconds}초\n'
            f'오답 횟수: {self.wrong_count}회\n'
            f'술래에게 잡힌 횟수: {self.caught_count}회\n'
            f'시간 초과 횟수: {self.timeout_count}회\n'
            f'힌트 사용 횟수: {self.hint_count}회\n\n'
            f'최근 로그\n'
            f'{log_text}\n\n'
            f'[ R ] 다시 시작\n'
            f'[ ESC ] 종료'
        )


game = GameManager()


def update():
    game.update()


def input(key):
    game.handle_input(key)


app.run()