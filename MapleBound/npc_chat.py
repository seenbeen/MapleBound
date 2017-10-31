from pygame import *
from glob import *

screen = display.set_mode((800,600))
running = True
mixer.pre_init(44100, 16, 2, 1024*4)
init()
#Load in files
click = mixer.Sound("chat/sound/click.ogg")
click.set_volume(0.1)
over = mixer.Sound("chat/sound/over.ogg")
over.set_volume(0.1)

top = image.load("chat/pieces/top.png")
content = image.load("chat/pieces/center.png")
bottom = image.load("chat/pieces/bottom.png")
npc_np = image.load("chat/pieces/npc_name.png")

mouseon = image.load("ui/pressed.png")
mouseoff = image.load("ui/normal.png")

#Function fetches chat box for npc frames
def chat_box(text_raw,colour,font_,font_size,npc,npc_name):
    return_list = []
    name_font = font.SysFont("Arial",14)
    font_ = font.SysFont(font_, font_size)
    #Dividing text up into two sections, one for the actual npc
    #speech, and the other for button action scripts.
    text = text_raw[:text_raw.find("/#e")].split()
    action_script = text_raw[text_raw.find("/#e")+3:].split()
    
    x_coord = 163 #Where the text starts
    paragraph = []
    
    while text:
        for i in range(len(text)+1): #extract all text, br to break line
            lol = font_.render(" ".join(text[:i+1]),True,colour)
            if text[i-1] == "/br": #note: works a bit like html
                del(text[i-1])
                i-=1
                break
            if lol.get_width() > 327:
                break
        line_text = font_.render(" ".join(text[:i]),True,colour)
        text = text[i:]
        paragraph.append(line_text)
    
    top_h = top.get_height()
    cont_h = content.get_height()
    cont_w = content.get_width()
    npc_ox = 0
    npc_oy = 0

    chat_box_offset = 4-len(paragraph)
    if chat_box_offset < 0: chat_box_offset = 0
    size = len(paragraph)*19/13+chat_box_offset
    surf_w = 519
    surf_h = top_h+cont_h*(size+3)+bottom.get_height()
    
    if npc:
        if npc.get_width()/2 > 77:
            npc_ox = abs(npc.get_width()/2 - 77)
        if int(surf_h*0.25)-npc.get_height()/2 < 0:
            npc_oy = abs(int(surf_h*0.25)-npc.get_height()/2)
    
    #Create surface
    surface = Surface((surf_w+npc_ox,surf_h+npc_oy),SRCALPHA)
    surface.fill((0,0,0,0))
    #Draw box on surface
    surface.blit(top,(0+npc_ox,0+npc_oy))
    for i in range(size+3):
        surface.blit(content,(0+npc_ox,top_h+cont_h*i+npc_oy))
    surface.blit(bottom,(0+npc_ox,top_h+cont_h*(size+3)+npc_oy))

    #Draw Text
    for i in range(len(paragraph)):
        surface.blit(paragraph[i],(x_coord+npc_ox,28+19*i+npc_oy))
    if npc:
        surface.blit(npc,(77-npc.get_width()/2+npc_ox, int(surf_h*0.30)-npc.get_height()/2+npc_oy))
    if npc_name:
        surface.blit(npc_np,(77-npc_np.get_width()/2+npc_ox,
                             int(surf_h*0.30)+npc.get_height()/2+5+npc_oy))
        name_pic = name_font.render(npc_name,True,(255,255,255))
        surface.blit(name_pic,(77-name_pic.get_width()/2+npc_ox,
                             int(surf_h*0.30)+npc.get_height()/2+6+npc_oy))

    b_coords = [(9+npc_ox,surf_h+npc_oy-23),(380+npc_ox,surf_h+npc_oy-60),(440+npc_ox,surf_h+npc_oy-60)]
    #Note 60 being the height of a button + height of bottom bar
    #404,451 being where the buttons are located. The only shift happens in the y axis (because of text size)
    
    for action,xy in zip(action_script,b_coords):
        #if action.split("$")[0] != "none":
        defaultb = image.load("chat/buttons/%sa.png"%action.split("$")[0]) #this would be when the button's passive
        surface.blit(defaultb,xy)
        #Used for setting a rectangle
        butw = defaultb.get_width()
        buth = defaultb.get_height()
        img_names = glob("chat/buttons/%s*.png"%action.split("$")[0])
        img_names.sort()
        return_list.append([image.load(each) for each in img_names
                            ]+[Rect(list(xy)+[butw,buth]),action.split("$")[-1]])
        
    return_list=[surface]+return_list
    return_list.append([surf_w,surf_h,npc_ox,npc_oy])
    return return_list

#The following function allows us to add an x and y value to an existing tuple or list
def add_cord(xy,ax,ay):
    return (xy[0]+ax,xy[1]+ay)

#Similar to the above function, this time returns a full rect
def add_rect(rectz,ax,ay):
    return Rect(rectz[0]+ax,rectz[1]+ay,rectz[2],rectz[3])

#when a button is clicked, what happens?
#This function takes the value linked with the button and does something to the game
def set_button(b_set,npc_quest,PLAYER):
    button = b_set.split("-")
    b_typ = button[0]
    if b_typ == "f": #changes frame of npc
        b_val = button[-1]
        return int(b_val)
    elif b_typ == "r": #end chat
        return "end"
    elif b_typ == "q": #quests
        b_val = button[1:]
        start = map(int,npc_quest[0])
        if PLAYER.quests[start[0]][0] == 0: #have they yet to start the quest?
            return int(b_val[0]) #if so, direct them to the quest starter
        elif PLAYER.quests[start[0]][0] == 2: #have they finished it already?
            return int(b_val[3])
        #alright so the only possibility now is if they're in the middle of it

        Achieved = True
        for each in npc_quest: #checks each condition if it's true or not
            conditions = each
            if PLAYER.quests[conditions[0]][conditions[1]+1] < conditions[2]:
                Achieved = False #they're not done the quest yet
                
        if Achieved:
            return int(b_val[1])
        else:
            return int(b_val[2])
    elif b_typ == "sp":
        b_val = button[2] #value we set quest status to
        quest_id = int(button[1]) #which quest is it?
        PLAYER.quests[quest_id][0] = int(b_val) #set quest status to value
        if int(b_val) == 2:
            quest_results = [int(each.strip()) for each in open("questeffects/%i.txt"%quest_id).readlines()]
            PLAYER.hp = quest_results[1]
            PLAYER.pattack = quest_results[0]
        
def refresh_page(frames,frame,lx,ly,fw,fh,backz):#this function refreshes the page
    screen.set_clip(lx,ly,fw,fh) #clip to prevent lagg from occuring per page refresh
    screen.blit(backz,(0,0))
    screen.set_clip(None) 
    screen.blit(frames[frame][0],(lx,ly))
    return False
    for each in frames[frame][1:-1]:
        screen.blit(each[0],(add_cord(each[-2],lx,ly)))
        
def npc_convo(npc_name,colour,font_,font_size,PLAYER): #begin conversation function
    lx,ly = 140,150
    sback = screen.copy() #Load in previous background
    font.init()
    npc = image.load("chat/npc/%s/%s.png"%(npc_name,npc_name)) #this will get us the data we need
    name = open("chat/npc/%s/name.txt"%npc_name).read() #in order to interpret chat and quests
    npc_quest = [map(int,each.strip().split()) for each in open("chat/npc/%s/quest.txt"%npc_name).readlines()]
    frames = [chat_box(open("%s"%each).read(),colour,font_,font_size,npc,name) for each in glob("chat/npc/%s/*.txt"%npc_name) if each.strip(".txt")[each.find("/",-1):].isdigit()]
    frame = 0
    #Initialize frame 0's dimensions
    fw = frames[frame][0].get_width()
    fh = frames[frame][0].get_height()
    talking = True
    global running #we'll need to alter global copy of running if they exit.
    
    #Insert oh-so-awesome transition into npc chat heheheheh C:<
    dimmer = Surface((800,600))
    for i in range(0,122):
        screen.blit(sback,(0,0))
        dimmer.set_alpha(i)
        screen.blit(dimmer,(0,0))
        display.flip()
    backz = screen.copy()
    screen.blit(frames[frame][0],(lx,ly))
    bset = False #clicking a button
    moving = False
    played = False
    waiting_off = False
    while talking and running:
        mx,my = mouse.get_pos()
        for evt in event.get():
            played = False
            if not talking: break
            if evt.type == QUIT:
                running = False
            for each in frames[frame][1:-1]:
                #Reoffset the rect according to position
                b_rect = add_rect(each[-2],lx,ly)
                screen.set_clip(b_rect)
                screen.blit(frames[frame][0],(lx,ly))
                screen.set_clip(None)
                #Default button blitted
                screen.blit(each[0],(add_cord(each[-2],lx,ly)))
                if b_rect.collidepoint(mx,my):
                    played = True #this is for handling sound so you dont get spam quality
                    screen.blit(each[1],(add_cord(each[-2],lx,ly)))
                    if evt.type == MOUSEBUTTONDOWN:
                        if evt.button == 1:
                            click.play() #if they click, play sound ONCE.
                            screen.blit(each[2],(add_cord(each[-2],lx,ly)))
                            bset = each[-1]
                            break #they click a single button, break. We don't want multiple events
                    elif evt.type == MOUSEBUTTONUP and bset:
                        if evt.button == 1:
                            frame = set_button(bset,npc_quest,PLAYER)
                            bset = "Set" #Set button down and view next frame
                            if type(frame) != int:
                                talking = False
                                screen.blit(backz,(0,0))
                                break
                            
            if evt.type == MOUSEBUTTONDOWN:
                cw,ch,ox,oy = frames[frame][-1]
                """notes: 10 is the distance from the edge of the box to the white content
                    cw,cy,ox,oy are content width and height, offsets x and y respectively.
                    Only planning on making drag if they click the blue part, but of course, good graphics
                    impose not a consistent colour throughout the border. What's worse? Alphas. T.T
                    One last thing. The bottom border isn't the same as top. It's where I get the value 28
                """
                if Rect(lx+ox,ly+oy,cw,ch).collidepoint(mx,my) and \
                Rect(lx+ox+10,ly+oy+10,cw-10-10,ch-10-28).collidepoint(mx,my) == False \
                and add_rect(frames[frame][1][-2],lx,ly).collidepoint(mx,my) == False:
                    #Above explained: Only want it to collide with border, but there's a button on the border
                    #all of these rect things make sure we're only on the boarder.
                    movex,movey = mx-lx,my-ly
                    moving = True
                    
            elif evt.type == MOUSEBUTTONUP:
                if moving:
                    moving = False
                    
            if evt.type == KEYDOWN:
                if evt.key == K_ESCAPE:
                    screen.blit(backz,(0,0))
                    talking = False

        if bset=="Set" and talking:
            bset = refresh_page(frames,frame,lx,ly,fw,fh,backz) #button set is now False
            fw = frames[frame][0].get_width()
            fh = frames[frame][0].get_height()
            
        if moving: #this moves the chat box around the screen
            screen.set_clip(lx,ly,fw,fh) #clips the bg according to its location
            screen.blit(backz,(0,0))
            screen.set_clip(None)
            lx,ly = mx-movex,my-movey #initial offset for the chatbox (lx and ly)
            screen.blit(frames[frame][0],(lx,ly))
        
        if waiting_off and not played:
            waiting_off = False #these lines handle music
        elif played and not waiting_off:
            over.play()
            waiting_off = True
        mb = mouse.get_pressed()
        #checking for awesomesauce mouse cursor
        mouseback = screen.copy()
        
        if mb[0] == 1:
            screen.blit(mouseon,(mx,my))
        else:
            screen.blit(mouseoff,(mx,my))
        display.flip()
        screen.set_clip(Rect(mx,my,32,32))
        screen.blit(mouseback,(0,0))
        screen.set_clip(None)
        
    #Insert exit animations xD
    for i in range(122,0,-1):
        
        screen.blit(sback,(0,0))
        dimmer.set_alpha(i)
        screen.blit(dimmer,(0,0))
        display.flip()
