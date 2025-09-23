from dataclasses import dataclass 
from typing import Optional, Tuple
from enum import Enum 
import math 
import time 

import matplotlib.pyplot as plt
import matplotlib.patches as patches

class CompType(Enum):
    MICROCONTROLLER = 1
    USBCONNECTOR = 2
    MICROBUS = 3
    CRYSTAL = 4
    KEEP_OUT_ZONE = 5

@dataclass 
class Component:
    w: int 
    h: int 
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
            case CompType.KEEP_OUT_ZONE:
                self.edge = False 
                self.KOZ = None 
                self.proximity = None 
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
    min_com = None 
    for c in components:
        candidates = gen_candidates(c, board_dims)
        if(len(candidates) > 0):
            min_com = min(candidates, key= lambda cand: score_candidate((cand[0], cand[1], c.h if cand[2] else c.w, c.w if cand[2] else c.h), board_dims, placed))
            if(min_com[2]): 
                c.w, c.h = c.h, c.w 
            place(c, (min_com[0], min_com[1]))
            if(c.KOZ != None and min_com[3] != None):
                koz_x, koz_y, koz_w, koz_h = min_com[3] 
                koz_c = Component(koz_w, koz_h, CompType.KEEP_OUT_ZONE)
                place(koz_c, (koz_x, koz_y))
#        else:
#            print("No possible positions found for component type " + str(c.comptype))
#            print("Exiting program...")
#            exit()

    for c in placed:
        curr_com = get_com(board_dims, placed)
        if not c.edge:
            for shift in [(1,0), (-1,0), (0,1), (0,-1)]:
                trial = (c.x+shift[0], c.y+shift[1], c.w, c.h)
                if (in_bounds(trial, board_dims) and check_overlap_comp(trial, [p for p in placed if p!=c])):
                    if(see_com(trial, board_dims, [p for p in placed if p!=c]) < curr_com):
                       c.x = c.x+shift[0] 
                       c.y = c.y+shift[1]


# generate possible position candidates for a component given the constraints 
def gen_candidates(c: Component, board_dims: Tuple[int]) -> list:
    candidates: list[Tuple] = []

    # if 0 constraints, prefer central placement 
    if (c.active_constraints() == 0):
        cx = board_dims[0]//2 
        cy = board_dims[1]//2 
        
        if(check_overlap_comp((cx, cy, c.w, c.h), placed)): # center is unoccupied
            candidates.append((cx - c.w//2, cy - c.h//2, False))
        elif (check_overlap_comp((cx, cy, c.h, c.w), placed)):
            candidates.append((cx - c.h//2, cy - c.w//2, True))
        else: # center is occupied, generate candidates around the center 
            angles = [0, 90, 180, 270, 45, 135, 225, 315]
            r = 6
            found = 0

            while(found <= 0):
                for a in angles:
                    rad = math.radians(a)
                    px = int(cx + (r*math.cos(rad)))
                    py = int(cy + (r*math.sin(rad)))

                    if (check_overlap_comp((px, py, c.w, c.h), placed) and in_bounds((px, py, c.w, c.h), board_dims)):
                        candidates.append((px, py, False, None)) 
                        found += 1
                r += 1 
        return candidates

        
    # edge constraint 
    # generate candidates for each edge with both orientations
    if(c.edge):
        edges = [
                ("left", [(0, py) for py in range(board_dims[1]+1)]),
                ("right", [(board_dims[0] - c.w, py) for py in range(board_dims[1]+1)]),
                ("bottom", [(px, 0) for px in range(board_dims[0]+1)]),
                ("top", [(px, board_dims[0] - c.h) for px in range(board_dims[0]+1)])
            ]

        if(c.KOZ != None):
            koz_w, koz_h = c.KOZ 
            for edge, positions in edges:
                for px, py in positions:
                    if not(in_bounds((px, py, c.w, c.h), board_dims)): pass 
                    else:
                        width = koz_w 
                        height = koz_h 
                        kx = px 
                        ky = py 
                        if(edge == "left"): # x = 0
                            width = c.w + koz_h 
                            height = koz_w 
                            ky = (py + c.h/2) - koz_w/2 
                            kx = px 
                        elif (edge == "right"): # x = max - w 
                            width = c.w + koz_h 
                            height = koz_w 
                            kx = px - koz_h 
                            ky = (py + c.h/2) - koz_w/2 
                        elif (edge == "bottom"): # y = 0
                            width = koz_w 
                            height = c.h + koz_h 
                            ky = py 
                            kx = (px + c.w/2) - koz_w/2  
                        elif (edge == "top"): # y = max - h 
                            width = koz_w 
                            height = c.h + koz_h 
                            ky = py - koz_h 
                            kx = (px + c.w/2) - koz_w/2 

                        if(check_overlap_comp((kx, ky, width, height), placed)): 
                            candidates.append((px, py, False, (kx, ky, width, height)))
                                                  
        else:
            for _, positions in edges:
                for px, py in positions:
                    if not (in_bounds((px, py, c.w, c.h), board_dims)): pass 
                    else: 
                        if(check_overlap_comp((px, py, c.w, c.h), placed)):
                            if (c.parallel != None):
                                par_comps = [comp for comp in placed if comp.comptype == c.parallel]
                                if (len(par_comps) == 0): candidates.append((px, py, False, None))
                                else:
                                    for comp in par_comps:
                                        if not (c.w == comp.w or c.h == comp.h): pass 
                                        else:
                                            if(px == 0 and comp.x + comp.w == board_dims[0]): candidates.append((px, py, False, None))
                                            if (px + c.w == board_dims[0] and comp.x == 0): candidates.append((px, py, False, None))
                                            if (py == 0 and comp.y + comp.h == board_dims[1]): candidates.append((px, py, False, None))
                                            if (py + c.h == board_dims[1] and comp.y == 0): candidates.append((px, py, False, None))
                            else:
                                candidates.append((px, py, False, None))

    # proximity constraint 
    if(c.proximity != None):
        
        for px in range(board_dims[0]):
            for py in range(board_dims[1]):
                if not (in_bounds((px, py, c.w, c.h), board_dims)): pass 
                else:
                    if(check_overlap_comp((px, py, c.w, c.h), placed)):
                        cx = px + c.w/2 
                        cy = py + c.h/2

                        for comp in [p for p in placed if p.comptype == c.proximity]:
                            comp_cx = comp.x + comp.w/2 
                            comp_cy = comp.y + comp.h/2 

                            if(distance((cx, cy), (comp_cx, comp_cy)) <= 10):
                                candidates.append((px, py, False, None))



    return candidates 

# calculate com score 
def get_com(board_dims: Tuple[int], placements: list[Component]):
    board_center = (board_dims[0]/2, board_dims[1]/2)
    sum_x = 0 
    sum_y = 0 
    length = 0 
    for c in placements: 
        if(c.comptype == CompType.KEEP_OUT_ZONE): pass 
        else:
            center = get_center(c)
            sum_x += center[0] 
            sum_y += center[1] 
            length += 1 

    com_x = sum_x / length 
    com_y = sum_y / length 
    
    return distance((com_x, com_y), board_center)


# calculate COM distance for a candidate 
def see_com(rect: Tuple[int], board_dims: Tuple[int], placements: list[Component]):
    board_center = (board_dims[0]/2, board_dims[1]/2)
    x, y, w, h = rect 
    length = 0
    sum_x = 0 
    sum_y = 0 
    for c in placements:
        if(c.comptype == CompType.KEEP_OUT_ZONE): pass 
        else: 
            center = get_center(c) 
            sum_x += center[0]
            sum_y += center[1]
            length += 1 
    sum_x += x+w/2 
    com_x = sum_x / (length+1)

    sum_y += y+h/2 
    com_y = sum_y / (length+1) 

    return distance((com_x, com_y), board_center)  

# calculate score for a candidate 
def score_candidate(cand, board_dims, placed):
    com_dist = see_com(cand, board_dims, placed)

    cx = cand[0] + cand[2]/2 
    cy = cand[1] + cand[3]/2 
    dist_to_center = distance((cx, cy), (board_dims[0]/2, board_dims[1]/2))
    return com_dist + 0.2 * dist_to_center 

# global constraints checks

def in_bounds(rect: Tuple, board_dims: Tuple):
    x, y, w, h = rect 
    bx, by = board_dims 
    return (x >= 0 and y >= 0 and
                x + w <= bx and 
                y + h <= by)

def check_overlap_comp(point, placements: list):
    x, y, w, h = point 
    for i in range(len(placements)):
        c = placements[i]
        if not (x + w < c.x or x > c.x + c.w or y + h < c.y or y > c.y + c.h):
            return False
    return True


def place(c: Component, point: Tuple):
    print("Placing " + str(c.comptype) + " at " + str(point))
    x, y = point

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
    

def visualize(placements: list[Component]):
    fig, ax = plt.subplots()
    ax.set_xlim(0, 50)
    ax.set_ylim(0, 50)

    for c in placements:
        # set color 
        clr = 'b'
        alpha = 1
        if (c.comptype == CompType.MICROCONTROLLER): clr = 'b'
        elif (c.comptype == CompType.CRYSTAL): clr = 'y'
        elif (c.comptype == CompType.MICROBUS): clr = 'r'
        elif (c.comptype == CompType.USBCONNECTOR): clr = 'g'
        elif (c.comptype == CompType.KEEP_OUT_ZONE):
            clr = 'g'
            alpha = 0.5
        # Create the Rectangle patch
        rect = patches.Rectangle(
            (c.x, c.y),
            c.w,
            c.h,
            linewidth=1,
            edgecolor=clr,
            facecolor=clr,
            alpha=alpha
        )

        if(c.comptype == CompType.MICROCONTROLLER):
            cx, cy = get_center(c)
            circ = patches.Circle(
                    (cx, cy),
                    10,
                    linewidth=1,
                    edgecolor='b',
                    facecolor='b',
                    alpha=0.5
            )
            ax.add_patch(circ)

        # Add the patch to the axes
        ax.add_patch(rect)

#    ax.invert_yaxis()
    ax.tick_params(top=True, labeltop=True, bottom=False, labelbottom=False)
    plt.grid()
    plt.show()

if __name__ == "__main__":
    components = []
    
    components.append(Component(5, 15, CompType.MICROBUS))
    components.append(Component(5, 5, CompType.MICROCONTROLLER))
    components.append(Component(5, 5, CompType.USBCONNECTOR))
    components.append(Component(5, 15, CompType.MICROBUS))
    components.append(Component(5, 5, CompType.CRYSTAL))

#    components.sort(key=lambda obj: obj.active_constraints())

    start_time = time.time()
    algo(components, (50, 50))
    end_time = time.time()
    print(f"Algo execution time : {(end_time - start_time):.4f} seconds")

    visualize(placed)

    with open("output.txt", 'w') as file:
        mb_count = 0 
        for p in placed: 
            name = ""
            if(p.comptype == CompType.MICROCONTROLLER):
                name = "MICROCONTROLLER" 
            elif (p.comptype == CompType.USBCONNECTOR):
                name = "USB_CONNECTOR"
            elif (p.comptype == CompType.CRYSTAL):
                name = "CRYSTAL"
            elif (p.comptype == CompType.MICROBUS):
                mb_count += 1 
                name = "MIKROBUS_CONNECTOR_" + str(mb_count)
            
            if not (p.comptype == CompType.KEEP_OUT_ZONE):
                file.write(f"{name} {p.x} {p.y} {p.w} {p.h}\n")

                

