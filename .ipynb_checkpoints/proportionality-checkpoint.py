import numpy as np
import random

def generate_grid(mean_voteshare):
    '''
    Generate an 8x8 grid of voteshares, which represents a state. 
    The voteshares of the grid are generated using a triangular distribution.
    Inputs:
        mean_voteshare (float): the average voteshare for the party
    Returns:
        grid (NumPy array of floats): an 8x8 grid of voteshares
    '''
    #Our goal is for the grid to have an average voteshare of exactly the
    #value specified in order to make comparisons and analysis more
    #meaningful. As a result, we must keep track of how much voteshare we've
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

    print(voteshare_list)
    random.shuffle(voteshare_list)
    print(voteshare_list)
    print(len(voteshare_list))
    grid = np.reshape(voteshare_list, (8, 8))

generate_grid(0.5)