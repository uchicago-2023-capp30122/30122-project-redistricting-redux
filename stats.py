#Separating basic stats that aren't *inherently* mapping functions into
#their own file for better code organization

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
        df = df[df.dist_id == district]

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

    try:
        return (blue_total - red_total) / (blue_total + red_total)
    except ZeroDivisionError:
        return 0.0


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
    #this doesn't seem to output the actual value for Georgia, which is 153910 sq km
    #this outputs 217813
    #it may not matter that much if we're just using density comparatively
    #we can also use a fudge factor if we need it to be accurate

def population_density(df, colname, district=None):
    '''A rough population density statistic to feed into Sarik's metrics'''
    return population_sum(df, colname, district) / metric_area(df, district)