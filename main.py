import os, pygame, time, random, math
from copy import deepcopy
from pprint import pprint
import numpy as np
import _2048
from _2048.game import Game2048
from _2048.manager import GameManager

# define events
EVENTS = [
  pygame.event.Event(pygame.KEYDOWN, {'key': pygame.K_UP}),   # UP
  pygame.event.Event(pygame.KEYDOWN, {'key': pygame.K_RIGHT}), # RIGHT
  pygame.event.Event(pygame.KEYDOWN, {'key': pygame.K_DOWN}), # DOWN
  pygame.event.Event(pygame.KEYDOWN, {'key': pygame.K_LEFT}) # LEFT
]

CELLS = [
  [(r, c) for c in range(4) for r in range(4)], # UP
  [(r, c) for r in range(4) for c in range(4 - 1, -1, -1)], # RIGHT
  [(r, c) for c in range(4) for r in range(4 - 1, -1, -1)], # DOWN
  [(r, c) for r in range(4) for c in range(4)], # LEFT
]

GET_DELTAS = [
  lambda r, c: ((i, c) for i in range(r + 1, 4)), # UP
  lambda r, c: ((r, i) for i in range(c - 1, -1, -1)), # RIGHT
  lambda r, c: ((i, c) for i in range(r - 1, -1, -1)), # DOWN
  lambda r, c: ((r, i) for i in range(c + 1, 4)) # LEFT
]

def free_cells(grid):
  return [(x, y) for x in range(4) for y in range(4) if not grid[y][x]]

def move(grid, action):
  moved, sum = 0, 0
  for row, column in CELLS[action]:
    for dr, dc in GET_DELTAS[action](row, column):
      # If the current tile is blank, but the candidate has value:
      if not grid[row][column] and grid[dr][dc]:
        # Move the candidate to the current tile.
        grid[row][column], grid[dr][dc] = grid[dr][dc], 0
        moved += 1
      if grid[dr][dc]:
        # If the candidate can merge with the current tile:
        if grid[row][column] == grid[dr][dc]:
          grid[row][column] *= 2
          grid[dr][dc] = 0
          sum += grid[row][column]
          moved += 1
        # When hitting a tile we stop trying.
        break
  return grid, moved, sum

def evaluation(grid, n_empty):
  grid = np.array(grid)

  score = 0

  # grid sum
  big_t = np.sum(np.power(grid, 2))

  # smoothness
  smoothness = 0
  s_grid = np.sqrt(grid)

  smoothness -= np.sum(np.abs(s_grid[:, 0] - s_grid[:, 1]))
  smoothness -= np.sum(np.abs(s_grid[:, 1] - s_grid[:, 2]))
  smoothness -= np.sum(np.abs(s_grid[:, 2] - s_grid[:, 3]))
  smoothness -= np.sum(np.abs(s_grid[0, :] - s_grid[1, :]))
  smoothness -= np.sum(np.abs(s_grid[1, :] - s_grid[2, :]))
  smoothness -= np.sum(np.abs(s_grid[2, :] - s_grid[3, :]))

  # monotonicity
  monotonic_up = 0
  monotonic_down = 0
  monotonic_left = 0
  monotonic_right = 0

  for x in range(4):
    current = 0
    next = current + 1
    while next < 4:
      while next < 3 and not grid[next, x]:
        next += 1
      current_cell = grid[current, x]
      current_value = math.log(current_cell, 2) if current_cell else 0
      next_cell = grid[next, x]
      next_value = math.log(next_cell, 2) if next_cell else 0
      if current_value > next_value:
        monotonic_up += (next_value - current_value)
      elif next_value > current_value:
        monotonic_down += (current_value - next_value)
      current = next
      next += 1

  for y in range(4):
    current = 0
    next = current + 1
    while next < 4:
      while next < 3 and not grid[y, next]:
        next += 1
      current_cell = grid[y, current]
      current_value = math.log(current_cell, 2) if current_cell else 0
      next_cell = grid[y, next]
      next_value = math.log(next_cell, 2) if next_cell else 0
      if current_value > next_value:
        monotonic_left += (next_value - current_value)
      elif next_value > current_value:
        monotonic_right += (current_value - next_value)
      current = next
      next += 1

  monotonic = max(monotonic_up, monotonic_down) + max(monotonic_left, monotonic_right)
  
  # weight for each score
  empty_w = 100000
  smoothness_w = 3
  monotonic_w = 10000

  empty_u = n_empty * empty_w
  smooth_u = smoothness ** smoothness_w
  monotonic_u = monotonic * monotonic_w

  score += big_t
  score += empty_u
  score += smooth_u
  score += monotonic_u

  return score

def maximize(grid, depth=0):
  best_score = -np.inf
  best_action = None

  for action in range(4):
    moved_grid = deepcopy(grid)
    moved_grid, moved, _ = move(moved_grid, action=action)

    if not moved:
      continue

    new_score = add_new_tiles(moved_grid, depth+1)
    if new_score >= best_score:
      best_score = new_score
      best_action = action

  return best_action, best_score

def add_new_tiles(grid, depth=0):
  fcs = free_cells(grid)
  n_empty = len(fcs)

  # early stopping
  if n_empty >= 6 and depth >= 3:
    return evaluation(grid, n_empty)

  if n_empty >= 0 and depth >= 5:
    return evaluation(grid, n_empty)

  if n_empty == 0:
    _, new_score = maximize(grid, depth+1)
    return new_score

  sum_score = 0

  for x, y in fcs:
    for v in [2, 4]:
      new_grid = deepcopy(grid)
      new_grid[y][x] = v

      _, new_score = maximize(new_grid, depth+1)

      if v == 2:
        new_score *= (0.9 / n_empty)
      else:
        new_score *= (0.1 / n_empty)

      sum_score += new_score

  return sum_score

def run_game(game_class=Game2048, title='2048!', data_dir='save'):
  pygame.init()
  pygame.display.set_caption(title)
  pygame.display.set_icon(game_class.icon(32))
  clock = pygame.time.Clock()

  os.makedirs(data_dir, exist_ok=True)

  screen = pygame.display.set_mode((game_class.WIDTH, game_class.HEIGHT))
  # screen = pygame.display.set_mode((50, 20))
  manager = GameManager(Game2048, screen,
              os.path.join(data_dir, '2048.score'),
              os.path.join(data_dir, '2048.%d.state'))

  # faster animation
  manager.game.ANIMATION_FRAMES = 1
  manager.game.WIN_TILE = 999999

  # game loop
  tick = 0
  running = True
  
  while running:
    clock.tick(120)
    tick += 1

    if tick % 5 == 0:
      old_grid = deepcopy(manager.game.grid)

      best_action, best_score = maximize(old_grid)

      if best_action is None:
        print('No way! Maximum number is %s' % np.max(manager.game.grid))
        break

      print(best_action)
      e = EVENTS[best_action]
      manager.dispatch(e)
      pprint(manager.game.grid, width=30)
      print(manager.game.score)

    for event in pygame.event.get():
      if event.type == pygame.QUIT:
        running = False
      elif event.type == pygame.MOUSEBUTTONUP:
        manager.dispatch(event)
    
    manager.draw()
  # end while

  pygame.quit()
  manager.close()

run_game()