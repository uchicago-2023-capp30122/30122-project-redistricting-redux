#print("Importing geopandas...")
import geopandas as gpd
import numpy as np
import random #SINCE YOU USE RANDOM YOU NEED TO SET A SEED SOMEWHERE FOR REPLICABILITY
import re
import time
from datetime import datetime
import matplotlib as plt

def startup():
    '''
    Get the GA 2018 data ready to do things with.
    Inputs:
        -none
    Returns: none, loads ga_data as the df
    '''
    print("Importing Georgia 2018 precinct shapefile data...")
    fp = "openprecincts_ga_2018/2018Precincts.shp"
    ga_data = gpd.read_file(fp)
    print("Georgia 2018 shapefile data imported")
    #ga_data['neighbors'] = None
    print("Calculating district neighbors:")
    set_precinct_neighbors(ga_data)
    print("District neighbors calculated")
    ga_data['fake_dist_id'] = None #maybe set to something like "Unassigned" so you can
    #do calculations on leftover area for incomplete maps?

    #This should write the geodataframe *back out* so you don't have to run it
    #every time

    return ga_data

def clear_district_drawings(df):
    df['fake_dist_id'] = None

def population_sum(df, colname, district=None):
    '''
    Calculates the total population across a state df, or district therein, of 
    all people designated a given way in a column. 'district' flag allows for
    calling this function on specific districts once they're drawn.
    Note that values can get weird due to floating points, so I round.

    Inputs:
        -df (Geopandas GeoDataFrame) 
        -col (str): name of a column in the data
        -district (any): district ID. If None, calculates total for whole state
    Returns (int): Total population
    '''

    if district is not None:
        df = df[df.fake_dist_id == district]

    return int(df[colname].sum())


def blue_red_margin(df, dcol, rcol, district=None):
    '''
    Returns the difference in votes, normalized to percentage points, between
    the Democratic candidate and the Republican candidate in the given area.
    Should only be called using candidates who actually ran against each other
    in the same race during the same election cycle.
    Inputs: 
        -df (Geopandas GeoDataFrame)
        -dcol (str): name of the column in the data representing the Democratic
        candidate's votes earned.
        -rcol (str): name of the column in the data representing the Republican
        candidate's votes earned.
        -district (any): district ID. If None, calculates margin for the whole
        state.
    Returns (float): number between -1.0 and 1.0, representing the difference
    (1.0 means the Democratic candidate got 100% of the vote and the Republican
    got 0%, for a margin of victory of 100 percentage points; -1.0 means the
    Republican candidate got 100% of the vote and the Democrat got 0%. An 
    exactly tied race will result in 0.0)
    '''
    blue_total = population_sum(df, dcol, district)
    red_total = population_sum(df, rcol, district)

    #do something to avoid division by zero
    return (blue_total - red_total) / (blue_total + red_total)


def target_dist_pop(df, n=14):
    '''
    Determine how many people should live in each district in a map where each
    district has an equal number of people, given its total population.

    Inputs:
        -df (GeoPandas GeoDataFrame)
        -n (int): number of districts to draw (for Georgia, this number is
        currently 14)
    Returns (int): Target population value 
    '''
    #gonna have to change what "tot" is named based on data source
    return population_sum(df, "tot") // n


def set_precinct_neighbors(df):
    '''
    Creates a list of neighbors for each precinct whose geometry is in the 
    GeoDataFrame.

    Inputs:
        -df (GeoPandas GeoDataFrame)

    Returns: None, modifies df in-place
    '''
    #Inspired by:
    #https://gis.stackexchange.com/questions/281652/finding-all-neighbors-using-geopandas
    df['neighbors'] = None
    
    #This is real slow, takes maybe 2 minutes for voting precincts
    for index, row in df.iterrows():
        neighbors = np.array(df[df.geometry.touches(row['geometry'])].loc_prec)
        #maybe there's a way to update neighbors for all the neighbors this one finds too? to speed up/reduce redundant calcs?
        #print(len(neighbors))
        overlap = np.array(df[df.geometry.overlaps(row['geometry'])].loc_prec)
        if len(overlap) > 0:
            #print(f"FOUND {len(overlap)} OVERLAPS!!!!")
            neighbors = np.union1d(neighbors, overlap)

        #print(neighbors)
        df.at[index, 'neighbors'] = neighbors
        if index % 100 == 0:
            print(f"Neighbors for precinct {index} calculated")

    #print(df['neighbors'])

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
    #warning: there are three fewer loc_prec than rows in the 2018 dataset
    df.loc[df['loc_prec'] == precinct, 'fake_dist_id'] = id

    #ok this works

#can you set a keyword argument to output of another function?
#i.e. target_pop = target_dist_pop(df, 14)?
def draw_random_district(df, target_pop, id, curr_precinct=None):
    '''
    Create a cHaOs dIsTrIcT. 
    FINISH DOCSTRING
    '''
    if population_sum(df, 'tot', district=id) >= target_pop:
        print("Target population met or exceeded. Ending district draw")
        #time.sleep(0.5)
        #clear_district_drawings(df)
        return None #"break"
        #TODO: code in some level of allowable deviation

    if curr_precinct is None:
        #select a random precinct to start at
        #TODO: Need to make sure it's outside districts that have been drawn
        curr_index = random.randint(0, len(df)-1)
        curr_precinct = df.loc[curr_index, 'loc_prec']
        # #https://datatofish.com/random-rows-pandas-dataframe/
        # curr_precinct = df.sample()['loc_prec'] 
        # #i JUST want a string here, not df nonsense
        # #it's not letting me just take out the string value of loc_prec
        # #because it requires the row index to use .loc, and that's whatever random number instead of 0
        # print(str(curr_precinct))
        print(f"We're gonna start at: {curr_precinct}")
        print(type(curr_precinct))
        #i think i have to do a neighbors check here or else start over
    else: 
        curr_index = df.index[df['loc_prec'] == curr_precinct].tolist()[0]
        print(f"We continue with: {curr_precinct}")

    if df.loc[curr_index, 'fake_dist_id'] is None:
        print(f"Now drawing {curr_precinct} into district")
        draw_into_district(df, curr_precinct, id)
        print(f"Current district population: {population_sum(df, 'tot', district=id)}")

    if len(all_allowed_neighbors_of_district(df, id)) == 0:
        print("It is impossible to continue drawing a contiguous district. Stopping")
        time.sleep(1)
        return None

    all_neighbors = df.loc[curr_index, 'neighbors']
    #print(all_neighbors)
    #again i JUST want a string. jfc. 
    #link to index derping stuff i've been drawing on: 
    #https://stackoverflow.com/questions/21800169/python-pandas-get-index-of-rows-where-column-matches-certain-value
    # filter those down to neighbors whose fake_dist_id is still None
    # consider redoing as an elegant list comprehension
    allowed_neighbors = []
    for nabe in all_neighbors:
        nabe_index = df.index[df['loc_prec'] == nabe].tolist()
        #print(nabe_index)
        if df.loc[nabe_index[0], 'fake_dist_id'] is None:
            allowed_neighbors.append(nabe)
    #print(allowed_neighbors)
    #Handle case where there are no available neighbors to draw into
    if len(allowed_neighbors) == 0:
        print("No valid neighbors to draw into! Handling error case...")
        #Interestingly, without this error case handled, it very rarely gets to the population limit
        #On Saturday 2/11 I ran a loop to do this procedure 1,000 times, and it only hit the population limit 19 times
        #clear_district_drawings(df)
        dist_so_far = list(df[df.fake_dist_id == id]['loc_prec']) 

        #handle the error if there are no valid neighbors and it's the first precinct for a new district
        if len(dist_so_far) == 0:
            print("It looks like you can't start drawing here. Restarting somewhere else...")
            time.sleep(1)
            draw_into_district(df, curr_precinct, None) #undo initial draw
            draw_random_district(df, target_pop, id)
        
        unstick_precinct = random.choice(dist_so_far)
        print(f"Trying again with {unstick_precinct} as resumption point")
        #time.sleep(0.1)
        draw_random_district(df, target_pop, id, curr_precinct=unstick_precinct)
        #return None
        #jump to a random precinct in the district and try again 
        #TODO: find some way to reference its "edges" to make this less shitty and bogosortish
    else:
    #select a neighbor at random and call this functoin again 
    #https://stackoverflow.com/questions/306400/how-can-i-randomly-select-an-item-from-a-list
        next_precinct = random.choice(allowed_neighbors)
        draw_random_district(df, target_pop, id, curr_precinct=next_precinct)


def all_allowed_neighbors_of_district(df, id):
    '''
    Ascertain if there are any allowed neighbors anywhere for a district. 
    If this returns a list of length 0, it is impossible to keep drawing a 
    contiguous district.
    '''
    nabe_set = set()
    nabes_so_far = list(df[df.fake_dist_id == id]['neighbors'])
    for array in nabes_so_far:
        for nabe in array:
            nabe_set.add(nabe)
    #print(nabe_set)

    #helperize this
    allowed_neighbors = []
    for nabe in nabe_set:
        nabe_index = df.index[df['loc_prec'] == nabe].tolist()
        #print(nabe_index)
        if df.loc[nabe_index[0], 'fake_dist_id'] is None:
            allowed_neighbors.append(nabe)

    return allowed_neighbors

def draw_random_state_map(df, num_districts):
    '''
    Uses draw_random_district() to draw a map of random districts of equal
    population for the whole state.
    FINISH DOCSTRING

    Inputs:
        -df (Geopandas GeoDataFrame): set of precincts or ideally census blocks
        for state
        -num_districts (int): Number of districts to draw (for Georgia, that's 14)
    '''
    #TODO: Finish this function
    target_pop = target_dist_pop(df, num_districts)
    for id in range(1, num_districts + 1):
        print(f"Now drawing district {id}...")
        time.sleep(0.5)
        draw_random_district(df, target_pop, id)
        #beware this can get stuck in an infinite loop rn
    #EXPORT SOMETHING SOMEWHERE SO MAP IS REPRODUCIBLE
    #maybe do something to add "orphan" precincts to the least populous nearby
    #district all at once at the end should be faster?

def plot_redblue_by_district(df, dcol, rcol):
    '''
    Outputs a map of the state that color-codes each district by the partisan
    balance of its vote, i.e. dark blue if it overwhelmingly voted for Democrat,
    dark red if it overwhelmingly voted for Republican, and some neutral for if it
    was close to even.
    Call this only AFTER drawing a map of districts.
    Inputs:
        -df (geopandas DataFrame): 
    Outputs:
        -plot as .png file in folder
    '''
    
    df['raw_margin'] = df['fake_dist_id']
    #antipattern time
    #for row in df.iterrows:
    #blue_red_margin(df, dcol, rcol, district=df['fake_dist_id'])
    #data['margin_points'] = data.raw_margin / (data.G20PREDBID + data.G20PRERTRU)

    df.plot(column='raw_margin', cmap='seismic_r', legend=True)

    timestamp = datetime.now().strftime("%m-%d_%H%M%S")
    filepath = 'maps/ga_test_map_' + timestamp
    plt.pyplot.savefig(filepath) 
#Multiple possible kinds of plot:
    #-state map (choropleth colored by Kemp-Abrams or Biden-Trump margin)
    #-state map (choropleth colored by racial demographics)
    #-state map (random colors)
    #-bar chart (put statewide margin on dotted line on x axis, give each district a bar with its %D/%R vertically through it)
    #-bar chart (racial demographics)



if __name__ == '__main__':
    startup()
    #print(target_dist_pop(ga_data, 14))
    #print("Here are all the columns:")
    #print(population_sum(ga_data, "totVAP"))
    #print("Finding neighbors for each precinct...")
    #set_precinct_neighbors(ga_data)
    #print("Neighbors set")
    #print(len(ga_data))
    print(ga_data.loc_prec)