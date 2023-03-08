# Title: Predicting Partisan Balance Using Statistical Parameters
# Author: Sarik Goyal
# Last Updated: 03/07/23

import proportionality
import load_state_data
import stats
import pandas as pd
import random
import matplotlib.pyplot as plt
from sklearn.linear_model import LinearRegression

# CONSTANTS

# We only train our model using voteshares above 0.5 since we expect the behavior
# of our other parameters to change depending on the majority party. When 
# using our model to predict partisan balance, we can simply input the voteshare
# of the majority party without loss of generality. Based on exploration of
# different values, we also noticed that mean voteshares over 0.7 tend to result
# in no seats for the minority party.
MIN_VOTESHARE = 0.5
MAX_VOTESHARE = 0.7
DEFAULT_VOTESHARE = 0.55

MIN_VAR = 0.01
MAX_VAR = 0.1
DEFAULT_VAR = 0.05

MIN_DIST_SIZE = 2
MAX_DIST_SIZE = 15
DEFAULT_DIST_SIZE = 5

MIN_SQRT_NUM_DISTRICTS = 2
MAX_SQRT_NUM_DISTRICTS = 7
DEFAULT_NUM_DISTRICTS = 49

DEFAULT_CLUSTER = True

def generate_training_data(ntrials, mean_voteshare = None, var = None, \
    district_size = None, num_districts = None, cluster = None):
    """
    Generates several grids with varying parameters and creates a dataframe
    of the parameters and the resulting per_districts_won for each trial. The
    choices used for the ranges of the parameters are based on exploration of
    different options. The ultimate choices are somewhat arbitrary but the
    intent is to sample from a reasonably large space.
    Inputs:
        ntrials (int): the number of grids to generate
        mean_voteshare (float), var (float), district_size (int),
            num_districts (int), cluster (bool): can be set to specified 
            values in order to only generate grids with the specified values, 
            otherwise randomly samples values with bounds defined in the above
            constants
    Returns:
        df (Pandas dataframe): a dataframe that contains all of the generated
            data
    """
    data = {"per_districts_won":[], "mean_voteshare":[], "var":[], 
        "district_size":[], "num_districts":[], "clustering_score":[]}

    for i in range(ntrials):
        if mean_voteshare:
            mean_vshare = mean_voteshare
        else:
            mean_vshare = random.uniform(MIN_VOTESHARE, MAX_VOTESHARE)
        if var:
            variance = var
        else:
            variance = random.uniform(MIN_VAR, MAX_VAR)
        if district_size:
            dist_size = district_size
        else:
            dist_size = random.randint(MIN_DIST_SIZE, MAX_DIST_SIZE)
        if num_districts:
            num_dists = num_districts
        else:
            num_dists = random.randint(MIN_SQRT_NUM_DISTRICTS, \
                MAX_SQRT_NUM_DISTRICTS) ** 2
        if cluster:
            clustered = cluster
        else:
            clustered = random.choice([True, False])
        
        per_districts_won, clustering_score = \
            proportionality.simulate_data(mean_vshare, variance, dist_size, \
            num_dists, cluster = clustered)
        
        data["per_districts_won"].append(per_districts_won)
        data["mean_voteshare"].append(mean_vshare)
        data["var"].append(variance)
        data["district_size"].append(dist_size)
        data["num_districts"].append(num_dists)
        data["clustering_score"].append(clustering_score)

    return pd.DataFrame(data)

def create_plots(ntrials):
    """
    Create plots exploring the relationships between each of the parameters
    individually and the percentage of districts won. As we explore each
    parameter individually, we hold the values of all of the other parameters
    constant. These constant values are designated by the default values
    assigned at the top of the script.
    Inputs:
        ntrials (int): the number of grids to generate, which is the number of
            datapoints on each plot
    Returns:
        Nothing, saves plots to redistricting_redux/plots
    """
    # We start by generating a dummy dataframe just to pull the column names in
    # an efficient manner
    dummy_df = generate_training_data(1)
    for column in dummy_df.columns:

        if column != "per_districts_won":

            default_values = {"mean_voteshare": DEFAULT_VOTESHARE, \
                "var": DEFAULT_VAR, \
                "district_size": DEFAULT_DIST_SIZE, \
                "num_districts": DEFAULT_NUM_DISTRICTS, \
                "clustering_score": DEFAULT_CLUSTER}
            # We set the default value of the parameter we're plotting to None
            # in order to produce variation in this parameter.
            default_values[f"{column}"] = None

            df = generate_training_data(100, \
                mean_voteshare = default_values["mean_voteshare"], \
                var = default_values["var"], \
                district_size = default_values["district_size"], \
                num_districts = default_values["num_districts"], \
                cluster = default_values["clustering_score"])

            plt.scatter(df[[column]], df[["per_districts_won"]])

            title = f"How {column} affects per_districts_won, with"
            for param, val in default_values.items():
                if val:
                    title += f" {param} = {val},"
            # delete the trailing comma
            title = title[:-1]
            plt.title(title, wrap = True)
            plt.xlabel(f"{column}")
            plt.ylabel("per_districts_won")
            plt.savefig(f"redistricting_redux/plots/{column}.png")
            plt.clf()

# The results of running create_plots(100) can be found in the plots directory.

# One can observe that there is a strong positive correlation between
# mean_voteshare and per_districts_won, which is of course what is expected.

# There is also a slight negative correlation between var and per_districts_won.
# In other words, a higher variance of voteshares across VTDs benefits the
# minority party. This is also makes intuitive sense but is less obvious. 

# The two clumps of points in the clustering_score plot are a result of our clustering
# algorithm not being able to produce varying degrees of clustering. However, we 
# can still see that a lower clustering score (more clustered voters) benefits
# the minority party, which is also expected.

# We see that there is no real relationship between num_districts and
# per_districts_won, which implies that this parameter doesn't bias our estimates.
# This means that we can drop num_districts from our model below, and stick with
# a default value of 49 in order to get more precise values of per_districts_won.

# However, there is a positive relationship between district_size and
# per_districts_won. Since we believe this relationship shouldn't exist in
# reality (only exists in our model), it is important to drop this variable. Due
# to our model's tendency to overpredict seats for the majority party, we chose
# to adjust our default value to 2 for district_size.

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
    print("generating training data")
    df = generate_training_data(ntrials, district_size = 2, num_districts = 49)
    X = df[["mean_voteshare", "var", "clustering_score"]]
    Y = df[["per_districts_won"]]

    print("creating model")
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

    print("applying model to state")
    gdf = load_state_data.load_state(state)
    neighbors_dict = load_state_data.make_neighbors_dict(gdf)

    var = gdf["dem_voteshare"].var()
    cluster_score = proportionality.clustering_score(neighbors_dict)
    mean_vshare = stats.mean_voteshare(gdf)
    if mean_vshare > 0.5:
        maj_party = "Democrats"
    else:
        mean_vshare = 1 - mean_vshare
        maj_party = "Republicans"

    prediction = model.predict([[mean_vshare, var, cluster_score]])[0][0]
    # Our model should never predict the minority party to obtain more than
    # 50% of the seats and should never predict the majority party to obtain
    # more than 100% of the seats.
    prediction = min(prediction, 1)
    prediction = max(0.5, prediction)
    print(f"{maj_party} are expected to win {round(prediction * 100, 2)}% of the seats")
    return prediction
