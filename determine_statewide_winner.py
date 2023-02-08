import geopandas as gpd
import matplotlib.pyplot as plt

#why does this hang for a few seconds?

#following
#https://automating-gis-processes.github.io/CSC/notebooks/L2/geopandas-basics.html

#2020 results disaggregated to census block:
#https://redistrictingdatahub.org/dataset/georgia-2020-general-election-results-disaggregated-to-the-2020-block/
#2021 districts disaggregated to census block:
#https://redistrictingdatahub.org/dataset/2021-georgia-congressional-districts-approved-plan/
#we should use census block XOR voting precinct and just handwave/apologize for not having the other

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

def plot_redblue_by_precinct(data):
    '''
    Outputs a map of the state that color-codes each precinct by the partisan
    balance of its vote, i.e. dark blue if it overwhelmingly voted for Biden,
    dark red if it overwhelmingly voted for Trump, and some neutral for if it
    was close to even.
    Inputs:
        -data (geopandas DataFrame):
    Outputs:
        -plot as .jpg file in folder
    '''
    data['raw_margin'] = data.G20PREDBID - data.G20PRERTRU
    data['margin_points'] = data.raw_margin / (data.G20PREDBID + data.G20PRERTRU)

    data.plot(column='margin_points', cmap='seismic_r', legend=True)
    plt.savefig('ga_test_map.jpg') 

if __name__ == '__main__':
    plot_redblue_by_precinct(ga_data)