#This file, and organization of project into package, by: Matt Jackson

#from .load_state_data import select_state #has to be this way for python3 -m to work
from load_state_data import load_state #has to be this way for poetry run python to work
from draw_random_maps import draw_dart_throw_map, repeated_pop_swap, population_deviation, target_dist_pop, dissolve_map, plot_dissolved_map
from collections import OrderedDict
import time
from stats import population_sum, mean_voteshare, winner_2020

#suppress FutureWarning and UserWarning in dissolve_map()
#syntax from "Mike" answer (1/22/2013) here:
#https://stackoverflow.com/questions/14463277/how-to-disable-python-warnings
import warnings
warnings.filterwarnings("ignore")

SUPPORTED_STATES = OrderedDict({
                                'AZ': {'fullname':"Arizona", 'num_districts':9},
                                'GA': {'fullname':"Georgia", 'num_districts':14},
                                'NV': {'fullname':"Nevada", 'num_districts':4},
                                'NC': {'fullname':"North Carolina", 'num_districts':14}
                                })

#TODO: allow for taking in state abbreviation as optional argument from command line

def run(state_input=None):

    while state_input not in SUPPORTED_STATES:
        state_input = input("Type a two-letter state postal abbreviation, or type 'list' to see list of supported states: ")
        if state_input == 'list':
            print("Here's a list of states currently supported by the program:")
            for k, v in SUPPORTED_STATES.items():
                print(k, v)
        elif state_input in {'quit', 'exit', 'esc', 'escape', 'halt', 'stop'}:
            break
        elif state_input not in SUPPORTED_STATES:
            print("That's not the postal code of a state we currently have data for.")
    #get value from key source: https://www.adamsmith.haus/python/answers/how-to-get-a-key-from-a-value-in-a-dictionary
    state_fullname = SUPPORTED_STATES[state_input]['fullname']
    print(f"You typed: {state_input} (for {state_fullname})")

    df = load_state(state_input)

    user_seed = ''
    while not user_seed.isnumeric():
        user_seed = input("Pick a lucky number for the seed of our random map drawing process: ")
        if user_seed in {'quit', 'exit', 'esc', 'escape', 'halt', 'stop'}:
            break
        elif type(user_seed) != int:
            print("Come on, buddy. Just a regular old positive integer.")
        else:
            user_seed = int(user_seed)
    print(f"Alright. You picked: {user_seed}")
    print("Let's draw a random map and see how fair it is!")
    time.sleep(1)

    num_districts = SUPPORTED_STATES[state_input]['num_districts']
    target_pop = target_dist_pop(df, num_districts)
    print(f"({state_fullname} has {num_districts} Congressional districts and {population_sum(df)} people.)\nGoal is: {target_pop} people per district")
    time.sleep(2)

    draw_dart_throw_map(df, num_districts, seed=user_seed)

    
    #maybe make this a while loop so people can choose how long to balance for
    deviation = population_deviation(df)
    if deviation <= target_pop // 10:
        print("It looks like these districts' populations are pretty balanced!")
    else:
        print("It looks like these districts are not very well balanced by population.")
    print("Note: In real life, a state's U.S. Congressional districts must be as close\nto equal as possible in population.")

    print("Do you want to try to swap precincts between districts to balance their population?\nIf so, type 'yes'.")
    swap_choice = input("WARNING: This swap process can take several minutes, and might not reach\nthe threshold you want:\n")
    YES = {'yes', 'Yes', 'YES', True, 1}
    if swap_choice not in YES:
        print("Okay, we'll leave these districts as is.")
    else:
        print("How much deviation will you allow between districts?")
        user_allowed_deviation = input(f"Given the imprecision of our precincts, we recommend no lower than {target_pop // 10}: ")
        if not user_allowed_deviation.isnumeric():
            print("That's not a valid integer, so we'll just go with {target_pop // 10}.")
            user_allowed_deviation = target_pop // 10
        #...this point
        user_steps = input(f"How many times do you want to iterate the swapping process? Each iteration can take 60-90 seconds.")
        if not user_steps.isnumeric():
            print("That's not a valid integer, so let's go with 5.")
            user_steps = 5
        repeated_pop_swap(df, allowed_deviation=int(user_allowed_deviation), 
                          plot_each_step=False, stop_after=int(user_steps))
        #if we're still not at user_allowed_deviation:
            #give user some chance to keep balancing here y/n, if y, go back up to...

    print("Okay, we have our map set up. Let's estimate how fair it is!")
    winner = winner_2020(df)
    if "JOE BIDEN" in winner:
        winner_party = 'd'
    elif "DONALD TRUMP" in winner:
        winner_party = 'r'
    print(f"For reference, {winner}, won {state_fullname} in 2020 with {mean_voteshare(df, party=winner_party, as_percent=True):.2f}% of the major-party vote.")
    print("Our statistical metrics suggest that a fair map should have:")
    print("SARIK METRICS STUFF GOES HERE\n")
    time.sleep(1)

    print("Let's get the by-district results for your map. This may take a few seconds...")
    df_dists = dissolve_map(df)
    print("Here are the 2020 presidential election vote margins in each district you drew:")
    print("positive point_swing: Democratic win; negative: Republican win")
    print(df_dists[['POP100', 'point_swing']])

    print("EVALUATE SARIK FAIRNESS CONDITION")
    print("Message about whether your map looks fair or unfair!")

    plot_choice = input("Would you like to see a plot of your map on the state?\n")
    if plot_choice not in YES:
        print("Okay. Though you really should pick 'yes' next time to see the map plotting feature!")
    else:
        fp = plot_dissolved_map(df_dists, state_input, dcol="G20PREDBID", rcol="G20PRERTRU", export_to=None)
        print(f"Map saved to filepath \"/{fp}\". Go open that file to look at your map!")




