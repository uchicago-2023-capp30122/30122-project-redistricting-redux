# Title: Simulating Partisan Proportionality of Districts
# Author: Sarik Goyal
# Last Updated: 2/22/23

import random
import numpy as np
import matplotlib.pyplot as plt

def generate_grid(mean_voteshare, grid_size):
    '''
    Generate a square grid of voteshares, which represents a state. 
    The voteshares of the grid are generated using the triangular distribution.
    Inputs:
        mean_voteshare (float): the mean voteshare of the party (must be
            between 0 and 1)
        grid_size (int): the side length of the grid (must be an even number)
    Returns:
        grid (NumPy array of floats): a grid of voteshares
    '''
    assert 0 <= mean_voteshare <= 1, f"mean_voteshare must be between 0 and 1"
    assert grid_size > 0 and grid_size % 2 == 0, f"grid_size must be an even \
        number greater than 0"

    #Our goal is for the grid to have a mean voteshare of exactly the
    #value specified in order to make comparisons and analysis meaningful.
    #As a result, we must keep track of how much voteshare we've
    #used and adjust the mean of our distribution accordingly.

    num_squares = grid_size ** 2
    remaining_voteshare = num_squares * mean_voteshare
    voteshare_list = []

    #We only generate (num_squares - 2 voteshares) to start since the 63rd and 
    #64th values will have special conditions to keep the sampling accurate.
    for i in range(num_squares - 2):
        mean_remaining_voteshare = remaining_voteshare / (num_squares - 2 - i)

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

    #Now we can handle the last two values separately.
    if remaining_voteshare < 1:
        voteshare_penult = random.triangular(0, remaining_voteshare, \
            remaining_voteshare / 2)
    else:
        voteshare_penult = random.triangular(remaining_voteshare - 1, 1, \
            remaining_voteshare / 2)
    voteshare_list.append(voteshare_penult)
    
    voteshare_ult = remaining_voteshare - voteshare_penult
    voteshare_list.append(voteshare_ult)

    #We shuffle the list before converting to a NumPy array, as each value is
    #technically generated from a unique distribution.
    random.shuffle(voteshare_list)
    grid = np.reshape(voteshare_list, (grid_size, grid_size))
    return grid

def calculate_district_voteshares(grid):
    '''
    Given a square grid of voteshares, partitions the grid into 2x2 districts.
    Then, calculates the total voteshare of each district.
    Inputs:
        grid (NumPy array of floats): a square grid of voteshares
    Returns (tuple):
        district_voteshares (list of floats): the voteshares of each district
        num_districts_won (int): the number of districts above 50% voteshare
    '''
    grid_shape = np.shape(grid)
    grid_size = grid_shape[0]
    assert grid_shape[0] == grid_shape [1], f"grid must be square"
    assert grid_size > 0 and grid_size % 2 == 0, f"grid_size must be an even \
        number greater than 0"

    long_districts = np.split(grid, (grid_size / 2))
    all_districts = []
    for long_district in long_districts:
        districts = np.split(long_district, (grid_size / 2), axis = 1)
        all_districts.extend(districts)

    district_voteshares = []
    num_districts_won = 0
    for district in all_districts:
        district_voteshare = np.mean(district)
        district_voteshares.append(district_voteshare)
        if district_voteshare > 0.5:
            num_districts_won += 1

    return (district_voteshares, num_districts_won)

def simulate_data(grid_size, ntrials, lb, ub, name):
    '''
    Generates many grids and count the number of districts won for each grid.
    Plots the relationship between the average statewide voteshare and the
    percentage of districts won.
    Inputs:
        grid_size (int): the side length of the grid (must be an even number)
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
    num_districts = grid_size ** 2 / 4
    for i in range(ntrials):
        #We generate the mean_voteshare of each trial randomly by using the
        #triangular distribution once again. This will help us explore the full
        #range of possibilities while obtaining more data points in the middle.
        #If a user wants to generate data for a single mean_voteshare, the user
        #can set lb = ub = mean_voteshare.
        mean_voteshare = random.triangular(lb, ub, (ub - lb) / 2 + lb)
        mean_voteshares.append(mean_voteshare)

        num_districts_won = \
            calculate_district_voteshares(generate_grid(mean_voteshare, \
                grid_size))[1]
        per_won = num_districts_won / num_districts
        per_districts_won.append(per_won)

        datapoints.append((mean_voteshare, per_won))

    plt.scatter(mean_voteshares, per_districts_won)
    filepath = '../plots/proportionality_' + name + '.png'
    plt.savefig(filepath)

    return datapoints