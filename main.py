import sys, pygame, spritesheet, wordwrap

WIDTH = HEIGHT = 500
TILE_SIZE = 20
uid = 0

DEBUG = True

screen = pygame.display.set_mode((WIDTH, HEIGHT))

def get_uid():
  get_uid.uid += 1
  return uid
get_uid.uid = 0


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

class Entity(object):
  def __init__(self, x, y, src_x, src_y, src_file):
    self.x = x
    self.y = y
    self.size = TILE_SIZE

    self.img = TileSheet.get(src_file, src_x, src_y)
    self.rect = self.img.get_rect()
    self.uid = get_uid()
    self.events = {}
  
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
    raise "UnimplementedGroupsException"
  
  def render(self, screen):
    raise "UnimplementedRenderException"

  def update(self, entities):
    raise "UnimplementedUpdateException"
  

class Ball(Entity):
  def __init__(self, x, y):
    super(Ball, self).__init__(x, y, 0, 0, "tiles.bmp")
  
  def groups(self):
    return ["renderable", "updateable"]
 
  def render(self, screen):
    self.rect.x = self.x
    self.rect.y = self.y
    screen.blit(self.img, self.rect)

  def update(self, entities):
    pass

class Entities:
  def __init__(self):
    self.entities = []
    self.entityInfo = []
  
  def add(self, entity):
    self.entities.append(entity)
  
  def get(self, *criteria):
    results = []

    for entity in self.entities:
      valid_entity = True

      for criterion in criteria:
        if isinstance(criterion, basestring):
          if criterion not in entity.groups():
            valid_entity = False
            break
        else:
          raise "UnsupportedCriteriaType"
       
      if valid_entity:
        results.append(entity)
    
    return results



def main():
  manager = Entities()
  ball = Ball(100, 100)
  manager.add(ball)

  pygame.display.init()
  pygame.font.init()

  if not DEBUG:
    pygame.mixer.init(frequency=22050, size=-16, channels=2, buffer=1024)
    pygame.mixer.music.load('ludumherp.mp3')
    pygame.mixer.music.play(-1) #Infinite loop! HAHAH!

  while True:
    for event in pygame.event.get():
      if event.type == pygame.QUIT:
        pygame.quit()
        sys.exit()
    
    for e in manager.get("updateable"):
      e.update(manager)

    screen.fill((255, 255, 255))

    for e in manager.get("renderable"):
      e.render(screen)
     
    pygame.display.flip()
    

main()
    

