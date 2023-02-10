import geopandas as gpd
import matplotlib.pyplot as plt
from datetime import datetime

#this should be helperized
print("Importing Georgia 2020 shapefile data...")
fp = "ga_2020/ga_2020.shp"
ga_data = gpd.read_file(fp)
print("Georgia 2020 shapefile data imported")

def plot_redblue_by_precinct(data):
    '''
    Outputs a map of the state that color-codes each precinct by the partisan
    balance of its vote, i.e. dark blue if it overwhelmingly voted for Biden,
    dark red if it overwhelmingly voted for Trump, and some neutral for if it
    was close to even.
    Inputs:
        -data (geopandas DataFrame):
    Outputs:
        -plot as .png file in folder
    '''
    data['raw_margin'] = data.G20PREDBID - data.G20PRERTRU
    data['margin_points'] = data.raw_margin / (data.G20PREDBID + data.G20PRERTRU)

    data.plot(column='margin_points', cmap='seismic_r', legend=True)

    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    filepath = 'maps/ga_test_map_' + timestamp
    plt.savefig(filepath) 

if __name__ == '__main__':
    print("Creating plot...")
    plot_redblue_by_precinct(ga_data)
    print("Plot created and stored in /maps")