import builtins
from pathlib import Path

from panda3d.core import AntialiasAttrib, loadPrcFileData
from ursina import Ursina, application, mouse, window

from game import GameManager

loadPrcFileData('', 'framebuffer-multisample 1')
loadPrcFileData('', 'multisamples 4')
loadPrcFileData('', 'render-mode forward')

app = Ursina()

window.fps_counter.enabled = False
window.entity_counter.enabled = False
window.collider_counter.enabled = False

mouse.visible = False
application.fonts_folder = Path('C:/Windows/Fonts')
builtins.render.setAntialias(AntialiasAttrib.MAuto)

game = GameManager()


def update():
    game.update()


def input(key):
    game.handle_input(key)


if __name__ == '__main__':
    app.run()
