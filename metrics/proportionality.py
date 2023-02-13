import random
import numpy as np
import matplotlib.pyplot as plt

def generate_grid(mean_voteshare):
    '''
    Generate an 8x8 grid of voteshares, which represents a state. 
    The voteshares of the grid are generated using the triangular distribution.
    Inputs:
        mean_voteshare (float): the mean voteshare of the party
    Returns:
        grid (NumPy array of floats): an 8x8 grid of voteshares
    '''
    #Our goal is for the grid to have a mean voteshare of exactly the
    #value specified in order to make comparisons and analysis meaningful.
    #As a result, we must keep track of how much voteshare we've
    #used and adjust the mean of our distribution accordingly.
    
    remaining_voteshare = 64 * mean_voteshare
    voteshare_list = []

    #We only generate 62 voteshares to start since the 63rd and 64th values 
    #will have special conditions in order to keep the sampling accurate.
    for i in range(62):
        mean_remaining_voteshare = remaining_voteshare / (64 - i)

        #We use the properties of the triangular distribution to compute
        #the peak and bounds of the distribution.
        if mean_remaining_voteshare < 1/3:
            voteshare = random.triangular(0, mean_remaining_voteshare * 3, 0)
        elif mean_remaining_voteshare > 2/3:
            voteshare = random.triangular(mean_remaining_voteshare * 3 - 2, 1, 1)
        else:
            voteshare = random.triangular(0, 1, mean_remaining_voteshare * 3 - 1)

        voteshare_list.append(voteshare)
        remaining_voteshare -= voteshare

    #Now we can handle the 63rd and 64th values separately.
    if remaining_voteshare < 1:
        voteshare_63 = random.triangular(0, remaining_voteshare, \
            remaining_voteshare / 2)
    else:
        voteshare_63 = random.triangular(remaining_voteshare - 1, 1, \
            remaining_voteshare / 2)
    voteshare_list.append(voteshare_63)
    
    voteshare_64 = remaining_voteshare - voteshare_63
    voteshare_list.append(voteshare_64)

    #We shuffle the list before converting to a NumPy array, as each value is
    #technically generated from a unique distribution.
    random.shuffle(voteshare_list)
    grid = np.reshape(voteshare_list, (8, 8))
    return grid

def calculate_district_voteshares(grid):
    '''
    Given an 8x8 grid of voteshares, partitions the grid into 16 2x2 districts.
    Then, calculates the total voteshare of each district.
    Inputs:
        grid (NumPy array of floats): an 8x8 grid of voteshares
    Returns (tuple):
        district_voteshares (list of floats): the voteshares of each district
        num_districts_won (int): the number of districts above 50% voteshare
    '''
    long_districts = np.split(grid, 4)
    all_districts = []
    for long_district in long_districts:
        districts = np.split(long_district, 4, axis = 1)
        all_districts.extend(districts)

    district_voteshares = []
    num_districts_won = 0
    for district in all_districts:
        district_voteshare = np.mean(district)
        district_voteshares.append(district_voteshare)
        if district_voteshare > 0.5:
            num_districts_won += 1

    return (district_voteshares, num_districts_won)

def simulate_data(ntrials, lb, ub, name):
    '''
    Generates many grids and count the number of districts won for each grid.
    Plots the relationship between the average statewide voteshare and the
    percentage of districts won.
    Inputs:
        ntrials (int): The number of grids to generate
        lb (float): The lower bound of generated voteshares
        ub (float): the upper bound of generated voteshares
        name (str): label for simulation attached to the filename
    Returns:
        datapoints (list of tuples): list of datapoints with each datapoint in 
        the form (mean_voteshare, per_won)
    '''
    mean_voteshares = []
    per_districts_won = []
    datapoints = []
    for i in range(ntrials):
        #We generate the mean_voteshare of each trial randomly by using the
        #triangular distribution once again. This will help us explore the full
        #range of possibilities while obtaining more data points in the middle.
        #If a user wants to generate data for a single mean_voteshare, the user
        #can set lb = ub = mean_voteshare.
        mean_voteshare = random.triangular(lb, ub, (ub - lb) / 2 + lb)
        mean_voteshares.append(mean_voteshare)

        num_districts_won = \
            calculate_district_voteshares(generate_grid(mean_voteshare))[1]
        per_won = num_districts_won / 16
        per_districts_won.append(per_won)

        datapoints.append((mean_voteshare, per_won))

    plt.scatter(mean_voteshares, per_districts_won)
    filepath = '../plots/proportionality_' + name + '.png'
    plt.savefig(filepath)

    return datapoints

simulate_data(1000, 0.3, 0.7, "basic")

def add_city(grid):
    '''
    Rearranges the grid to form a city, or a 3x3 cluster within the grid where 
    the voteshares are the highest.
    Inputs:
        grid (NumPy array): an 8x8 grid of voteshares
    Returns:
        city_grid (NumPy array): an 8x8 grid of voteshares with the 9 highest
            voteshares clustered in a 3x3 region
    '''
    #We first randomly locate the center of our city. Since our city will
    #always be 3x3, the city must not be at the border of the grid.
    city = np.array([random.randint(1, 6), random.randint(1, 6)])
