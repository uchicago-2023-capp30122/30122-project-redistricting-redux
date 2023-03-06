#This file, and organization of project into package, by: Matt Jackson

from load_state_data import load_state 
from draw_random_maps import draw_dart_throw_map, repeated_pop_swap, population_deviation, district_pops, target_dist_pop, dissolve_map, plot_dissolved_map
from regression import predict_state_voteshare
from collections import OrderedDict
import time
from stats import population_sum, mean_voteshare, winner_2020

#suppress FutureWarning and UserWarning in dissolve_map()
#syntax from "Mike" answer (1/22/2013) here:
#https://stackoverflow.com/questions/14463277/how-to-disable-python-warnings
import warnings
warnings.filterwarnings("ignore")

SUPPORTED_STATES = OrderedDict({
                                'AZ': {'fullname':"Arizona", 'num_districts':9,
                                        'curr_d':3, 'curr_r':6},
                                'GA': {'fullname':"Georgia", 'num_districts':14,
                                        'curr_d':5, 'curr_r':9},
                                'NV': {'fullname':"Nevada", 'num_districts':4,
                                        'curr_d':3, 'curr_r':1},
                                'NC': {'fullname':"North Carolina", 'num_districts':14,
                                        'curr_d':7, 'curr_r':7},
                                'OH': {'fullname':"Ohio", 'num_districts':15,
                                        'curr_d':5, 'curr_r':10},
                                'TX': {'fullname':"Texas", 'num_districts':38,
                                        'curr_d':13, 'curr_r':25}
                                })

def run(state_input=None):

    while state_input not in SUPPORTED_STATES:
        state_input = input("Type a two-letter state postal abbreviation, or type 'list' to see list of supported states: ").upper()
        #print(state_input)
        if state_input == 'LIST':
            print("Here's a list of states currently supported by the program:")
            for k, v in SUPPORTED_STATES.items():
                print(f"{k} ({v['fullname']})")
        elif state_input in {'QUIT', 'EXIT', 'ESC', 'ESCAPE', 'HALT', 'STOP'}:
            break
        elif state_input not in SUPPORTED_STATES:
            print("That's not the postal code of a state we currently have data for.")
    state_fullname = SUPPORTED_STATES[state_input]['fullname']
    print(f"You typed: {state_input} (for {state_fullname})")

    print(f"Importing {state_input} 2020 Redistricting Data Hub data...")
    df = load_state(state_input)

    user_seed = ''
    while not type(user_seed) == int:
        user_seed = input("\nPick a lucky number for the seed of our random map drawing process: ")
        if user_seed in {'quit', 'exit', 'esc', 'escape', 'halt', 'stop'}:
            break
        elif not user_seed.isdigit():
            print("Come on, buddy. Just a regular old positive integer.")
        else:
            user_seed = int(user_seed)
    print(f"Alright. You picked: {user_seed}")
    print("Let's draw a random map and see how fair it is!")
    time.sleep(1)

    num_districts = SUPPORTED_STATES[state_input]['num_districts']
    target_pop = target_dist_pop(df, num_districts)
    print(f"({state_fullname} has {num_districts} Congressional districts and {population_sum(df)} people.)\nGoal is: {target_pop} people per district\n")
    time.sleep(2)

    draw_dart_throw_map(df, num_districts, seed=user_seed)

    print(f"\nThe populations of your districts are:\n{district_pops(df)}")
    deviation = population_deviation(df)
    print(f"The most and least populous district differ by: {deviation}")
    
    if deviation <= target_pop // 10:
        print("It looks like these districts' populations are pretty balanced!")
    else:
        print("It looks like these districts are not very well balanced by population.")
    print("(Note: In real life, a state's U.S. Congressional districts must be as close\nto equal as possible in population.)")

    print("Do you want to try to swap precincts between districts to balance their population?\nIf so, type 'yes'.")
    swap_choice = input("WARNING: This swap process can take several minutes, and might not reach\nthe threshold you want:\n")
    YES = {'yes', 'Yes', 'YES', True, 1}
    if swap_choice not in YES:
        print("Okay, we'll leave these districts as is.")
    else:
        print("How much deviation will you allow between districts?")
        user_allowed_deviation = input(f"Given the imprecision of our precincts, we recommend no lower than {target_pop // 10}: ")
        if not user_allowed_deviation.isdigit():
            print("That's not a valid integer, so we'll just go with {target_pop // 10}.")
            user_allowed_deviation = target_pop // 10
        else:
            #since user input is type str, must be hard-cast to int for comparisons to work
            user_allowed_deviation = int(user_allowed_deviation)
        #Let user continue swapping process if they so choose
        while swap_choice in YES:
            user_steps = input(f"How many times do you want to iterate the swapping process? Each iteration can take 60-90 seconds: ")
            if not user_steps.isdigit():
                print("That's not a valid integer, so let's go with 5.")
                user_steps = 5
            repeated_pop_swap(df, allowed_deviation=user_allowed_deviation, 
                            plot_each_step=False, stop_after=int(user_steps))
            deviation = population_deviation(df)
            if deviation <= user_allowed_deviation:
                break
            else:
                print("It looks like districts still aren't as balanced as you want.")
                swap_choice = input("Do you wish to continue the swapping process for more steps? ")

    print("\nOkay, we have our map set up. Let's estimate how fair it is!")
    winner = winner_2020(df)
    if "JOE BIDEN" in winner:
        winner_party = 'd'
    elif "DONALD TRUMP" in winner:
        winner_party = 'r'
    print(f"For reference, {winner}, won {state_fullname} in 2020 with {mean_voteshare(df, party=winner_party, as_percent=True):.2f}% of the major-party vote.")

    time.sleep(1)

    print("Let's get the by-district results for your map. This may take a few seconds...")
    df_dists = dissolve_map(df)
    print("Here are the 2020 presidential election vote margins in each district you drew:")
    print("positive point_swing: Democratic win; negative: Republican win")
    print(df_dists[['POP100', 'point_swing']])

    time.sleep(1)

    print("Let's now use our partisan balance model to predict the expected\npartisan balance of our state.")
    print("Please input the number of trials you would like to run\nto generate the model.")
    print("More trials will result in longer runtime, but\nwill produce more precise results.")
    ntrials = input("For context, 100 trials takes about \na minute.: ")
    if not ntrials.isdigit():
        ntrials = 50
        print("Setting ntrials to 50 - input was not numeric")
    prediction = predict_state_voteshare(state_input, int(ntrials))
    
    d_dists_on_map = 0
    r_dists_on_map = 0
    for dist_swing in df_dists['point_swing']:
        if dist_swing > 0:
            d_dists_on_map +=1
        else:
            r_dists_on_map += 1

    print(f"\nBy contrast, your map has {d_dists_on_map} districts that lean Democratic and {r_dists_on_map} districts that lean Republican.")
    if "Democratic" in winner:
        maj_party_seatshare = (d_dists_on_map / num_districts) * 100
    elif "Republican" in winner:
        maj_party_seatshare = (r_dists_on_map / num_districts) * 100
    print(f"Which looks like the majority party is likely to get {maj_party_seatshare:.2f}% of the seats.")
    print(f"\nAnd, for reference, the current real world map for {state_fullname} elected {SUPPORTED_STATES[state_input]['curr_d']} Democrats and {SUPPORTED_STATES[state_input]['curr_r']} Republicans in 2022.")
    print("Interesting!")

    plot_choice = input("Would you like to see a plot of your map on the state?\n")
    if plot_choice not in YES:
        print("Okay. Though you really should pick 'yes' next time to see the map plotting feature!")
    else:
        fp = plot_dissolved_map(df_dists, state_input, dcol="G20PREDBID", rcol="G20PRERTRU", export_to=None)
        print(f"Map saved to filepath \"/{fp}\". Go open that file to look at your map!")

    print("Goodbye for now!")



