from pyray import *
import random
import math
import numpy as np
import hashlib as hl
from struct import unpack
from PIL import Image, ImageDraw
import io

ogseed = random.uniform(100,10000)
empty_tileset = [[None],[None]]
def init():
    empty_tileset.clear()
    for x in range(0,16):
        empty_tileset.append([])
        for y in range(0,16):
            empty_tileset[x].append(None)


class Tile:
    image = None
    x = 0
    y = 0
    meta = []
    def __init__(self, x, y, image):
        self.x = x
        self.y = y
        self.image = image

class Chunk:
    background_color= BLUE
    x = 0
    y= 0
    tiles = [[None],[None]]
    def __init__(self, x, y):
        self.x = x
        self.y = y
        # self.background_color = background_color
        self.tiles = empty_tileset
    def modifyTile(self,tile):
        self.tiles[tile.x][tile.y] = tile
    def removeTile(self,x,y):
        self.tiles[x][y] = None
    def removeTile(self,tile):
        self.tiles[tile.x][tile.y] = None



def normalize2d(array):#normalize a point
    if(array[0]==0):
        if(array[1]==0):
            return array
    scalar = np.array(math.sqrt(array[0]**2+array[1]**2))
    return array/scalar
def fade(t): #fade function with second derivative = to 0 for some reason that is important
    return  t * t * t * (t * (t * 6 - 15) + 10)
def lerp(a, b, x):#interpolate between two points with weight a which should be the fade function
    return a + x * (b - a)

#((0,1),(1,1),(1,0),(1,-1),(0,-1),(-1,-1),(-1,0),(-1,1)) switch statement vectors
def computeDirection(values,vector_hash):
    x = values[0]
    y = values[1]
    switch = {
        0: y,
        1: x+y,
        2: x,
        3: x-y,
        4: -y,
        5: -x-y,
        6: -x,
        7: -x+y
    }
    return switch.get(vector_hash)
def genGrid(chunk,sqrval):#generate the grid values
    grid = []
    for x in range(0,sqrval+1):
        grid.append([])
        for y in range(0,sqrval+1):

            rx = sqrval*chunk.x
            rx = x+rx

            ry = sqrval*chunk.y
            ry = y+ry
            stringify = str(rx)+"axf"+str(ogseed)+"ayf"+str(ry)
            hash = hl.sha256(bytes(stringify, 'utf-8')).digest()
            hashx = (unpack('Q',hash[4:12])[0]/(2<<63))

            values = int(hashx*8) #number 0-7 of direction hashmap to choose
            
            grid[x].append(values)

            # image_draw_circle(img,int(x*scale)+50,int(y*scale)+50,4,BLACK)
            # image_draw_line(img,int(x*scale)+50,int(y*scale)+50,int((x+valuex)*scale)+50,int((y+valuey)*scale)+50,BLACK)
    return grid
def genGrad(sqrval, winwidth, grid, finalimg):
        img = ImageDraw.Draw(finalimg)

        gridwidth = int(winwidth/sqrval)

        for x in range(0,winwidth):
            xr = x % gridwidth
            gridx = x-xr
            gridxm = int(gridx/gridwidth)
            for y in range(0,winwidth):
                yr = y % gridwidth
                gridy = y - yr
                gridym = int(gridy/gridwidth)

                blr = np.array([(xr), (yr-gridwidth)])/gridwidth
                blv = grid[gridxm][gridym+1]
                bl = computeDirection(blr,blv)

                tlr = np.array([xr, yr])/gridwidth
                tlv = grid[gridxm][gridym]
                tl = computeDirection(tlr,tlv)

                brr = np.array([xr-gridwidth, yr-gridwidth])/gridwidth
                brv = grid[gridxm+1][gridym+1]
                br = computeDirection(brr,brv)

                trr = np.array([xr-gridwidth, yr])/gridwidth
                trv = grid[gridxm+1][gridym]
                tr = computeDirection(trr,trv)




                u = fade((xr/gridwidth))
                v = fade((yr/gridwidth))
                # print(gridx/winwidth,gridy/winwidth)
                # print(interp)
                # print(interp)
                # print("bl: ", bl)
                # print("br: ", br)
                # print("tl: ", tl)
                # print("tr: ", tr)
                interp1 = lerp(tl, tr, u)

                interp2 = lerp(bl,br,u)
                # print("interp1: ",interp1)
                # print("interp2: ",interp2)

                interp = ((lerp(interp1, interp2,v))+1)/2
                interp = int(interp*255)

                # print("val: ", values)
                img.point((x,y),(interp,interp,interp,255))


def genChunk(xxx,yyy,sqrval,winwidth):
    chunk = Chunk(xxx,yyy)

    finalimg = Image.new('RGBA',(winwidth,winwidth),255)

    grid = genGrid(chunk,sqrval)

    genGrad(sqrval,winwidth,grid,finalimg)


    print("done")
    return finalimg
def PILto(image,res):
    image = image.resize((res,res))

    buf = io.BytesIO()
    image.save(buf, 'png')
    bufval = buf.getvalue()
    image = load_image_from_memory(".png",bufval,len(bufval))
    return image