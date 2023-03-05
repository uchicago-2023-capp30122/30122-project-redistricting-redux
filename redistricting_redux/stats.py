'''
All functions in file by: Matt Jackson
'''
from math import sqrt

#Separating basic stats that aren't *inherently* mapping functions into
#their own file for better code organization

def population_sum(df, colname="POP100", district=None):
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

def set_blue_red_diff(df, dcol="G20PREDBID", rcol="G20PRERTRU", district=None):
    '''
    Gives the df a new attribute for raw difference in votes between the 
    Democratic and Republican candidate

    Inputs: 
        -df (Geopandas GeoDataFrame): state data by precinct/VTD
        -dcol (str): name of the column in the data representing the Democratic
        candidate's votes earned.
        -rcol (str): name of the column in the data representing the Republican
        candidate's votes earned.
        -district (any): district ID. If None, calculates margin for the whole
        state.
    Returns: None, modifies df in place
    '''
    df['raw_dr_dif'] = df[dcol] - df[rcol]


def blue_red_margin(df, dcol="G20PREDBID", rcol="G20PRERTRU", district=None):
    '''
    Returns the difference in votes, normalized to percentage points, between
    the Democratic candidate and the Republican candidate in the given area.
    Should only be called using candidates who actually ran against each other
    in the same race during the same election cycle.
    Inputs: 
        -df (Geopandas GeoDataFrame): state data by precinct/VTD
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
    d_total = population_sum(df, dcol, district)
    r_total = population_sum(df, rcol, district)

    try:
        return (d_total - r_total) / (d_total + r_total)
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
    return population_sum(df) // n

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
    #this outputs 217785.269...
    #it may not matter that much if we're just using density comparatively
    #we can also use a fudge factor if we need it to be accurate

def population_density(df, colname, district=None):
    '''A rough population density statistic to feed into Sarik's metrics'''
    #Is there any reason to also do this for precincts?
    return population_sum(df, colname, district) / metric_area(df, district)


###MORE STUFF ADDED 3/4 TO FEED INTO METRICS###

def mean_voteshare(df, party="d", dcol="G20PREDBID", rcol="G20PRERTRU", district=None, as_percent=False):
    '''
    Returns the mean voteshare for candidate in a state or district.
    Note: for simplicity's sake, considers only Democratic and Republican votes
    in the relevant area (ignores third-party votes, as different third party
    candidates are on the ballot in different states, making that a confusing
    thing to take into account this late)

    To get Republican voteshare in two-way contest, call 1 - mean_voteshare()
    (or 100 - mean_voteshare() for percent mode)

    Inputs: 
        -df (Geopandas GeoDataFrame): state data by precinct/VTD
        -party (int): abbreviation 
        -dcol (str): name of the column in the data representing the Democratic
        candidate's votes earned.
        -rcol (str): name of the column in the data representing the Republican
        candidate's votes earned.
        -district (any): district ID. If None, calculates margin for the whole
        state.
        -as_percent (boolean): determines whether to use a decimal (e.g. 0.52) 
        or a percent-like number (e.g. 52 for 52%)
    
    Returns (float): that voteshare
    '''
    assert party[0].lower() in ['d', 'r'], "Our model only supports 'd' and 'r' parties" 

    d_total = population_sum(df, dcol, district)
    r_total = population_sum(df, rcol, district)

    if party[0].lower() == 'd':
        voteshare = (d_total) / (d_total + r_total)
    elif party[0].lower() == 'r':
        voteshare = (r_total) / (d_total + r_total)
    else: 
        voteshare = 0
    if as_percent:
        return voteshare * 100
    else:
        return voteshare

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

def winner_2020(df):
    if mean_voteshare(df, party="d") > mean_voteshare(df, party="r"):
        return "JOE BIDEN, the Democratic (blue) candidate"
    else:
        return "DONALD TRUMP, the Republican (red) candidate"