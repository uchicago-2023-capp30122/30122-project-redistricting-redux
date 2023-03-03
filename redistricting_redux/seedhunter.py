import draw_random_maps as drand 

def seedhunt(df, num_districts=14, starting_seed=1, stop_after=99):
    '''
    Determine population deviation for lots of maps at scale.
    Inputs:
        df (geopandas GeoDataFrame):
        num_districts(int):
        starting_seed(int):
        stop_after(int): 
    '''
    deviation_dict = {}
    curr_seed = starting_seed
    for i in range(curr_seed, stop_after+1):
        drand.draw_dart_throw_map(df, num_districts, seed=i, clear_first=True, map_each_step=False)
        print(f"seed: {i}, population devation: {drand.population_deviation(df)}")
        deviation_dict[i] = drand.population_deviation(df)
        print(deviation_dict)
        time.sleep(1)
    return deviation_dict