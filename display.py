import practice as m
import pyray as pr
import raylib as rl
import io
import os
import threading

s_print_lock = threading.Lock()
def s_print(*a, **b):
    """Thread safe print function"""
    with s_print_lock:
        print(*a, **b)
class Display:
    def __init__(self):
        pass
    def init(self):
        self.close = False
        self.xpos = 0
        self.ypos = 0
        self.updateFlag = False
        m.init()
        pr.init_window(1800,1000, "Perlin Noise")
        pr.set_target_fps(120)

        self.camera = pr.Camera2D([0,0],[0,0],0,0)

        image = m.genChunk(2,2,4,200)
        image4 = m.genChunk(3,2,4,200)
        image5 = m.genChunk(2,3,4,200)
        image6 = m.genChunk(3,3,4,200)
        image7 = m.genChunk(4,2,4,200)


        self.texture = pr.load_texture_from_image(m.PILto(image,400))
        self.texture4 = pr.load_texture_from_image(m.PILto(image4,400))
        self.texture5 = pr.load_texture_from_image(m.PILto(image5,400))
        self.texture6 = pr.load_texture_from_image(m.PILto(image6,400))
        self.texture7 = pr.load_texture_from_image(m.PILto(image7,400))

    def display(self):
        x = round(self.xpos)
        y = round(self.ypos)
        pr.draw_texture(self.texture4,x + 500,y + 100,pr.Color(255,255,255,255))
        pr.draw_texture(self.texture, x + 100,y + 100,pr.Color(255,255,255,255))
        pr.draw_texture(self.texture5,x + 100,y + 500,pr.Color(255,255,255,255))
        pr.draw_texture(self.texture6,x + 500,y + 500,pr.Color(255,255,255,255))
        pr.draw_texture(self.texture7,x + 900,y + 100,pr.Color(255,255,255,255))
        centerx = int(pr.get_screen_width()/2)
        centery = int(pr.get_screen_height()/2)
        pr.draw_circle(centerx,centery,10,pr.BLACK)

    def setUpdateFlag(self): #set when input is updated so screen is redrawn properly
        self.updateFlag = True


    def inputHandler(self):
        if(pr.is_key_down(pr.KEY_W)):
            self.ypos = self.ypos + .001
            self.setUpdateFlag()
        if(pr.is_key_down(pr.KEY_A)):
            self.xpos = self.xpos + .001
            self.setUpdateFlag()

        if(pr.is_key_down(pr.KEY_S)):
            self.ypos = self.ypos - .001
            self.setUpdateFlag()

        if(pr.is_key_down(pr.KEY_D)):
            self.xpos = self.xpos - .001
            self.setUpdateFlag()


    def update(self):
        while not self.close:
            self.inputHandler()
            if(self.updateFlag is True):

                pass

    def main(self):
        while not pr.window_should_close():
            pr.begin_drawing()
            pr.clear_background(pr.RAYWHITE)

            self.display()
            pr.end_drawing()
        pr.close_window()
        self.close = True


display = Display()
display.init()
updatethread = threading.Thread(target=display.update)

updatethread.daemon = True
updatethread.start()
display.main()
