import Tkinter
import random
import math

blobs = []
blobs_to_update = []
foods = []
disease_regions = []

COLOR_RED = ["#ef0000", "#ff8080"] #first is base color, second is outline color
COLOR_BLUE = ["#0000ef", "#6666ff"]
COLOR_YELLOW = ["#efef00", "#ffff80"]

COLOR_ORANGE = ["#ffa500", "#ffc966"]
COLOR_GREEN = ["#00ef00", "#66ff66"]
COLOR_PURPLE = ["#bb00bb", "#ff1aff"]

COLOR_DEAD = ["#eeddaa", "#fbf7ea"]

COLOR_BACKGROUND = "#ffffff" #can't find a good background color

COLOR_FOOD = ["#805500", "#805500"]
RADIUS_FOOD = 3
FOOD_LOCATING_RAD = 30
FOOD_SPAWN_CHANCE = 10 #on average, food will spawn in 1/10 of all frames
MAX_FOOD = 200

MIN_SIZE_TO_SPLIT = 13
CHANCE_SPLIT = 0.03

MAX_AGE = 10000
STARVE_TIME = 1000

BLOB_DENSITY = 0.1
FOOD_DENSITY = 0.5

SCREEN_SIZE = 800

CURRENT_DIR_STDEV = 0.1 # standard deviation for change in angle of current each frame (mean is 0)
CURRENT_STRENGTH_STDEV = 0.2 # standard deviation for change in strength of current each frame (mean is 0)

CURRENT_CORRECTION_STDEV = 0.3 #stdev for how much each (inanimate) object will deviate from the calculated value for motion given by the current and its size
MV_CURR_POWER = 1.5 #speed from current is proportional to size^x - i thought 2 would make sense at first but it would actually be less due to drag

DECAY_TIME = 400 #avg time for dead blob to decay
DECAY_STDEV = 100

MOVE_LENGTH_AVG = 50 #about how long between bursts of motion?
MOVE_LENGTH_CORR = 25 #not an stdev but you know
MOVE_BURST_STRENGTH = 10 #strength of bursts of motion
MV_DIR_STDEV = 0.2 # standard deviation for change in angle of random motion each frame
MV_SPD_MEAN = 1 # mean speed of blob's random motion each frame
MV_SPD_STDEV = 0.2 # standard deviation for speed of blob's random motion each frame

DISEASE_DEATH_CHANCE = 300 #1/100 chance of death
DISEASE_LOC_RADIUS_MULT = 3 #how much bigger than blob.size is the radius of disease left behind by decay?
DISEASE_LOC_SPREAD_CHANCE = 40 #1/40 chance that the disease location spreads
COLOR_DISEASE = ["#666699", "#b3b3cc"]
COLOR_DISEASE_REG = ["#667399", "#a3abc2"]
DISEASE_FOOD_CHANCE = 500

current = [(0.5-random.random())*5, (0.5-random.random())*5]

class Floater:
	def __init__(self, x, y):
		self.x = x
		self.y = y
		self.x_speed = 0
		self.y_speed = 0
		self.exists = True
		self.width = 2

	def vel_to_pos(self):
		self.x += self.x_speed
		self.y += self.y_speed
		self.x_speed = 0
		self.y_speed = 0

	def move_current(self, current):
		self.x_speed += current[0]/(self.density*self.size**MV_CURR_POWER) + random.gauss(0, CURRENT_CORRECTION_STDEV)
		self.y_speed += current[1]/(self.density*self.size**MV_CURR_POWER) + random.gauss(0, CURRENT_CORRECTION_STDEV)
		if self.x>=SCREEN_SIZE: #wraps around
			self.x = 1
		if self.x <= 0:
			self.x = SCREEN_SIZE - 1
		if self.y>=SCREEN_SIZE:
			self.y = 1
		if self.y <= 0:
			self.y = SCREEN_SIZE - 1

	def update(self):
		self.move_current(current)
		self.vel_to_pos()

	def draw(self, canvas):
		canvas.create_oval(self.x-(self.size/2), self.y-(self.size/2), self.x + self.size/2, self.y + self.size/2,
                           fill=self.color[0], outline=self.color[1], width=self.width)

class Food(Floater):
	def __init__(self, x, y):
		Floater.__init__(self, x, y)
		self.size = 2
		self.density = FOOD_DENSITY
		if random.randint(0,DISEASE_FOOD_CHANCE) == 1:
			self.diseased = True
			self.color = COLOR_DISEASE
		else:
			self.diseased = False
			self.color = COLOR_FOOD

class Disease_Region(Floater): #unfinished: color change
	def __init__(self, x, y, size):
		Floater.__init__(self, x, y)
		self.size = size
		self.potency = 1 #if a blob enters, what's the chance it gets infected?
		self.color = COLOR_DISEASE_REG #should lighten as potency drops
		self.density = FOOD_DENSITY
		self.width = 5

	def spread(self):
		if random.randint(0, DISEASE_LOC_SPREAD_CHANCE) == 1:
			self.potency *= pow(self.size, 2) / pow(self.size+1, 2)
			self.size += 1
	def update(self):
		for blob in blobs:
			if blob.diseased == False and is_touching(self, blob, blob.size) == True and random.random() < self.potency:
				blob.diseased = True
				blob.color = COLOR_DISEASE
		Floater.update(self)
		self.spread()

class Blob(Floater): # unfinished: food finding, splitting
	def __init__(self, x, y, diseased, color, size):
		Floater.__init__(self, x, y)
		self.x_speed = 0 #(0.5-random.random())*0.5
		self.y_speed = 0 #(0.5-random.random())*0.5
		if size == "random": #size is diameter, not radius
			self.size = random.randint(6,10) #default (8,10)
		else:
			self.size = size
		self.age = 0
		if color == "random":
			self.color = random.choice([COLOR_RED, COLOR_BLUE, COLOR_YELLOW])
		else:
			self.color = color
		self.dead = False
		self.food_timer = 0 #time since food
		self.finding_food = -1 #-1 means not finding food, values >= 0 are the index of the food it is finding
		self.move_period = random.randint(0, 50) #every so often the blob will move itself faster, where in that cycle is it?
		self.diseased = diseased #disease spreads from food to blob and from blob to blob
		self.decay_timer = 0
		self.moving_theta = 0
		self.density = BLOB_DENSITY
		self.exists = True

	def move_independent(self):
			if self.finding_food == -1 and self.diseased == False:
				for food in foods:
					if is_touching(self, food, FOOD_LOCATING_RAD) == True:
						self.finding_food = foods.index(food)
			if self.move_period >= 0:
				self.move_period += 1

			if self.move_period > MOVE_LENGTH_AVG + random.randint(-MOVE_LENGTH_CORR, MOVE_LENGTH_CORR):

				if self.diseased == True: #attack other blobs
					for blob in blobs:
						if blob != self and is_touching(self, blob, FOOD_LOCATING_RAD):
							self.moving_theta = math.atan2(blob.y - self.y, blob.x - self.x)

				elif self.finding_food == -1:
					for blob in blobs:
						if is_touching(self, blob, FOOD_LOCATING_RAD) and opposite_color(self.color) == blob.color: #try to attack opposite color
							self.moving_theta = math.atan2(blob.y - self.y, blob.x - self.x)
						else: #if no food or enemies in range, orient randomly
							self.moving_theta = random.random()*math.pi*2
				else:

					try:
						food = foods[self.finding_food]
						theta = math.atan2(food.y - self.y, food.x - self.x)
						self.moving_theta = theta
					except IndexError:
						self.finding_food = -1
						self.moving_theta = random.random()*math.pi*2

				self.x_speed += MOVE_BURST_STRENGTH*math.cos(self.moving_theta)
				self.y_speed += MOVE_BURST_STRENGTH*math.sin(self.moving_theta)
				self.move_period = -2

			elif self.move_period == -20: #the lower this number is, the more frames the darting will last
				self.move_period = 0
			elif self.move_period < 0:
				self.x_speed += MOVE_BURST_STRENGTH*(-1.0/self.move_period)*math.cos(self.moving_theta)*1.5
				self.y_speed += MOVE_BURST_STRENGTH*(-1.0/self.move_period)*math.sin(self.moving_theta)*1.5
				self.move_period -= 1

	def collide(self):
		for other in blobs:
			if other.exists == True and self.exists == True and is_touching(self, other, 0) == True and blobs.index(other) > blobs.index(self):
				theta = math.atan2(other.y - self.y, other.x - self.x)
				other.x += 2*math.cos(theta)
				other.y += 2*math.sin(theta)
				self.x -= 2*math.cos(theta)
				self.x -= 2*math.sin(theta)
				if (other.color == COLOR_BLUE and self.color == COLOR_RED) or (other.color == COLOR_RED and self.color == COLOR_BLUE):
					self.color = COLOR_PURPLE
					other.color = COLOR_PURPLE
				elif (other.color == COLOR_RED and self.color == COLOR_YELLOW) or (other.color == COLOR_YELLOW and self.color == COLOR_RED):
					self.color = COLOR_ORANGE
					other.color = COLOR_ORANGE
				elif (other.color == COLOR_BLUE and self.color == COLOR_YELLOW) or (other.color == COLOR_YELLOW and self.color == COLOR_BLUE):
					self.color = COLOR_GREEN
					other.color = COLOR_GREEN
				elif opposite_color(self.color) == other.color:
					#opposite colors kill each other
					smaller(other, self).die() #is it possible to use smaller() to return the larger object or would i need a larger() function?
				if (self.diseased == True or other.diseased == True) and self.dead == False and other.dead == False:
					other.diseased = True
					self.diseased = True
					other.color = COLOR_DISEASE
					self.color = COLOR_DISEASE
	def eat(self):
		for food in foods:
			if is_touching(self, food, 0):
				if food.diseased == True:
					self.diseased = True
					self.color = COLOR_DISEASE
				foods.remove(food)
				self.size += 1
				self.food_timer = 0
				self.finding_food = -1

	def die(self):
		self.dead = True
		self.color = COLOR_DEAD

	def check_deaths(self):
		self.age += 1
		self.food_timer+= 1
		if self.age>MAX_AGE or self.food_timer>STARVE_TIME or (self.diseased == True and random.randint(0,DISEASE_DEATH_CHANCE) == 1):
			self.die()

	def check_split(self):
		if self.size>=MIN_SIZE_TO_SPLIT and random.random()<CHANCE_SPLIT*(self.size-MIN_SIZE_TO_SPLIT):
			self.size = self.size/(math.sqrt(2))
			blobs.append(Blob(self.x+random.randint(5,10), self.y+random.randint(5,10), self.diseased, self.color, self.size))

	def update_live(self):
		self.check_deaths()
		self.check_split()
		self.move_independent()
		self.eat()

	def update_dead(self):
		self.decay_timer+=1
		if self.decay_timer > DECAY_TIME + random.gauss(0, DECAY_STDEV): #decay
			if self.diseased == True:
				disease_regions.append(Disease_Region(self.x, self.y, self.size*DISEASE_LOC_RADIUS_MULT))
				if random.random() < 0.2:
					blobs.append(Blob(self.x+5, self.y, True, self.color, "random")) #may remove
				self.exists = False
			for i in range(0, int(round(self.size/2))):
				foods.append(Food(self.x + random.randint(-5, 5), self.y + random.randint(-5, 5))) #decays into food
				self.exists = False

	def update(self):
		if self.dead == False:
			self.update_live()
		elif self.exists == True:
			self.update_dead()
		self.collide()
		Floater.update(self)

def change_current():
	theta = math.atan2(current[1], current[0]) #calculate angle of current
	rad = (current[0]**2 + current[1]**2)**(1/2) #calculate strength of current
	theta += random.gauss(0, CURRENT_DIR_STDEV) #add a number picked from a normal distribution to theta
	rad += random.gauss(0, CURRENT_STRENGTH_STDEV) #add a number picked from a nromal distribution to rad
	current[0] = math.cos(theta)*rad #change current according to additions
	current[1] = math.sin(theta)*rad

def food_spawn():
	if random.randint(0, FOOD_SPAWN_CHANCE) == 1:
		global foods
		foods.append(Food(random.randint(0, SCREEN_SIZE), random.randint(0, SCREEN_SIZE)))

def opposite_color(color):
	if color == COLOR_RED:
		return COLOR_GREEN
	elif color == COLOR_ORANGE:
		return COLOR_BLUE
	elif color == COLOR_YELLOW:
		return COLOR_PURPLE
	elif color == COLOR_GREEN:
		return COLOR_RED
	elif color == COLOR_BLUE:
		return COLOR_ORANGE
	elif color == COLOR_PURPLE:
		return COLOR_YELLOW

def is_touching(object1, object2, pm_radius): #pm_radius is an adjustment to how close the centers of the objects need to be to each other. if it's -1, is_touching will return True if the centers are within object1.size + object2.size - 1 of each other
	if math.sqrt(pow(object1.x-object2.x, 2) + pow(object1.y-object2.y, 2)) <= 0.5*(object1.size + object2.size) + pm_radius:
		return True
	else:
		return False
def smaller(object1, object2):
	if object1.size < object2.size:
		return object1
	elif object2.size < object1.size:
		return object2
	elif object2.size == object1.size:
		return random.choice([object1, object2]) #i would prefer it return neither, but that could cause issues for lines which use this function

def addBlob(event):
	global blobs
	blobs.append(Blob(event.x, event.y, False, "random", "random"))

def draw(canvas):
	canvas.delete(Tkinter.ALL)
	global blobs # i wrote this bc it was in circles.py but why isn't it just assumed that blobs is global?
	global foods
	global disease_regions
	change_current()
	if len(foods) < MAX_FOOD:
		food_spawn()
	canvas.create_rectangle(0, 0, SCREEN_SIZE, SCREEN_SIZE, fill = COLOR_BACKGROUND, outline = COLOR_BACKGROUND)
	for disease_region in disease_regions:
		disease_region.update()
		disease_region.draw(canvas)
	for food in foods:
		food.update()
		food.draw(canvas)
	blobs_to_update = []
	for blob in blobs:
		if blob.exists == True:
			blobs_to_update.append(blob)
	for blob in blobs_to_update:
			blob.update()
			blob.draw(canvas)
	delay = 33 # milliseconds
	canvas.after(delay, draw, canvas) # call this draw function with the canvas argument again after the delay

if __name__ == "__main__":
	root = Tkinter.Tk()
	canvas = Tkinter.Canvas(root, width=SCREEN_SIZE, height=SCREEN_SIZE)
	canvas.pack()

	root.bind('<Button-1>', addBlob)
	draw(canvas)
	root.mainloop()
