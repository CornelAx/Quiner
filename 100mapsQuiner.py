from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.action_chains import ActionChains
from wireframe import Wireframe
from collections import deque
from colorama import Fore,init
import copy
import time,threading

init(autoreset=True)
options = Options()
options.add_argument('--start-maximized')
browser = webdriver.Chrome(options=options)
actions = ActionChains(browser)
cookies_debounce = False
current_map = '1'
debounce = False
solvedGrid = []


def die(): # this function was used for debugging
    while True:
        time.sleep(1)

def sqrt(number):
    return int(pow(number,1/2))

def runBot():
    global solvedGrid
    global debounce
    debounce = False
    solvedGrid = []

    def openBrowser():
        global cookies_debounce
        global current_map

        sel = Wireframe(browser)

        browser.get(f'https://www.queens-game.com/?map=map{current_map}')


        if cookies_debounce == False:
            time.sleep(1)
            cookies_debounce = True
            browser.switch_to.frame(3)
            closeModal = browser.find_element(By.XPATH,"//button[text()='Accept']")
            closeModal.click()
            browser.switch_to.default_content()
            
        grid = sel.getId('grid')
        colors = grid.find_elements(By.CLASS_NAME, 'case')
        return colors




    children = openBrowser()
    #

    colors_array = []
    for i in children:
        color = i.get_attribute('style')

        if not color in colors_array:
            colors_array.append(color)

    colors_grid = []
    for i in range(len(children)):
        for j in range(len(colors_array)):
            if children[i].get_attribute('style') == colors_array[j]:
                colors_grid.append(j)
                break

    pathway = colors_grid

    total_length = len(children)-1



    gridSize = sqrt(len(children))

    matrix = []
    x=[]

    # pathway = [ # This is a test grid, use this if you want to test the bot with console
    #     '1', '1', '1', '4', '3', '3', '3', '3', '3',
    #     '4', '1', '1', '4', '5', '5', '5', '5', '5',
    #     '4', '4', '4', '4', '5', '5', '5', '5', '5',
    #     '4', '4', '4', '4', '5', '5', '5', '5', '5',
    #     '4', '4', '4', '4', '9', '5', '5', '5', '6',
    #     '4', '4', '8', '8', '8', '6', '6', '6', '6',
    #     '4', '8', '8', '8', '8', '6', '6', '6', '6',
    #     '8', '8', '8', '8', '8', '8', '6', '6', '9',
    #     '8', '8', '9', '8', '6', '6', '6', '6', '9'
    # ]
    gridSize = sqrt(len(pathway))
    total_length = len(pathway)
    def setMatrix(matrix,x):
        for i in range(len(pathway)+1):
            if(i % gridSize == 0 and i > 1 ):
                matrix.append(x)
                print(x)
                x = []
            if i == len(pathway):
                break
            x.append(pathway[i])
    #
    setMatrix(matrix,x)
    #
    def printMatrix(grid):
        for i in range(len(grid)):
            val = grid[i]
            if val == 'X':
                print(Fore.GREEN + val, end=' ')
            elif val == 'O':
                print(Fore.RED + val, end=' ')
            else:
                print(val, end=' ')
            
            if (i + 1) % gridSize == 0:
                print()  # Newline at the end of each row

    def findNeighbors(index,gridSize=gridSize,total_length=total_length):
        neighbors = []

        row,col = divmod(index,gridSize)

        directions = [(-1, -1), (-1, 0), (-1, 1),
                    ( 0, -1),          ( 0, 1),
                    ( 1, -1), ( 1, 0), ( 1, 1)]
        
        for dr,dc in directions:
            r,c=row+dr, col + dc
            if 0 <= r < gridSize and 0 <= c < gridSize:
                neighbor_index = r*gridSize + c
                neighbors.append(neighbor_index)

        return neighbors


    def find_color_region(grid,gridSize):
        visited = set()
        regions = []
        for i in range(len(grid)):
            if i in visited:
                continue
            
            color = grid[i]
            region = []
            queue = deque([i])

            while queue:
                current = queue.popleft()
                if current in visited or grid[current] != color:
                    continue
                
                visited.add(current)

                region.append(current)

                for neighbor in findNeighbors(current,gridSize,len(grid)):
                    if neighbor not in visited:
                        queue.append(neighbor)
            
            regions.append(region)

        return regions


    regions =find_color_region(pathway,gridSize)

    def getSmallestRegion(regions):
        smallest_region = min(regions,key=len)

        return smallest_region

    def setOMarkColumn(grid,gridSize,index=0):
        if index >= total_length:
            return grid
        
        grid[index] = 'O'
        index+=gridSize

        setOMarkColumn(grid,gridSize,index)

    def setOMarkRow(grid,_min,_max,index=0):
        if index >= total_length or index > _max:
            return grid


        if index >= _min and index < _max:
            grid[index] = 'O'    
        
        index+=1
        setOMarkRow(grid,_min,_max,index)

    def setOMarkNeighbors(grid,neighbors):
        for i in neighbors:
            grid[i] = 'O'

    def setOMarkRegion(grid,region):
        for i in region:
            grid[i] = 'O'

    foundPositions = []
    def placeQueen(aux_grid,region,index,regions,iteration=0):
        row,col = divmod(index,gridSize)
        grid = aux_grid.copy()
        iterationRegions = copy.deepcopy(regions)
        global debounce
        global solvedGrid

        if iteration == 50:
            return False


        count = 0
        for i in grid:
            if i == 'X':
                count+=1
        
        if count == gridSize:
            return True

        def setOMarkOverall():
            setOMarkColumn(grid,gridSize,col)
            _min = row*gridSize
            _max = _min+gridSize
            setOMarkRow(grid,_min,_max,row)
            setOMarkNeighbors(grid,findNeighbors(index))
            setOMarkRegion(grid,region)
        
        def checkOtherRegions(newRegions):
            for i in range(len(newRegions)):
                if len(newRegions[i]) == 0:
                    print(f'{Fore.YELLOW}⚠️ __Region : {i} is blocked, backtracking...')
                    return False
            
            return True

        def setNewRegions():
            length = len(iterationRegions)
            aux_length = length
            for i in range(length):
                if i == aux_length:
                    break

                region = iterationRegions[i]
                for j in region:
                    if grid[j] == 'X':
                        iterationRegions.remove(region)
                        aux_length -= 1
                        break

            length = len(iterationRegions)
            for i in range(length):
                region = iterationRegions[i]
                aux = []
                for j in region:
                    if grid[j] == 'O':
                        aux.append(j)
                
                for j in aux:
                    iterationRegions[i].remove(j)
                
            print(iterationRegions)
            return iterationRegions

        setOMarkOverall()
        print(f'setting {index} as X')
        grid[index] = 'X'

        newRegions = setNewRegions()
        canRecurse = checkOtherRegions(newRegions)


        if len(newRegions) == 0:
            return True

        smallestRegion = getSmallestRegion(newRegions)
        if canRecurse :
            index=0
            smallestRegion_length = len(smallestRegion)
            iteration+=1
            print(f'{Fore.YELLOW}entering recursion {iteration}')
            for i in range(smallestRegion_length):

                rez = placeQueen(grid,smallestRegion,smallestRegion[index],newRegions,iteration=iteration)
                if rez==False:
                    index+=1

                    if index == smallestRegion_length:
                        return False
                
                if rez == True:
                    if debounce == False:
                        solvedGrid=grid.copy()
                        debounce = True
                    return rez
                print(f'{Fore.YELLOW}Backtrack try #{index}')
        else:
            return False


    smallestRegion = getSmallestRegion(regions)

    def solveFor(index):
        children[index].click()
        # time.sleep(0.2)
        # children[index].click()

    index=0
    REGIONS = regions.copy()
    print(f'_regions : {REGIONS}')
    for i in range(len(smallestRegion)):
        rez = placeQueen(pathway,smallestRegion,smallestRegion[index],REGIONS,0)
        if rez == False:
            index+=1
            print(f'Re-entering in {REGIONS}')
            if index == len(smallestRegion):
                break
        if rez == True:
            pass
    if rez == True:
        print(f'{Fore.LIGHTGREEN_EX}All Queens are placed! VICTORYY')
        for i in range(len(solvedGrid)):
            
            if solvedGrid[i] != 'X' and solvedGrid[i]!='O':
                solvedGrid[i] ='X'
            if solvedGrid[i] =='X' and not solvedGrid[i] in foundPositions:
                print(f'adding {i}')
                foundPositions.append(i)

        
        print(f"Found positions {foundPositions}")
        for i in foundPositions:
            thread = threading.Thread(target=solveFor,args=(i,))
            thread.start()

    printMatrix(solvedGrid)


no_of_maps = 100 # change this if you want to increase/decrease the number of maps
                 # there are only 100 maps on that website
for i in range(no_of_maps):
    current_map = i+1
    runBot()
    time.sleep(0.5) # wait a bit to see the results for each map




