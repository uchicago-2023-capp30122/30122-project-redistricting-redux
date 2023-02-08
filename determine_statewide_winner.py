import geopandas as gpd

#why does this hang for a few seconds?

#following
#https://automating-gis-processes.github.io/CSC/notebooks/L2/geopandas-basics.html

fp = "ga_2020/ga_2020.shp"
ga_data = gpd.read_file(fp)

def determine_winner(data):
    '''
    Determine who won the election in a state from vote totals in its precincts.
    Inputs:
        -data (geopandas DataFrame): dataframe with precinct vote totals by candidate,
        currently using field names from Michael McDonald's Elect Project data from
        presidential 2020
    Returns: 
        -winner (str): Name of candidate who won the election across all precincts in
        the dataframe
    '''
    #would have to "find" the relevant candidate rows if candidate changes
    biden = data.G20PREDBID
    trump = data.G20PRERTRU
    jorgensen = data.G20PRELJOR

    vote_totals = {'Biden': 0, 'Trump': 0, 'Jorgensen': 0}

    for i in range(len(biden)):
        vote_totals['Biden'] += biden[i]
        vote_totals['Trump'] += trump[i]
        vote_totals['Jorgensen'] += jorgensen[i]

    print(vote_totals)

    all_votes_cast = sum(vote_totals.values())
    vote_percents = {k: (v / all_votes_cast) for k, v in vote_totals.items()}
    print(vote_percents)

    for key, val in vote_percents.items():
        if val == max(vote_percents.values()):
            print(f"{key} wins!")
            return key

if __name__ == '__main__':
    determine_winner(ga_data)