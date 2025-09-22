from dataclasses import dataclass 
from typing import Optional, Tuple
from enum import Enum 
import math 

import matplotlib.pyplot as plt
import matplotlib.patches as patches

class CompType(Enum):
    MICROCONTROLLER = 1
    USBCONNECTOR = 2
    MICROBUS = 3
    CRYSTAL = 4

@dataclass 
class Component:
    base_w: int 
    base_h: int 
    edge: bool 
    KOZ: Optional[Tuple]
    proximity: Optional[CompType]
    parallel: Optional[CompType]
    x: Optional[int]
    y: Optional[int]
    placed: bool = False 

    def __init__(self, width, height, comptype):
        self.w = width
        self.h = height
        self.comptype = comptype 
        
        match self.comptype:
            case CompType.MICROCONTROLLER:
                self.edge = False
                self.KOZ = None
                self.proximity = None
                self.parallel = None 
            case CompType.USBCONNECTOR:
                self.edge = True
                self.KOZ = (10, 15)
                self.proximity = None
                self.parallel = None
            case CompType.MICROBUS:
                self.edge = True
                self.KOZ = None 
                self.proximity = None 
                self.parallel = CompType.MICROBUS 
            case CompType.CRYSTAL:
                self.edge = False 
                self.KOZ = None 
                self.proximity = CompType.MICROCONTROLLER 
                self.parallel = None 

    def active_constraints(self) -> int:
        return sum(
                1
                for c in (self.edge, self.KOZ, self.proximity, self.parallel)
                if c not in (False, None)
        )

# helper geometric functions
def get_center(c):
    return (c.x + c.w/2, c.y + c.h/2)

def distance(p1, p2):
    return math.sqrt((p2[0] - p1[0])**2 + (p2[1] - p1[1])**2)

placed: list[Component] = []
occupied_rects = []

def algo(components: list[Component], board_dims: Tuple[int]):

    for c in components:
        candidates = gen_candidates(c, board_dims)
        print("Candidates for " + str(c.comptype) + ": " + str(candidates))
        if(len(candidates) > 0):
            min_com = min(candidates, key= lambda cand: see_com((cand[0], cand[1], c.w, c.h), board_dims, placed))
            print(min_com)
            place(c, min_com)
#        else:
#            print("No possible positions found for component type " + str(c.comptype))
#            print("Exiting program...")
#            exit()


# generate possible position candidates for a component given the constraints 
def gen_candidates(c: Component, board_dims: Tuple[int]) -> list:
    candidates: list[Tuple[int]] = []

    # if 0 constraints, prefer central placement 
    if (c.active_constraints() == 0):
        cx = board_dims[0]//2 
        cy = board_dims[1]//2 
        
        if(check_overlap_comp((cx, cy, c.w, c.h), placed)): # center is unoccupied
            candidates.append((cx - c.w//2, cy - c.h//2))
        else: # center is occupied, generate candidates around the center 
            angles = [0, 90, 180, 270, 45, 135, 225, 315]
            r = 6
            found = 0

            while(found <= 0):
                for a in angles:
                    rad = math.radians(a)
                    px = int(cx + (r*math.cos(rad)))
                    py = int(cy + (r*math.sin(rad)))

                    if (check_overlap_comp((px, py, c.w, c.h), placed)):
                        candidates.append((px - c.w//2, py - c.h//2))
                        found += 1
                r += 2 
        return candidates 

        
    # edge constraint 

    # proximity constraint 

    # parallel constraint

    return candidates 

# calculate COM score for a candidate 
def see_com(rect: Tuple[int], board_dims: Tuple[int], placements: list[Component]) -> int:
    board_center = (board_dims[0]/2, board_dims[1]/2)
    x, y, w, h = rect 
    com_x = sum(get_center(c)[0] for c in placements)
    com_x += x+w/2 
    com_x = com_x / (len(placements)+1)

    com_y = sum(get_center(c)[1] for c in placements)
    com_y += y+h/2 
    com_y = com_y / (len(placements)+1) 

    return distance((com_x, com_y), board_center)  


# global constraints checks

def in_bounds(c, board_dims):
    bx, by = board_dims 
    return not (c.x >= 0 and c.y >= 0 and
                c.x + c.w <= bx and 
                c.y + c.h <= by)

def check_overlap_comp(point, placements: list):
    x, y, w, h = point 
    for i in range(len(placements)):
        c = placements[i]
        if not (x + w <= c.x or x >= c.x + c.w or y + h <= c.y or y >= c.y + c.h):
            return False
    return True


def place(c: Component, point: Tuple):
    print("Placing " + str(c.comptype) + " at " + str(point))
    (x,y) = point

    p1 = (int(x), int(y)) # top left point 
    p2 = (int(x+c.w), int(y)) # top right point 
    p3 = (int(x), int(y+c.h)) # bottom left point 
    p4 = (int(x+c.w), int(y+c.h)) # bottom right point 
    print("\tp1: " + str(p1))
    print("\tp2: " + str(p2))
    print("\tp3: " + str(p3))
    print("\tp4: " + str(p4))

    c.x = x 
    c.y = y 
    occupied_rects.append((c.x, c.y, c.w, c.h))
    placed.append(c)
    

def visualize(rectangles):
    fig, ax = plt.subplots()
    ax.set_xlim(0, 50)
    ax.set_ylim(0, 50)

    for r in rectangles:
        # Get the bottom-left corner and the dimensions
        width = r[2]
        height = r[3]

        # Create the Rectangle patch
        rect = patches.Rectangle(
            (r[0], r[1]),
            width,
            height,
            linewidth=1,
            edgecolor='b'
        )

        # Add the patch to the axes
        ax.add_patch(rect)

    ax.invert_yaxis()
    ax.tick_params(top=True, labeltop=True, bottom=False, labelbottom=False)
    plt.grid()
    plt.show()

if __name__ == "__main__":
    components = []
    
    components.append(Component(5, 5, CompType.USBCONNECTOR))
    components.append(Component(5, 15, CompType.MICROBUS))
    components.append(Component(5, 5, CompType.MICROCONTROLLER))
    components.append(Component(5, 5, CompType.MICROCONTROLLER))
    components.append(Component(5, 5, CompType.MICROCONTROLLER))
    components.append(Component(5, 15, CompType.MICROBUS))
    components.append(Component(5, 5, CompType.CRYSTAL))

    components.sort(key=lambda obj: obj.active_constraints())

    algo(components, (50, 50))

    visualize(occupied_rects)



