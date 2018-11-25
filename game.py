import pygame, os
import _2048
from _2048.game import Game2048
from _2048.manager import GameManager

def run_game(game_class=Game2048, title='2048!', data_dir='save'):
  pygame.init()
  pygame.display.set_caption(title)
  pygame.display.set_icon(game_class.icon(32))
  clock = pygame.time.Clock()

  os.makedirs(data_dir, exist_ok=True)

  screen = pygame.display.set_mode((game_class.WIDTH, game_class.HEIGHT))
  manager = GameManager(Game2048, screen,
              os.path.join(data_dir, '2048.score'),
              os.path.join(data_dir, '2048.%d.state'))

  # game loop
  running = True
  
  while running:

    for event in pygame.event.get():
      if event.type == pygame.QUIT:
        running = False
        break

      manager.dispatch(event)
    
    manager.draw()
  # end while

  pygame.quit()
  manager.close()

run_game()