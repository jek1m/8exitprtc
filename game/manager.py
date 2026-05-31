import random

from ursina import Entity, Text, camera, color, mouse, time, application
from ursina.prefabs.first_person_controller import FirstPersonController

from .constants import BASE_FLOOR_TIME, MIN_FLOOR_TIME, MAX_FLOOR, ANOMALY_TYPES
from .chaser import ChaserNPC
from .level import LevelManager
from .quiz import QuizZone


class GameManager:
    def __init__(self):
        self.floor = 1
        self.state = 'start'

        self.message_timer = 0
        self.objective_timer = 0
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
        self.player.set_position((0, 2, -35))
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
            position=(-0.70, 0.40),
            scale=(0.38, 0.20),
            color=color.rgba(0, 0, 0, 150),
            z=0.2,
            enabled=False,
        )

        self.hud_text = Text(
            parent=camera.ui,
            text='',
            position=(-0.86, 0.47),
            z=-0.2,
            scale=1.05,
            color=color.white,
            font='malgun.ttf',
            enabled=False,
        )

        self.timer_text = Text(
            parent=camera.ui,
            text='',
            position=(-0.86, 0.41),
            z=-0.2,
            scale=1.0,
            color=color.white,
            font='malgun.ttf',
            enabled=False,
        )

        self.status_text = Text(
            parent=camera.ui,
            text='',
            position=(-0.86, 0.35),
            z=-0.2,
            scale=0.95,
            color=color.yellow,
            font='malgun.ttf',
            enabled=False,
        )

        self.objective_panel = Entity(
            parent=camera.ui,
            model='quad',
            position=(0.16, 0.42),
            scale=(0.68, 0.12),
            color=color.rgba(0, 0, 0, 130),
            z=0.2,
            enabled=False,
        )

        self.objective_text = Text(
            parent=camera.ui,
            text='목표: 초록색 출구로 이동',
            position=(-0.12, 0.445),
            z=-0.2,
            scale=0.95,
            color=color.white,
            font='malgun.ttf',
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
            font='malgun.ttf',
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
            font='malgun.ttf',
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
            font='malgun.ttf',
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
            font='malgun.ttf',
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
            font='malgun.ttf',
            enabled=False,
        )

    def setup_floor(self):
        self.floor_timer = max(MIN_FLOOR_TIME, BASE_FLOOR_TIME - (self.floor - 1) * 2)
        self.current_anomaly = random.choice(ANOMALY_TYPES)
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

        # 뒤로 가면 현재 층 새로 시작
        if self.check_back_route():
            return

        self.level.wrap_player(self.player, self.quiz_zone.active)
        self.level.keep_player_in_corridor(self.player)
        self.chaser.update()

        if self.chaser.caught_player():
            self.player_caught()
            return

        self._refresh_hud()
        self._update_message_timer()
        self._update_objective_timer()

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
        self.show_objective('목표: 초록색 출구로 이동', 4)

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

        self.player.set_position((0, 2, -35))
        self.player.rotation_y = 0

        self.chaser.reset(self.floor)

        self._refresh_hud()

    def show_message(self, message, duration):
        self.message_text.text = message
        self.message_timer = duration

        self.message_panel.enabled = True
        self.message_text.enabled = True

    def show_objective(self, message, duration):
        self.objective_text.text = message
        self.objective_timer = duration

        self.objective_panel.enabled = True
        self.objective_text.enabled = True

    def _update_message_timer(self):
        if self.message_timer > 0:
            self.message_timer -= time.dt

            if self.message_timer <= 0:
                self.message_text.text = ''
                self.message_panel.enabled = False
                self.message_text.enabled = False

    def _update_objective_timer(self):
        if self.objective_timer > 0:
            self.objective_timer -= time.dt

            if self.objective_timer <= 0:
                self.objective_text.text = ''
                self.objective_panel.enabled = False
                self.objective_text.enabled = False

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

    def check_back_route(self):
        if self.quiz_zone.active:
            return False

        if self.player.position.x > 25 and self.player.position.z < -50:
            self.event_logs.append(f'{self.floor}층 뒤로 이동하여 재시작')

            self.reset_current_floor()
            self.show_message('뒤로 이동했습니다. 현재 층을 다시 시작합니다.', 3)
            return True

        return False

    def _hide_game_ui(self):
        self.hud_panel.enabled = False
        self.hud_text.enabled = False
        self.timer_text.enabled = False
        self.status_text.enabled = False
        self.objective_panel.enabled = False
        self.objective_text.enabled = False
        self.objective_timer = 0
        self.message_panel.enabled = False
        self.message_text.enabled = False

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
