print("Importing geopandas...")
import geopandas as gpd
import numpy as np
import random

print("Importing Georgia 2018 precinct shapefile data...")
fp = "openprecincts_ga_2018/2018Precincts.shp"
ga_data = gpd.read_file(fp)
print("Georgia 2018 shapefile data imported")
ga_data['neighbors'] = None
ga_data['fake_dist_id'] = None


def population_sum(df, colname, district=None):
    '''
    Calculates the total population across a state df, or district therein, of 
    all people designated a given way in a column. 'district' flag allows for
    calling this function on specific districts once they're drawn.
    Note that values can get weird due to floating points, so I round.

    Inputs:
        -df (Geopandas GeoDataFrame) 
        -col (str): name of a column in the data
        -district (any): ID
    Returns (int): Total population
    '''

    if district is not None:
        df == df[df.fake_dist_id == district]

    pop_sum = 0
    #this is probably an antipattern, there's gotta be a way to sum a Series
    #in one line
    for precinct_pop in df[colname]:
        #print(int(precinct_pop))
        pop_sum += int(precinct_pop)

    return pop_sum


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
    
    for index, row in df.iterrows():
        neighbors = np.array(df[df.geometry.touches(row['geometry'])].loc_prec)
        overlap = np.array(df[df.geometry.overlaps(row['geometry'])].loc_prec)

        neighbors = np.union1d(neighbors, overlap)
        #print(neighbors)
        df.at[index, 'neighbors'] = neighbors

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
    #TODO: something like:
    #df[df.precinct == precinct].fake_dist_id = id

def draw_random_district(df, target_pop, id, curr_precinct=None):
    '''
    Create a cHaOs dIsTrIcT. 
    '''
    #TODO: Implement random algo
    #if the total pop of all things with fake_dist_id==id >= target_pop:
        #code in some level of allowable deviation
        #end the program
    #if curr_precinct is None:
        #select a random precinct to start at
    #if df[df.precinct == precinct].fake_dist_id is None:
        #draw_into_district(df, precinct, id)
    # bring up df[df.precinct== precinct].neighbors
    # filter those down to neighbors whose fake_dist_id is still None
    #if that's not true of any of these neigbhbors:
        #jump to a random precinct in the district and try again 
        #find some way to reference its "edges" to make this less shitty and bogosortish
    # call this function with curr_precinct as that neighbor


if __name__ == '__main__':
    #print(target_dist_pop(ga_data, 14))
    #print("Here are all the columns:")
    print(population_sum(ga_data, "totVAP"))
    #print("Finding neighbors for each precinct...")
    #set_precinct_neighbors(ga_data)
    #print("Neighbors set")
    #print(ga_data.columns)