import pygame
import neat
import os
import time
import random

WIDTH = 500
HEIGHT = 800

BIRD_IMGS = [pygame.transform.scale2x(pygame.image.load(os.path.join("imgs","bird1.png"))),pygame.transform.scale2x(pygame.image.load(os.path.join("imgs","bird2.png"))),pygame.transform.scale2x(pygame.image.load(os.path.join("imgs","bird3.png")))]
#BIRD_IMGS= [pygame.transform.scale(pygame.image.load(os.path.join("imgs","bird1.png")),(2.5,2.5))], using scale() instead of scale2x()

PIPE_IMG = pygame.transform.scale2x(pygame.image.load(os.path.join("imgs","pipe.png")))
BASE_IMG = pygame.transform.scale2x(pygame.image.load(os.path.join("imgs","base.png")))
BG_IMG = pygame.transform.scale2x(pygame.image.load(os.path.join("imgs","bg.png")))

class Bird:
    IMGS = BIRD_IMGS
    MAX_ROTATION =25
    ROT_VEL = 5
    ANIMATION_TIME = 10

    def __init__(self,x,y):
        self.x = x
        self.y = y
        self.tilt = 0
        self.tick_count = 0
        self.vel = 0
        self.height = self.y
        self.img_count = 0 # which of the 3 images we are using in a tick
        self.img = self.IMGS[0]

    def jump(self):
        self.vel = -10.5
        self.tick_count= 0
        self.height= self.y
    
    def move(self): # tells how much we move in the y axis only
        self.tick_count+=1
        displacement=self.tick_count*self.vel + 1.5*self.tick_count**2 # A parabolic graph

        if displacement >=8: # A failsafe. To ensure we are not falling too quickly
            displacement =8

        if displacement <0:
            displacement -=1

        self.y=self.y +displacement # Add the displacement to the y coordinate.

        if displacement <0 or self.y<self.height+50: #Really 50?
            #Here, 50 just means that the rotation will start after the height
            #is 50 below the original height.
            if self.tilt<self.MAX_ROTATION:
                self.tilt=self.MAX_ROTATION
        else:
            if self.tilt >=-90:
                self.tilt-=self.ROT_VEL
    
    def draw(self,win):
        self.img_count+=1
        if self.img_count < self.ANIMATION_TIME:
            self.img =self.IMGS[0]
        elif self.img_count < self.ANIMATION_TIME*2:
            self.img =self.IMGS[1]
        elif self.img_count < self.ANIMATION_TIME*3:
            self.img =self.IMGS[2]
        elif self.img_count < self.ANIMATION_TIME*4:
            self.img =self.IMGS[1]
        elif self.img_count == self.ANIMATION_TIME*4+1: 
            self.img =self.IMGS[0] 
            self.img_count = 0 

        if self.tilt <= -80: 
            # If tilt is less than -80, we dont want the bird to flap its wings
            self.img=self.IMGS[1]
            self.img_count=self.ANIMATION_TIME*2 # You can add a -1

        rotated_image = pygame.transform.rotate(self.img,self.tilt)
        #This will do the rotation for us, but it will rotate about
        #the top left corner. To rotate about the center, we use the following
        new_rect=rotated_image.get_rect(center=self.img.get_rect(topleft=(self.x,self.y)).center)
        #The x and y coordinates of the the image gives the coordinates of the topleft corner of the image.
        #Check it by setting the coordinates of the image to 0,0
        #https://stackoverflow.com/questions/4183208/how-do-i-rotate-an-image-around-its-center-using-pygame
        win.blit(rotated_image,new_rect.topleft)

    def get_mask(self):
        return pygame.mask.from_surface(self.img)
    
class Pipe:
    GAP = 200
    VEL = 5

    def __init__(self,x):
        self.x = x
        self.height = 0

        self.top=0
        self.bottom=0
        self.PIPE_TOP=pygame.transform.flip(PIPE_IMG,False,True)
        #.flip() method takes arguments surface, flip_x, flip_y, in that order.
        # We only want to flip it across y axis
        self.PIPE_BOTTOM = PIPE_IMG

        self.passed = False
        self.set_height() # As soon as a Pipe object is created, the set_height method
        # is automatically called.

    def set_height(self):
        self.height = random.randint(50,450) # Also can use randrange
        self.top = self.height - self.PIPE_TOP.get_height()
        # image.get_height() method gets the height of the image
        # Theres also image.get_width() method.
        self.bottom = self.height +self.GAP
    
    def move(self):
        self.x-=self.VEL

    def draw(self,win):
        win.blit(self.PIPE_TOP,(self.x,self.top))
        win.blit(self.PIPE_BOTTOM,(self.x,self.bottom))
    
    #Here, we use the mask function to find exactly where the pixels are present in the image
    #and thus determine exactly if a collision has occured or not
    def collide(self,bird):
        #Get the mask of all 3 images
        bird_mask=bird.get_mask()
        top_mask=pygame.mask.from_surface(self.PIPE_TOP)
        bottom_mask=pygame.mask.from_surface(self.PIPE_BOTTOM)

        #Find the offset - The difference between the positions of the images (taking top left corner)
        top_offset=(self.x-bird.x,self.top-round(bird.y)) 
        #bird.y got converted into a float because of the parabolic displacement
        bottom_offset = (self.x-bird.x,self.bottom-round(bird.y))

        #The function below returns None if there's no overlap
        b_point = bird_mask.overlap(bottom_mask,bottom_offset)
        t_point = bird_mask.overlap(top_mask,top_offset)
        #The above overlap() function uses some maths to figure out if theres any intersecting pixel
        #between the two images given the offset
        #Note that the offset is taken from the pipe to the bird
        #meaning that it's the distance the bird would need to travel to reach the pipe

        if(b_point or t_point):
            return True
        return False
    
class Base:
    VEL = 5 # Must be the same as Pipe's vel
    WIDTH = BASE_IMG.get_width()
    IMG = BASE_IMG

    def __init__(self,y):
        self.y = y
        self.x1 = 0
        self.x2 = WIDTH

    def move(self):
        self.x1-=self.VEL
        self.x2-=self.VEL

        #Basically seeing that if the first image goes completely out of the window, put it behind the second image
        if(self.x1+self.WIDTH < 0):
            self.x1=self.x2+self.WIDTH
        #Same here
        if(self.x2+self.WIDTH < 0):
            self.x2=self.x1+self.WIDTH
        #This works provided the image's width is larger than or equal to the window's width
        #Otherwise, we would need to use 3,4,etc such images

    def draw(self,win):
        win.blit(self.IMG, (self.x1,self.y))
        win.blit(self.IMG, (self.x2,self.y))

    


def draw_window(win,bird,pipes,base):
    win.blit(BG_IMG, (0,0))
    bird.draw(win)

    for pipe in pipes:
        pipe.draw(win)

    base.draw(win)
    pygame.display.update()

def main():
    bird=Bird(0,0)
    base = Base(730)
    pipes = [Pipe(500)]
    win = pygame.display.set_mode((WIDTH,HEIGHT))
    clock= pygame.time.Clock()

    run= True
    while run:
        clock.tick(60)
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                run = False
        
        #Note that you're doing all this for one frame.
        #You have time to go out of the loop, and come back again
        #To make a list of the pipes to be removed
        rem= []
        for pipe in pipes:
            if ( pipe.x + pipe.PIPE_BOTTOM.getwidth() < 0):
                #Pipe has moved completely out of the screen
                rem.append(pipe)

            if not pipe.passed and pipe.x < bird.x:
                #If the pipe has not passed the bird yet, but pipe.x<bird.x now, then:
                pipe.passed = True
                add_pipe = True
            pipe.move()
        
        if add_pipe:
            score += 1
        #bird.move()
        base.move()
        draw_window(win,bird,pipes,base)
    
    pygame.quit()
    quit()

main()