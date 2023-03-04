def mapwide_pop_swap2(df, allowed_deviation=70000):
    '''
    attempted some performance improvements with vectorization.
    None of them made any difference.Just gonna live with this being slow
    see docstring for mapwide_pop_swap in other file
    '''
    start = time.time()
    print("This is the current version")
    #maybe generate *a column of the df* with that row's precinct's proper neighbor districts?
    #then use a df boolean filter to select down to rows with with 1 or more proper neighbors
    #set a dist_to_move_to on those in a vectorized fashion
    #then do those moves, 
    #and clear off/drop all those columns after each go round
    #The issue with this is I'm not sure if my functions which take whole df as input vectorize
    #I may be able to rewrite them to take a row though
    #cole: this is called "mask it" - applying to boolean just applies it to things that are true
    target_pop = target_dist_pop(df, n=max(df['dist_id']))

    #This takes 11-15 seconds
    print("setting neighbor districts...")
    df['neighboring_dists'] = [{df.loc[df.GEOID20 == i, 'dist_id'].item() for i in array} for array in df['neighbors']]
    #leave in only proper neighbors (i.e. not dist_id precinct is in)
    for i, set in enumerate(df['neighboring_dists']):
        set.remove(df.loc[i, 'dist_id'])

    #filter to rows where len(df['neighboring_dists']) > 0 
    #apparently it is:
    overpopulated = {k for k in list(district_pops(df)) if district_pops(df)[k] > 761000}
    #TODO: figure out how to vectorize checking for smallest neighbor: min([district_pops(df)[k] for k in test_dist_set])
    borders = df.loc[df['dist_id'].isin(overpopulated) 
                     & df['neighboring_dists'].str.len() > 0]

    draws_to_do = []

    print("iterating through borders")
    idx = {name: i for i, name in enumerate(list(borders), start=1)}
    for row in borders.itertuples():
        this_precinct = row[idx['GEOID20']]
        acceptor_district = smallest_neighbor_district(borders, row[idx['neighboring_dists']])
        if (population_sum(df, district=acceptor_district) < target_pop):
            draw_into_district(df, this_precinct, acceptor_district)
            print(f"drew {this_precinct} into district {acceptor_district}")

    #fix any district that is fully surrounded by dist_ids other than its 
    #own (redraw it to match majority dist_id surrounding it)
    print("Reassigning districts 'orphaned' by swapping process...")
    recapture_orphan_precincts(df, idx)

    print(district_pops(df))

    end = time.time()
    print(end-start)

