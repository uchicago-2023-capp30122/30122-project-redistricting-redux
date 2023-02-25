'''
All functions in this file by: Matt Jackson

Special thanks to Ethan Arsht for advice on mapwide_pop_swap
'''
import pandas as pd
import geopandas as gpd
import numpy as np
import random 
import re
import time
from datetime import datetime
import matplotlib as plt
from ast import literal_eval
from stats import population_sum, blue_red_margin, target_dist_pop, metric_area, population_density #not sure i did this relative directory right

def startup_2018(init_neighbors=False):
    '''
    Get the GA 2018 data ready to do things with.
    Inputs:
        -none
    Returns (geopandas GeoDataFrame): df for 2018 Georgia OpenPrecincts
    '''
    print("Importing Georgia 2018 precinct shapefile data...")
    fp = "openprecincts_ga_2018/2018Precincts.shp"
    ga_data = gpd.read_file(fp)
    print("Georgia 2018 shapefile data imported")
    if init_neighbors:
        print("Calculating district neighbors:")
        set_precinct_neighbors(ga_data)
        print("District neighbors calculated")
    ga_data['dist_id'] = None #use .isnull() to select all of these

    return ga_data

def startup():
    '''
    Get the GA 2020 data ready to do things with.
    Generalize to other states when API call becomes functional.
    Inputs:
        -none (for now, give it a state or state postal code abbrev later)
    Returns (geopandas GeoDataFrame): 
    '''
    #TODO: implement
    pass

###DRAWING-RELATED FUNCTIONS###

def clear_dist_ids(df):
    '''
    Clears off any district IDs that precincts may have been assigned in the
    past. Call this between calls to any map-drawing function.
    Inputs:
        df (geopandas GeoDataFrame)
    Returns: None, modifies GeoDataFrame in-place
    '''
    df['dist_id'] = None

def set_precinct_neighbors(df):
    '''
    Creates a list of neighbors (adjacency list) for each precinct/VTD whose 
    geometry is in the GeoDataFrame.
    Takes about 80-90 seconds for the Georgia 2018 precinct map, or about .03
    seconds per precinct.

    Inputs:
        -df (GeoPandas GeoDataFrame)

    Returns: None, modifies df in-place
    '''
    #Inspired by:
    #https://gis.stackexchange.com/questions/281652/finding-all-neighbors-using-geopandas
    df['neighbors'] = None
    
    for index, row in df.iterrows():
        neighbors = np.array(df[df.geometry.touches(row['geometry'])].loc_prec)
        #maybe there's a way to update neighbors for all the neighbors this one finds too? to speed up/reduce redundant calcs?
        overlap = np.array(df[df.geometry.overlaps(row['geometry'])].loc_prec)
        if len(overlap) > 0:
            neighbors = np.union1d(neighbors, overlap)
        #If you convert to tuple here, later procedures to find available neighbors can use sets instead of lists
        #(np.array is an unhashable type)
        df.at[index, 'neighbors'] = neighbors
        if index % 100 == 0:
            print(f"Neighbors for precinct {index} calculated")
    
    print("Saving neighbors list to csv so you don't have to do this again...")
    df['neighbors'].to_csv('test_dfs/ga_2018_neighbors.csv')


def affix_neighbors_list(df, neighbor_filename):
    '''
    Affix an adjacency list of neighbors to the appropriate csv.
    Input:
        -df(geopandas GeoDataFrame): precinct/VTD-level data for a state
        -neighbor_filename (str): name of file where neighbors list is
    '''

    #2018 Open Precincts neighbors filename: "test_dfs/ga_2018_neighbors.csv"
    #do some exception/assertion checks: make sure length of neighbor list matches df
    #also, maybe make sure it's not somehow sorted so as to make the list in the wrong order?
    neighbor_csv = pd.read_csv(neighbor_filename)
    neighbor_list = neighbor_csv['neighbors'] #this comes in as a string, has to be list-ified
    #deserialize, TODO: use re to make this neater
    df['neighbors'] = neighbor_list
    df['neighbors'] = df['neighbors'].apply(lambda x: np.array(literal_eval(x.replace("\n", "").replace("' '", "', '")), dtype=object))
    #this doesn't work exactly right on loc_precs; hopefully GEOID20 is standard enough that it works on it
    #i think it's because the commas and single quotes mess stuff up

def draw_into_district(df, precinct, id):
    '''
    Assigns a subunit of the state (currently, voting precinct; ideally, census
    block) to a district. The district is a property of the row of the df, 
    rather than a spatially joined object, at least for now.
    Will get called repeatedly by district drawing methods.

    Inputs:
        -df (GeoPandas GeoDataFrame):
        -precinct(str): ID of the precinct to find and draw into district.
        -id (anything, but probably int): Name or number of the district to be
        drawn into.

    Returns: Nothing, modifies df in-place
    '''
    df.loc[df['loc_prec'] == precinct, 'dist_id'] = id


def draw_chaos_district(df, target_pop, id, curr_precinct=None):
    '''
    Draw a random district. Select a random starting precinct, use draw_into_district
    to give it a dist_id, then repeatedly call draw_into_district on random
    neighbors of precincts already in the district being drawn.

    Terminates if the district reaches a target population value, or if there
    are no eligible empty neighboring precincts to keep drawing into.

    Inputs:
        -df (geopandas GeoDataFrame): 
        -target-pop (int): target population of each district. When drawing a 
        state map, this will be 1/n, where n is the total population of the state
        as measured in the data.
        -id (any, usually int): The label to give precincts within the district.
        For a state map, this will usually be 1 for the first district drawn,
        2 for the second, etc.
        -curr_precinct (str): the current precinct being drawn into. When function
        is initialized without this keyword argument, it selects an empty precinct
        at random.
    '''
    if population_sum(df, 'tot', district=id) >= target_pop:
        print("Target population met or exceeded. Ending district draw")
        return None #"break"

    if curr_precinct is None:
        neighboring_dists = {None}
        #Select a random precinct to start at. It should be empty and
        #have neighbors that are all also empty.
        while len(neighboring_dists) != 0:
            curr_index = random.randint(0, len(df)-1)
            curr_precinct = df.loc[curr_index, 'loc_prec']
            neighboring_dists = find_neighboring_districts(df, df.loc[curr_index, 'neighbors'],
                                                       include_None=False)
            #time.sleep(0.5)
        print(f"Starting at: {curr_precinct}")
        #time.sleep(1)

    else: 
        curr_index = df.index[df['loc_prec'] == curr_precinct].tolist()[0]
        print(f"We continue with: {curr_precinct}")

    #if df.loc[df.loc_prec==curr_precinct,'dist_id'].item() is None:
    if df.loc[curr_index, 'dist_id'] is None:
        #print(f"Now drawing {curr_precinct} into district")
        draw_into_district(df, curr_precinct, id)
        print(f"Current district population: {population_sum(df, 'tot', district=id)}")

    all_neighbors = df.loc[curr_index, 'neighbors']
    #print(all_neighbors)
    #Indexing code inspired by:
    #https://stackoverflow.com/questions/21800169/python-pandas-get-index-of-rows-where-column-matches-certain-value
    #TODO: consider helperizing and/or redoing as an elegant list comprehension
    allowed_neighbors = []
    for nabe in all_neighbors:
        nabe_index = df.index[df['loc_prec'] == nabe].tolist()
        #print(nabe, nabe_index)
        if df.loc[nabe_index[0], 'dist_id'] is None:
            allowed_neighbors.append(nabe)
    #print(allowed_neighbors)
    #Handle case where there are no available neighbors to draw into
    if len(allowed_neighbors) == 0:
        print("No valid neighbors to draw into! Handling error case...")
 
        dist_so_far = [] + list(df[df.dist_id == id]['loc_prec'])

        #handle if there are no valid neighbors and it's the first precinct for a new district
        #This should never trigger now that starting precinct must have empty neighbors.
        # if dist_so_far is None or len(dist_so_far) == 0:
        #     print("It looks like you can't start drawing here. Restarting somewhere else...")
        #     draw_into_district(df, curr_precinct, None) #undo initial draw
        #     draw_chaos_district(df, target_pop, id)

        #handle the error where there are no neighbors of *any* point in district
        #This shouldn't print multiple times for one district, and yet it sometimes prints
        #two or three times
        if len(all_allowed_neighbors_of_district(df, id)) == 0:
            print("It is impossible to continue drawing a contiguous district. Stopping")
            time.sleep(0.2)
            return None

        #pick a neighbor that is guaranteed to be empty and allowed
        unstick_precinct = random.choice(all_allowed_neighbors_of_district(df, id))
        print(f"Trying again with {unstick_precinct} as resumption point")
        #jumps to that precinct and tries again
        draw_chaos_district(df, target_pop, id, curr_precinct=unstick_precinct)
    else:
    #select a neighbor at random and call this function again 
    #https://stackoverflow.com/questions/306400/how-can-i-randomly-select-an-item-from-a-list
        next_precinct = random.choice(allowed_neighbors)
        draw_chaos_district(df, target_pop, id, curr_precinct=next_precinct)


def all_allowed_neighbors_of_district(df, id):
    '''
    Ascertain if there are any allowed neighbors anywhere for a district. 
    If this returns a list of length 0, it is impossible to keep drawing a 
    contiguous district.
    '''
    nabe_set = set()
    nabes_so_far = list(df[df.dist_id == id]['neighbors']) #use np.union1d and set here
    for array in nabes_so_far:
        for nabe in array:
            nabe_set.add(nabe)
    #print(nabe_set)

    #helperize this
    allowed_neighbors = []
    for nabe in nabe_set:
        nabe_index = df.index[df['loc_prec'] == nabe].tolist()
        #print(nabe, nabe_index)
        if df.loc[nabe_index[0], 'dist_id'] is None:
            allowed_neighbors.append(nabe)

    return allowed_neighbors

def draw_chaos_state_map(df, num_districts, seed=2023, clear_first=True, export=False):
    '''
    Uses draw_chaos_district() to draw a map of random districts of equal
    population for the whole state.
    FINISH DOCSTRING

    Inputs:
        -df (Geopandas GeoDataFrame): set of precincts or ideally census blocks
        for state
        -num_districts (int): Number of districts to draw (for Georgia, that's 14)
    '''
    if clear_first:
        print("Clearing off previous district drawings, if any...")
        clear_dist_ids(df)
        time.sleep(1)

    random.seed(seed) 
    target_pop = target_dist_pop(df, num_districts)
    for id in range(1, num_districts + 1):
        print(f"Now drawing district {id}...")
        draw_chaos_district(df, target_pop, id)
        time.sleep(0.2)

    #deal with empty space
    print("Filling holes in map...")
    fill_district_holes(df)

    print(district_pops(df))

    #allow for export so df is reproducible
    if export:
        export_df_to_file(df)

### PLOTTING FUNCTIONS ###

def plot_dissolved_map(df, dcol, rcol):
    '''
    Plot a map without pesky precinct lines in it. FINISH DOCSTRING
    '''
    #df = df[['loc_prec', 'G18DGOV', 'G18RGOV', 'tot', 'geometry', 'dist_id', 'raw_margin']]
    #print(df)
    print("Dissolving precincts to full districts...")
    df_dists = df.dissolve(by='dist_id')
    df_dists.reset_index(drop=True)

    df_dists['center'] = df_dists['geometry'].centroid #these points have a .x and .y attribute
    df_dists['point_swing'] = df_dists['raw_margin'].round(3)*100

    df_dists.plot(column='raw_margin', cmap='seismic_r')
    
    #Annotating
    #https://stackoverflow.com/questions/38899190/geopandas-label-polygons
    for idx, row in df_dists.iterrows():
        #TODO: Make font size reasonable, plot truncated floats, perhaps in white
        plt.pyplot.annotate(text=row['point_swing'], 
                            xy=(row['center'].x, row['center'].y), 
                            horizontalalignment='center')
    #for future reference: districts.loc[1]['center'].x, districts.loc[1]['center'].y, districts.loc[1]['raw_margin'].round(2)
    #Why is this map so much redder than the by-precinct one?
    #you want to set vmax to abs(max(df_dists['raw_margin'])), and vmin to negative that, i think
    #so that dead even is always in the middle

    #TODO: Add a legend of dist_ids that doesn't overlap with map

    timestamp = datetime.now().strftime("%m%d-%H%M%S")
    filepath = 'maps/ga_testmap_' + timestamp
    plt.pyplot.savefig(filepath, dpi=300) 
    print(f"District map saved to {filepath}")

def plot_redblue_by_district(df, dcol, rcol, num_dists=14):
    '''
    Outputs a map of the state that color-codes each district by the partisan
    balance of its vote, i.e. dark blue if it overwhelmingly voted for Democrat,
    dark red if it overwhelmingly voted for Republican, and some neutral for if it
    was close to even.
    Call this only AFTER drawing a map of districts.
    FINISH DOCSTRING
    Inputs:
        -df (geopandas DataFrame): 
        -dcol (str): indicates name of geopandas column
        -rcol (str):
        -num_dists (int):
    Outputs:
        -plot as .png file in folder
    '''
    
    df['raw_margin'] = None
    for i in range(1, num_dists+1): #this should be doable on one line vectorized
        df.loc[df.dist_id == i, 'raw_margin'] = blue_red_margin(df, dcol, rcol, i)

    #TODO: figure out how to push legend off map, or maybe turn it into categorical color bar
    df.plot(column='raw_margin', cmap='seismic_r')
    #fig, ax = plt.subplots(1)
    #sm = plt.cm.ScalarMappable(cmap='seismic_r')
    #cbar = fig.colorbar(sm) #all of these extremely basic things from many matplotlib StackOverflow answers fail

    timestamp = datetime.now().strftime("%m%d-%H%M%S")
    filepath = 'maps/ga_testmap_' + timestamp
    plt.pyplot.savefig(filepath, dpi=300) 
    print(f"District map saved to {filepath}")


def get_all_holes(df):
    '''
    Get a dataframe of all precincts that have not yet been drawn into a district.
    Inputs:
        -df(geopandas GeoDataFrame)

    Returns (df object): set of precincts with all their attributes
    '''
    return df.loc[df['dist_id'].isnull()]


def fill_district_holes(df, map_each_step=False):
    '''
    Generate all the holes, then iterate across all holes and do
    something to them.
    Then maybe surround it with a while loop
    FINISH DOCSTRING
    Inputs:
        -df (geopandas GeoDataFrame):
    Returns: None, returns df in-place
    '''
    holes = df.loc[df['dist_id'].isnull()]
    go_rounds = 0
    while len(holes) > 0: 
        go_rounds += 1
        print(f"Starting cleanup go-round number {go_rounds}.")
        holes = df.loc[df['dist_id'].isnull()]
        print(holes.shape)
        for index, hole in holes.iterrows():
            real_dists_ard_hole = find_neighboring_districts(df, hole['neighbors'], include_None=False)
            if len(real_dists_ard_hole) == 1: #i.e. if this borders or is inside exactly one district:
                neighbor_dist_id = int(list(real_dists_ard_hole)[0]) #extract that district id
                #THIS WILL BREAK IF YOU GIVE YOUR DISTRICTS ANY ID OTHER THAN INTEGERS
                #print(f"Now drawing {hole['loc_prec']} into district {neighbor_dist_id}...")
                draw_into_district(df, hole['loc_prec'], neighbor_dist_id)
            elif len(real_dists_ard_hole) >= 2: #i.e. if this could go into one of two other districts
                #a cleaner way to do this might involve finding the neighboring district
                #with least population and always drawing into that, so as to make the
                #pop-swap stuff to come later less onerous.
                #neighbor_pops_dict = {id: population_sum(df, 'tot', id) for id in real_dists_ard_hole}
                #print(neighbor_pops_dict)
                neighbor_dist_id = random.choice(tuple(real_dists_ard_hole)) #pick one at random
                #print(f"drawing into district {neighbor_dist_id} tho")
                draw_into_district(df, hole['loc_prec'], neighbor_dist_id)
        
        if map_each_step:
            print(f"Exporting map for go-round number {go_rounds}...")
            plot_redblue_by_district(df, "G18DGOV", "G18RGOV")
    print("Cleanup complete. All holes in districts filled. Districts expanded to fill empty space.")


def mapwide_pop_swap(df, allowed_deviation=70000):
    '''
    If we're going to get to close-to-even populations, this is the approach
    I think I can do with my current skills.

    Inputs:
        -df (geopandas GeoDataFrame): every precinct should have a dist_id
        -allowed_deviation (int)
    '''
    #QUESTION: Can you iterate geographically rather than by df index?
    #TODO: Figure out how to deal with contiguity issues
    #assert (the dist_id column has no Nones in it)
    target_pop = target_dist_pop(df, n=max(df['dist_id']))
    draws_to_do = []

    for _, precinct in df.iterrows():
        #generate list of precinct neighbors, and list of districts those neighbors are in
        neighboring_dists = find_neighboring_districts(df, precinct['neighbors'])

        if len(neighboring_dists) == 1 and tuple(neighboring_dists)[0] == precinct['dist_id']:
            #this is not on a district border
            pass #is there a way to only iterate through borders upfront? saves a lot of computation time
        else: #if this precinct has neighbors in other districts:

            #get population of this precinct's district
            this_prec_dist_pop = population_sum(df, 'tot', precinct['dist_id'])

            #get current population of each neighboring district with below-target population
            proper_neighbors = {dist : population_sum(df, 'tot', dist) 
                                for dist in neighboring_dists 
                                if dist != precinct['dist_id']
                                and population_sum(df, 'tot', dist) < target_pop}
            if len(proper_neighbors) > 0: #all neighbors are of higher population
                if this_prec_dist_pop > target_pop:
                    #get value from key source: https://www.adamsmith.haus/python/answers/how-to-get-a-key-from-a-value-in-a-dictionary
                    smallest_neighbor = [k for k,v in proper_neighbors.items() if v == min(proper_neighbors.values())][0] #JANK
                    #prepare to reassign THIS precinct's dist_id to that of the least populous underpopulated neighbor
                    draw_to_do = (precinct['dist_id'], precinct['loc_prec'], smallest_neighbor)
                    draws_to_do.append(draw_to_do)

    print("Doing all valid drawings one at a time...")
    for draw in draws_to_do:
        donor_district, precinct, acceptor_district = draw
        #make sure acceptor district isn't too large to be accepting precincts
        #see past commits for more notes re: cyclical behavior
        if population_sum(df, 'tot', acceptor_district) <= target_pop + (allowed_deviation / 2):
            draw_into_district(df, precinct, acceptor_district)

    #TODO: fix any district that is fully surrounded by dist_ids other than its 
    #own (redraw it to match majority dist_id surrounding it)

    print(district_pops(df))

def repeated_pop_swap(df, allowed_deviation=70000, plot_each_step=True, stop_after=99):
    '''Do repeated pop swaps until populations are balanced. Check for fragmentation visually as you go."
    Hardcoded to 14 for now
    '''
    count = 1
    dist_pops = district_pops(df)
    time.sleep(1)
    population_deviation = max(dist_pops.values()) - min(dist_pops.values())
    pop_devs_so_far = []
    while population_deviation >= allowed_deviation:
        if len(pop_devs_so_far) > 5 and pop_devs_so_far[-4:-2] == pop_devs_so_far[-2::]:
            print("It looks like this swapping process is trapped in a cycle. Stopping")
            break
            #might want to add something for a "near-cycle" i.e. same value has shown up 3 times in the last 5 spins
        print(f"Now doing swap cycle #{count}...")
        print("The most and least populous district differ by:")
        print(population_deviation)
        pop_devs_so_far.append(population_deviation)
        time.sleep(1)
        mapwide_pop_swap(df, allowed_deviation)
        if plot_each_step:
            plot_redblue_by_district(df, "G18DGOV", "G18RGOV")
        count += 1
        if count >= stop_after:
            print(f"You've now swapped {count} times. Stopping")
            break
        dist_pops = district_pops(df)
        population_deviation = max(dist_pops.values()) - min(dist_pops.values())
    if population_deviation <= allowed_deviation:
        print("You've reached your population balance target. Hooray!")
    print(f"Population deviation at every step was: \n{pop_devs_so_far}")


def find_neighboring_districts(df, lst, include_None=True):
    '''
    Helperizing this function. Takes in a list of precinct names, and 
    outputs a set of all districts those precincts have been drawn into.
    Inputs:
        -df: geopandas GeoDataFrame
        -lst (NumPy array): list of neighbors as found by df['neighbors']
        -include_None (boolean): Determines whether the returned set includes
        None if some neighbors aren't drawn into districts.
    Returns (set): set of dist_ids
    '''
    dists_theyre_in = set()
    for precinct_name in lst:
        #extract the number of the district of each neighbor.
        dist_its_in = df.loc[df['loc_prec'] == precinct_name, 'dist_id'].iloc[0]
        dists_theyre_in.add(dist_its_in)
    
    if include_None:
        return dists_theyre_in
    else:
        return {i for i in dists_theyre_in if i is not None}


def recapture_orphan_precincts(df):
    '''
    Finds precincts that are entirely disconnected from the bulk of their 
    district and reassigns them to a surrounding district.
    Inputs:
        -df (geopandas GeoDataFrame)
    Returns: None, modifies df in-place 
    '''
    for _, row in df.iterrows():
        neighboring_districts = find_neighboring_districts(df, row['neighbors']) #include_None should be unnecessary
        if row['dist_id'] not in neighboring_districts: 
            print(f"{row['dist_id']} not in {tuple(neighboring_districts)})
            row['dist_id'] = random.choice(tuple(neighboring_districts))
            print(f"It's been reassigned to {row['dist_id']} now")

def results_by_district(df):
    '''
    Compresses the df down to a table of by-district stats, where each row
    represents entire area with one dist_id. e.g. population, racial demographics,
    Dem vote, Rep vote, and margin, for easier calling and plotting .

    Possibly exports as csv for replicability.
    '''
    df = df.drop(['neighbors'])
    df_dists = df.dissolve(by='dist_id', aggfunc=sum)
    df_dists.reset_index(drop=True)
    return df_dists


def district_pops(df):
    '''Outputs the population of the districts from 1 to n'''
    pops_dict = {}
    for i in range(1, max(df.dist_id)+1):
        pops_dict[i] = population_sum(df, 'tot', district=i)
    return pops_dict


if __name__ == '__main__':
    ga_data = startup()
    print("Drawing random map:")
    draw_chaos_state_map(ga_data, 14)
    print("Plotting non-cleaned districts on state map:")
    plot_redblue_by_district(ga_data, "G18DGOV", "G18RGOV")
    print("Cleaning up districts one iteration...")
    fill_district_holes(ga_data)
    print("Plotting cleaned districts on state map for contrast:")
    plot_redblue_by_district(ga_data, "G18DGOV", "G18RGOV")
    print("Clearing districts...")
    clear_dist_ids(ga_data)