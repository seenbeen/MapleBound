"""
Game classes of maplebound by weiyi and shiyang
"""

from pygame import *
from math import *
from random import *
from npc_chat import *
from glob import *

grav = 0.05
UI = image.load("ui/UI.png")

#this is the class for mouse. It controls everythign that goes on
#with displaying the mouse on the screen.
class MOUSE():
    def __init__(self):
        self.x = 0
        self.y = 0
        self.on = image.load("ui/pressed.png").convert_alpha()
        self.off = image.load("ui/normal.png").convert_alpha()
    def display(self,mx,my,mb):
        if mb[0]:
            screen.blit(self.on,(mx,my))
        else:
            screen.blit(self.off,(mx,my))

#Function gets everything within a type in map scripts
#Note: Map scripts are set up with tags.
#open up a map file and you'll notice a few things that include portals
#initial spawn mobs and spawn points,etc.
def retrieve(data,A):
    return data[data.index(A)+1:data.index(A,data.index(A)+1)]

#this function gets all damage images (numbers that display when damage is done)
class dmg_img():
    def __init__(self):
        #opens up a script. Since images are set up with offsets
        #We've used a notepad file to pull data from
        info = [each.strip().split()[-1] for each in open("ui/damage/data.txt").readlines()]

        #arbitrary frame counter
        self.frame = 0

        #Extracting animation images
        while info:
            ani_name = info.pop(0)
            #Probably not the best way, but it worked C:
            temp = []
            ani_data = info[:info.index("/#!")]
            #gets image, x y offsets, and delay in a package, then stows in a list
            #named as the value of ani_name
            for package in zip(ani_data[::4],ani_data[1:][::4],ani_data[2:][::4],ani_data[3:][::4]):
                package = list(package)
                package[3] = image.load("ui/damage/%s/%s"%(ani_name,package[3])).convert_alpha()
                temp.append(package)
                exec("self.%s=temp"%ani_name)
                for i in range(4):
                    del(info[0])
            del(info[0])

#this is a class that handles a single damage number
#it takes in a picture location and an offset for origin
#and displays a number taht floats upwards for a few miliseconds then
#disappears
class dmg_num():
    def __init__(self,pic,location,lox,loy): #lox and loy being its own origin in its own space
        self.x,self.y = location
        self.image = pic.copy()
        self.frames = 15 #float up for 15 frames
        self.ox,self.oy = 0,0
        self.x+= int(lox)
        self.y+= int(loy)
        #how fast you animate
        self.clock = time.Clock()
        self.last_time = 0 #current time
    def animate(self,MAP): #Pretty much animates the number. If enough time has
        if self.last_time <= 0: #passed, then move the number up a bit
            if self.frames != 0: 
                self.y -= 2
                self.image.set_alpha(self.frames)
                self.frames-=1
                self.last_time = 50
            else: #if they've hit the frame limit, remove it from the map
                MAP.countdmgs[0]= MAP.countdmgs[0][:-1]
                if not MAP.countdmgs[0]:
                    del(MAP.countdmgs[0])
                del(MAP.dmgs[MAP.dmgs.index(self)])
        else:
            self.last_time-=self.clock.tick()
            
    def display(self): #displays the number with offsets
        screen.blit(self.image,(self.x-self.ox,self.y-self.oy))

    def offset(self,x,y):
        self.ox,self.oy = x,y


#this class separately handles damage being done to the player
#because we dont' want numbers overlapping too much, we've used a
#counter that tells us how many numbers are currently being displayed on the
#screen. However the monster numbers shouldn't affect player damage
class sdmg_num(): #dmg for self and mobs are different
    def __init__(self,pic,location,lox,loy): #lox and loy being its own origin in its own space
        self.x,self.y = location
        self.image = pic.copy()
        self.frames = 15
        self.ox,self.oy = 0,0
        self.x+= int(lox)
        self.y+= int(loy)
        #how fast you animate
        self.clock = time.Clock()
        self.last_time = 0 #current time
    def animate(self,MAP): #again, pretty much the exact same as the mob dmg
        if self.last_time <= 0: #cept this time, we don't care about y offsets
            if self.frames != 0: #since there is a time limit between when
                self.y -= 2      #the player can get hit.
                self.image.set_alpha(self.frames)
                self.frames-=1
                self.last_time = 50
            else:
                del(MAP.sdmgs[MAP.sdmgs.index(self)])
        else:
            self.last_time-=self.clock.tick()
            
    def display(self): #displays with offsets
        screen.blit(self.image,(self.x-self.ox,self.y-self.oy))

    def offset(self,x,y):
        self.ox,self.oy = x,y 



#this class handles all portals on the map
class portal():
    def __init__(self,ID,locate,Type):
        #Extract info on portal object (txt file located in portals)
        info = open("portals/%s.txt"%ID).read().strip().split("-")
        
        animating = [each.strip().split()[1] for each in open("portals/%s/data.txt"%Type).readlines()]

        self.frame = 0
        self.clock = time.Clock()
        self.last_time = 10000 #arbitrarily big number so that first frame comes immedietely
        #gets image, x y offsets, and delay in a package, then stows in a list
        self.frameset = []

        #Extract frames from portal animate
        for package in zip(animating[::4],animating[1:][::4],animating[2:][::4],animating[3:][::4]):
            package = list(package)
            package[3] = image.load("portals/%s/%s"%(Type,package[3])).convert_alpha()
            self.frameset.append(package)
        
        self.to_map = info[0] #Where this portal takes you
        self.map_port = int(info[1]) #which portal on the map that this portal takes you
        self.lox,self.loy = locate #original x,y without offsets
        self.x,self.y = self.lox,self.loy #this would be the x and y that will be offsetted
        
        #Set rect for collision (entry of portal)
        self.rect = Rect(self.x-30/2,self.y-10,30,15)
        #ox and oy for map offset since camera's in player point of view
        self.ox,self.oy = 0,0

        #arbitrary first image of frameset for an image
        self.image = self.frameset[0][3] 

    #the warp method. The map activates this method when a player is detected
    #to have pressed up while in the space of a portal rect
    def warp(self): 
        return (self.to_map,self.map_port)
    
    def animate(self): #portals have their own animations too
        passed = self.clock.tick() #for this animation, once the portal has hit
        frame_inf = self.frameset[self.frame] #the end of its animate frames
        if self.last_time > int(frame_inf[2]): #instead of being destroyed,
            len_frame = len(self.frameset) #it starts back from the beginning
            if self.frame+1 < len_frame:    #of the frames
                self.image = frame_inf[3]
                self.frame+=1
            else:
                self.frame = 0
                self.image = frame_inf[3]
            
            self.x = self.lox +(int(frame_inf[0])) #offset the portal in accordance
            self.y = self.loy +(int(frame_inf[1])) #to the image's origin

            portw = self.image.get_width()
            porth = self.image.get_height()    
            self.last_time = 0
            
        else:
            self.last_time += passed
            
    def display(self): #display in camera space
        screen.blit(self.image,(self.x-self.ox,self.y-self.oy))
    def offset(self,x,y):
        self.ox,self.oy = x,y

#This class handles all of the npcs that are to be displayed on the map
#it takes in an npc name and location and creates an instance of the npc
#at the location
class npc():
    def __init__(self,npc_name,location):
        self.name = npc_name

        info = [each.strip().split()[-1] for each in open("npc/%s/data.txt"%npc_name).readlines()]
        self.animating = "a"
        self.clock = time.Clock()
        self.last_time = 10000 #arbitrarily big number so that first frame comes immedietely
        self.info = []
        #arbitrary frame counter
        self.frame = 0

        #Extracting animation images
        while info:
            ani_name = info.pop(0)
            self.info.append(ani_name) #this adds a frameset. We've separated our framesets with a
                                        # /#! sign in the txt file of the npc
            #Probably not the best way, but it worked C:
            exec("self.%s=[]"%ani_name)
            temp = []
            ani_data = info[:info.index("/#!")]
            #gets image, x y offsets, and delay in a package, then stows in a list
            #named as the value of ani_name
            for package in zip(ani_data[::4],ani_data[1:][::4],ani_data[2:][::4],ani_data[3:][::4]):
                package = list(package)
                package[3] = image.load("npc/%s/%s/%s"%(self.name,ani_name,package[3])).convert_alpha()
                temp.append(package)
                exec("self.%s=temp"%ani_name)
                for i in range(4):
                    del(info[0])
            del(info[0])

        #change origin offsets and image properties
        self.image = self.a[0][3]
        npcw = self.image.get_width()
        npch = self.image.get_height()

        self.lox = location[0]
        self.loy = location[1]

        self.x,self.y = self.lox,self.loy
        #because npc frames may not exactly the same width as the previous frame
        #we have to change the rectangle to be safe
        self.rect = Rect(self.x,self.y,npcw,npch)

        #offset x and y for camera
        self.ox,self.oy = 0,0

    #animates the npc if the time per frame has passed.
    #If a frameset has been completed, it chooses a random frameset to animate
    def animate(self):
        passed = self.clock.tick()
        frame_inf = eval("self.%s[%s]"%(self.animating,self.frame))
        if self.last_time > int(frame_inf[2]):
            exec("len_frame=len(self.%s)"%self.animating)
            if self.frame+1 < len_frame:
                self.image = frame_inf[3]
                self.frame+=1
            else:
                self.frame = 0
                self.animating = choice(self.info) #pick random frameset
                self.image = frame_inf[3]
            self.x = self.lox +(int(frame_inf[0]))
            self.y = self.loy +(int(frame_inf[1]))

            npcw = self.image.get_width()
            npch = self.image.get_height()    
            self.rect = Rect(self.x-self.ox,self.y-self.oy,npcw,npch)
            self.last_time = 0
            
        else:
            self.last_time += passed
                
    
    def chat(self,PLAYER):
        npc_convo(self.name,(0,0,255),"Calibri",14,PLAYER)
    
    def display(self):
        screen.blit(self.image,(self.x-self.ox,self.y-self.oy))
    def offset(self,x,y):
        self.ox,self.oy = x,y

#this class handles all the mobs to be spawned on the map
class mob():
    #it takes in a mob_name and location and creates an instance of the
    #mob at the location variable ->(x,y)
    def __init__(self,mob_name,location):
        self.mob_name = mob_name
        self.x,self.y = location
        #direction handles whether it's facing left or right
        self.direction = False
        self.last_decision = "STAND" #start out at stand decision (since mobs have ai)
        mob_data = open("mob/%s/data.txt"%mob_name).readlines()
        mob_info = [each.strip() for each in open("mob/%s/info.txt"%mob_name).readlines()]
        
        #Load up properties of mob contained by mob data
        self.hp = int(mob_info[0])
        self.pattack = int(mob_info[1])
        self.id = map(int,mob_info[2].split())
        
        self.aggravated = False
        self.aggra_time = 0 #used to time for mobs
        self.aggra_timer = time.Clock()
        
        #When you die, you maek a naise sound lolol
        self.sound_die = mixer.Sound("mob/%s/die.ogg"%mob_name)
        self.sound_die.set_volume(0.1)
        
        #get hit? make sound pl0x
        self.sound_hit = mixer.Sound("mob/%s/damage.ogg"%mob_name)
        self.sound_hit.set_volume(0.35)
        
        #can this mob jump? (also, can he walk off of a ledge?)
        self.can_jump = int(mob_data[0].strip())

        self.freeze_clock = time.Clock()
        self.freeze_time = 0

        
        #load in sprites
        info = [each.strip().split()[-1] for each in mob_data[1:]]
        #general clock used for animations
        self.clock = time.Clock()
        self.last_time = 10000 #arbitrarily big number so that first frame comes immedietely
        self.info = []
        #arbitrary frame counter
        self.frame = 0
        
        
        self.vy = 0
        self.ox,self.oy = 0,0 #an offset for displaying the character on map (depending on camera)
        self.state = "stand" #state for animating (action wise)
        self.last_state = "stand"

        #Extracting animation images
        while info:
            ani_name = info.pop(0)
            self.info.append(ani_name)
            #Probably not the best way, but it worked C:
            exec("self.%s=[]"%ani_name)
            temp = []
            ani_data = info[:info.index("/#!")]
            #gets image, x y offsets, and delay in a package, then stows in a list
            #named as the value of ani_name
            for package in zip(ani_data[::4],ani_data[1:][::4],ani_data[2:][::4],ani_data[3:][::4]):
                package = list(package)
                package[3] = image.load("mob/%s/%s/%s"%(mob_name,ani_name,package[3])).convert_alpha()
                temp.append(package)
                exec("self.%s=temp"%ani_name)
                for i in range(4):
                    del(info[0])
            del(info[0])

        self.image = self.jump[0][3]
        self.lox,self.loy = self.x+int(self.jump[0][0]),self.y+int(self.jump[0][1])
        m_imgw = self.image.get_width()
        m_imgh = self.image.get_height()
        self.rect = Rect(self.lox-self.ox,self.loy-self.oy,m_imgw,m_imgh)
        
    def move_right(self,MAP): #this method moves the mob right
        self.direction = True
        if self.state == "stand":    
            self.state = "move"
            
        if self.x+1 > MAP.walk.get_width()-125: return


        #explanation of next chunk of code as well as for move left
        """We can assume that the land they're walking on isn't flat
            because of this, we have to make them check for whether the next
            pixel block is too high for them to reach or not, and if not,
            move them onto the next pixel block"""
        if self.state != "jump" and MAP.walk.get_at((self.x+1,self.y))[3] == 0:
            for j in range(5):
                if MAP.walk.get_at((self.x+1,self.y+j))[3] != 0:
                    self.y +=j
                    if self.can_jump:
                        self.x +=1
                    return     

        go = True
        side = 0
        
        high = 0
        for j in range(1,6): #Power of crawl
            if MAP.walk.get_at((self.x+1,self.y-j))[3] != 0:
                if j==5:
                    go = False
                    break
                if go:
                    high = -j
        if go:
            self.y+=high
            self.x+=1


        
    def move_left(self,MAP): #this method moves the mob instance left. 
        self.direction = False #note explanation in move_right
        if self.state == "stand":
            self.state = "move"
            
        if self.x-125 < 0: return

        if self.state != "jump" and MAP.walk.get_at((self.x-1,self.y))[3] == 0:
            for j in range(5):
                if MAP.walk.get_at((self.x-1,self.y+j))[3] != 0:
                    self.y +=j
                    if self.can_jump:
                        self.x -=1
                    return
                
        go = True
        side = 0
        
        high = 0
        for j in range(1,6): #Power of crawl
            if MAP.walk.get_at((self.x-1,self.y-j))[3] != 0:
                if j==5:
                    go = False
                    break
                if go:
                    high = -j
        if go:
            self.y+=high
            self.x-=1

    #this method makes the mob instance perform a jump if they're touching the ground
    def perform_jump(self,MAP): 
        if self.state == "stand" or MAP.walk.get_at((self.x,self.y+5))[3] == 255:
            self.vy = -2.3
            
    #this method animates the mob according to their state
    def animate(self):
        if self.freeze_time <= 0:
            if self.state != self.last_state:
                self.frame = 0
                #force a state animation by setting last_time delay to an
                #arbitrarily high number
                self.last_time = 10000
                self.last_state = self.state
                
            passed = self.clock.tick()
            
            frame_inf = eval("self.%s[%s]"%(self.state,self.frame))
            if self.last_time > int(frame_inf[2]): #takes the frames of the state
                exec("len_frame=len(self.%s)"%(self.state))
                if self.frame+1 < len_frame: #and if their time per frame is up
                    self.image = frame_inf[3] #changes the sprite frame
                    self.frame+=1
                else:
                    self.frame = 0
                    self.image = frame_inf[3] 
                self.last_time = 0
                
            else:
                self.last_time += passed
            self.lox = self.x +(int(frame_inf[0])) #again reset frame image origins
            self.loy = self.y +(int(frame_inf[1]))
            m_imgw = self.image.get_width()
            m_imgh = self.image.get_height()
            self.rect = Rect(self.lox,self.loy,m_imgw,m_imgh)


        else:
            frame_inf = eval("self.%s[%s]"%(self.state,self.frame))
            self.image = frame_inf[3]
            self.freeze_time -= self.freeze_clock.tick()
            self.lox = self.x +(int(frame_inf[0]))
            self.loy = self.y +(int(frame_inf[1]))
            m_imgw = self.image.get_width()
            m_imgh = self.image.get_height()
            self.rect = Rect(self.lox,self.loy,m_imgw,m_imgh)
            #print "frozen",self.state

    #this method handles the gravity that affects the mob.
    def gravity(self,MAP):
        #same here
        newy = int(float(self.y+self.vy))
        #if they're in the air (colour is transparent)
        if MAP.walk.get_at((self.x,newy))[3] == 0 or self.vy < 0:
                self.y = int(self.y+self.vy)
                self.vy += grav
                if self.freeze_time <= 0:
                    self.state = "jump"
                
        else:
            #so in other words, according to their fall velocity,
            #they've hit the "ground". But because the loop cuts
            #before they actually hit the ground, a "to-ground" check is needed
            while MAP.walk.get_at((self.x,self.y))[3] == 0:
                self.y += 1
            
            #One more case check. Are they "stuck" between two blocks?
            if MAP.walk.get_at((self.x,self.y-1))[3] == 0:
                self.vy = 0
                if self.freeze_time <= 0:
                    if not self.aggravated:
                        self.state = "stand"
                
                #it's okay to climb a rope again
                #so set rl_time to greater than 500 (time delay)
                self.rl_time = 501
            else:
                while MAP.walk.get_at((self.x,self.y))[3] != 0:
                    self.y -= 1

    def mob_live(self,MAP): #AI for mob, chases you when angry
        if self.aggravated:
            if self.aggra_time <= 0:
                self.aggravated = False
            else:
                self.aggra_time -= self.aggra_timer.tick()
            if choice([0 for i in range(15)]+[1 for i in range(30)]):
                if self.freeze_time <= 0: #if they're not stunned, chase player
                    if MAP.player.x < self.x and abs(MAP.player.x-self.x) > 10: #mobs follow you
                        self.move_left(MAP)
                    elif MAP.player.x > self.x and abs(MAP.player.x-self.x) > 10:
                        self.move_right(MAP)
                    if MAP.player.y < self.y and self.y-MAP.player.y >45:
                        if self.can_jump:
                            self.perform_jump(MAP)
                        else:
                            self.state = "jump"
                    else:
                        if self.state != "jump":
                            self.state = "move"

            else:
                self.state = "move"
        else:            
            if self.freeze_time <= 0: #otherwise, they just go about randomly
                chance = randint(1,100)
                if randint(1,100) == chance:
                    decisions = ["GL" for i in range(1000)]+["GR" for i in range(1000)]+["STAND" for i in range(1000)]
                    self.last_decision = choice(decisions)
                    jump_chances = [1 for i in range(10) if self.can_jump]+[0 for i in range(100)]
                    do_jump = choice(jump_chances)
                    if do_jump:
                        self.perform_jump(MAP)
                if self.last_decision == "GL":#go left
                    self.move_left(MAP)
                elif self.last_decision == "GR": #go right
                    self.move_right(MAP)
        if self.freeze_time > 0:
            self.state = "hit"
    def display(self): #this method displays the mob in camera space
        #draw.rect(screen,(0,255,255),self.rect) #test self rectangle
        screen.blit(transform.flip(self.image,self.direction,False),(self.lox-self.ox,self.loy-self.oy))

    def offset(self,x,y):
        self.ox,self.oy = x,y

#this class handles the player in the game
class player():        
    def __init__(self,loadfile):
        load_file = [each.strip() for each in open("players/%s.txt"%loadfile,"r").readlines()]
        #load in player properties
        #note: could probably add to this in the future because of it's flexibility
        self.name = load_file[0]
        self.x = int(load_file[1])
        self.y = int(load_file[2])
        self.hp = int(load_file[3])
        self.pattack = int(load_file[4])
        self.quests = [map(int,each.split()) for each in load_file[5].split("$")]
        self.death = False
        self.win = False #have you won the game? Lol.
        self.direction = False
        #load sound
        self.sound_jump = mixer.Sound("sound/player/jump.ogg")
        self.sound_jump.set_volume(0.1)
        
        #this is to make sure they don't glitch with jump sound by jump, climb, jump, climb-ing
        self.rl_clock = time.Clock() #rope ladder clock ^^^^^


        #load in sprites
        info = [each.strip().split()[-1] for each in open("players/sprites/data.txt").readlines()]
        #general clock used for animations
        self.clock = time.Clock()
        self.last_time = 10000 #arbitrarily big number so that first frame comes immedietely
        self.info = []
        #arbitrary frame counter
        self.frame = 0

        
        self.vy = 0 
        self.ox,self.oy = 0,0 #an offset for displaying the character on map (depending on camera)
        self.state = "stand" #state for animating (action wise)
        self.last_state = "stand"
        self.angle = 0
        self.angle_clock = time.Clock()
        self.ang_shift_time = 10000 #arbitrary long time so angle can be changed right away
        #hit timer so that he's not hit 24/7 at once (or the speed of the computer, whichever comes first)
        self.hit_time = 0
        self.hit_timer = time.Clock()
        
        #Extracting animation images
        while info:
            ani_name = info.pop(0)
            self.info.append(ani_name)
            #Probably not the best way, but it worked C:
            exec("self.%s=[]"%ani_name)
            temp = []
            ani_data = info[:info.index("/#!")]
            #gets image, x y offsets, and delay in a package, then stows in a list
            #named as the value of ani_name
            for package in zip(ani_data[::4],ani_data[1:][::4],ani_data[2:][::4],ani_data[3:][::4]):
                package = list(package)
                package[3] = image.load("players/sprites/%s/%s"%(ani_name,package[3])).convert_alpha()
                temp.append(package)
                exec("self.%s=temp"%ani_name)
                for i in range(4):
                    del(info[0])
            del(info[0])

        self.image = self.stand_p[0][3]
        self.lox,self.loy = self.x,self.y

    #this method shifts the angle up
    def angle_up(self):
        a_time = self.angle_clock.tick()
        #note: the maximum angle up is -30
        if self.ang_shift_time + a_time > 10 and self.angle >= -30:
            if self.angle >= -30:
                self.angle -= 1
                self.ang_shift_time = 0
        else:
            self.ang_shift_time += a_time

    #this method shifts the angle down
    def angle_down(self):
        a_time = self.angle_clock.tick()
        #Note: the max angle down is 35
        if self.ang_shift_time + a_time > 10 and self.angle <= 35:
            if self.angle <= 35:
                self.angle += 1
            self.ang_shift_time = 0
        else:
            self.ang_shift_time += a_time    


    #other note: for angle shifting above, there is an angle shift time
    #so that it's still controllable by the player and not by how fast
    #the computer is

    #this method handles the player moving right
    def move_right(self,MAP):
        if self.state == "rope" or self.state == "ladder": return
        #Why didn't I put the above and below returns together with an or?
        #ropes and ladders only have one direction, so a change of direction would be pointless
        self.direction = True
        if self.state in ["firing%i"%i for i in range(3)]: return
        if self.state == "stand":    
            self.state = "walk"
        if self.x+1 > MAP.walk.get_width()-125: return

        #if you're curious about this part, refer to the mob class's move explanation
        if self.state != "jump" and MAP.walk.get_at((self.x+1,self.y))[3] == 0:
            for j in range(5):
                if MAP.walk.get_at((self.x+1,self.y+j))[3] != 0:
                    self.y +=j
                    self.x +=1
                    return     

        go = True
        
        high = 0
        for j in range(1,6): #Power of crawl
            if MAP.walk.get_at((self.x+1,self.y-j))[3] != 0:
                if j==5:
                    go = False
                    break
                if go:
                    high = -j
        if go:
            self.y+=high
            self.x+=1


    #this method handles the player moving left        
    def move_left(self,MAP):
        if self.state == "rope" or self.state == "ladder": return
        self.direction = False
        if self.state in ["firing%i"%i for i in range(3)]: return
        if self.state == "stand":
            self.state = "walk"
        if self.x-125 < 0: return

        if self.state != "jump" and MAP.walk.get_at((self.x-1,self.y))[3] == 0:
            for j in range(5):
                if MAP.walk.get_at((self.x-1,self.y+j))[3] != 0:
                    self.y +=j
                    self.x -=1
                    return
                
        go = True
        
        #if you're curious about this part, refer to the mob class's move explanation
        high = 0
        for j in range(1,6): #Power of crawl
            if MAP.walk.get_at((self.x-1,self.y-j))[3] != 0:
                if j==5:
                    go = False
                    break
                if go:
                    high = -j
        if go:
            self.y+=high
            self.x-=1

    #this method handles the player jumping
    #it takes in KL and KR (key left and right)
    #to allow the player to jump off of a rope or ladder while hanging
    def jump(self,KL,KR,MAP):
        if self.state == "stand" and MAP.walk.get_at((self.x,self.y+5))[3] == 255:
            self.sound_jump.play()
            self.vy = -2.3
        elif self.state == "ladder" or self.state == "rope":
            if KL or KR:
                self.sound_jump.play()
                #Note: the player has less energy when jumping off while hanging
                self.vy = -2.0
                self.state = "jump"
                self.rl_clock.tick()

    #This method gets the coordinates of the center of a rope on a rope map
    #this way, the climbing seems uniform. C:

    #this method gets the climbing coordinates
    #and centers the character on the rope or ladder when they start climbing
    def get_clcords(self,MAP,colour):
        left_offset = 0
        right_offset = 0
        while MAP.climb.get_at((self.x+left_offset,self.y))[:3] == colour:
            left_offset-=1
        while MAP.climb.get_at((self.x+right_offset,self.y))[:3] == colour:
            right_offset+=1
        
        return (left_offset+self.x*2+right_offset)/2 #formula for midpoint of line

    #this method checks for whether the player is standing in a climb-able
    #place on the map, according to the climb map, which contains climbable
    #areas in red and cyan
    def check_climb(self,MAP):
        if self.state != "rope" and self.state != "ladder":
            #since the animation for rope and ladder is different,
            #we use red for ladder and cyan for rope
            is_rope = MAP.climb.get_at((self.x,self.y))[:3] == (0,255,255)
            is_ladder = MAP.climb.get_at((self.x,self.y))[:3] == (255,0,0)
            if is_rope or is_ladder:
                last_rl_time =  self.rl_clock.tick() > 500
            if is_rope and last_rl_time:
                self.state = "rope"
                self.direction = False
                self.x = self.get_clcords(MAP,(0,255,255))
                self.animate()
            elif is_ladder and last_rl_time:
                self.state = "ladder"
                self.direction = False
                self.x = self.get_clcords(MAP,(255,0,0))
                self.animate()
        else:
            #check for whether going up will still be in the rope or ladder zone
            if MAP.climb.get_at((self.x,self.y-1))[:3] == (0,255,255) or\
               MAP.climb.get_at((self.x,self.y-1))[:3] == (255,0,0):
                self.y-=1
            else: #otherwise, fall (jump mode)
                self.y-=1
                self.state = "jump"
            self.animate()

    #This method is for when the down arrow key is pressed
    #it checks for the event of climbing or prone (player laying on ground)
    def prone_climb(self,MAP):
        #Again, gotta make sure you aren't climbing
        if self.state == "stand" or self.state == "walk":
            is_rope = MAP.climb.get_at((self.x,self.y+1))[:3] == (0,255,255)
            is_ladder = MAP.climb.get_at((self.x,self.y+1))[:3] == (255,0,0)
            if is_rope:
                self.y +=1
                self.state = "rope"
                self.direction = False
                self.x = self.get_clcords(MAP,(0,255,255))
                self.animate()
            elif is_ladder:
                self.y +=1
                self.state = "ladder"
                self.direction = False
                self.x = self.get_clcords(MAP,(255,0,0))
                self.animate()
            else:
                if self.direction: #which way are you facing? (origin offsets are different
                    self.state = "prone2"
                else:
                    self.state = "prone"
                
        elif self.state == "rope" or self.state == "ladder":
            #check for whether going up will still be in the rope or ladder zone
            if MAP.climb.get_at((self.x,self.y+1))[:3] == (0,255,255) or\
               MAP.climb.get_at((self.x,self.y+1))[:3] == (255,0,0):
                self.y+=1
            else: #otherwise, fall (jump)
                self.y+=1
                self.state = "jump"
            self.animate()

    #this function animates the player according to their state and delays
    def animate(self):
        if self.state not in ["firing%i"%i for i in range(3)]:
            if self.state != self.last_state:
                self.frame = 0
                #force a state animation by setting last_time delay to an
                #arbitrarily high number
                self.last_time = 10000
                self.last_state = self.state
                
            passed = self.clock.tick()

            #refer to previous animating frame explanations above
            frame_inf = eval("self.%s[%s]"%(self.state+"_p",self.frame))
            if self.last_time > int(frame_inf[2]):
                exec("len_frame=len(self.%s)"%(self.state+"_p"))
                if self.frame+1 < len_frame:
                    self.image = frame_inf[3]
                    self.frame+=1
                else:
                    self.frame = 0
                    self.image = frame_inf[3]
                self.last_time = 0
                
            else:
                self.last_time += passed
            self.lox = self.x +(int(frame_inf[0]))
            self.loy = self.y +(int(frame_inf[1]))
            
            #climbing is an exception to gravity (and as a result any other frame)
            if self.state != "ladder" and self.state != "rope":
                self.state = "stand"
        else:
            frame_inf = eval("self.%s[%s]"%(self.state+"_p","1"))
            frame_inf2 = eval("self.%s[%s]"%(self.state+"_p","0"))
            self.image = frame_inf[3].copy()
            arm_image = transform.rotate(frame_inf2[3],self.angle)
            a_imgw = arm_image.get_width()
            a_imgh = arm_image.get_height()            
            self.image.blit(arm_image,(38-a_imgw/2,50-a_imgh/2))
            self.lox = self.x +(int(frame_inf[0]))
            self.loy = self.y +(int(frame_inf[1]))
    def gravity(self,MAP):
        #same here
        if self.state != "ladder" and self.state != "rope":
            newy = int(float(self.y+self.vy))
            #if they're in the air (colour is transparent)
            if MAP.walk.get_at((self.x,newy))[3] == 0 or self.vy < 0:
                    self.y = int(self.y+self.vy)
                    self.vy += grav
                    #if self.state not in ["firing%i"%i for i in range(3)]:
                    self.state = "jump"
                    
            else:
                #so in other words, according to their fall velocity,
                #they've hit the "ground". But because the loop cuts
                #before they actually hit the ground, a "to-ground" check is needed
                while MAP.walk.get_at((self.x,self.y))[3] == 0:
                    self.y += 1
                
                #One more case check. Are they "stuck" between two blocks?
                if MAP.walk.get_at((self.x,self.y-1))[3] == 0:
                    self.vy = 0
                    self.state = "stand"
                    
                    #it's okay to climb a rope again
                    #so set rl_time to greater than 500 (time delay)
                    self.rl_time = 501
                else:
                    while MAP.walk.get_at((self.x,self.y))[3] != 0:
                        self.y -= 1
                
        
    def display(self): #display in camera space
        screen.blit(transform.flip(self.image,self.direction,False),(self.lox-self.ox,self.loy-self.oy))
    def offset(self,x,y):
        self.ox,self.oy = x,y

#this is the camera of the game. it handles offseting the map and all ther
#components into the player space and as a result, it's own space.
class camera():
    def __init__(self,camx,camy):
        self.x = camx
        self.y = camy

    def to_player(self,MAP,PLAYER):
        
        width = MAP.platform.get_width()
        height = MAP.platform.get_height()


        #Note: The camera clips at coords (0,0) and not the center of the screen
        #in which case would be (400,300). Take note that this means
        #if the player is too far up the map, we set cam to 0 and not 300
        if PLAYER.x <= width-495 and PLAYER.x >= 495:
            self.x = PLAYER.x
        else:
            if PLAYER.x > width-495:
                self.x = width-495
            if PLAYER.x < 495:
                self.x = 495
        
        if PLAYER.y <= height-300 and PLAYER.y >= 300:
            self.y = PLAYER.y-300
        else:
            if PLAYER.y > height-300:
                self.y = height-600
            if PLAYER.y < 300:
                self.y = 0

        MAP.offset(self.x-400,self.y)

#this handles all the spawn points
#spawn points are organized by time per spawn and type of spawn
#it takes in a mob type and a location as well as a time per spawn
#and generates mobs according to those
class spawn_point():
    def __init__(self,mob_name,location,time_per_spawn):
        self.mob_name = mob_name
        self.time_per_spawn = time_per_spawn
        self.location = location
        self.last_time = 100000
        self.clock = time.Clock()
    def animate(self,MAP):
        time = self.clock.tick()
        if self.last_time+time > self.time_per_spawn:
            if len(MAP.mobs) < MAP.mobcount:
                #there is one more condition; the map needs to have room for the
                #mob to spawn to prevent lagg
                MAP.mobs.append(mob(self.mob_name,self.location))
                MAP.offset(MAP.ox,MAP.oy)
            self.last_time = 0
                
        else:
            self.last_time+=time
        
#this is the game map class. It takes every other component of
#the game and neatly packages it into something handl-able by the main loop
class game_map():
    #note: if there's an old_bg, the program will compare sound tracks and
    #decide whether a new soundtrack is needed
    def __init__(self,map_name,load,old_bg,from_player):
        self.map_id = map_name
        #initialize player, whether it be from a dif map, or a load file
        if from_player:
            self.player = from_player
        else:
            self.player = player(load)
        
        map_file = [each.strip() for each in open("map/%s/map.txt"%map_name).readlines()]

        #load in all other components of the game
        bg_name = retrieve(map_file,"/#bg")[0]
        npc_data = retrieve(map_file,"/#npc")
        portal_data = retrieve(map_file,"/#portal")
        mob_data = retrieve(map_file,"/#mob")
        spawn_points = retrieve(map_file,"/#spawnpoint")
        bg_music = retrieve(map_file,"/#sound")

        #these are the separate images used as a map. Our player
        #and mobs move using colour code by map. alpha of 0 being no block
        self.walk = image.load("map/%s/platform.png"%map_name).convert_alpha()
        self.back = image.load("map/bg/%s.png"%bg_name).convert_alpha()
        self.platform = image.load("map/%s/nature.png"%map_name).convert_alpha()
        self.climb = image.load("map/%s/climb.png"%map_name).convert_alpha()

        #Okay, so apparently if they spam the up key, you can portal zoom. Yeah. No
        #Let's make a time limit to portal entries.
        self.warp_clock = time.Clock()
        self.last_portal_time = 0

        #generate npcs
        self.npcs = []
        for each in npc_data:
            info = each.split("$")
            self.npcs.append(npc(info[0],map(int,info[1].split(","))))

        #load up portals
        self.portals = []
        for each in portal_data:
            info = each.split("$")
            self.portals.append(portal(info[0],map(int,info[1].split(",")),info[2]))

        #reator reacts if player has completed a certain quest
        reactor = [each.strip().split() for each in open("map/%s/reactor.txt"%map_name).readlines()][0]
        if reactor[-1] != "none":
            r_id = int(reactor[0])
            if self.player.quests[r_id][0] == 2:
                info = reactor[-1].split("$")
                self.portals.append(portal(info[0],map(int,info[1].split(",")),info[2]))

        #load up music
        self.bgm = old_bg
        if self.bgm != bg_music[0]:
            #suppose they're on the same map. The music doens't change.
            mixer.music.load("sound/bgm/%s.ogg"%bg_music[0])
            mixer.music.play(-1)
            mixer.music.set_volume(0.02)
            self.bgm = bg_music[0]

        self.hit_sound = mixer.Sound("sound/player/hit1.ogg")
        self.hit_sound.set_volume(0.1)
        
        #generate mobs
        self.mobs = []
        for each in mob_data:
            info = each.split("$")
            self.mobs.append(mob(info[0],map(int,info[1].split(","))))

        self.spawn_points = []
        for each in spawn_points:
            info = each.split("$")
            self.spawn_points.append(spawn_point(info[0],map(int,info[1].split(",")),int(info[2])))

        #mobcount per map pl0x (for spawner)
        self.mobcount = len(self.mobs)
        
        #initialize mouse
        self.mouse = MOUSE()

        self.shots = []

        #initialize damage images
        self.dmg_img = dmg_img()

        self.dmgs = []

        self.countdmgs = [] #this is used to determine number offsets on the y axis when drawing

        self.sdmgs = [] #your own dmg counter
        
        self.effects = [] #one time only animating for effects such as mob death

        screen.blit(UI,(0,0))
        
    def set_player(self,x,y): #this function moves the player to a certain location (for portals)
        self.player.x,self.player.y = (x,y)

    #this method sets the portal of "portalid" on the map
    def set_portal(self,portalid):
        self.set_player(self.portals[portalid].x,self.portals[portalid].y-1)

    #if the player's mouse button comes down, it checks for whether
    #there was a collision with an npc and if so, activates the npc's script
    def check_npc(self,mx,my):
        for each in self.npcs:
            if each.rect.collidepoint(mx,my):
                if each.image.get_at((mx-each.x+each.ox,my-each.y+each.oy))[3] != 0:
                    each.chat(self.player)

    #this method checks for whether the player's trying to enter a portal
    #or not, and if so, changes the map
    def check_portal(self,x,y,CAM,mx,my,mb):
        for each in self.portals:
            if each.rect.collidepoint(x,y):
                last = self.warp_clock.tick()
                #there is a time limit per portal so that they can't same poral entering
                if  last+self.last_portal_time >= 1000:
                    #plays the portal sound
                    go_portal = mixer.Sound("portals/portal.ogg")
                    go_portal.set_volume(0.1)
                    go_portal.play()
                    to_map,portid = each.warp()
                    #transitional surface for fade effects
                    transition = Surface((800,600))
                    back = screen.copy()
                    #insert epic fade effects C:
                    for i in range(0,255,2):
                        transition.set_alpha(i)
                        screen.blit(back,(0,0))
                        screen.blit(transition,(0,0))
                        display.flip()

                    #re-initialize the map to where the portal leads
                    self.__init__(to_map,self.player.name,self.bgm,self.player)
                    self.set_portal(portid)
                    #reset the camera to the player
                    CAM.to_player(self,self.player)
                    self.offset(self.ox,self.oy)
                    self.animate()
                    self.display()

                    self.mouse.display(mx,my,mb)
                    
                    back = screen.copy()
                    #fade back in to display the new map
                    for i in range(255,0,-2):
                        transition.set_alpha(i)
                        screen.blit(back,(0,0))
                        screen.blit(transition,(0,0))
                        display.flip()

                else:
                    self.last_portal_time+=last
    
    #this method checks if the player is touching a mob. If they are, then they get hurt
    def check_mob(self):
        for each in self.mobs:
            px,py = self.player.x,self.player.y-10
            #Note: lox and loy are the original location of the player
            #(without the offsets made by the image)
            
            #Note: I add ox and oy back in order to move back to world space where i can check the colours around the npc
            if each.rect.collidepoint(px,py):
                if each.image.get_at((px-each.lox,py-each.loy))[3] != 0:
                    if self.player.hp - each.pattack <= 0:
                        self.player.death = True
                    else:
                        if self.player.hit_time < 0:
                            self.player.hp -= each.pattack
                            self.player.hit_time = 1000
                            pattk = each.pattack
                            num = str(randint(int(pattk*0.9),int(pattk*1.1)))
                            for each,i in zip(num,range(len(num))):
                                number = self.dmg_img.violet[int(each)]
                                self.sdmgs.append(sdmg_num(number[3],(self.player.x-len(num)/2*26+i*26,self.player.y-randint(35,45)),number[0],number[1]))
                        else:
                            self.player.hit_time-=self.player.hit_timer.tick()

    #this method fires a shot into the map. shots can only
    #be fired if the player isn't hanging on a rope or ladder
    def fire_shot(self,power,TYPE):
        if self.player.state != "rope" and self.player.state != "ladder":
            otherdirection = 1
            left_right = -1 #used as a multiplier to determine shot direction
            if self.player.direction:
                otherdirection = 0
                left_right = 1
            ang = radians(self.player.angle)
            vx = cos(radians(self.player.angle+180*otherdirection))*power
            vy = sin(ang)*power
            if TYPE == 1: #... there was a thought at one time to utilize skills.
                #too bad time ran out. This area was designed to allow for multiple shot types
                #If there's time in the future, it may be added. For now, shot 2 ftw
                self.shots.append(shot("1",self.player.x,self.player.y-30,vx,vy))
            if TYPE == 2:
                for i in range(4):
                    self.shots.append(shot("1",self.player.x+i*int(20*cos(ang))*left_right,self.player.y-i*int(2*sin(ang))-30,vx,vy*i/3.0))
    #this method checks for whether any shots are colliding with
    #either a solid part on the the map or a mob
    def check_shot(self):
        for each_mob in self.mobs:
            for each_shot in self.shots:
                sx,sy = map(int,(each_shot.hx,each_shot.hy))
                if each_mob.rect.collidepoint(sx,sy):
                    if each_mob.image.get_at((sx-each_mob.lox,sy-each_mob.loy))[3] != 0:
                        if each_shot.vx < 0:
                            for i in range(1,31):
                                if self.walk.get_at((each_mob.x-i,each_mob.y-10))[3] != 0 or each_mob.x -i < 95:
                                    break
                            each_mob.x += -i+1
                            each_mob.direction = True
                        else:
                            for i in range(1,31):
                                if self.walk.get_at((each_mob.x+i,each_mob.y-10))[3] != 0 or each_mob.x +i > self.walk.get_width()-120:
                                    break
                            each_mob.x += i-1
                            each_mob.direction = False
                        each_mob.frame = 0
                        pattk = self.player.pattack
                        crit = choice([1 for i in range(3)]+[0 for i in range(7)])
                        effect = self.dmg_img.crit[-1]
                        #add the damage number to the map
                        self.dmgs.append(dmg_num(effect[3],(each_mob.x,each_mob.y-randint(5,10)-len(self.countdmgs)*5),effect[0],effect[1]))
                        self.countdmgs+= "D" #add a d offset to the number animating since we added shot effect
                        if crit: #handles critical damage since pictures are different
                            num = str(randint(int(pattk*1.1),int(pattk*1.25)))
                            for each,i in zip(num,range(len(num))):
                                number = self.dmg_img.crit[int(each)]
                                self.dmgs.append(dmg_num(number[3],(each_mob.x-len(num)/2*26+i*26,each_mob.y-randint(15,20)-len(self.countdmgs)*5),number[0],number[1]))                            
                        else:
                            num = str(randint(int(pattk*0.9),int(pattk*1.1)))
                            for each,i in zip(num,range(len(num))):
                                number = self.dmg_img.red[int(each)]
                                self.dmgs.append(dmg_num(number[3],(each_mob.x-len(num)/2*26+i*26,each_mob.y-randint(15,20)-len(self.countdmgs)*5),number[0],number[1]))

                        self.countdmgs+=num
                        each_mob.aggravated = True #aggravate mob for 15 seconds
                        each_mob.aggra_time = 15000
                        
                        each_mob.state = "hit"
                        each_mob.freeze_time = 500
                        each_mob.freeze_clock.tick()
                        each_mob.sound_hit.play()
                        
                        if each_mob.hp - self.player.pattack <= 0:
                            each_mob.sound_die.play()
                            self.effects.append(effects(each_mob.die,each_mob.x,each_mob.y))
                            try:
                                self.player.quests[each_mob.id[0]][each_mob.id[1]+1]+=1
                            except:
                                pass
                            if each_mob.mob_name == "arkarium":
                                self.player.win = True
                            del(self.mobs[self.mobs.index(each_mob)])
                            break
                        else:
                            each_mob.hp -= self.player.pattack

                        del (self.shots[self.shots.index(each_shot)])

    #this method offsets all components of the map
    def offset(self,x,y):
        self.ox,self.oy = x,y
        for each in self.npcs+self.portals+[self.player]+self.mobs+self.shots+self.dmgs+self.sdmgs+self.effects:
            each.offset(x,y)
            
    #this method animates all components of the map
    def animate(self):
        for each in self.spawn_points+self.shots+self.dmgs+self.sdmgs+self.effects:
            each.animate(self)
        for each in self.mobs:
            each.gravity(self)
            each.mob_live(self)
        for each in self.npcs+self.portals+self.mobs:
            each.animate()
        #rope animates on its own according to user input
        if self.player.state != "ladder" and self.player.state != "rope":
            self.player.animate()
        self.player.gravity(self)

    #display all components of the map
    def display(self):
        screen.set_clip(Rect(0,0,800,554))
        screen.blit(self.back,(0,0))
        screen.blit(self.platform,(-self.ox,-self.oy))
        for each in self.npcs+self.mobs+[self.player]+self.shots+self.effects+self.dmgs+self.sdmgs+self.portals:
            each.display()
        screen.set_clip(None)

#this class is for effects that only play once, such as a mob's death      
class effects():
    def __init__(self,obj_frameset,X,Y):
        self.frames = obj_frameset
        self.frame = 0
        self.frame_time = 0
        self.frame_clock = time.Clock()
        self.image = self.frames[0][3]
        self.ox,self.oy = 0,0
        self.lox,self.loy = X,Y #original location without imaging offsets
        self.x,self.y = X+int(self.frames[0][0]),Y+int(self.frames[0][1])
    def animate(self,MAP):
        current_time = self.frame_clock.tick()#current time passed since calling this method
        if self.frame_time+current_time >= int(self.frames[self.frame][2]):
            if self.frame+1 < len(self.frames):
                self.image = self.frames[self.frame][3]
                self.lox = self.lox+int(self.frames[self.frame][0])
                self.lox = self.lox+int(self.frames[self.frame][1])
                self.frame_time = 0
                self.frame += 1
            else: #if they're frames are up, remove them
                del(MAP.effects[MAP.effects.index(self)])
        else:
            self.frame_time += current_time

    def offset(self,x,y): #refer to offsets and display explanation of other classes
        self.ox,self.oy = x,y
    def display(self):
        screen.blit(self.image,(self.x-self.ox,self.y-self.oy))

#this handles the shots on the map
class shot():
    def __init__(self,Type,x,y,vx,vy):  #initialize a shot and x y with direction vx and vy
        self.image = image.load("shots/%s.png"%Type).convert_alpha()
        self.x = x
        self.y = y
        self.vx = vx
        self.vy = vy
        self.ox,self.oy = 0,0
        self.hx,self.hy = 0,0
    def animate(self,MAP):
        self.vy += grav
        self.x += self.vx
        self.y += self.vy
        angle = radians(degrees(atan2(self.vx,self.vy)))
        #print degrees(angle)
        self.hx = self.x
        self.hy = self.y
        #are you out of map? if so, get rid of ya'
        sx,sy = map(int,(self.x,self.y))
        #if they're out of the map, remove them
        if self.x >= MAP.walk.get_width() or self.x <= 0 or self.y >= MAP.walk.get_height():
            del (MAP.shots[MAP.shots.index(self)])
        elif self.y > 0:
            if MAP.walk.get_at((sx,sy))[3] != 0:
                del (MAP.shots[MAP.shots.index(self)])        
            
    #this method displays the shot.
    def display(self):
        #Note: rot_pic is not a rotten picture. Rotated image pls
        rot_pic = transform.rotate(self.image,degrees(atan2(self.vx,self.vy)))
        projw = rot_pic.get_width() #proj as in projectile
        projh = rot_pic.get_height()
        nx,ny = map(int,(self.x,self.y))
        screen.blit(rot_pic,(nx-projw/2-self.ox,ny-projh/2-self.oy))
    #reoffset cam space offsets
    def offset(self,x,y):
        self.ox,self.oy = x,y
        
