def metric_area(df, district=None):
    '''
    Area will be wrong if we use lat/long projection so we have to convert to 
    metric and then calculate area to get population density
    '''
    #https://stackoverflow.com/questions/70714271/how-to-turn-latitude-and-longitude-distance-into-meters
    if district is not None:
        df = df[df.dist_id == district].copy() #need the copy or it says 
        #"attempting to set values on a slice of a dataframe"
    #EPSG:3857 is a pseudo-Mercator projection whose units are meters
    df['area'] = df['geometry'].to_crs('EPSG:3857').area

    METERS_TO_KM = .000001

    return df['area'].sum() * METERS_TO_KM
    #Note: this doesn't output the actual value for Georgia, which is 153910 sq km
    #It outputs 217785.269...our use of areas is strictly comparative though

def population_density(df, colname, district=None):
    '''A rough population density statistic to feed into Sarik's metrics.
    
    Inputs:
        -df (geopandas GeoDataFrame): state data by precincts/VTDs
        -colname (str): column to use (defaults to 'POP100' through call to
        population_sum in function)
        -district (int or None): dist_id to obtain density for
        
        Returns (float): population density value
        '''
    return population_sum(df, colname, district) / metric_area(df, district)

def district_size(df, num_districts=None, sqrt_output=True):
    '''
    A measure of how many VTDs in the state are expected to be in each district.
    Used in metrics stuff.
    Idea for function from Sarik Goyal.

    Inputs:
        -df(geopandas GeoDataFrame): state data by precinct/VTD
        -num_districts(int or None): optional parameter if you want to hard-set
        number of districts to something other than what it is supposed to be
        -sqrt_output(boolean): determines whether output of function is square rooted
    '''
    if num_districts is None: #if user didn't pass in a number of districts as
    #input, get the number of districts from the actual map under consideration
        try:
            num_districts = max(df['dist_id'])
        except:
            print("This map has no districts drawn on it")
            num_districts = 0
    
    num_vtds = len(df)

    try:
        size_metric = num_vtds / num_districts 
    except ZeroDivisionError:
        size_metric = 0

    if sqrt_output:
        size_metric = sqrt(size_metric)

    return size_metric


###The below is redundant with dissolve_map

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
    df_dists['popdensity'] = df_dists['POP100'] / df_dists['area']

    if export_to:
        print("Exporting by-district vote results to file...")
        timestamp = datetime.now().strftime("%m%d-%H%M%S")
        filepath = f"redistricting_redux/exports/{state_abbv}_test_dists_{timestamp}.shp"
        df_dists.to_file(filepath)
        print("Export complete.")
        
    return df_dists