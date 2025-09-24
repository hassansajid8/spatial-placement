## 2D Spatial Placement Problem
#### [Hassan Sajid](github.com/hassansajid8) 

### Problem 
See [this](https://hassansajid8.github.io/spatial-placement/) 

### Approach 
Single Iteration Brute Force 

- The algorithm runs only on a single iteration 
- Produces best results when components are sorted in the order:
    - MIKROBUS 
    - USBCONNECTOR 
    - MICROCONTROLLER
    - CRYSTAL 
- Iterates through each component once
- Generates all possible valid positions (candidates) 
- Chooses the position which produces the least COM score (distance between COM and center of board)

- The code is a bit messy and unoptimized, but works well and falls within all required constraints 

- Complexities
    - Time Complexity: Worst Case - O(n<sup>2</sup>) for n components and fixed board size
    - Space Complexity: O(n) for n components and fixed board size 

- For 5 components, the algorithm takes about ~30 ms for producing results






