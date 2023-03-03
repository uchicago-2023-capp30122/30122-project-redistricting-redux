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
        print("Precinct neighbors calculated")
    ga_data['dist_id'] = None #use .isnull() to select all of these

    return ga_data