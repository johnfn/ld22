import sys, pygame, spritesheet, wordwrap

WIDTH = HEIGHT = 500
TILE_SIZE = 20

DEBUG = True

PRESENT = 0
FUTURE = 1

TICKS_PER_SEC = 60
TIME_IN_FUTURE = 5

screen = pygame.display.set_mode((WIDTH, HEIGHT))

def get_uid():
  get_uid.uid += 1
  return get_uid.uid
get_uid.uid = 0

class DialogData:
  @staticmethod
  def all_data():
    d_dict={ (0, 0) : [ "You're looking pretty tired there, Ben."
                      , "Before you go to sleep, can you get some apple pie from Grandma?"
                      , "Her house is really close. Just follow the path outside of the house."
                      , "Why do you look scared?"
                      ],
             (0,0,True) : [ "Ah, the pie! Thanks, Ben!"
                          , "Try a slice."
                          , "SPECIAL It tastes a little funny, but you don't say anything."
                          , "Well, time for bed. Tomorrow's another big day!"
                          , "ADVANCESTATE"
                          ],
             (1, 1) : [ "You hear a sound, far off... like a cry"], #TODO
             (1, 0) : [ "Here's an apple pie!"
                      , "GET ApplePie"
                      , "SPECIAL She hands you an apple pie."
                      , "Enjoy!"
                      ]
           }

    if not hasattr(DialogData, 'data'):
      actual = {}
      for tpl in d_dict:
        actual[tpl] = d_dict[tpl]
        actual[tpl].append("") #end of dialog

      DialogData.data = actual

    return DialogData.data

  @staticmethod
  def get_data(who, state, map_x, map_y):

    d_list = DialogData.all_data()[(map_x, map_y)]
    if map_x == 0 and map_y == 0 and who.has_apple_pie():
      d_list = DialogData.all_data()[(map_x, map_y, True)]
      
    return d_list[state % len(d_list)]

class Rect:
  def __init__(self, x, y, w, h):
    assert(w==h)
    self.x = x
    self.y = y
    self.size = w
    self.w = self.h = w

  def __str__(self):
    return "<Rect %d %d %d %d>" % (self.x, self.y, self.w, self.h)

class Point:
  def __init__(self, x, y):
    self.x = x
    self.y = y

  def __cmp__(self, other):
    return 0 if self.x == other.x and self.y == other.y else 1

  def __str__(self):
    return "<Point x : %f y : %f>" % (self.x, self.y)

class TileSheet:
  """ Memoize all the sheets so we don't load in 1 sheet like 50 times and 
  squander resources. This is a singleton, which is generally frowned upon, 
  but I think it's okay here."""
  sheets = {}

  @staticmethod
  def add(file_name):
    if file_name in TileSheet.sheets:
      return

    new_sheet = spritesheet.spritesheet(file_name)
    width, height = dimensions = new_sheet.sheet.get_size()
    TileSheet.sheets[file_name] =\
     [[new_sheet.image_at((x, y, TILE_SIZE, TILE_SIZE), colorkey=(255,255,255))\
       for y in range(0, height, TILE_SIZE)] for x in range(0, width, TILE_SIZE)]

  @staticmethod
  def get(sheet, x, y):
    if sheet not in TileSheet.sheets:
      TileSheet.add(sheet)
    return TileSheet.sheets[sheet][x][y]

def rect_touchpoint(rect, point):
    return rect.x <= point.x <= rect.x + rect.size and\
           rect.y <= point.y <= rect.y + rect.size

def rect_intersect(rect1, rect2):
  corners = [ Point(rect1.x, rect1.y)\
            , Point(rect1.x + rect1.size, rect1.y)\
            , Point(rect1.x, rect1.y + rect1.size)\
            , Point(rect1.x + rect1.size, rect1.y + rect1.size)]

  for p in corners:
    if rect_touchpoint(rect2, p):
      return True
  return False

def rect_contains(big, small):
  corners = [ Point(small.x, small.y)\
            , Point(small.x + small.size, small.y)\
            , Point(small.x, small.y + small.size)\
            , Point(small.x + small.size, small.y + small.size)]

  for p in corners:
    if not rect_touchpoint(big, p):
      return False
  return True

class Entity(object):
  def __init__(self, x, y, groups, src_x = -1, src_y = -1, src_file = ""):
    self.x = x
    self.y = y
    self.size = TILE_SIZE
    self.flicker = 0
    self.src_file = src_file

    if src_x != -1 and src_y != -1:
      self.set_img(src_x, src_y)
     
    self.uid = get_uid()
    self.events = {}
    self.groups = groups

  def set_img(self, src_x, src_y):
    self.img = TileSheet.get(self.src_file, src_x, src_y)
    self.rect = self.img.get_rect()

  def start_flicker(self, duration=30):
    self.flicker = duration

  def collides_with_wall(self, entities):
    return entities.any("wall", lambda x: x.touches_rect(self))

  def touches_point(self, point):
    return self.x <= point.x <= self.x + self.size and\
           self.y <= point.y <= self.y + self.size
  
  def touches_rect(self, other):
    if hasattr(self, 'uid') and hasattr(other, 'uid') and self.uid == other.uid: 
       return False
    return rect_intersect(self, other)

  def add_group(self, group):
    self.groups.append(group)

  # Add and remove callbacks

  def on(self, event, callback):
    if event in self.events:
      self.events[event].append(callback)
    else:
      self.events[event] = [callback]
  
  def off(self, event, callback = None):
    if callback is None:
      self.events[event] = []
    else:
      self.events[event].remove(callback)
  
  def emit(self, event):
    for callback in self.events:
      callback()
  
  # How high/low this object is
  def depth(self):
    return 0
  
  # Methods that must be implemented if you extend Entity
  def groups(self):
    return groups
  
  def render(self, screen):
    if self.flicker > 0:
      self.flicker -= 1
      if self.flicker % 4 >= 2:
        return

    self.rect.x = self.x
    self.rect.y = self.y
    screen.blit(self.img, self.rect)

  def update(self, entities):
    raise "UnimplementedUpdateException"
  

class Tile(Entity):
  def __init__(self, x, y, tx, ty):
    super(Tile, self).__init__(x, y, ["renderable", "updateable"], tx, ty, "tiles.bmp")
  
  def update(self, entities):
    pass
 
  def depth(self):
    return 0

def isalambda(v):
  return isinstance(v, type(lambda: None)) and v.__name__ == '<lambda>'

class Entities:
  def __init__(self):
    self.entities = []
    self.entityInfo = []
  
  def remove(self, some_ent):
    self.entities.remove(some_ent)

  def render_all(self, screen):
    for e in sorted(self.get("renderable"), key=lambda x: x.depth()):
      e.render(screen)

  def add(self, entity):
    self.entities.append(entity)
  
  def elem_matches_criteria(self, elem, *criteria):
    for criterion in criteria:
      if isinstance(criterion, basestring):
        if criterion not in elem.groups:
          return False
      elif isalambda(criterion):
        if not criterion(elem):
          return False
      else:
        raise "UnsupportedCriteriaType"
    
    return True
       
  
  def get(self, *criteria):
    results = []

    for entity in self.entities:
      if self.elem_matches_criteria(entity, *criteria):
        results.append(entity)
    
    return results
 
  def one(self, *criteria):
    results = self.get(*criteria)

    assert(len(results) == 1)
    return results[0]
  
  def any(self, *criteria):
    return len(self.get(*criteria)) > 0

  def remove_all(self, *criteria):
    retained = []

    for entity in self.entities:
      if not self.elem_matches_criteria(entity, *criteria):
        retained.append(entity)
    
    self.entities = retained

class Map(Entity):
  def __init__(self, startx=0, starty=0):
    super(Map, self).__init__(0, 0, ["updateable", "map"])
    self.map_coords = [startx, starty]
    self.map_width = 20
    self.abs_map_width = TILE_SIZE * self.map_width
    self.map_rect = Rect(0, 0, self.abs_map_width, self.abs_map_width)

    self.current = PRESENT
    self.map_name = "map.bmp"

  def current_state(self):
    return self.current    

  def switch(self, to_what, entities):
    if to_what == self.current: 
      return

    if to_what == FUTURE:
      self.map_name = "map2.bmp"
    else:
      self.map_name = "map.bmp"

    self.new_map(entities)
    self.current = to_what

  def contains(self, entity):
    return rect_contains(self.map_rect, entity)

  def update(self, entities):
    # Check if we are on a new map.
    char = entities.one("character")
    if self.contains(char): return

    # We are!

    new_mapx, new_mapy = self.map_coords

    if char.x + TILE_SIZE < 0: 
      new_mapx -= 1
      char.move_delta(self.abs_map_width, 0)

    if char.x > self.abs_map_width: 
      new_mapx += 1
      char.move_delta(-self.abs_map_width, 0)

    if char.y + TILE_SIZE < 0: 
      new_mapy -= 1
      char.move_delta(0, self.abs_map_width)

    if char.y > self.abs_map_width: 
      new_mapy += 1
      char.move_delta(0, -self.abs_map_width)


    self.map_coords = [new_mapx, new_mapy]
    self.new_map(entities)

  def cur_pos(self):
    return self.map_coords

  def new_map(self, entities):
    entities.remove_all("map_element")

    self.current_map = TileSheet.get(self.map_name, *self.map_coords)
    
    for i in range(self.map_width):
      for j in range(self.map_width):
        data = self.current_map.get_at((i, j))
        if data == (255, 255, 255):
          tile = Tile(i * TILE_SIZE, j * TILE_SIZE, 0, 0)
        if data == (0, 150, 0):
          tile = Tile(i * TILE_SIZE, j * TILE_SIZE, 4, 0)
        elif data == (0, 255, 0): #npc
          tile = NPC(i * TILE_SIZE, j * TILE_SIZE)
        elif data == (0, 254, 0): #grass tile
          tile = Tile(i * TILE_SIZE, j * TILE_SIZE, 3, 1)
        elif data == (0, 0, 0):
          tile = Tile(i * TILE_SIZE, j * TILE_SIZE, 1, 0)
          tile.add_group("wall")

        tile.add_group("map_element")
        entities.add(tile)

class UpKeys:
  """ Simple abstraction to check for recent key released behavior. """
  keysup = []
  keysactive = []
  
  @staticmethod
  def flush():
    UpKeys.keysup = []

  @staticmethod
  def add_key(val):
    UpKeys.keysup.append(val)
    UpKeys.keysactive.append(val)

  # This is a setter.
  @staticmethod
  def release_key(val):
    if val in UpKeys.keysactive:
      UpKeys.keysactive.remove(val)

  @staticmethod
  def key_down(val):
    return val in UpKeys.keysactive

  @staticmethod
  def key_up(val):
    if val in UpKeys.keysup:
      UpKeys.keysup.remove(val)
      return True 
    return False

class NPC(Entity):
  def __init__(self, x, y):
    super(NPC, self).__init__(x, y, ["renderable", "npc"], 1, 1, "tiles.bmp")
    self.speed = 2
    self.text_state = 0

  def talk_to(self, who, entities):
    entities.remove_all("text")
    next_text = DialogData.get_data(who, self.text_state, *entities.one("map").cur_pos())
    if "GET" in next_text:
      who.add_to_inventory(next_text.split(" ")[1])
      # stop here, dont actually show this text, but do show next one.
      self.text_state += 1
      return self.talk_to(who, entities)
    if "ADVANCESTATE" in next_text:
      GameState.current_state += 1
      return

    entities.add(Text(self, next_text))
    self.text_state += 1

class Text(Entity):
  def __init__(self, follow, contents):
    super(Text, self).__init__(follow.x, follow.y, ["renderable", "text"])
    self.contents = contents

  def render(self, screen):
    print self.contents

class TextTimeout(Text):
  def __init__(self, follow, contents, time_left):
    super(TextTimeout, self).__init__(follow, contents)
    self.time_left = time_left

  def update(self, entities):
    self.time_left -= 1
    if self.time_left == 0:
      entities.remove(self)


DOWN = 4
UP = 5
RIGHT = 6
LEFT = 7
ANIM_FRAMES = 4

class Character(Entity):
  def __init__(self, x, y):
    super(Character, self).__init__(x, y, ["renderable", "updateable", "character"], 0, 1, "tiles.bmp")
    self.speed = 4
    self.inventory = []
    self.time_left = -1
    self.safe_spot = []
    self.safe_map  = []
    self.anim_step = 0
    self.tick = 0
    self.orientation = DOWN

  def render(self, screen):
    super(Character, self).render(screen)

  def add_to_inventory(self, item):
    self.inventory.append(item)

  def has_apple_pie(self):
    return "ApplePie" in self.inventory

  def interact(self, entities):
    # Talk
    if UpKeys.key_up(pygame.K_x):
      self.interact_rect = Rect(self.x - self.size, self.y - self.size, self.size * 3, self.size * 3)
      npcs_near = entities.get("npc", lambda x: x.touches_rect(self))
      for npc in npcs_near:
        npc.talk_to(self, entities)

    if GameState.current_state >= GameState.act2:
      self.check_time_switch(entities)

  def check_time_switch(self, entities):
    m = entities.one("map")

    print m.current_state()

    up_pressed = UpKeys.key_up(pygame.K_SPACE)

    # Always allow PRESENT => FUTURE where you belong
    if up_pressed and m.current_state() == PRESENT:
      m.switch(FUTURE, entities)
      self.time_left = -1

      if self.collides_with_wall(entities): # Fail - restore to safe spot.
        self.start_flicker()
        m.switch(FUTURE, entities)
        self.move_abs(*self.safe_spot)
        self.time_left = -1
    elif up_pressed and m.current_state() == FUTURE:
      # Player initiated, can instantly fail
      m.switch(PRESENT, entities)
      self.time_left = TIME_IN_FUTURE * TICKS_PER_SEC

      if self.collides_with_wall(entities): # Fail.
        self.start_flicker()
        m.switch(FUTURE, entities)
        self.time_left = -1

    print self.time_left

    # Countdown back to past.
    self.time_left -= 1
    if self.time_left == 0:
      m.switch(FUTURE, entities)
      self.time_left = -1

      if self.collides_with_wall(entities): # Fail - restore to safe spot.
        self.start_flicker()
        m.switch(FUTURE, entities)
        self.move_abs(*self.safe_spot)
        self.time_left = -1

  def move_abs(self, x, y):
    self.x = x
    self.y = y

  def move_delta(self, dx, dy):
    self.x += dx
    self.y += dy

  def update(self, entities):
    self.tick += 1

    dx, dy = (0, 0)

    if UpKeys.key_down(pygame.K_DOWN): dy += self.speed
    if UpKeys.key_down(pygame.K_UP): dy -= self.speed
    if UpKeys.key_down(pygame.K_LEFT): dx -= self.speed
    if UpKeys.key_down(pygame.K_RIGHT): dx += self.speed

    delta = .1
    dest_x = self.x + dx
    dest_y = self.y + dy

    self.x += dx
    if self.collides_with_wall(entities):
      self.x -= dx

    self.y += dy
    if self.collides_with_wall(entities):
      self.y -= dy

    if dx > 0: self.orientation = RIGHT
    if dx < 0: self.orientation = LEFT
    if dy > 0: self.orientation = DOWN
    if dy < 0: self.orientation = UP

    if (dx != 0 or dy != 0) and self.tick % 5 == 0:
      self.anim_step += 1
      self.anim_step = self.anim_step % ANIM_FRAMES

    self.set_img(self.anim_step, self.orientation)

    self.interact(entities)

    state = entities.one("map").current_state()

    if state == FUTURE:
      self.safe_spot = [self.x, self.y]

  def depth(self):
    return 1

class GameState:
  initial = 0
  sleep_sequence = 1
  act2 = 2

  current_state = 0

  @staticmethod
  def next_state(entities):
    GameState.current_state += 1

    if GameState.current_state == GameState.act2:
      entities.one("map").switch(FUTURE, entities)

def init(manager):
  manager.add(Character(40, 40))

def sleep_sequence(entities):
  print "You sleep soundly."
  sleep_sequence.ticker += 1
  if sleep_sequence.ticker > 10000:
    GameState.next_state(entities)

sleep_sequence.ticker = 0

def main():
  manager = Entities()

  init(manager)

  if DEBUG:
    m = Map(0, 0)
    m.new_map(manager)
    manager.add(m)

    GameState.current_state = GameState.sleep_sequence
    GameState.next_state(manager)
  else:
    m = Map()
    m.new_map(manager)
    manager.add(m)

  pygame.display.init()
  pygame.font.init()

  if not DEBUG:
    pygame.mixer.init(frequency=22050, size=-16, channels=2, buffer=1024)
    pygame.mixer.music.load('ludumherp.mp3')
    pygame.mixer.music.play(-1) #Infinite loop! HAHAH!

  clock = pygame.time.Clock()
  while True:
    clock.tick(TICKS_PER_SEC)

    if GameState.current_state == GameState.sleep_sequence:
      sleep_sequence(manager)
      continue

    for event in pygame.event.get():
      UpKeys.flush()
      if event.type == pygame.QUIT:
        pygame.quit()
        sys.exit()
      if event.type == pygame.KEYDOWN:
        UpKeys.add_key(event.key)
      if event.type == pygame.KEYUP:
        UpKeys.release_key(event.key)
    
    for e in manager.get("updateable"):
      e.update(manager)

    screen.fill((255, 255, 255))

    manager.render_all(screen)
     
    pygame.display.flip()
    

main()
    

