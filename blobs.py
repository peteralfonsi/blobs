import Tkinter
import random
import math

blobs = []
foods = []
disease_regions = []

COLOR_RED = "#ef0000" #maybe make outlines a lighter version to make them look blobbier?
COLOR_BLUE = "#0000ef"
COLOR_YELLOW = "#efef00"

COLOR_ORANGE = "#ffa500"
COLOR_GREEN = "#00ef00"
COLOR_PURPLE = "#ef00ef"

COLOR_DEAD = "#eeddaa"

COLOR_FOOD = "#805500"
RADIUS_FOOD = 3
FOOD_LOCATING_RAD = 30

MIN_SIZE_TO_SPLIT = 20 #maybe won't include?
CHANCE_SPLIT = 0.01

MAX_AGE = 10000
STARVE_TIME = 1000

BLOB_DENSITY = 0.05 #will probably be set to ~0.5
FOOD_DENSITY = 0.5

SCREEN_SIZE = 800

CURRENT_DIR_STDEV = 0.1 # standard deviation for change in angle of current each frame (mean is 0)
CURRENT_STRENGTH_STDEV = 0.2 # standard deviation for change in strength of current each frame (mean is 0)
#going to remove the significant shifts as the other part has it covered
#C_DIR_TIMER_MEAN = 500 #on average, how often will there be a significant shift in current direction
#C_DIR_TIMER_STDEV = 100 # standard deviation for how often there will be a significant shift in current

CURRENT_CORRECTION_STDEV = 0.3 #stdev for how much each (inanimate) object will deviate from the calculated value for motion given by the current and its size 
MV_CURR_POWER = 1.5 #speed from current is proportional to size^x - i thought 2 would make sense at first but it would actually be less due to drag

DECAY_TIME = 400 #avg time for dead blob to decay
DECAY_STDEV = 100

MOVE_LENGTH_AVG = 50 #about how long between bursts of motion?
MOVE_LENGTH_CORR = 20 #not an stdev but you know
MV_DIR_STDEV = 0.2 # standard deviation for change in angle of random motion each frame
MV_SPD_MEAN = 1 # mean speed of blob's random motion each frame
MV_SPD_STDEV = 0.2 # standard deviation for speed of blob's random motion each frame

DISEASE_DEATH_CHANCE = 50 #1/50 chance of death
DISEASE_LOC_RADIUS_MULT = 3 #how much bigger than blob.size is the radius of disease left behind by decay?
DISEASE_LOC_SPREAD_CHANCE = 40 #1/40 chance that the disease location spreads
COLOR_DISEASE = "#881579"
DISEASE_FOOD_CHANCE = 100

current = [(0.5-random.random())*5, (0.5-random.random())*5]


class Food: #unfinished: deletion
	def __init__(self, x, y):
		self.x = x
		self.y = y
		self.x_speed = 0
		self.y_speed = 0
		self.eaten = False
		self.size = 2
		self.density = FOOD_DENSITY
		if random.randint(0,DISEASE_FOOD_CHANCE) == 1:
			self.diseased = True
		else:
			self.diseased = False
	#def get_eaten(self):
		#???
	def update(self):
		move_current(self, current)
		vel_to_pos(self)

	def draw(self, canvas):
		canvas.create_oval(self.x-(self.size/2), self.y-(self.size/2), self.x + self.size/2, self.y + self.size/2,
                           fill=COLOR_FOOD, outline=COLOR_FOOD)

class Disease_Region: #unfinished: color change
	def __init__(self, x, y, size):
		self.x = x
		self.y = y
		self.size = size
		self.potency = 1 #if a blob enters, what's the chance it gets infected?
		self.color = COLOR_DISEASE #should lighten as potency drops

	def spread(self):
		if random.randint(0, DISEASE_LOC_SPREAD_CHANCE) == 1:
			self.potency *= self.size**2 / ((self.size+1)**2)
			self.size += 1
	def update(self):
		move_current(self, current)
		spread()
		vel_to_pos(self)
		for blob in blobs:
			if ((blob.x-self.x)**2 + (blob.y-self.y)**2)**(1/2) <= self.size and random.random() < self.potency:
				blob.diseased = True
	def draw(self, canvas):
		canvas.create_oval(self.x-(self.size/2), self.y-(self.size/2), self.x + self.size/2, self.y + self.size/2,
                           fill=self.color, outline=self.color) #apparently tkinter doesn't support rgba values... transparency may be hard

class Blob: # unfinished: food finding, eating, splitting, and purposeful motion
	def __init__(self, x, y, diseased, color, size):
		self.x = x
		self.y = y
		self.x_speed = (0.5-random.random())*0.5
		self.y_speed = (0.5-random.random())*0.5
		if size == "random": #size is diameter, not radius
			self.size = random.randint(3,6) #will shrink later
		else: 
			self.size = size
		self.age = 0
		#self.num = num #index of this blob in game_objects, required to make sure a blob isn't compared to itself? there's probably a better way
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
		self.density = BLOB_DENSITY
		self.exists = True

	def find_food(self):
		if foods[self.finding_food].eaten == True:
			self.finding_food = -1
		#else:
		
	def move_independent(self):
		i=0
		for food in foods: 
			if ((food.x-self.x)**2 + (food.y-self.y)**2)**(1/2) <= FOOD_LOCATING_RAD:
				self.finding_food = i
				self.find_food()
			i += 1
			# how do i say "if none of the foods are in radius, set self.finding_food = -1"?
		#else:
		self.move_period += 1
		#if self.move_period > MOVE_LENGTH_AVG + random.randint(-MOVE_LENGTH_CORR, MOVE_LENGTH_CORR):

	def collide(self): #something is horribly horribly wrong with this
		for other in blobs: 
			if other != self and other.exists == True and self.exists == True and is_touching(self, other, 0) == True: #this sometimes causes blobs to get stuck in a jittery loop on contact
				'''self.x_speed = -self.x_speed
				self.y_speed = -self.y_speed
				other.x_speed = -other.x_speed
				other.y_speed= -other.y_speed'''
					
				if (other.color == COLOR_BLUE and self.color == COLOR_RED) or (other.color == COLOR_RED and self.color == COLOR_BLUE):
					self.color = COLOR_PURPLE
					other.color = COLOR_PURPLE
				elif (other.color == COLOR_RED and self.color == COLOR_YELLOW) or (other.color == COLOR_YELLOW and self.color == COLOR_RED):
					self.color = COLOR_ORANGE
					other.color = COLOR_ORANGE
				elif (other.color == COLOR_BLUE and self.color == COLOR_YELLOW) or (other.color == COLOR_YELLOW and self.color == COLOR_BLUE):
					self.color = COLOR_GREEN
					other.color = COLOR_GREEN
				if self.diseased == True and other.diseased == False: 
					other.diseased = True
	def die(self):
		self.dead = True
		self.color = COLOR_DEAD

	def check_deaths(self):
		self.age += 1
		self.food_timer+= 1
		if self.age>MAX_AGE or self.food_timer>STARVE_TIME or (self.diseased == True and random.randint(0,DISEASE_DEATH_CHANCE) == 1):
			self.die()

	def check_split(self):
		if self.size>=MIN_SIZE_TO_SPLIT and random.random()<CHANCE_SPLIT*(size-MIN_SIZE_TO_SPLIT):
			self.size /= 2**(1/2)
			blobs.append(Blob(self.x+random.randint(5,10), self.y+random.randint(5,10), self.diseased, self.color, self.size))

	def update_live(self):
		self.check_deaths()
		self.move_independent()

	def update_dead(self):
		self.decay_timer+=1
		if self.decay_timer > DECAY_TIME + random.gauss(0, DECAY_STDEV): #decay
			if self.diseased == True: 
				disease_regions.append(Disease_Region(self.x, self.y, self.size*DISEASE_LOC_RADIUS_MULT))
				for i in range(0,2):
					blobs.append(Blob(self.x+(-1)**i*5), self.y, True, self.color, "random")
			for i in range(0, self.size/2):
				foods.append(Food(self.x + random.randint(-10, 10), self.y + random.randint(-10, 10))) #decays into food
				self.exists = False
			#blobs[self.num] = 0 #will this work? i don't want to change the indices of other objects so this may be the best way

	def update(self):
		if self.dead == False:
			self.update_live()
		elif self.exists == True:
			self.update_dead()
		move_current(self, current)
		self.collide()
		vel_to_pos(self)

	def draw(self, canvas):
		canvas.create_oval(self.x-(self.size/2), self.y-(self.size/2), self.x + self.size/2, self.y + self.size/2,
                           fill=self.color, outline=self.color)
		#canvas.create_line(300, 300, 300+5*self.x_speed, 300+5*self.y_speed, fill="#000000") #velocity visualizer

def change_current(): #clicking DOES NOT CHANGE the actual current -- it seems to change how blobs (and not foods) respond to it?
# oh my god clicking isn't even the cause of it
# it appears that the length mod 2 of the list blobs determines it
# if it's odd, the blobs move in the direction of the current and if it's even they move in the exact opposite direction
# as blobs are deleted, the direction shifts without clicking
# BUT WAIT
# those blobs don't cease to exist
# their "exists" field is just set to false so they aren't executing any functions
# so the direction is somehow determined by how many blobs actually execute the method update/draw/whatever???
# AAAAAAAAAAAAAAAAaAAA

	#global c_dir_timer
	#print(c_dir_timer)
	theta = math.atan2(current[1], current[0]) #turns out atan2 takes y then x
	rad = (current[0]**2 + current[1]**2)**(1/2)
	theta += random.gauss(0, CURRENT_DIR_STDEV)
	#if c_dir_timer >= random.gauss(C_DIR_TIMER_MEAN, C_DIR_TIMER_STDEV): # every so often, shift the average current significantly
	#	theta += random.random()*6.28
	#	c_dir_timer = 0
	rad += random.gauss(0, CURRENT_STRENGTH_STDEV)
	#c_dir_timer += 1
	current[0] = math.cos(theta)*rad
	current[1] = math.sin(theta)*rad


def move_current(object, current):
	object.x_speed += current[0]/(object.density*object.size**MV_CURR_POWER) + random.gauss(0, CURRENT_CORRECTION_STDEV)
	object.y_speed += current[1]/(object.density*object.size**MV_CURR_POWER) + random.gauss(0, CURRENT_CORRECTION_STDEV)
	if object.x>=SCREEN_SIZE: #wraps around
		object.x = 1
	if object.x <= 0: 
		object.x = SCREEN_SIZE - 1
	if object.y>=SCREEN_SIZE: 
		object.y = 1
	if object.y <= 0:
		object.y = SCREEN_SIZE - 1

def vel_to_pos(object):
	object.x += object.x_speed
	object.y += object.y_speed
	object.x_speed = 0
	object.y_speed = 0

def is_touching(object1, object2, pm_radius): #pm_radius is an adjustment to how close the centers of the objects need to be to each other. if it's -1, is_touching will return True if the centers are within object1.size + object2.size - 1 of each other
	if math.sqrt(pow(object1.x-object2.x, 2) + pow(object1.y-object2.y, 2)) <= 0.5*(object1.size + object2.size) + pm_radius:
		return True
	else:
		return False

def addBlob(event):
	global blobs
	blobs.append(Blob(event.x, event.y, False, "random", "random"))
	print("ADDED")

def draw(canvas):
	canvas.delete(Tkinter.ALL)
	global blobs # i wrote this bc it was in circles.py but why isn't it just assumed that blobs is global?
	global foods
	global disease_regions
	change_current()
	for disease_region in disease_regions:
		disease_region.update()
		disesase_region.draw(canvas)
	for food in foods:
		food.update()
		food.draw(canvas)
	for blob in blobs:
		if blob.exists == True: #lmao @ efficiency
			#print(blob.diseased) #blob.diseased prints correctly so blob is indeed in class Blob
			blob.update()
			blob.draw(canvas)
	print(current)
	#these lines show a visualization of the current
	canvas.create_oval(300 + current[0]*10 - 2, 300 + current[1]*10 - 2, 300+ current[0]*10 + 2, 300 + current[1]*10 + 2, fill="#000000", outline="#ff0000")
	canvas.create_line(300, 100, 300, 500)
	canvas.create_line(100, 300, 500, 300)
	delay = 33 # milliseconds	
	canvas.after(delay, draw, canvas) # call this draw function with the canvas argument again after the delay

if __name__ == "__main__":
	root = Tkinter.Tk()
	canvas = Tkinter.Canvas(root, width=SCREEN_SIZE, height=SCREEN_SIZE)
	canvas.pack()

	root.bind('<Button-1>', addBlob) #for some reason, clicking triggers a shift in current direction??
	draw(canvas)
	root.mainloop()
