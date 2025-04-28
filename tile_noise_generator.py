import pyray as pr
import time
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
    imageObj = None
    texture = None
    imageDim = 0
    imageObjDim = 0
    intersects = False
    renderRange = False
    expired = False
    renderBounds = (3,2)
    renderOutofBounds = (7,6)
    x = 0
    y = 0
    scale = 2 #default scaling factor
    meta = []
    def __init__(self, x, y,imageDim, image):
        self.x = x
        self.y = y
        self.imageDim = imageDim
        self.image = image

    def getImageObj(self,scale=None): #possibly change to scale texture instead of resizing image and reloading texture
        if scale is None:
            scale = self.scale
            if self.imageObj is None:
                self.imageObj = PILtoRayLibObj(self.image,self.scale*self.imageDim)
                self.imageObjDim = self.scale*self.imageDim
        else:
            self.scale = scale
            self.imageObj = PILtoRayLibObj(self.image,self.scale*self.imageDim)
            self.imageObjDim = self.scale*self.imageDim
        
        return self.imageObj
    def checkBounds(self, x, y):

        if (x >= self.x) and (x <= self.x + 1):
            if(y >= self.y) and ( y <= self.y + 1):
                
                return True
        return False
    def checkRenderBounds(self, x, y):
        if (x >= self.x-self.renderBounds[0]) and (x <= self.x + 1 + self.renderBounds[0]):
            if(y >= self.y-self.renderBounds[1]) and ( y <= self.y + 1 + self.renderBounds[1]):

                return True
        return False
    def renderOuterBounds(self, x, y):
        if (x >= self.x-self.renderOutofBounds[0]) and (x <= self.x + 1 + self.renderOutofBounds[0]):
            if(y >= self.y-self.renderOutofBounds[1]) and ( y <= self.y + 1 + self.renderOutofBounds[1]):

                return True
        return False
        
    def setTexture(self, texture):
        self.texture = texture
    def getTexture(self):
        return self.texture
        
############## NOT FULLY USED CURRENTLY ##############################
### would be used if I was periodically saving tiles to disk #########
### since im not im just saving tiles in memory render list and regenerating ###
class Chunk:
    background_color= pr.BLUE
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
##############################################################


def normalize2d(array):#normalize a point
    if(array[0]==0):
        if(array[1]==0):
            return array
    scalar = np.array(math.sqrt(array[0]**2+array[1]**2))
    return array/scalar
def fade(t): #fade function with second derivative = to 0 for a smooth transition (no )
    return  t * t * t * (t * (t * 6 - 15) + 10)
def lerp(a, b, x):#interpolate between two points with weight, a which should be the fade function
    
    return a + x * (b - a)


#((0,1),(1,1),(1,0),(1,-1),(0,-1),(-1,-1),(-1,0),(-1,1)) switch statement vectors
def computeDirection(x,y,vector_hash):
    if vector_hash == 0:
        return y
    elif vector_hash == 1:
        return x + y
    elif vector_hash == 2:
        return x
    elif vector_hash == 3:
        return x - y
    elif vector_hash == 4:
        return -y
    elif vector_hash == 5:
        return -x - y
    elif vector_hash == 6:
        return -x
    elif vector_hash == 7:
        return -x + y
    else:
        return 0
    
def genGrid(tile,sqrval):#generate the grid values
    grid = []
    for x in range(0,sqrval+1):
        grid.append([])
        for y in range(0,sqrval+1):

            rx = sqrval*tile.x
            rx = x+rx

            ry = sqrval*tile.y
            ry = y+ry
            stringify = str(rx)+"axf"+str(ogseed)+"ayf"+str(ry)
            hash = hl.sha256(bytes(stringify, 'utf-8')).digest()
            hashx = (unpack('Q',hash[4:12])[0]/(2<<63))

            values = int(hashx*8) #number 0-7 of direction hashmap to choose
            
            grid[x].append(values)

    return grid

def genGrad(sqrval, winwidth, grid):
    grid = np.array(grid)
    gridwidth = int(winwidth/sqrval)

    # Create coordinate grids row major order <<<<< important
    y_coords, x_coords = np.meshgrid(np.arange(winwidth), np.arange(winwidth))
    # print(x_coords)
    # Normalize the coordinates
    xr = x_coords % gridwidth
    yr = y_coords % gridwidth

    gridx = x_coords - xr
    gridy = y_coords - yr
    # calculate grid indices
    gridxm = gridx // gridwidth
    gridym = gridy // gridwidth
    
    # vectorized computation for relative positions
    blr = np.stack([(xr), (yr - gridwidth)], axis=-1) / gridwidth         #bottom left
    tlr = np.stack([xr, yr], axis=-1) / gridwidth                         #top left
    brr = np.stack([xr - gridwidth, yr - gridwidth], axis=-1) / gridwidth #bottom right
    trr = np.stack([xr - gridwidth, yr], axis=-1) / gridwidth             #top right
    # compute values for each position using generated psuedo-random vectors.
    blv = grid[gridxm, gridym+1]
    tlv = grid[gridxm, gridym]
    brv = grid[gridxm+1, gridym+1]
    trv = grid[gridxm+1, gridym]

    # apply computeDirection function
    bl = np.vectorize(computeDirection)(blr[:,:,0],blr[:,:,1], blv)
    tl = np.vectorize(computeDirection)(tlr[:,:,0],tlr[:,:,1], tlv)
    br = np.vectorize(computeDirection)(brr[:,:,0],brr[:,:,1], brv)
    tr = np.vectorize(computeDirection)(trr[:,:,0],trr[:,:,1], trv)

    # Compute u and v
    u = fade(xr / gridwidth)
    v = fade(yr / gridwidth)

    # Linear interpolation
    interp1 = lerp(tl, tr, u)
    interp2 = lerp(bl, br, u)
    interp = ((lerp(interp1, interp2, v)) + 1) / 2
    interp = (interp * 255).astype(int)

    return Image.fromarray(interp.T.astype(np.uint8), mode='L')

def genChunk(xxx, yyy, sqrval, tilewidth):
    chunk = Chunk(xxx, yyy)
    grid = genGrid(Tile(xxx, yyy, tilewidth, None), sqrval)
    finalimg = genGrad(sqrval, tilewidth, grid)
    tile = Tile(xxx, yyy, tilewidth, finalimg)
    return tile

def PILtoRayLibObj(image,res):
    start = time.time()
    image = image.resize((res, res))
    pixel_data = image.tobytes()
    width, height = image.size

    img = pr.Image(
        pixel_data, #data
        width, #width
        height, #height
        1, #mipmaps
        pr.PIXELFORMAT_UNCOMPRESSED_GRAYSCALE  # format grayscale
    )
    end = time.time()
    # print(end-start)
    return img