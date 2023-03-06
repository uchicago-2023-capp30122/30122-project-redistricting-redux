'''
All functions in this file by: Matt Jackson
'''
import pandas as pd
import geopandas as gpd
import numpy as np
import math
from collections import OrderedDict
from ast import literal_eval


def load_state(state_input, init_neighbors=False, affix_neighbors=True):
    '''
    Helper function that actually imports the state after selecting it.

    Inputs:
        -state_input (str): 2-letter state postal code abbreviation
    Returns (geopandas GeoDataFrame)
    '''

    print(f"Importing {state_input} 2020 Redistricting Data Hub data...")
    fp = f"redistricting_redux/merged_shps/{state_input}_VTD_merged.shp"
    state_data = gpd.read_file(fp)
    if "Tot_2020_t" in state_data.columns:
        state_data.rename(columns={"Tot_2020_t","POP100"})
        print("Renamed population column to POP100")
    print(f"{state_input} 2020 Redistricting Data Hub shapefile data imported")
    if init_neighbors:
        set_precinct_neighbors(state_data, state_input)
        print("Precinct neighbors calculated")
    if affix_neighbors:
        neighbor_fp = f'redistricting_redux/merged_shps/{state_input}_2020_neighbors.csv'
        affix_neighbors_list(state_data, neighbor_fp)
        print("Neighbors list affixed from file")
    state_data['dist_id'] = None

    return state_data   


def set_precinct_neighbors(df, state_postal):
    '''
    Creates a list of neighbors (adjacency list) for each precinct/VTD whose 
    geometry is in the GeoDataFrame.
    Takes about 80-90 seconds for the Georgia 2018 precinct map, or about .03
    seconds per precinct.

    Inputs:
        -df (GeoPandas GeoDataFrame): state data by precinct/VTD
        -state_postal (2-character string): postal code for a state supported
        by the program, e.g. "GA" for Georgia

    Returns: None, modifies df in-place
    '''
    #Inspired by:
    #https://gis.stackexchange.com/questions/281652/finding-all-neighbors-using-geopandas
    df['neighbors'] = None
    
    for index, row in df.iterrows():
        neighbors = np.array(df[df.geometry.touches(row['geometry'])].GEOID20)
        overlap = np.array(df[df.geometry.overlaps(row['geometry'])].GEOID20)
        if len(overlap) > 0:
            neighbors = np.union1d(neighbors, overlap)
        df.at[index, 'neighbors'] = neighbors
        if index % 100 == 0:
            print(f"Neighbors for precinct {index} calculated")
    
    print("Saving neighbors list to csv so you don't have to do this again...")
    df['neighbors'].to_csv(f'redistricting_redux/merged_shps/{state_postal}_2020_neighbors.csv')


def affix_neighbors_list(df, neighbor_filename):
    '''
    Affix an adjacency list of neighbors to the appropriate csv.

    Input:
        -df(geopandas GeoDataFrame): precinct/VTD-level data for a state
        -neighbor_filename (str): name of file where neighbors list is

    Returns: None, modifies df in-place
    '''
    neighbor_csv = pd.read_csv(neighbor_filename)
    neighbor_list = neighbor_csv['neighbors']
    #deserialize 
    df['neighbors'] = neighbor_list
    df['neighbors'] = df['neighbors'].apply(lambda x: 
                                            np.array(literal_eval(x.replace("\n", "").replace("' '", "', '")),
                                            dtype=object))

def make_neighbors_dict(df, neighbors_as_lists=True):
    '''
    Creates a dictionary where each precinct's GEOID is a key,
    and the GEOIDs of the precinct's neighbors are a corresponding value.
    For metric stuff. Idea for function from Sarik Goyal

    Inputs:
        -df(geopandas GeoDataFrame): state data by precinct/VTD. MUST HAVE
        NEIGHBORS LIST INSTANTIATED CORRECTLY

    Returns (dict): that dictionary.
    '''
    assert 'neighbors' in df.columns, "This dataframe doesn't have neighbors instantiated yet!"

    #Zip method for quick dict construction:
    #https://www.includehelp.com/python/how-to-create-a-dictionary-of-two-pandas-dataframes-columns.aspx

    df["dem_voteshare"] = df["G20PREDBID"] / (df["G20PREDBID"] + df["G20PRERTRU"])
    geoids_to_voteshares = pd.Series(df.dem_voteshare.values, index = \
        df.GEOID20).to_dict()
    
    #First map voteshares to array of neighboring GEOIDs
    voteshares_to_geoid_neighbs = dict(zip(df.dem_voteshare, df.neighbors))
        
    neighbors_dict = {}
    for voteshare, neighbors in voteshares_to_geoid_neighbs.items():
        if not math.isnan(voteshare):
            voteshare_neighbs = []
            for neighbor in neighbors:
                voteshare_neighb = geoids_to_voteshares[neighbor]
                if not math.isnan(voteshare_neighb):
                    voteshare_neighbs.append(voteshare_neighb)
            if voteshare_neighbs:
                neighbors_dict[voteshare] = voteshare_neighbs
            
    return neighbors_dict