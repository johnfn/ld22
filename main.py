import sys, pygame
pygame.init()

WIDTH = HEIGHT = 500
uid = 0

screen = pygame.display.set_mode((WIDTH, HEIGHT))

def get_uid():
  get_uid.uid += 1
  return uid
get_uid.uid = 0

class Entity(object):
  def __init__(self, x, y, size):
    self.x = x
    self.y = y
    self.size = size
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
  def __init__(self, x, y, size):
    super(Ball, self).__init__(x, y, size)
    self.img = pygame.image.load("ball.jpg")
    self.rect = self.img.get_rect()
  
  def groups(self):
    return ["renderable", "updateable"]
 
  def render(self, screen):
    self.rect.x = self.x
    self.rect.y = self.y
    screen.blit(self.img, self.rect)
  
  def update(self, entities):
    self.x += 1

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
  ball = Ball(100, 100, 25)
  manager.add(ball)
  while True:
    for event in pygame.event.get():
      if event.type == pygame.QUIT:
        sys.exit()
    
    for e in manager.get("updateable"):
      e.update(manager)

    screen.fill((0, 0, 0))

    for e in manager.get("renderable"):
      e.render(screen)
     
    pygame.display.flip()
    

main()
    

