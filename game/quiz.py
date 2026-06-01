import random

from ursina import Entity, Text, camera, color, mouse

from .constants import KOREAN_FONT


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

        elif self.question_type == 'python_basic':
            self.hint_text = '힌트: 파이썬의 기본 문법을 떠올려보세요.'

        self._render()
        return True

    def _make_question(self):
        # 이상현상이 있는 층이면 무조건 이상현상 관련 문제만 출제
        if self.game.current_anomaly is not None:
            return self._make_anomaly_related_question()

        # 이상현상이 없는 정상 층이면 파이썬 상식 문제 또는 일반 문제 출제
        question_types = ['math', 'python_basic', 'anomaly_yes_no']
        question_type = random.choice(question_types)

        if question_type == 'math':
            return self._make_math_question(question_type)

        if question_type == 'python_basic':
            return self._make_python_basic_question(question_type)

        return self._make_anomaly_question(question_type)

    def _make_anomaly_related_question(self):
        # 이상현상이 있는 층에서는 파이썬 문제 금지
        # 오직 이상현상 확인 문제만 출제
        return self._make_anomaly_question('anomaly_yes_no')

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

    def _make_python_basic_question(self, question_type):
        quiz_list = [
            {
                'question': '파이썬에서 출력할 때 사용하는 함수는?',
                'choices': ['print()', 'input()', 'random()'],
                'answer': 'print()',
            },
            {
                'question': '파이썬에서 값을 입력받을 때 사용하는 함수는?',
                'choices': ['input()', 'print()', 'len()'],
                'answer': 'input()',
            },
            {
                'question': '파이썬에서 문자열을 나타낼 때 사용하는 기호는?',
                'choices': ['따옴표', '대괄호', '중괄호'],
                'answer': '따옴표',
            },
            {
                'question': '파이썬에서 리스트를 만들 때 사용하는 기호는?',
                'choices': ['[]', '{}', '()'],
                'answer': '[]',
            },
            {
                'question': '파이썬에서 조건문을 만들 때 사용하는 키워드는?',
                'choices': ['if', 'for', 'def'],
                'answer': 'if',
            },
            {
                'question': '파이썬에서 반복문을 만들 때 사용할 수 있는 키워드는?',
                'choices': ['for', 'print', 'int'],
                'answer': 'for',
            },
            {
                'question': '파이썬에서 함수를 만들 때 사용하는 키워드는?',
                'choices': ['def', 'if', 'list'],
                'answer': 'def',
            },
            {
                'question': '파이썬에서 주석을 작성할 때 사용하는 기호는?',
                'choices': ['#', '@', '&'],
                'answer': '#',
            },
        ]

        selected_quiz = random.choice(quiz_list)

        question = selected_quiz['question']
        choices = selected_quiz['choices'][:]
        answer = selected_quiz['answer']

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