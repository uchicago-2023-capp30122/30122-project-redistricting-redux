# Title: Simulating Partisan Proportionality of Districts Using a Grid
# Author: Sarik Goyal
# Last Updated: 03/04/23

import random
import numpy as np
import matplotlib.pyplot as plt
import math
from statistics import mean

#CONSTANTS

#We define the below constants to ensure that we're generating reasonable
#values using the Beta distribution. These bounds are liberal enough that
#we can still explore a meaningful range of parameters.
MIN_MEAN = 0.3
MAX_MEAN = 0.7
MAX_VARIANCE = 0.05

def generate_voteshares(mean_voteshare, var, district_size, num_districts):
    '''
    Generate a list of voteshares which comprise a state. Each voteshare
    generated represents a VTD, or voting district. The voteshares are 
    generated using the beta distribution.
    Inputs:
        mean_voteshare (float): the desired mean voteshare
        var (float): the desired variance of the voteshares
        district_size (int): the side length of a district
        num_districts (int): the number of districts (must be a perfect square)
    Returns:
        voteshare_list (list of floats): a list of voteshares
    '''
    assert MIN_MEAN <= mean_voteshare <= MAX_MEAN, \
        f"mean_voteshare must be between {MIN_MEAN} and {MAX_MEAN}"
    assert 0 <= var <= MAX_VARIANCE, f"variance must be between 0 and \
        {MAX_VARIANCE}"
    assert math.sqrt(num_districts).is_integer(), f"num_districts must be a \
        perfect square (i.e. 9, 16, 25)"

    num_vtds = (district_size ** 2) * num_districts
    voteshare_list = []
    #The formulas to compute alpha and beta of the beta distribution were found
    #here: https://stats.stackexchange.com/questions/12232/calculating-the-parameters-of-a-beta-distribution-using-the-mean-and-variance
    alpha = ((1 - mean_voteshare) / var - 1 / mean_voteshare) * \
        mean_voteshare ** 2
    beta = alpha * (1 / mean_voteshare - 1)

    for i in range(num_vtds):
        voteshare_list.append(random.betavariate(alpha, beta))

    return voteshare_list

def generate_random_grid(voteshare_list, district_size, num_districts):
    """
    Given a list of voteshares, generates a square grid that represents a state.
    Inputs:
        voteshare_list (list of floats): a list of voteshares
        district_size (int): the side length of a district
        num_districts (int): the number of districts (must be a perfect square)
    Returns:
        grid (2D NumPy array): a square grid of voteshares
    """
    grid_size = int(district_size * math.sqrt(num_districts))
    grid = np.reshape(voteshare_list, (grid_size, grid_size))
    return grid

def neighbors_index_dict(district_size, num_districts):
    """
    Assumes that we are working with a list with length = 
    (district_size ** 2) * num_districts. This list will eventually be
    converted to a square grid. The function creates a dictionary that maps
    each index of the list to the indexes of its neighbors within the grid.
    Inputs:
        district_size (int): the side length of a district
        num_districts (int): the number of districts (must be a perfect square)
    Returns:
        neighbors_index_dict (dict): a dictionary that maps each index of the
            list to the indexes of its neighbors within the grid
    """
    neighbors_index_dict = {}
    num_vtds = (district_size ** 2) * num_districts
    grid_size = int(math.sqrt(num_vtds))
    indexes = np.arange(num_vtds)
    index_grid = np.reshape(indexes, (grid_size, grid_size))
        
    return generate_neighbors(index_grid)

def mean_neighbor(cluster_dict, neighbors_index_dict, index):
    """
    Given a partially complete cluster_dict, first checks if a given index has
    any completed neighbors. If so, returns the mean percentile rank of its
    neighbors.
    Inputs:
        cluster_dict (dict): maps indexes to a list whose first element is a 
            voteshare, and the second element is the percentile of the voteshare
            among all voteshares
        neighbors_index_dict (dict): a dictionary that maps each index of the
            list to the indexes of its neighbors within the grid
        index (int): the index that we wish to check
    Returns:
        False: if the index has no completed neighbors, otherwise:
        mean_neighbor (float): the mean value of the completed neighbors
    """
    neighbor_indexes = neighbors_index_dict[index]
    neighbors = []

    for i in neighbor_indexes:
        if cluster_dict[i][1]:
            neighbors.append(cluster_dict[i][1])
    
    if neighbors:
        return mean(neighbors)
    return False

def generate_clustered_grid(voteshare_list, district_size, num_districts):
    """
    Given a list of voteshares, generates a square grid that represents a state,
    where VTDs with similar voteshares are clustered to the specified degree.
    Inputs:
        voteshare_list (list of floats): a list of voteshares
        district_size (int): the side length of a district
        num_districts (int): the number of districts (must be a perfect square)
    Returns:
        grid (2D NumPy array): a square grid of voteshares
    """
    num_vtds = (district_size ** 2) * num_districts
    grid_size = int(math.sqrt(num_vtds))
    sorted_voteshares = sorted(voteshare_list)
    remaining = len(sorted_voteshares)
    ranks = {sorted_voteshares[x]:x for x in range(remaining)}
    index_list = np.arange(num_vtds)
    neighbors_index_d = neighbors_index_dict(district_size, num_districts)
    cluster_dict = {x:[None, None] for x in index_list}

    #We randomize the order that we assign voteshares to indexes.
    np.random.shuffle(index_list)
    for i in index_list:
        mean_neighb = mean_neighbor(cluster_dict, neighbors_index_d, i)
        if mean_neighb:
            #If the index that we're about to assign already has neighbors,
            #then we choose the value from our remaining list whose percentile
            #is closest to mean_neighb.
            voteshare_index = round(mean_neighb * (remaining - 1))
        else:
            #If the index has no neighbors, we randomly choose a value.
            voteshare_index = random.randint(0, remaining - 1)
        
        cluster_dict[i][0] = sorted_voteshares[voteshare_index]
        cluster_dict[i][1] = ranks[cluster_dict[i][0]] / len(voteshare_list)
        del sorted_voteshares[voteshare_index]
        remaining -= 1

    clustered_list = [None]*len(voteshare_list)
    for index, (voteshare, percentile) in cluster_dict.items():
        clustered_list[index] = voteshare

    grid = np.reshape(clustered_list, (grid_size, grid_size))

    return grid

def calculate_district_voteshares(grid, num_districts):
    '''
    Given a square grid of voteshares, partitions the grid into square districts.
    Then, calculates the total voteshare of each district.
    Inputs:
        grid (NumPy array of floats): a square grid of voteshares
        num_districts (int): the number of districts (must be a perfect square)
    Returns (tuple):
        district_voteshares (list of floats): the voteshares of each district
        num_districts_won (int): the number of districts above 50% voteshare
    '''
    grid_shape = np.shape(grid)
    grid_size = grid_shape[0]
    districts_length = int(math.sqrt(num_districts))
    assert grid_shape[0] == grid_shape [1], f"grid must be square"
    assert (grid_size / math.sqrt(num_districts)).is_integer(), f"grid must be \
        divisible into the number of specified districts"

    long_districts = np.split(grid, districts_length)
    all_districts = []
    for long_district in long_districts:
        districts = np.split(long_district, districts_length, axis = 1)
        all_districts.extend(districts)

    district_voteshares = []
    num_districts_won = 0
    for district in all_districts:
        district_voteshare = np.mean(district)
        district_voteshares.append(district_voteshare)
        if district_voteshare > 0.5:
            num_districts_won += 1

    return (district_voteshares, num_districts_won)

def simulate_data(mean_voteshare, var, district_size, num_districts, \
        cluster = True):
    '''
    Generates a grid and counts the percentage of districts won.
    Inputs:
        mean_voteshare (float): the desired mean voteshare
        var (float): the desired variance of the voteshares
        district_size (int): the side length of a district
        num_districts (int): the number of districts (must be a perfect square)
        cluster (bool): generates clustered grids if True, otherwise generates
            random grids
    Returns:
        tuple of 2 values:
            per_districts_won (float): the percentage of districts won
            cluster_score (float): the clustering score for the grid
    '''
    voteshare_list = generate_voteshares(mean_voteshare, var, \
        district_size, num_districts)
    if cluster:
        grid = generate_clustered_grid(voteshare_list, district_size, \
            num_districts)
    else:
        grid = generate_random_grid(voteshare_list, district_size, \
            num_districts)
    num_districts_won = calculate_district_voteshares(grid, \
        num_districts)[1]
    per_districts_won = num_districts_won / num_districts

    neighbors_d = generate_neighbors(grid)
    cluster_score = clustering_score(neighbors_d)

    return (per_districts_won, cluster_score)

def generate_neighbors(grid):
    """
    Finds the neighboring values of each value in a square grid. Diagonally
    adjacent elements are considered to be a neighbor. We don't find the
    neighbors for the elements at the border of the grid in order to make
    calculations easier and to keep the number of neighbors consistent.
    Inputs:
        grid (NumPy array of floats): a square grid of voteshares
    Returns:
        neighbors_d (dict): a dictionary that maps each value in the grid to a
            list of neighboring values
    """
    neighbors_d = {}
    grid_shape = np.shape(grid)
    grid_size = grid_shape[0]

    #Create a border of -1s around the grid so that it's not necessary
    #to write out all of the border exceptions.
    grid = np.pad(grid, 1, constant_values = -1)

    for row in range(1, grid_size + 1):
        for col in range(1, grid_size + 1):
            neighbors = []

            neighbors.append(grid[row-1][col-1])
            neighbors.append(grid[row-1][col])
            neighbors.append(grid[row-1][col+1])

            neighbors.append(grid[row][col-1])
            neighbors.append(grid[row][col+1])

            neighbors.append(grid[row+1][col-1])
            neighbors.append(grid[row+1][col])
            neighbors.append(grid[row+1][col+1])

            neighbors = [i for i in neighbors if i != -1]
            neighbors_d[grid[row][col]] = neighbors

    return neighbors_d

def clustering_score(neighbors_d):
    """
    Calculates a measure of how clustered are the voteshares within a state.
    This score is similar to computing the average variance in voteshares among
    each possible group of neighbors. This means that a lower score indicates 
    that a state's voters are more clustered. Please note that this metric was 
    created by Sarik Goyal for the purposes of this project, and potentially has
    statistical flaws. However, the goal is to have some measure of clustering
    that is relatively easy to compute, even if it is not perfect.
    Inputs:
        neighbors_d (dict): a dictionary that maps the voteshare of each VTD
            within a state to the voteshares of each of its neighboring VTDs
    Outputs:
        clustering_score (float): a measure of how clustered voters are within
            the grid
    """
    mean_deviations = []

    for vtd, neighbors in neighbors_d.items():
        deviations = []
        for neighbor in neighbors:
            deviations.append((neighbor - vtd) ** 2)

        mean_deviations.append(mean(deviations))

    return mean(mean_deviations)