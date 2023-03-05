def plot_redblue_precincts(df, state_postal="", dcol="G20PREDBID", rcol="G20PRERTRU", num_dists=14):
    '''
    Old district drawing method replaced by plot_dissolved_map().
    
    Plot a map that color-codes each precinct by the partisan margin of the vote
    in the district it's part of, i.e. dark blue if it largely voted Democratic,
    dark red if it overwhelmingly voted Republican, and white if it was close to even.

    Inputs:
        -df (geopandas DataFrame): state data by precincts/VTDs, with polygons
        -state_postal (str length 2)
        -dcol (str): Name of column that contains Democratic voteshare data
        (i.e. estimated number of votes cast for Joe Biden in the precinct in
        the November 2020 presidential election)
        -rcol (str): Name of the column that contains Republican voteshare data
        (i.e. estimated number of votes cast for Donald Trump in the precinct
        in the November 2020 presidnetial election)
        -num_dists (int):
        -export_to (str or None): TODO: location to export the map to

    Returns: None, displays plot on screen and/or saves image to file
    '''
    num_dists = max([id for id in df['dist_id'] if id is not None])
    print(num_dists)

    #TODO: Move this to df setup, and have it be by precinct, with dissolve aggfunc-ing it 
    df['raw_margin'] = None
    for i in range(1, num_dists+1): #this should be doable on one line vectorized
        df.loc[df.dist_id == i, 'raw_margin'] = blue_red_margin(df, dcol, rcol, i)

    #TODO: figure out how to push legend off map, or maybe turn it into categorical color bar
    df.plot(column='raw_margin', cmap='seismic_r', vmin=-.6, vmax=.6)
    #fig, ax = plt.subplots(1)
    #sm = plt.cm.ScalarMappable(cmap='seismic_r')
    #cbar = fig.colorbar(sm) #all of these extremely basic things from many matplotlib StackOverflow answers fail

    timestamp = datetime.now().strftime("%m%d-%H%M%S")
    filepath = f'maps/{state_postal}20_testmap_' + timestamp
    plt.pyplot.savefig(filepath, dpi=300) 
    print(f"District map saved to {filepath}")
    plt.pyplot.close()