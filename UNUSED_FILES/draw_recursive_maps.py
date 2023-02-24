def draw_recursive_map(df, target_pop, highest=14, drawzone=None):
    '''
    Okay, I'm gonna spam these thoughts out so I have them, and then pare back
    to a docstring for once.
    What's annoying about the true "chaos mode" random districts I've been drawing
    is that I have to correct them later -- they can have holes, fail to cover
    the whole map, require really complex and nasty precinct transfers that could
    be computationally expensive, etc.
    Maybe there's a way to solve a lot of those problems in one swoop, using a 
    recursive approach that divides the state into halves (or thereabout) and then
    draws smaller subsections within each subsection until the state is full.
    This should prevent the "It's impossible to keep drawing" scenario from ever 
    occurring, because each subdivision is "as if new" -- so there's always going
    to be empty space within the smallest yet-made subdivision for a new, even
    smaller district to grow within.

    Here's how it'll go:
        -All districts start with a backdrop ['dist_id'] of None.
        -if backdrop is None:
            -fill the entire map with 'dist_id' 1 (using vectorized pandas)
            -call this function again immediately
        -if start == max:
            -Do nothing! You should already have a fully populated district of this
            dist_id by default.
        -else:
            -calculate the median, rounded up, between 1 and the total number of
            districts to draw. (For Georgia, n = 14, so (n // 2) + 1 = 8.) 
            -Tracking against total population, fill as close to *exactly half* of
            the map as possible with the median value, using draw_chaos_district
            to select that half randomly from a random starting point. 
            (At first pass, this should result in a GA map where half the population
            lives in 'dist_id' 1 and half lives in 'dist_id' 8.)
            -Call this function again twice, once with (1, n // 2) as the district numbers
            and a backdrop of 1; a second time with (n // 2 + 1, 14) as the district numbers
            and a backdrop of that upper median (in this case, 8). (Sure seems like 'start' and 'backdrop' can be just one
            input parameter.)
                -The population to draw towards should be divided proportionally:
                    -if the current number of districts to draw is even, each new call 
                    inherits a tot_pop of the old tot_pop divided by 2.
                    -if the current number of districts to draw is odd, the first call
                    inherits a tot_pop of the old tot_pop times (upper median/tot_pop),
                    and the second inherits a tot_pop of the old tot_pop times (lower
                    median/tot_pop). So with n = 7 districts to draw, the first call
                    draws 4 and the second call draws 3.
        
        The main advantage of this is that, as each draw_chaos_district call walks around,
        it is bounded by the backdrop dist_id -- if you're drawing district 5 at the second
        generation of the call tree, you can't cross over into or overwrite district 8.
        I can code in a hard barrier where it either tells you "You can't go that way" when
        it tries to escape the bounds of the backdrop dist_id, or more ideally simply never
        allows for attempting it. This may require modifying the behavior of, or creating 
        different versions of, some of the neighbor calculation functions I've already made.

        One downside of this is that splits high in the tree may make other desirable
        traits like VRA compliance impossible (i.e. if each subsection of the state has
        too small a %Black VAP to create a majority-Black district)

        A downside of both methods is that, due to their reliance on touches() and overlap()
        geopandas methods, they fail for states with non-contiguous landmasses (e.g. Virginia
        with the tip of the Delmarva peninsula, Michigan with its Upper Peninsula, Hawai'i
        with its non-connected islands). Worth thinking about how to handle this.
    '''
    #Initial call
    if drawzone is None:
        print("Assigning full map to dist_id 1...")
        df['dist_id'] = 1
        #print(df.head())

        #start the division process
        draw_recursive_map(df, int(target_pop / 2), highest, drawzone=1)

    if drawzone == highest:
        print(f"District {drawzone} is fully set without needing to draw more")
        return None #end evaluation

    n_dists = highest - drawzone + 1 #for GA to start, this is 14
    upper_median = (drawzone + n_dists) // 2 + 1 #for GA to start, this is 8
    lower_median = (drawzone + n_dists) // 2 #for GA to start, this is 7

    #cover half the bounding area with new district number
    #you may have to modify the base function so it doesn't go out of bounds
    print(f"Now drawing half of drawzone {drawzone} into district {upper_median}...")
    time.sleep(0.5)
    draw_recursive_region(df, target_pop, upper_median, drawzone)

    #if n_dists % 2 == 0: #even number, divide evenly
    #actually it shouldn't matter if this is even or not
    #in regions with an odd number of districts left, the smaller call comes first
    #oh no it does matter because it affects target pop
    if n_dists % 2 == 0:
        left_target_pop = right_target_pop = int(target_pop / 2)
    else:
        left_target_pop = target_pop * (lower_median / highest)
        right_target_pop = target_pop * (upper_median / highest)

    #reversing these calls might fix the issue where you can be drawing district 4 and have a place surrounded by district 8
    #no, the issue is that the left calls drawzone is not always 1. it changes
    draw_recursive_map(df, left_target_pop, lower_median, drawzone=1) #for VA this is 1-5 (5 dists), for GA this is 1-7 (7 dists)
    draw_recursive_map(df, right_target_pop, highest, drawzone=upper_median) #for VA this is 6-11 (6 dists), for GA this is 8-14 (7 dists)


def draw_recursive_region(df, target_pop, id, drawzone, debug_mode=False):
    '''
    Using the region currently marked by a preexisting dist_id as a drawzone,
    creates a new region with a new dist_id, overwriting an area whose population
    is half that of the drawzone. Selects a random starting precinct in the
    drawzone, then uses draw_into_district to overwrite its old drawzone dist_id
    with the new one. Then moves about to random eligible neighboring precincts in the
    drawzone, repeatedlying call draw_into_district until that target population
    is reached.

    Terminates if the district reaches a target population value, or if there
    are no eligible empty neighboring precincts to keep drawing into. (But the
    latter should never happen.)

    Inputs:
        -df (geopandas GeoDataFrame): 
        -target_pop (int): target population of each district. When drawing a 
        state map, this will be 1/n, where n is the total population of the state
        as measured in the data.
        -id (int): The label to give precincts within the district.
        For a state map, this will usually be 1 for the first district drawn,
        2 for the second, etc. but the recursive procedure won't draw them in
        that order.
        -drawzone (int): the current precinct serving as the bounds for the new region.
        -curr_precinct(None): You probably don't need to input this actually
    Returns: None, modifies df in-place
    '''
    #get all the indices where dist_id == drawzone.
    #then sample one and get its loc_prec.
    #inspiration: https://stackoverflow.com/questions/21800169/python-pandas-get-index-of-rows-where-column-matches-certain-value
    drawzone_indices = set(df.index[df['dist_id'] == drawzone].tolist())
    #print(drawzone_indices)
    dist_so_far = set()
    neighbors_so_far = set() #this isn't updating properly all the time
    #may need to keep track of something like district_edges, which is 
    #all precincts in district with at least one neighbor whose dist_id == drawzone

    start_index = random.choice(tuple(drawzone_indices))
    curr_precinct = df.loc[start_index, 'loc_prec']
    print(f"We're gonna start at: {curr_precinct}")

    #Make the population sum a giant while loop
    while population_sum(df, 'tot', district=id) <= target_pop:

        print(f"Now drawing {curr_precinct} into district")
        draw_into_district(df, curr_precinct, id)
        print(f"Current district population: {population_sum(df, 'tot', district=id)}")
        dist_so_far.add(curr_precinct)

        #do the neighbors_so_far stuff now in case you need it later
        curr_neighbors = set(df[df.loc_prec == curr_precinct]['neighbors'].iloc[0].tolist()) #you could do the "is in drawzone" calculations each time here
        neighbors_so_far = neighbors_so_far.union(curr_neighbors) #and here
        #you then need to eliminate any overlap between neighbors_so_far and dist_so_far
        neighbors_so_far = neighbors_so_far - dist_so_far #using minus sign to do set difference operation
        #https://learnpython.com/blog/python-set-operations/

        #Try to draw into a neighbor of current precinct
        curr_valid_neighbors = {neighbor for neighbor in curr_neighbors
                            if df.loc[df.loc_prec == neighbor]['dist_id'].iloc[0] == drawzone} #This line seems to break, uniquely, for "Columbia,New Life Church"
        if len(curr_valid_neighbors) > 0:
            curr_precinct = random.choice(tuple(curr_valid_neighbors))
            #"ValueError("can only convert an array of size 1 to a Python scalar")"#
        else:
            print("This precinct has no neighbors it can draw into. Jump elsewhere")
            #look at allowable neighbors of ENTIRE DISTRICT, reduced to unique values
            #This makes the program hang for a bit
            for neighbor in neighbors_so_far:
                print(df.loc[df.loc_prec == neighbor]['dist_id'].item())
            neighbors_so_far = {neighbor for neighbor in neighbors_so_far
                                if int(df.loc[df.loc_prec == neighbor]['dist_id'].item()) == drawzone} #this can sometimes reduce neighbors_so_far to 0 which shouldn't be possible
            #some Columbia County precincts break this, raising ValueErorr("can only convert an array of size 1 to a Python scalar")
            #So does Lincoln,Faith Temple Of Linc
            print(f"The district has {len(neighbors_so_far)} allowed neighbors so far") #this can evaluate to 0 on the first precinct of a new district
            
            if debug_mode:
                for neighbor in neighbors_so_far:
                    df[df.loc_prec == neighbor]['dist_id'] = 999 #highlight all neighbors
                    plot_redblue_by_district(df, "G18DGOV", "G18RGOV")
                return None

            curr_precinct = random.choice(tuple(neighbors_so_far)) #and this broke for 'Hall, Gillsville'

        print(f"We continue with: {curr_precinct}")

    #once district is at full population:
    #TODO: code in some level of allowable deviation, perhaps with backtracking
    print("Target population met or exceeded. Ending district draw")    
    return None 
    
###END RECURSIVE STUFF###