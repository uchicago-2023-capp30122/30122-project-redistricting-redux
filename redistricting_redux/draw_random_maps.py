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


def draw_dart_throw_map(df, num_districts, seed=2023, clear_first=True):
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

    #throw darts
    for id in range(1, num_districts+1):
        curr_index = random.randint(0, len(df)-1)
        while df.loc[curr_index, 'dist_id'] is not None:
            curr_index = random.randint(0, len(df)-1)
        curr_precinct = df.loc[curr_index, 'GEOID20']
        print(f"Throwing dart for district {id} at precinct {curr_precinct}...")
        draw_into_district(df, curr_precinct, id)

    #expand into area around darts
    holes_left = len(df.loc[df['dist_id'].isnull()])
    expand_order = [i for i in range(1,num_districts+1)]
    holes_by_step = []
    while holes_left > 0: 
        holes_left = len(df.loc[df['dist_id'].isnull()])
        holes_by_step.append(holes_left)
        print(f"{holes_left} unfilled precincts remain")
        if holes_left == 0:
            break
        if len(holes_by_step) > 2 and holes_by_step[-1] == holes_by_step[-2]:
            print("Switching methods to fill rest of map...")
            fill_district_holes(df)
            break
        #randomize the order in which districts expand each go-round
        random.shuffle(expand_order) 
        for id in expand_order:
            allowed = all_allowed_neighbors_of_district(df, id)
            for neighbor in allowed:
                if population_sum(df, district=id) <= target_pop:
                    draw_into_district(df, neighbor, id)
                else:
                    print(f"District {id} has hit its target population size")
                    if id in expand_order:
                        expand_order.remove(id)
                    break

    print(district_pops(df))


### MAP CLEANUP FUNCTIONS ###


def fill_district_holes(df):
    '''
    Helper function for draw_chaos_state_map. Determine where the remaining 
    unfilled precincts are across the map, then expand existing districts 
    out into those unfilled precincts (or into the gaps within the districts),
    and iterate until every precinct on the map has a dist_id.

    Inputs:
        -df (geopandas GeoDataFrame): state data by precinct/VTD

    Returns: None, returns df in-place
    '''
    holes = df.loc[df['dist_id'].isnull()]
    go_rounds = 0
    while len(holes) > 0: 
        go_rounds += 1
        holes = df.loc[df['dist_id'].isnull()]
        print(f"{holes.shape[0]} unfilled precincts remaining")
        for index, hole in holes.iterrows():
            real_dists_ard_hole = find_neighboring_districts(df, hole['neighbors'], include_None=False)
            if len(real_dists_ard_hole) > 0: 
                draw_into_district(df, hole['GEOID20'], 
                                   smallest_neighbor_district(df, real_dists_ard_hole))

    print("Cleanup complete. All holes in districts filled. Districts expanded to fill empty space.")


def mapwide_pop_swap(df, allowed_deviation=70000):
    '''
    Iterates through the precincts in a state with a drawn district map and 
    attempts to balance their population by moving  precincts from overpopulated
    districts into underpopulated ones.

    This function is VERY SLOW - takes about 75-90 seconds to iterate
    through the rows of the df, and then about 10-15 seconds to reclaim
    'orphan' precincts. Attempts to vectorize and speed it up (visible in
    UNUSED_FILES/mapwide_popswap_2.py) were largely unsuccessful and abandoned.

    Inputs:
        -df (geopandas GeoDataFrame): state data by precinct/VTD. Every precinct 
        should have a dist_id assigned before calling this function.
        -allowed_deviation (int): Largest allowable difference between the 
        population of the most populous district and the population of the 
        least populous district.

    Returns: None, modifies df in-place
    '''
    target_pop = target_dist_pop(df, n=max(df['dist_id']))
    draws_to_do = []
    print("Checking for precincts to move from overpopulated districts to underpopulated neighbors.")
    print("This could take up to a minute...")
    #source for itertuples:
    #https://stackoverflow.com/questions/44634972/how-to-access-a-field-of-a-namedtuple-using-a-variable-for-the-field-name
    idx = {name: i for i, name in enumerate(list(df), start=1)}
    for row in df.itertuples():
        neighboring_dists = find_neighboring_districts(df, row[idx['neighbors']])
        proper_neighbors = {dist for dist in neighboring_dists if dist != row[idx['dist_id']]}
        if len(proper_neighbors) > 0:
            smallest_neighbor = smallest_neighbor_district(df, proper_neighbors)
            if (population_sum(df, district=row[idx['dist_id']]) > target_pop and 
                population_sum(df, district=smallest_neighbor) < target_pop):
                draw_to_do = (row[idx['dist_id']], row[idx['GEOID20']], smallest_neighbor)
                draws_to_do.append(draw_to_do)

    print("Doing all valid precinct reassignments...")
    for draw in draws_to_do:
        donor_district, precinct, acceptor_district = draw
        #make sure acceptor district isn't too large to be accepting precincts
        if population_sum(df, district=acceptor_district) >= target_pop + (allowed_deviation / 2):
            pass
        #make sure donor district isn't to small to be giving precincts
        elif population_sum(df, district=donor_district) <= target_pop - (allowed_deviation / 2):
            pass
        else:
            draw_into_district(df, precinct, acceptor_district)

    #fix any district that is fully surrounded by dist_ids other than its 
    #own (redraw it to match majority dist_id surrounding it)
    print("Reassigning districts 'orphaned' by swapping process...")
    recapture_orphan_precincts(df, idx)

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


def repeated_pop_swap(df, allowed_deviation=70000, plot_each_step=False, stop_after=20):
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
    count = 0

    pop_devs_so_far = []
    while population_deviation(df) >= allowed_deviation:
        #check whether method is repeatedly swapping same districts back & forth
        if len(pop_devs_so_far) > 5 and pop_devs_so_far[-4:-2] == pop_devs_so_far[-2::]:
            print("It looks like this swapping process is trapped in a cycle. Stopping")
            break
        count += 1
        if count > stop_after:
            print(f"You've now swapped {count-1} times. Stopping")
            break
        print(f"Now doing swap cycle #{count}...")
        print(f"The most and least populous district differ by: {population_deviation(df)}")
        pop_devs_so_far.append(population_deviation(df))
        mapwide_pop_swap(df, allowed_deviation)
        if plot_each_step:
            plot_dissolved_map(df, "test")
        dist_pops = district_pops(df)
    if population_deviation(df) <= allowed_deviation:
        print("You've reached your population balance target. Hooray!")
    #print(f"Population deviation at every step was: \n{pop_devs_so_far}")


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
    #multiindexing suggested by: Cole von Glahn
    #Code inspired by: https://stackoverflow.com/questions/12096252/use-a-list-of-values-to-select-rows-from-a-pandas-dataframe
    dists_theyre_in = set(df[df['GEOID20'].isin(lst)].dist_id)
    
    if include_None:
        return dists_theyre_in
    else:
        return {i for i in dists_theyre_in if i is not None}


def smallest_neighbor_district(df, neighbor_districts):
    '''
    Finds the least populous district among those in a given set of districts
    (i.e. that a list of precincts has been drawn into).
    Seeing about refactoring some code.

    Inputs:
        -df (geopandas GeoDataFrame): State data by precinct/VTD
        -precinct (str): GEOID20 field of precinct
    Returns (int): dist_id
    '''
    #print(neighboring_districts)
    nabe_dists_by_pop = {v:k for k,v in district_pops(df).items() if k in neighbor_districts}
    #print(nabe_dist_pops)
    smallest_neighbor = nabe_dists_by_pop[min(nabe_dists_by_pop)]
    return smallest_neighbor


def recapture_orphan_precincts(df, idx):
    '''
    Finds precincts that are entirely disconnected from the bulk of their 
    district and reassigns them to a surrounding district.
    This is very slow. TODO: Find a way to isolate the rows worth iterating over 
    first, ideally vectorized, and then just iterate across those

    Inputs:
        -df (geopandas GeoDataFrame): state level precinct/VTD data. Should
        have dist_id assigned for every precinct.
        -idx (dict): idx object created when using itertuples earlier

    Returns: None, modifies df in-place 
    '''
    #make a complex boolean to filter the df and then just iterate on that

    for row in df.itertuples():
        neighboring_districts = find_neighboring_districts(df, row[idx['neighbors']])
        if row[idx['dist_id']] not in neighboring_districts: 
            print(f"Reclaiming orphan precinct {row[idx['GEOID20']]}...")
            draw_into_district(df, row[idx['GEOID20']], smallest_neighbor_district(df, neighboring_districts))


def dissolve_map(df):
    '''
    Dissolves a precinct-level map into districts. To be used only after
    district assignment is finalized (i.e. after any population balancing
    or modification you want to do).
    The goal will be to refactor plot_dissolved_map to use this instead of doing
    it in-function.

    Inputs:
        -df (geopandas GeoDataFrame): state preinct/VTD-level data, with 
        polygons. 
    
    Returns (geopandas GeoDataFrame): state district-level data, by custom
    disttricts we drew.
    '''
    df_dists = df.dissolve(by='dist_id', aggfunc=sum)
    df_dists.reset_index(drop=True)

    #may cause ZeroDivisionError in the edge case where a district is exactly tied
    df_dists['raw_margin'] = (df_dists["G20PREDBID"] - df_dists["G20PRERTRU"]) / (df_dists["G20PREDBID"] + df_dists["G20PRERTRU"])
    df_dists['center'] = df_dists['geometry'].centroid #these points have a .x and .y attribute
    df_dists['point_swing'] = round(df_dists['raw_margin']*100, 2)

    return df_dists


def plot_dissolved_map(df_dists, state_postal, dcol="G20PREDBID", rcol="G20PRERTRU", export_to=None):
    '''
    Plot a map that dissolves precinct boundaries to show districts as solid
    colors based on their vote margin. Displays it on screen if user's 
    device allows for that.

    Inputs:
        -df (geopandas GeoDataFrame): state DISTRICT-level data, with 
        polygons (you should call dissolve_map(df) first if you are trying to 
        call this on a precinct-level map)
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

    df_dists.plot(edgecolor="gray", linewidth=0.15, column='raw_margin', 
                  cmap='seismic_r', vmin=-.6, vmax=.6)
    
    #Annotating
    #https://stackoverflow.com/questions/38899190/geopandas-label-polygons
    for idx, row in df_dists.iterrows():
        plt.pyplot.annotate(text=row['point_swing'], 
                            xy=(row['center'].x, row['center'].y), 
                            horizontalalignment='center', fontsize=4)

    #TODO: Add a legend of dist_ids that doesn't overlap with map

    timestamp = datetime.now().strftime("%m%d-%H%M%S")
    filepath = f'redistricting_redux/maps/{state_postal}_map_' + timestamp
    plt.pyplot.savefig(filepath, dpi=300) 
    plt.pyplot.close()

    return filepath


### STATS FUNCTIONS (to be moved over to stats or elsewhere, perhaps) ###

def results_by_district(df, state_abbv="", export_to=False):
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
        filepath = f"redistricting_redux/exports/{state_abbv}_test_dists_{timestamp}.shp"
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
    for i in range(1, max([id for id in df.dist_id if id is not None])+1):
        pops_dict[i] = population_sum(df, district=i)
    return pops_dict


### DEBUGGING FUNCTIONS ###

def plot_GEOID20s(df):
    '''
    Creates a giant blank map of every precinct with its GEOID20 on it for debugging
    purposes. That map can then be eyeballed to see if neighbors functions are
    working accurately.
    Inputs:
        -df(geopandas GeoDataFrame)
    Returns: None, outputs plot to file
    '''
    df['center'] = df['geometry'].centroid #these points have a .x and .y attribute

    df.plot(edgecolor="black", linewidth=0.1)
    
    #Annotating
    #https://stackoverflow.com/questions/38899190/geopandas-label-polygons
    for idx, row in df.iterrows():
        plt.pyplot.annotate(text=row['GEOID20'], 
                            xy=(row['center'].x, row['center'].y), 
                            horizontalalignment='center', fontsize=0.5)

    timestamp = datetime.now().strftime("%m%d-%H%M%S")
    filepath = f'maps/GEOID_testmap_' + timestamp
    plt.pyplot.savefig(filepath, dpi=600) 
    print(f"District map saved to {filepath}")
    plt.pyplot.close()