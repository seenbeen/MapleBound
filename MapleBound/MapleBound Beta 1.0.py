#MapleBound Final by
#Shiyang Han and Weiyi Dai
import pygame._view #required for py2exe
from pygame import *
from math import *
from game_classes import *

screen = display.set_mode((800,600))#,FULLSCREEN)
display.set_caption("Maplebound Beta 1.0")
display.set_icon(image.load("icon.png"))

gaming = True
running = True

powerbar = image.load("ui/power.png").convert_alpha()

font.init()
comicFont = font.SysFont("Comic Sans MS", 14)

firing = False
fire_power = 0

fire_timer = time.Clock()#how often you can fire, coincidentally the frames for pulling an arrow back
reverting = False #this determines the amount of time required for the player to go back to normal mode
fire_time = 0

game_clock = time.Clock()

fire_type = 2

menu = image.load("menu.png")

while running: #if they wanna continue after death or after winning the game
    in_menu = True
    screen.blit(menu,(0,0))
    display.flip()
    while in_menu and running:
        for evt in event.get():
            if evt.type == QUIT:
                running = False
            if evt.type == MOUSEBUTTONDOWN:
                in_menu = False
                gaming = True

    if running: #if they didn't click exit, start game
        Map = game_map("dtot0","player",None,None) #player starts all over per quit or death
        cam = camera(0,0)
        mouse.set_visible(False)
        
    while gaming and running: #start game loop
        mx,my = mouse.get_pos()
        mb = mouse.get_pressed()
        keys = key.get_pressed()
        for evt in event.get():
            if evt.type == QUIT:
                gaming = False
                running = False
                mixer.music.stop() #any quits, music stops
                mouse.set_visible(True)
            if evt.type == MOUSEBUTTONDOWN: #if they click down, check for an npc click
                if evt.button == 1:
                    Map.check_npc(mx,my)
            if evt.type == KEYDOWN: #if they press up, enter portals
                if evt.key == K_UP:
                    Map.check_portal(Map.player.x,Map.player.y,cam,mx,my,mb)
                    break
                #if evt.key == K_ESCAPE:
                #    gaming = False
                #    mixer.music.stop()
                #    mouse.set_visible(True)
            if evt.type == KEYUP:
                if evt.key == K_LSHIFT and not reverting and Map.player.state != "rope" and Map.player.state != "ladder":
                    Map.player.state = "firing2" #if they release shift, fire shot 
                    reverting = True #at the current power level
                    #fire_timer.tick() #reset clock, b/c last time they fired coulda been forever ago
                    fire_time = 50
                    Map.fire_shot(fire_power,fire_type)
                    firing = False
                    fire_power = 0
                    
        if reverting: #this variable is the trigger that allows the player to fire again
            Map.player.state = "firing2"
            if fire_time <= 0: #there is a firing time wait so no rapid fire.
                Map.player.state = "stand"
                reverting = False
            else:
                fire_time -= 1#fire_timer.tick()
            
        if firing and fire_power < 10:
            fire_power += 0.1
        #map event functions. checks for mobs, npcs, spawnpoints, shots, etc.
        Map.check_mob()
        Map.check_shot()
        #alt= jump
        if keys[K_LALT] or keys[K_RALT]:
            Map.player.jump(keys[K_LEFT],keys[K_RIGHT],Map)

        #shift = Fire
        if keys[K_LSHIFT] and Map.player.state != "rope" and Map.player.state != "ladder" and not reverting:
            Map.player.state = "firing1"
            firing = True
            
        if keys[K_UP]:                     #get arrow keys and key inputs
            Map.player.check_climb(Map)   #up is climbing, down is laying down
        if keys[K_RIGHT]:
            Map.player.move_right(Map) #left right, moves char left and right
        elif keys[K_LEFT]:
            Map.player.move_left(Map)
        elif keys[K_DOWN]:
            Map.player.prone_climb(Map)

        if keys[K_w]: #changes angle
            Map.player.angle_up()
        elif keys[K_s]:
            Map.player.angle_down()
            
        cam.to_player(Map,Map.player)
        Map.animate() #animate's map. Refer to class file
        Map.display() #same here
        txtPic = comicFont.render(str(Map.player.hp), False, (255,255,255))
        screen.blit(txtPic,(292,558))
        #set rect to the power bar. cut off as much as we need to display.
        screen.set_clip(Rect(452,568,int(fire_power/10.0*164),23))
        screen.blit(powerbar,(452,568))
        screen.set_clip(None)
        Map.mouse.display(mx,my,mb)
        display.flip()
        screen.set_clip(Rect(mx,my,32,32)) #clip the mouse to prevent lag
        screen.blit(UI,(0,0)) #epic bashing. Cutting ui out and also mouse
        screen.set_clip(None)
        screen.set_clip(Rect(452,568,int(fire_power/10.0*164),23))
        screen.blit(UI,(0,0))
        screen.set_clip(None)
        screen.set_clip(292,558,txtPic.get_width(),txtPic.get_height())
        screen.blit(UI,(0,0))
        screen.set_clip(None)
        
        if Map.player.death or Map.player.win: #if they've died or won
            gaming = False
            mixer.music.stop()
            mouse.set_visible(True)
        fire_timer.tick(90)

    if running:
        if Map.player.win: #if they've won display a cheesy the end lol
            theend = True
            the_end = image.load("the-end.jpg")
            screen.blit(the_end,(0,0))
            display.flip()
            while theend:
                for evt in event.get():
                    if evt.type == QUIT:
                        theend = False
                    elif evt.type == MOUSEBUTTONDOWN:
                        theend = False
        elif Map.player.death:
            youlose = True #otherwise, game over. Either way, click to continue
            game_over = image.load("game-over.jpg")
            screen.blit(game_over,(0,0))
            display.flip()
            while youlose:
                for evt in event.get():
                    if evt.type == QUIT:
                        youlose = False #Note: this doesn't mean you win, it means restart the loop
                    elif evt.type == MOUSEBUTTONDOWN:
                        youlose = False

quit()
