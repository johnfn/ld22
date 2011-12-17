import sys, pygame, spritesheet, wordwrap

WIDTH = HEIGHT = 500
TILE_SIZE = 20

DEBUG = True

screen = pygame.display.set_mode((WIDTH, HEIGHT))

def get_uid():
  get_uid.uid += 1
  return get_uid.uid
get_uid.uid = 0

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
    if rect2.touches_point(p):
      return True
  return False

class Entity(object):
  def __init__(self, x, y, groups, src_x = -1, src_y = -1, src_file = ""):
    self.x = x
    self.y = y
    self.size = TILE_SIZE

    if src_x != -1 and src_y != -1:
      self.img = TileSheet.get(src_file, src_x, src_y)
      self.rect = self.img.get_rect()
     
    self.uid = get_uid()
    self.events = {}
    self.groups = groups

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

def isalambda(v):
  return isinstance(v, type(lambda: None)) and v.__name__ == '<lambda>'

class Entities:
  def __init__(self):
    self.entities = []
    self.entityInfo = []
  
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
  
  def any(self, *criteria):
    return len(self.get(*criteria)) > 0

  def remove_all(self, *criteria):
    retained = []

    for entity in self.entities:
      if not self.elem_matches_criteria(entity, *criteria):
        retained.append(entity)
    
    self.entities = retained

class Map(Entity):
  def __init__(self):
    super(Map, self).__init__(0, 0, ["updateable"])
    self.map_coords = [0, 0]
    self.map_width = 20
  
  def update(self, entities):
    pass

  def new_map(self, entities):
    entities.remove_all("map_element")

    self.current_map = TileSheet.get("map.bmp", *self.map_coords)
    
    for i in range(self.map_width):
      for j in range(self.map_width):
        data = self.current_map.get_at((i, j))
        if data == (255, 255, 255):
          tile = Tile(i * TILE_SIZE, j * TILE_SIZE, 0, 0)
        elif data == (0, 255, 0): #NPC
          tile = NPC(i * TILE_SIZE, j * TILE_SIZE)
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
    self.speed = 1

  def talk_to(self, who, entities):
    entities.add(Text(self, "HI THIS IS TEXT"))

class Text(Entity):
  def __init__(self, follow, contents):
    super(Text, self).__init__(follow.x, follow.y, ["renderable"])
    self.contents = contents

  def render(self, screen):
    print self.contents

class Character(Entity):
  def __init__(self, x, y):
    super(Character, self).__init__(x, y, ["renderable", "updateable"], 0, 1, "tiles.bmp")
    self.speed = 1

  def interact(self, entities):
    if UpKeys.key_down(pygame.K_x):
      self.interact_rect = Rect(self.x - self.size, self.y - self.size, self.size * 3, self.size * 3)
      npcs_near = entities.get("npc", lambda x: x.touches_rect(self))
      for npc in npcs_near:
        npc.talk_to(self, entities)

  def update(self, entities):
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

    self.interact(entities)
      
def init(manager):
  manager.add(Character(40, 40))

def main():
  manager = Entities()

  init(manager)

  m = Map()
  m.new_map(manager)

  pygame.display.init()
  pygame.font.init()

  if not DEBUG:
    pygame.mixer.init(frequency=22050, size=-16, channels=2, buffer=1024)
    pygame.mixer.music.load('ludumherp.mp3')
    pygame.mixer.music.play(-1) #Infinite loop! HAHAH!

  while True:
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

    for e in manager.get("renderable"):
      e.render(screen)
     
    pygame.display.flip()
    

main()
    

