# Title: Predicting Partisan Balance Using Statistical Parameters
# Author: Sarik Goyal
# Last Updated: 03/04/23

import proportionality
import load_state_data
import stats
import pandas as pd
import random
from sklearn.linear_model import LinearRegression

def generate_training_data(ntrials):
    """
    Generates several grids with varying parameters and creates a dataframe
    of the parameters and the resulting per_districts_won for each trial. The
    choices used for the ranges of the parameters are based on exploration of
    different options. The ultimate choices are somewhat arbitrary but the
    intent is to sample from a reasonably large space.
    Inputs:
        ntrials (int): the number of grids to generate
    Returns:
        df (Pandas dataframe): a dataframe that contains all of the generated
            data
    """
    data = {"per_districts_won":[], "mean_voteshare":[], "var":[], 
        "district_size":[], "num_districts":[], "clustering_score":[]}
    possible_num_districts = [4, 9, 16, 25, 36, 49]

    for i in range(ntrials):
        mean_voteshare = random.uniform(0.5, 0.7)
        var = random.uniform(0.01, 0.05)
        district_size = random.randint(2, 15)
        num_districts = random.choice(possible_num_districts)
        
        per_districts_won, clustering_score = \
            proportionality.simulate_data(mean_voteshare, var, district_size, \
            num_districts)
        
        data["per_districts_won"].append(per_districts_won)
        data["mean_voteshare"].append(mean_voteshare)
        data["var"].append(var)
        data["district_size"].append(district_size)
        data["num_districts"].append(num_districts)
        data["clustering_score"].append(clustering_score)

    return pd.DataFrame(data)

def create_linear_model(ntrials):
    """
    Creates a linear model where the first column of the dataframe is the
    dependent variable and subsequent columns are the explanatory variables.
    Inputs:
        df (Pandas dataframe): a dataframe as described above
        ntrials (int): the number of datapoints to generate
    Returns:
        model (LinearRegression object)
    """
    df = generate_training_data(ntrials)
    X = df[["mean_voteshare", "district_size", "num_districts", \
            "clustering_score"]]
    Y = df[["per_districts_won"]]

    model = LinearRegression().fit(X, Y)

    return model

def predict_state_voteshare(state, ntrials):
    """
    Predicts the expected partisan balance of a state based on our model.
    Inputs:
        state (str): the two-letter abbreviation of the state
        ntrials (int): the number of datapoints to generate - a larger number
            will result in a more accurate estimate at the expense of runtime
    Returns:
        Nothing - prints the expected partisan balance
    """
    model = create_linear_model(ntrials)

    gdf = load_state_data.load_state(state)
    load_state_data.affix_neighbors_list(gdf, \
        f"merged_shps/{state}_2020_neighbors.csv")
    neighbors_dict = load_state_data.make_neighbors_dict(gdf)

    cluster_score = proportionality.clustering_score(neighbors_dict)
    mean_vshare = stats.mean_voteshare(gdf)
    if mean_vshare > 0.5:
        maj_party = "Democrats"
    else:
        mean_vshare = 1 - mean_vshare
        maj_party = "Republicans"
    dist_size = stats.district_size(gdf)
    num_districts = max(gdf['dist_id'])

    prediction = model.predict([[mean_vshare, dist_size, num_districts, \
        cluster_score]])

    print(f"{maj_party} are expected to win {prediction * 100}% of the seats")

predict_state_voteshare("GA", 100)