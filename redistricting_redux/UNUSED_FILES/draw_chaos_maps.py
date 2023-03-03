def draw_chaos_district(df, target_pop, id, curr_precinct=None):
    '''
    Draw a random district by selecting a random starting precinct at a relatively
    empty spot on the map, use draw_into_district() to give it a dist_id, then 
    move to a random unfilled neighbor, call draw_into_district() on that
    neighbor, and repeat.

    Terminates if the district reaches a target population value, or if there
    are no eligible empty neighboring precincts to keep drawing into (i.e. is
    "trapped" by surrounding precincts that have already been drawn into other
    districts).

    Inputs:
        -df (geopandas GeoDataFrame): state data by precinct/VTD
        -target-pop (int): target population of each district. When drawing a 
        state map, this will be 1/n, where n is the total population of the state
        as measured in df.
        -id (int): The label for the district being drawn (e.g. 1 for the 
        1st district, 2 for the 2nd, etc.
        -curr_precinct (str): name (GEOID20) of the current precinct being drawn 
        into. Function is initialized without this keyword argument, and continues
        by selecting the next precinct to draw and calling itself again with
        that precinct's name in this argument.

    Returns: None, modifies df in-place
    '''
    if population_sum(df, district=id) >= target_pop:
        print("Target population met or exceeded. Ending district draw")
        return None #"break"

    
    if curr_precinct is None:
        neighboring_dists = {None}
        #Select a random precinct to start at. It should be empty and
        #have neighbors that are all also empty.
        curr_index = random.randint(0, len(df)-1)
        while df.loc[curr_index, 'dist_id'] is not None:
            curr_index = random.randint(0, len(df)-1)
        curr_precinct = df.loc[curr_index, 'GEOID20']
        print(f"Trying to start at {curr_precinct}...")
        neighboring_dists = find_neighboring_districts(df, df.loc[curr_index, 'neighbors'],
                                                    include_None=False)
        #time.sleep(0.5)
        print(f"Starting at: {curr_precinct}")
        #time.sleep(1)

    else: 
        curr_index = df.index[df['GEOID20'] == curr_precinct].tolist()[0]
        #print(f"We continue with: {curr_precinct}")

    #if df.loc[df.GEOID20==curr_precinct,'dist_id'].item() is None:
    if df.loc[curr_index, 'dist_id'] is None:
        #print(f"Now drawing {curr_precinct} into district")
        draw_into_district(df, curr_precinct, id)
        print(f"Current district population: {population_sum(df, district=id)}")

    all_neighbors = df.loc[curr_index, 'neighbors']
    #print(all_neighbors)
    #Indexing code inspired by:
    #https://stackoverflow.com/questions/21800169/python-pandas-get-index-of-rows-where-column-matches-certain-value
    #TODO: consider helperizing and/or redoing as an elegant list comprehension
    allowed_neighbors = []
    for nabe in all_neighbors:
        nabe_index = df.index[df['GEOID20'] == nabe].tolist()
        #print(nabe, nabe_index)
        if df.loc[nabe_index[0], 'dist_id'] is None:
            allowed_neighbors.append(nabe)
    #print(allowed_neighbors)

    #Handle case where there are no available neighbors to draw into
    if len(allowed_neighbors) == 0:
        dist_so_far = [] + list(df[df.dist_id == id]['GEOID20'])

        #Handle case where there are no available neighbors of *any* precinct in district
        if len(all_allowed_neighbors_of_district(df, id)) == 0:
            print("It is impossible to continue drawing a contiguous district. Stopping")
            time.sleep(0.2)
            return None
        #pick an empty neighbor of a different precinct in the district
        else:
            #THE BELOW LINE TAKES LONGER AS DISTRICT GROWS. HANGS FOR A NOTICEABLE
            #SECOND OR TWO ONCE DISTRICT IS OVER ~400K PEOPLE. TODO: Improve efficiency
            unstick_precinct = random.choice(all_allowed_neighbors_of_district(df, id))
            print(f"Trying again with {unstick_precinct} as resumption point")
            #jump to that precinct and try again
            draw_chaos_district(df, target_pop, id, curr_precinct=unstick_precinct)
    else:
    #select a neighbor of this precinct at random and call this function again 
    #Inspired by: https://stackoverflow.com/questions/306400/how-can-i-randomly-select-an-item-from-a-list
        next_precinct = random.choice(allowed_neighbors)
        draw_chaos_district(df, target_pop, id, curr_precinct=next_precinct)


def draw_chaos_state_map(df, num_districts, seed=2023, clear_first=True, export_to=None):
    '''
    Uses draw_chaos_district() to attempt to draw a map of random districts of 
    equal population for the whole state. Is very likely to result in a map
    with extreme population deviation between districts, to be fixed later
    with repeated_pop_swap().

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
    print(f"Drawing {num_districts} districts. Target population per district is {target_pop}")
    time.sleep(1)
    for id in range(1, num_districts + 1):
        print(f"Now drawing district {id}...")
        draw_chaos_district(df, target_pop, id)
        time.sleep(0.2)
        plot_redblue_precincts(df, state_postal="TEST")

    #deal with empty space
    print("Filling holes in map...")
    fill_district_holes(df)

    print(district_pops(df))

    #allow for export so df is reproducible
    if export_to is not None:
        pass #TODO: figure out minimum export and export it as csv
        #probably: GEOID20, dist_id