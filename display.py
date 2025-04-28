import tile_noise_generator as m
import pyray as pr
import time
import threading
import time
import queue

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
        self.updateFlag = True
        self.renderlist = []
        self.rendercoordlist = {}
        self.renderloadqueue = queue.Queue()
        self.renderloadset = set()
        self.sqrval = 4
        self.delta_time = 0
        self.MAX_TPS = 100
        self.TIME_PER_TICK = 1000000000 / self.MAX_TPS
        m.init()
        pr.init_window(1800,1000, "Perlin Noise")
        pr.set_target_fps(120)

        self.camera = pr.Camera2D([0,0],[0,0],0,0)


    def render(self):


            centerx = int(pr.get_screen_width()/2)
            centery = int(pr.get_screen_height()/2)
            
            cum = 0
            
            x = round(self.xpos)
            y = round(self.ypos)
            n = len(self.renderlist) - 1
            while(n >= 0):
                tile = self.renderlist[n]
                if tile.expired is True:
                    texture = tile.getTexture()
                    pr.unload_texture(texture)
                    self.renderlist.pop(n)
                    self.rendercoordlist.pop((tile.x, tile.y))
                    n = n-1
                else:
                    
                    if tile.renderRange is True and tile.imageObj:
                        # print(self.renderlist)
                        texture = tile.getTexture()
                        if texture is None:
                            # print("got texture")
                            texture = pr.load_texture_from_image(tile.imageObj)
                            tile.setTexture(texture)

                        
                        xoff = tile.x * tile.imageObjDim + centerx
                        yoff = tile.y * tile.imageObjDim + centery
                        pr.draw_texture(texture,xoff-x,yoff-y,pr.Color(255,255,255,255))
                        
                        if tile.intersects is True:
                            pr.draw_text(str(tile.x) + ", " + str(tile.y),xoff-x,yoff-y,40,pr.BLACK)
                            pr.draw_rectangle_lines(xoff+1-x,yoff+1-y,398,398,pr.RED)
                    n -= 1
            

            pr.draw_circle(centerx,centery,10,pr.BLACK)
            pr.draw_circle(centerx-x,centery-y,20,pr.RED)
            
        

    def setUpdateFlag(self): #set when input is updated so screen is redrawn with minimal calls
        self.updateFlag = True


    def inputHandler(self):
        #pixels per second
        speed = 280
        if(pr.is_key_down(pr.KEY_W)):
            self.ypos = self.ypos - speed * self.delta_time
            self.setUpdateFlag()
        if(pr.is_key_down(pr.KEY_A)):
            self.xpos = self.xpos - speed * self.delta_time
            self.setUpdateFlag()

        if(pr.is_key_down(pr.KEY_S)):
            self.ypos = self.ypos + speed * self.delta_time
            self.setUpdateFlag()

        if(pr.is_key_down(pr.KEY_D)):
            self.xpos = self.xpos + speed * self.delta_time
            self.setUpdateFlag()


    def checkBounds(self): #WARNING: in update loop, cannot do graphics calls
        intersects = 0
        n = len(self.renderlist) - 1
        x = round(self.xpos // 400)
        y = round(self.ypos // 400)
        while(n >= 0):
            obj = self.renderlist[n]

            obj.intersects = False

            renderBool = obj.checkRenderBounds(x,y)
            obj.renderRange = renderBool

            if not obj.renderOuterBounds(x,y):
                obj.expired = True
            n -= 1

        if self.rendercoordlist.get((x,y)):
            self.rendercoordlist.get((x,y)).intersects = True
        else:
            if  (x, y) not in self.renderloadset:
                self.renderloadset.add((x,y))
                self.renderloadqueue.put((x,y))
            
            if not (self.rendercoordlist.get((x+1, y)) or (x+1, y) in self.renderloadset):
                self.renderloadset.add((x+1,y))
                self.renderloadqueue.put((x+1,y))
                
            if not (self.rendercoordlist.get((x+1, y+1)) or (x+1, y+1) in self.renderloadset):
                self.renderloadset.add((x+1,y+1))
                self.renderloadqueue.put((x+1,y+1))
                
            if not (self.rendercoordlist.get((x, y+1)) or (x, y+1) in self.renderloadset):
                self.renderloadset.add((x,y+1))
                self.renderloadqueue.put((x,y+1))
 
            if not (self.rendercoordlist.get((x-1, y)) or (x-1, y) in self.renderloadset):
                self.renderloadset.add((x-1,y))
                self.renderloadqueue.put((x-1,y))

            if not (self.rendercoordlist.get((x-1, y-1)) or (x-1, y-1) in self.renderloadset):
                self.renderloadset.add((x-1,y-1))
                self.renderloadqueue.put((x-1,y-1))

            if not (self.rendercoordlist.get((x, y-1)) or (x, y-1) in self.renderloadset):
                self.renderloadset.add((x,y-1))
                self.renderloadqueue.put((x,y-1))
                

                
    def loader(self): #specific image loading thread
        while not self.close:
            (x,y) = self.renderloadqueue.get()
            tile = m.genChunk(x,y,4,200)
            tile.getImageObj()
            self.renderlist.append(tile)
            self.rendercoordlist[(x,y)] = tile
            self.renderloadset.discard((x,y))
            
       
    def update(self): #WARNING: separate thread, cannot do graphics calls
        last_frame_time = time.time_ns()
        
        while not self.close:
            current_time = time.time_ns()  # get the current time
            elapsedtime = current_time - last_frame_time  # calculate delta time
            self.delta_time = min(max(elapsedtime / 1_000_000_000, 1 / self.MAX_TPS), 0.1)
            sleeptime = self.TIME_PER_TICK - elapsedtime
            sleeptime = sleeptime / 1_000_000_000
            last_frame_time = current_time
            

            self.inputHandler()
            if self.updateFlag:

               self.checkBounds()
               self.updateFlag = False

            
            if(sleeptime > 0):
                time.sleep(sleeptime)
            


    def main(self):
        while not pr.window_should_close():


            pr.begin_drawing()
            pr.clear_background(pr.RAYWHITE)
            
            self.render()

            pr.end_drawing()
            
                
            
        pr.close_window()
        self.close = True


display = Display()
display.init()
updatethread = threading.Thread(target=display.update)
loaderthread1 = threading.Thread(target=display.loader)
loaderthread2 = threading.Thread(target=display.loader)
loaderthread3 = threading.Thread(target=display.loader)

updatethread.daemon = True
loaderthread1.daemon = True
loaderthread2.daemon = True
loaderthread3.daemon = True
updatethread.start()
loaderthread1.start()
loaderthread2.start()
loaderthread3.start()
display.main()
