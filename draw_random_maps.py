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
from stats import population_sum, blue_red_margin, target_dist_pop, metric_area, population_density, set_blue_red_diff #not sure i did this relative directory right


def clear_dist_ids(df):
    '''
    Clears off any district IDs that precincts may have been assigned in the
    past. Call this between calls to any map-drawing function.
    Inputs:
        df (geopandas GeoDataFrame)

    Returns: None, modifies GeoDataFrame in-place
    '''
    df['dist_id'] = None

def draw_into_district(df, precinct, id):
    '''
    Assigns a subunit of the state (currently, voting precinct; ideally, census
    block) to a district. The district is a property of the row of the df, 
    rather than a spatially joined object, at least for now.
    Will get called repeatedly by district drawing methods.

    Inputs:
        -df (GeoPandas GeoDataFrame):
        -precinct(str): ID of the precinct to find and draw into district.
        -id (int): Number of the district to be drawn into.

    Returns: Nothing, modifies df in-place
    '''
    df.loc[df['GEOID20'] == precinct, 'dist_id'] = id


def draw_chaos_district(df, target_pop, id, curr_precinct=None):
    '''
    Draw a random district by selecting a random starting precinct at a relatively
    empty spot on the map, use draw_into_district() to give it a dist_id, then 
    move to a random unfilled neighbor, call draw_into_district() on that
    neighbor, and repeat.

    Terminates if the district reaches a target population value, or if there
    are no eligible empty neighboring precincts to keep drawing into (i.e. is
    "trapped" by surrounding precincts that have already been drawn into other
    districts).

    Inputs:
        -df (geopandas GeoDataFrame): state data by precinct/VTD
        -target-pop (int): target population of each district. When drawing a 
        state map, this will be 1/n, where n is the total population of the state
        as measured in df.
        -id (int): The label for the district being drawn (e.g. 1 for the 
        1st district, 2 for the 2nd, etc.
        -curr_precinct (str): name (GEOID20) of the current precinct being drawn 
        into. Function is initialized without this keyword argument, and continues
        by selecting the next precinct to draw and calling itself again with
        that precinct's name in this argument.

    Returns: None, modifies df in-place
    '''
    if population_sum(df, district=id) >= target_pop:
        print("Target population met or exceeded. Ending district draw")
        return None #"break"

    
    if curr_precinct is None:
        neighboring_dists = {None}
        #Select a random precinct to start at. It should be empty and
        #have neighbors that are all also empty.
        curr_index = random.randint(0, len(df)-1)
        while df.loc[curr_index, 'dist_id'] is not None:
            curr_index = random.randint(0, len(df)-1)
        curr_precinct = df.loc[curr_index, 'GEOID20']
        print(f"Trying to start at {curr_precinct}...")
        neighboring_dists = find_neighboring_districts(df, df.loc[curr_index, 'neighbors'],
                                                    include_None=False)
        #time.sleep(0.5)
        print(f"Starting at: {curr_precinct}")
        #time.sleep(1)

    else: 
        curr_index = df.index[df['GEOID20'] == curr_precinct].tolist()[0]
        #print(f"We continue with: {curr_precinct}")

    #if df.loc[df.GEOID20==curr_precinct,'dist_id'].item() is None:
    if df.loc[curr_index, 'dist_id'] is None:
        #print(f"Now drawing {curr_precinct} into district")
        draw_into_district(df, curr_precinct, id)
        print(f"Current district population: {population_sum(df, district=id)}")

    all_neighbors = df.loc[curr_index, 'neighbors']
    #print(all_neighbors)
    #Indexing code inspired by:
    #https://stackoverflow.com/questions/21800169/python-pandas-get-index-of-rows-where-column-matches-certain-value
    #TODO: consider helperizing and/or redoing as an elegant list comprehension
    allowed_neighbors = []
    for nabe in all_neighbors:
        nabe_index = df.index[df['GEOID20'] == nabe].tolist()
        #print(nabe, nabe_index)
        if df.loc[nabe_index[0], 'dist_id'] is None:
            allowed_neighbors.append(nabe)
    #print(allowed_neighbors)

    #Handle case where there are no available neighbors to draw into
    if len(allowed_neighbors) == 0:
        dist_so_far = [] + list(df[df.dist_id == id]['GEOID20'])

        #Handle case where there are no available neighbors of *any* precinct in district
        if len(all_allowed_neighbors_of_district(df, id)) == 0:
            print("It is impossible to continue drawing a contiguous district. Stopping")
            time.sleep(0.2)
            return None
        #pick an empty neighbor of a different precinct in the district
        else:
            #THE BELOW LINE TAKES LONGER AS DISTRICT GROWS. HANGS FOR A NOTICEABLE
            #SECOND OR TWO ONCE DISTRICT IS OVER ~400K PEOPLE. TODO: Improve efficiency
            unstick_precinct = random.choice(all_allowed_neighbors_of_district(df, id))
            print(f"Trying again with {unstick_precinct} as resumption point")
            #jump to that precinct and try again
            draw_chaos_district(df, target_pop, id, curr_precinct=unstick_precinct)
    else:
    #select a neighbor of this precinct at random and call this function again 
    #Inspired by: https://stackoverflow.com/questions/306400/how-can-i-randomly-select-an-item-from-a-list
        next_precinct = random.choice(allowed_neighbors)
        draw_chaos_district(df, target_pop, id, curr_precinct=next_precinct)


def all_allowed_neighbors_of_district(df, id):
    '''
    Ascertain if there are any precincts bordering an in-progress district
    which are empty and available to draw into. If this returns a list of 
    length 0, it is impossible to keep drawing a contiguous district.

    Inputs:
        -df (geopandas GeoDataFrame): state level data by precinct/VTD
        -id (int): dist_id of the district you're investigating

    Returns (list of strings): IDs of available precincts.
    '''
    #idea for np.concatenate: https://stackoverflow.com/questions/28125265/concatenate-numpy-arrays-which-are-elements-of-a-list
    nabe_set = set(np.concatenate(df.loc[df.dist_id == id, 'neighbors'].values))

    #seems to be slower as a set comprehension than as a list comprehension
    allowed_neighbors = [nabe for nabe in nabe_set
                         if df.loc[df.GEOID20 == nabe, 'dist_id'].item() is None]

    return allowed_neighbors


def draw_dart_throw_map(df, num_districts, seed=2023, clear_first=True, map_each_step=False):
    '''
    NEW 3/2/2023! See if we can avoid some of the drama of chaos district draw,
    and make things go faster.
    Start by picking random precincts on the map, as if "throwing a dart" at it,
    to represent starting points of each district.
    Then just call fill_district_holes to expand the map out from each starting
    point until it's full.

    Initial idea of "throwing darts at a map" suggested by office hours 
    conversation with James Turk.

    Inputs:
        -df (Geopandas GeoDataFrame): state data by precinct/VTD
        -num_districts (int): Number of districts to draw (for Georgia, that's 14)
        -seed (int): Seed for random number generation, for replicability
        -clear_first (boolean): Determines whether to erase any dist_id
        assignments already in map. Should not be set to False unless
        debugging.
        -export_to (str): File location to export map district data to when
        drawing is completed. Used for replicability.

    Returns: None, modifies df in-place
    '''
    if clear_first:
        print("Clearing off previous district drawings, if any...")
        clear_dist_ids(df)
        time.sleep(0.1)

    random.seed(seed) 
    
    target_pop = target_dist_pop(df, num_districts)
    print(target_pop)
    time.sleep(1)

    #throw darts
    for id in range(1, num_districts+1):
        print(f"Aiming dart at map for district {id}...")
        curr_index = random.randint(0, len(df)-1)
        while df.loc[curr_index, 'dist_id'] is not None:
            curr_index = random.randint(0, len(df)-1)
        curr_precinct = df.loc[curr_index, 'GEOID20']
        print(f"Throwing dart at {curr_precinct}...")
        draw_into_district(df, curr_precinct, id)

    #expand into area around darts
    holes_left = len(df.loc[df['dist_id'].isnull()])
    go_rounds = 0
    #randomize the order with each go-round so the first district doesn't get
    #really big first, etc.
    expand_order = [i for i in range(1,num_districts+1)]
    holes_by_step = []
    while holes_left > 0: 
        go_rounds += 1
        print(f"Starting expansion go-round number {go_rounds}.")
        if map_each_step:
            print(f"Exporting map prior to go-round number {go_rounds}...")
            plot_redblue_precincts(df, state_postal="TEST")
        holes_left = len(df.loc[df['dist_id'].isnull()])
        holes_by_step.append(holes_left)
        print(f"{holes_left} unfilled districts remain")
        if holes_left == 0:
            break
        if len(holes_by_step) > 2 and holes_by_step[-1] == holes_by_step[-2]:
            print("No more viable holes to fill through dart expansion")
            fill_district_holes(df)
            break
        #randomize which district gets expanded so earlier ones aren't bigger
        #random.shuffle(expand_order) - not sure this is super necessary
        for id in expand_order:
            print(f"Expanding out from dart {id}...")
            allowed = all_allowed_neighbors_of_district(df, id)
            #print(allowed)
            for neighbor in allowed:
            #print(neighbor)
            #print(df.loc[df.GEOID20 == neighbor, 'dist_id'])
                if df.loc[df.GEOID20 == neighbor, 'dist_id'].item() is None:
                    if population_sum(df, district=id) <= target_pop:
                    #print(f"Drawing {neighbor} into district {id}...")
                        draw_into_district(df, neighbor, id)
                    else:
                        print(f"District {id} has hit its target population size")
                        if id in expand_order:
                            expand_order.remove(id)
                            print(f"No longer expanding district{id} in future cycles")
                        break

    print(district_pops(df))

def draw_chaos_state_map(df, num_districts, seed=2023, clear_first=True, export_to=None):
    '''
    Uses draw_chaos_district() to attempt to draw a map of random districts of 
    equal population for the whole state. Is very likely to result in a map
    with extreme population deviation between districts, to be fixed later
    with repeated_pop_swap().

    Inputs:
        -df (Geopandas GeoDataFrame): state data by precinct/VTD
        -num_districts (int): Number of districts to draw (for Georgia, that's 14)
        -seed (int): Seed for random number generation, for replicability
        -clear_first (boolean): Determines whether to erase any dist_id
        assignments already in map. Should not be set to False unless
        debugging.
        -export_to (str): File location to export map district data to when
        drawing is completed. Used for replicability.

    Returns: None, modifies df in-place
    '''
    if clear_first:
        print("Clearing off previous district drawings, if any...")
        clear_dist_ids(df)
        time.sleep(0.1)

    random.seed(seed) 
    target_pop = target_dist_pop(df, num_districts)
    print(f"Drawing {num_districts} districts. Target population per district is {target_pop}")
    time.sleep(1)
    for id in range(1, num_districts + 1):
        print(f"Now drawing district {id}...")
        draw_chaos_district(df, target_pop, id)
        time.sleep(0.2)
        plot_redblue_precincts(df, state_postal="TEST")

    #deal with empty space
    print("Filling holes in map...")
    fill_district_holes(df)

    print(district_pops(df))

    #allow for export so df is reproducible
    if export_to is not None:
        pass #TODO: figure out minimum export and export it as csv
        #probably: GEOID20, dist_id


### MAP CLEANUP FUNCTIONS ###


def get_all_holes(df):
    '''
    Get a dataframe of all precincts that have not yet been drawn into a district.
    Helper for fill_district_holes().
    Inputs:
        -df(geopandas GeoDataFrame): state data by precinct/VTD

    Returns (df object): set of precincts with all their attributes
    '''
    return df.loc[df['dist_id'].isnull()]


def fill_district_holes(df, map_each_step=False):
    '''
    Helper function for draw_chaos_state_map. Determine where the remaining 
    unfilled precincts are across the map, then expand existing districts 
    out into those unfilled precincts (or into the gaps within the districts),
    and iterate until every precinct on the map has a dist_id.

    Inputs:
        -df (geopandas GeoDataFrame): state data by precinct/VTD
        -map_each_step (boolean): debugging parameter that checks how full
        the map has gotten with each iteration by plotting a map after each
        step.

    Returns: None, returns df in-place
    '''
    holes = df.loc[df['dist_id'].isnull()]
    go_rounds = 0
    while len(holes) > 0: 
        go_rounds += 1
        print(f"Starting cleanup go-round number {go_rounds}.")
        holes = df.loc[df['dist_id'].isnull()]
        print(f"({holes.shape[0]} unassigned precincts remaining)")
        for index, hole in holes.iterrows():
            real_dists_ard_hole = find_neighboring_districts(df, hole['neighbors'], include_None=False)
            if len(real_dists_ard_hole) == 1: #i.e. if this borders or is inside exactly one district:
                neighbor_dist_id = list(real_dists_ard_hole)[0] 
                draw_into_district(df, hole['GEOID20'], neighbor_dist_id)
            elif len(real_dists_ard_hole) >= 2: #i.e. if this could go into one of two other districts
                #TODO: Make this find the neighboring district with least population 
                #and always draw into that, to make upcoming pop-swap less onerous
                neighbor_dist_id = random.choice(tuple(real_dists_ard_hole)) #pick one at random
                draw_into_district(df, hole['GEOID20'], neighbor_dist_id)
        
        if map_each_step:
            print(f"Exporting map for go-round number {go_rounds}...")
            plot_redblue_precincts(df)

    print("Cleanup complete. All holes in districts filled. Districts expanded to fill empty space.")
    print(district_pops(df))

def mapwide_pop_swap(df, allowed_deviation=70000):
    '''
    Iterates through the precincts in a state with a drawn district map and 
    attempts to balance their population by moving  precincts from overpopulated
    districts into underpopulated ones.

    This function is VERY SLOW

    Inputs:
        -df (geopandas GeoDataFrame): state data by precinct/VTD. Every precinct 
        should have a dist_id assigned before calling this function.
        -allowed_deviation (int): Largest allowable difference between the 
        population of the most populous district and the population of the 
        least populous district.

    Returns: None, modifies df in-place
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
            this_prec_dist_pop = population_sum(df, district=precinct['dist_id'])

            #get current population of each neighboring district with below-target population
            proper_neighbors = {dist : population_sum(df, district=dist) 
                                for dist in neighboring_dists 
                                if dist != precinct['dist_id']
                                and population_sum(df, district=dist) < target_pop}
            if len(proper_neighbors) > 0: #all neighbors are of higher population
                if this_prec_dist_pop > target_pop:
                    #get value from key source: https://www.adamsmith.haus/python/answers/how-to-get-a-key-from-a-value-in-a-dictionary
                    smallest_neighbor = [k for k,v in proper_neighbors.items() if v == min(proper_neighbors.values())][0] #JANK
                    #prepare to reassign THIS precinct's dist_id to that of the least populous underpopulated neighbor
                    draw_to_do = (precinct['dist_id'], precinct['GEOID20'], smallest_neighbor)
                    draws_to_do.append(draw_to_do)

    print("Doing all valid drawings one at a time...")
    for draw in draws_to_do:
        donor_district, precinct, acceptor_district = draw
        #make sure acceptor district isn't too large to be accepting precincts
        #see past commits for more notes re: cyclical behavior
        if population_sum(df, district=acceptor_district) >= target_pop + (allowed_deviation / 2):
            print("Skipping a draw because target district is already too big")
        elif population_sum(df, district=donor_district) <= target_pop - (allowed_deviation / 2):
            print("Skipping a draw because donor district is too small to give up more people")
        else:
            draw_into_district(df, precinct, acceptor_district)

    #fix any district that is fully surrounded by dist_ids other than its 
    #own (redraw it to match majority dist_id surrounding it)
    print("Reassigning districts 'orphaned' by swapping process...")
    recapture_orphan_precincts(df)

    print(district_pops(df))


def population_deviation(df):
    '''
    Obtain the deviation between the district with highest population
    and the district with lowest population. 
    '''
    dist_pops = district_pops(df)
    if len(dist_pops) < 2:
        return None
    pop_dev = max(dist_pops.values()) - min(dist_pops.values())
    return pop_dev

def repeated_pop_swap(df, allowed_deviation=70000, plot_each_step=False, stop_after=99):
    '''Repeatedly calls mapwide_pop_swap() until populations of districts are 
    within allowable deviation range. Terminates early if the procedure is 
    unable to equalize district populations any further. 
    
    Inputs:
        -df (geopandas GeoDataFrame): state-level precinct/VTD data. Should
        have dist_ids assigned to every precinct.
        -allowed_deviation (int): Largest allowable difference between the 
        population of the most populous district and the population of the 
        least populous district.
        -plot_each_step (boolean): if True, tells program to export a map
        of each iteration of mapwide_pop_swap(), to check for district 
        fragmentation and/or inspect progress or cycles visually.
        -stop_after (int): manual number of steps to stop after if procedure
        hasn't yet terminated.

    Returns: None, modifies df in place
    '''
    count = 1

    pop_devs_so_far = []
    while population_deviation(df) >= allowed_deviation:
        if len(pop_devs_so_far) > 5 and pop_devs_so_far[-4:-2] == pop_devs_so_far[-2::]:
            print("It looks like this swapping process is trapped in a cycle. Stopping")
            break
            #might want to add something for a "near-cycle" i.e. same value has shown up 3 times in the last 5 spins
        print(f"Now doing swap cycle #{count}...")
        print("The most and least populous district differ by:")
        print(population_deviation(df))
        pop_devs_so_far.append(population_deviation(df))
        time.sleep(1)
        print("Finding valid precincts to swap... This could take a few seconds...")
        mapwide_pop_swap(df, allowed_deviation)
        if plot_each_step:
            plot_redblue_precincts(df)
        count += 1
        if count > stop_after:
            print(f"You've now swapped {count} times. Stopping")
            break
        dist_pops = district_pops(df)
    if population_deviation(df) <= allowed_deviation:
        print("You've reached your population balance target. Hooray!")
    print(f"Population deviation at every step was: \n{pop_devs_so_far}")


def find_neighboring_districts(df, lst, include_None=True):
    '''
    Takes in a list of precinct names, and outputs a set of all districts 
    those precincts have been drawn into.

    Inputs:
        -df: geopandas GeoDataFrame
        -lst (NumPy array): list of neighbors, as found by calling
         df['neighbors']
        -include_None (boolean): Determines whether the returned set includes
        None if some neighbors aren't drawn into districts.

    Returns (set): set of dist_ids
    '''
    dists_theyre_in = set()
    for precinct_name in lst:
        #extract the number of the district of each neighbor.
        dist_its_in = df.loc[df['GEOID20'] == precinct_name, 'dist_id'].iloc[0]
        dists_theyre_in.add(dist_its_in)
    
    if include_None:
        return dists_theyre_in
    else:
        return {i for i in dists_theyre_in if i is not None}


def recapture_orphan_precincts(df):
    '''
    Finds precincts that are entirely disconnected from the bulk of their 
    district and reassigns them to a surrounding district.
    This is very slow. TODO: Find a way to isolate the rows worth iterating over 
    first, ideally vectorized, and then just iterate across those

    Inputs:
        -df (geopandas GeoDataFrame): state level precinct/VTD data. Should
        have dist_id assigned for every precinct.

    Returns: None, modifies df in-place 
    '''
    #make a complex boolean to filter the df and then just iterate on that

    #It seems like this is happening way too often
    num_orphans_reclaimed = 0 #debugging
    for idx, row in df.iterrows():
        neighboring_districts = find_neighboring_districts(df, row['neighbors']) #include_None should be unnecessary
        if row['dist_id'] not in neighboring_districts: 
            print(f"Reclaiming orphan precinct {row['GEOID20']}...")
            draw_into_district(df, row['GEOID20'], random.choice(tuple(neighboring_districts)))
            num_orphans_reclaimed += 1
    print(num_orphans_reclaimed)


### PLOTTING FUNCTIONS ###

def plot_GEOID20s(df):
    '''
    I need a giant blank map of every precinct with its GEOID20 on it for debugging
    purposes.
    Inputs:
        -df(geopandas GeoDataFrame)
    Returns: None
    '''
    df['center'] = df['geometry'].centroid #these points have a .x and .y attribute

    df.plot(edgecolor="black", linewidth=0.1)
    
    #Annotating
    #https://stackoverflow.com/questions/38899190/geopandas-label-polygons
    for idx, row in df.iterrows():
        #TODO: Make font size reasonable, plot truncated floats, perhaps in white
        plt.pyplot.annotate(text=row['GEOID20'], 
                            xy=(row['center'].x, row['center'].y), 
                            horizontalalignment='center', fontsize=0.5)

    timestamp = datetime.now().strftime("%m%d-%H%M%S")
    filepath = f'maps/GEOID_testmap_' + timestamp
    plt.pyplot.savefig(filepath, dpi=600) 
    print(f"District map saved to {filepath}")
    plt.pyplot.close()

def plot_dissolved_map(df, state_postal, dcol="G20PREDBID", rcol="G20PRERTRU", export_to=None):
    '''
    Plot a map that dissolves precinct boundaries to show districts as solid
    colors based on their vote margin. Displays it on screen if user's 
    device allows for that.

    Inputs:
        -df (geopandas GeoDataFrame): state precinct/VTD-level data, with 
        polygons
        -state_postal (str of length 2)
        -dcol (str): Name of column that contains Democratic voteshare data
        (i.e. estimated number of votes cast for Joe Biden in the precinct in
        the November 2020 presidential election)
        -rcol (str): Name of the column that contains Republican voteshare data
        (i.e. estimated number of votes cast for Donald Trump in the precinct
        in the November 2020 presidnetial election)
        -export_to (str or None): TODO: location to export the map image to.

    Returns: None, displays plot on-screen and saves image to file
    '''
    print("Dissolving precincts to full districts...")
    df_dists = df.dissolve(by='dist_id', aggfunc=sum)
    df_dists.reset_index(drop=True)
    set_blue_red_diff(df_dists)
    #will cause a ZeroDivisionError if any districts are exactly tied
    df_dists['raw_margin'] = (df_dists["G20PREDBID"] - df_dists["G20PRERTRU"]) / (df_dists["G20PREDBID"] + df_dists["G20PRERTRU"])

    df_dists['center'] = df_dists['geometry'].centroid #these points have a .x and .y attribute
    df_dists['point_swing'] = round(df_dists['raw_margin']*100, 2)

    df_dists.plot(column='raw_margin', cmap='seismic_r', vmin=-.6,
                                                         vmax=.6)
    
    #Annotating
    #https://stackoverflow.com/questions/38899190/geopandas-label-polygons
    for idx, row in df_dists.iterrows():
        #TODO: Make font size reasonable, plot truncated floats, perhaps in white
        plt.pyplot.annotate(text=row['point_swing'], 
                            xy=(row['center'].x, row['center'].y), 
                            horizontalalignment='center', fontsize=4)

    #TODO: Add a legend of dist_ids that doesn't overlap with map

    timestamp = datetime.now().strftime("%m%d-%H%M%S")
    filepath = f'maps/{state_postal}_testmap_' + timestamp
    plt.pyplot.savefig(filepath, dpi=300) 
    print(f"District map saved to {filepath}")
    plt.pyplot.close()

def plot_redblue_precincts(df, state_postal="", dcol="G20PREDBID", rcol="G20PRERTRU", num_dists=14):
    '''
    Plot a map that color-codes each precinct by the partisan margin of the vote
    in the district it's part of, i.e. dark blue if it largely voted Democratic,
    dark red if it overwhelmingly voted Republican, and white if it was close to even.

    Inputs:
        -df (geopandas DataFrame): state data by precincts/VTDs, with polygons
        -state_postal (str length 2)
        -dcol (str): Name of column that contains Democratic voteshare data
        (i.e. estimated number of votes cast for Joe Biden in the precinct in
        the November 2020 presidential election)
        -rcol (str): Name of the column that contains Republican voteshare data
        (i.e. estimated number of votes cast for Donald Trump in the precinct
        in the November 2020 presidnetial election)
        -num_dists (int):
        -export_to (str or None): TODO: location to export the map to

    Returns: None, displays plot on screen and/or saves image to file
    '''
    num_dists = max([id for id in df['dist_id'] if id is not None])
    print(num_dists)

    #TODO: Move this to df setup, and have it be by precinct, with dissolve aggfunc-ing it 
    df['raw_margin'] = None
    for i in range(1, num_dists+1): #this should be doable on one line vectorized
        df.loc[df.dist_id == i, 'raw_margin'] = blue_red_margin(df, dcol, rcol, i)

    #TODO: figure out how to push legend off map, or maybe turn it into categorical color bar
    df.plot(column='raw_margin', cmap='seismic_r', vmin=-.6, vmax=.6)
    #fig, ax = plt.subplots(1)
    #sm = plt.cm.ScalarMappable(cmap='seismic_r')
    #cbar = fig.colorbar(sm) #all of these extremely basic things from many matplotlib StackOverflow answers fail

    timestamp = datetime.now().strftime("%m%d-%H%M%S")
    filepath = f'maps/{state_postal}20_testmap_' + timestamp
    plt.pyplot.savefig(filepath, dpi=300) 
    print(f"District map saved to {filepath}")
    plt.pyplot.close()


### STATS FUNCTIONS (to be moved over to stats or elsewhere, perhaps) ###

def results_by_district(df, export_to=False):
    '''
    Compresses the df down to a table of by-district stats, where each row
    represents the entire area with one dist_id. Dissolve process is slow,
    but could speed up plotting and metrics generation.

    Inputs:
        -df (geopandas GeoDataFrame): state level precinct/VTD data. Should
        have dist_id assigned for every precinct.
        -export_to (str): name of file to export to

    Returns (geopandas GeoDataFrame): state level data by custom district
    '''
    df = df.drop(['neighbors'], axis=1)
    df_dists = df.dissolve(by='dist_id', aggfunc=sum)
    df_dists.reset_index(drop=True)
    set_blue_red_diff(df_dists)
    #will cause a ZeroDivisionError if any districts are exactly tied
    df_dists['raw_margin'] = (df_dists["G20PREDBID"] - df_dists["G20PRERTRU"]) / (df_dists["G20PREDBID"] + df_dists["G20PRERTRU"])
    df_dists['area'] = df_dists['geometry'].to_crs('EPSG:3857').area
    #TODO: add df_dists['perimeter']?
    df_dists['popdensity'] = df_dists['POP100'] / df_dists['area']

    if export_to:
        print("Exporting by-district vote results to file...")
        timestamp = datetime.now().strftime("%m%d-%H%M%S")
        filepath = f"merged_shps/ga20_test_dists_{timestamp}.shp"
        df_dists.to_file(filepath)
        print("Export complete.")
        
    return df_dists


def district_pops(df):
    '''
    Outputs the population of each district drawn so far.

    Inputs:
        -df (geopandas GeoDataFrame): state data by precinct/VTD
    
    Returns (dict): dictionary with dist_ids as keys and population totals
    as values
    '''
    pops_dict = {}
    for i in range(1, max(df.dist_id)+1):
        pops_dict[i] = population_sum(df, district=i)
    return pops_dict