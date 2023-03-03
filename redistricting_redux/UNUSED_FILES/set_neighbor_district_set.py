def set_precinct_neighbor_set(df):
    '''
    Creates a SET of neighbors for each precinct whose geometry is in the 
    GeoDataFrame. FOR DEBUGGING EXPORT/IMPORT

    THIS DIDN'T WORK because pandas casts sets to numpy array when putting them
    into a Series. gughghghhgghghhhhhh

    Inputs:
        -df (GeoPandas GeoDataFrame)

    Returns: None, modifies df in-place
    '''
    #Inspired by:
    #https://gis.stackexchange.com/questions/281652/finding-all-neighbors-using-geopandas
    df['neighborset'] = None
    
    #This is real slow, takes maybe 2 minutes for voting precincts
    for index, row in df.iterrows():
        neighbors = np.array(df[df.geometry.touches(row['geometry'])].loc_prec)
        #maybe there's a way to update neighbors for all the neighbors this one finds too? to speed up/reduce redundant calcs?
        #print(len(neighbors))
        overlap = np.array(df[df.geometry.overlaps(row['geometry'])].loc_prec)
        if len(overlap) > 0:
            neighbors = np.union1d(neighbors, overlap)
            neighbors = set(neighbors)
            #neighbors = neighbors.tolist() #may help with import/export (update: it doesn't; 
            #pandas casts list to nparray to store it in df. darn
        df.at[index, 'neighborset'] = neighbors
        print(type(df[index, 'neighborset']))
        if index % 100 == 0:
            print(f"Neighbor set for precinct {index} calculated")