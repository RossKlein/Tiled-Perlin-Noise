# Tiled Perlin Noise Implementation

### Unique hashing designed for procedural generation
---
This project is a demonstration of my skills in a variety of programming paradigms. I implemented perlin noise into a procedural chunk rendering system. Perlin noise is a type of gradient noise developed by Ken Perlin. It's purpose is to create a random, but smooth image texture. The image generation pipeline is run on 3 worker threads, separate from the update and render threads. Far away chunks are culled, chunks outside of the render distance are not rendered.


**How to run:**
Note: python must be installed
You can use the requirements.txt files to install the requirements.
Required python modules:
>raylib
>pip3 install raylib==5.5.0.2
>numpy
>numpy==1.26.4
>PIL
>pillow==10.2.0

Once downloaded, navigate to the directory, open terminal, and run
>pip install -r requirements.txt

>python display.py

Alternatively
>python3 display.py

Once open the WASD keys will move a small dot around the screen.
You can also press SPACE to view a smaller render window.
SHIFT for a speed boost
## Watch the demo!!!
![see demo](https://github.com/RossKlein/Tiled-Perlin-Noise/assets/11377562/92541319-dd42-4866-990c-9a10746002c4)


### Breakdown of tile_noise_generator.py
Each time the program is run, a unique noise map will be generated. The procedural implementation builds off of Perlin's original gradient vector operation. A grid of points is created where each are assigned a random direction. Pixels in the forward direction of a gradient point are made darker while pixels behind a gradient point are lighter. For speed, the direction is assigned via a lookup table with 8 direction options. This was an optimization perlin used. The grid points are then given a weight using a quintic fade function. The weight value is then applied as each vector in a box, top-left, top-right, bottom-left, bottom-right, is interpolated between. Each pixel is then assigned a value based on the calculated gradient. 
![Oops! see fade function](fadefunction.png)

Calculating the gradient is the most process intensive step of the application. Numpy was used to vectorize the computations. Numpy meshgrid was an extremely useful data structure to use, allowing me to easily create a grid data structure to operate on. Numpy vectorize was also invaluable, allowing me to apply a function to an entire array of numbers in one step. Though, I have read that vectorize is not actually parallelized code. A better implementation would be to use a compute shader, leveraging the parallel processing of the GPU, to perform these calculations. But, this is a python project. 

The hashing function combines a random seed value and a grid coordinate to generate perlin noise values for one tile. SHA256 is used as the hashing function. Modern implementations of SHA256 are extremely fast. The use case for SHA256 to generate perlin noise values is for its psuedo-randomness, small changes in x and y will give significantly different hash outputs, and yet it is still reproducible, regenerating unloaded tiles is possible.

### Breakdown of display.py

A standard game engine architecture is used. There are two threads, the main thread and the update thread, as well as 3 worker threads for image processing.  The main thread contains the graphics context and performs all GPU calls. The update thread handles input and computation routines like tile boundary checking. The worker threads were added to asyncronously process the image data quickly. This allows movement to be unbound by image processing bottlenecks. The intersected tile is flagged to be highlighted. Tiles which are in 'render distance' are flagged to be drawn. Tiles which are 'out of render distance' are flagged to be culled. The program keeps track of render objects in a renderlist which is shared between the threads. The update thread will add tiles when the dot is no longer intersecting a tile in the renderlist. The render thread will loop through the renderlist, remove tiles flagged as expired and unload their texture from the GPU, and render tiles which are flagged as in render range. The update loop is regulated by a simple delta time implementation. This is done to free the movement speed from the framerate. The movement speed is scaled by the time taken between frames, ensuring that longer frame times does not change the distance traveled.
