"""
The following functions were written by special guest contributor Ethan Arsht.
Some slight modifications were made by Matt Jackson to adjust it to current
codebase.
"""
import pandas as pd
import geopandas as gpd
import numpy as np
import random 
import re
import time
from datetime import datetime
import matplotlib as plt
from stats import population_sum, blue_red_margin, target_dist_pop, metric_area, population_density, set_blue_red_diff #not sure i did this relative directory right
from draw_random_maps import * #i know this is bad practice but idk where he used it and not

run = 0
run_dict = {}

#suppress UserWarning
#syntax from "Mike" answer (1/22/2013) here:
#https://stackoverflow.com/questions/14463277/how-to-disable-python-warnings
import warnings
warnings.filterwarnings("ignore")

def batch_balance_transfer(df, neighbor_dict=None, run=run, run_dict=run_dict, allowed_deviation=70000):
    '''
    Identifies the border between the smallest population and its largest
    neighbor and trade all precincts on that border from the larger district
    to the smaller district. This is a heavy-handed approach, but
    it does a lot of balancing before a slower, more careful approach is needed.

    Inputs:
        -df (geopandas GeoDataFrame): state data by precinct/VTD. Every precinct 
        should have a dist_id assigned before calling this function.
        -allowed_deviation (int): Largest allowable difference between the 
        population of the most populous district and the population of the 
        least populous district.
    
    Returns: none, modifies df in-place.
    '''
    neighbor_dict = {
        id: n for (id, n) in zip(df.GEOID20, df.neighbors)
    }

    df_trade = pd.DataFrame(df)
    df_trade_pop = district_pops(df) #swapping in preexisting function
    #df_trade_pop = df_trade.groupby('dist_id').sum()[['POP100']].reset_index()
    recent_transfer = []
    while (population_deviation(df_trade) > allowed_deviation):
    #while (df_trade_pop.POP100.max() - df_trade_pop.POP100.min()) > allowed_deviation:
    #small districts take
        df_trade = pd.DataFrame(df)
        df_trade_pop = district_pops(df)
        #df_trade_pop = df_trade.groupby('dist_id').sum()[['POP100']].reset_index()
        print(df_trade_pop)

        smallest = {k:v for k,v in df_trade_pop.items() if v == min(df_trade_pop.values())}
        #smallest = df_trade_pop[df_trade_pop.POP100 == min(df_trade_pop.POP100)]

        df_rec = df[df.dist_id == min(smallest.keys())]
        #df_rec = df[df.dist_id == smallest.dist_id.item()]

        dist_nabes = []
        nabe_other_dist = []
        for prec in df_rec['GEOID20']:
            nabes = neighbor_dict[prec]
            for n in nabes:
                if len(n) != 22: #why is this here?
                    dist = df[df.GEOID20 == n].dist_id.item()
                    if dist != min(smallest.keys()):
                        dist_nabes.append(dist)
                    
                    nabe_other_dist.append(n)


        dist_set = set(dist_nabes)

        neighbor_pop_dict = {}
        for i in dist_set:
            pop = df_trade_pop[i]
            #pop = df_trade_pop[df_trade_pop.dist_id == i]["POP100"].item()
            #pop = df_district_pop[df_district_pop.dist_id == i]["POP100"].item()
            neighbor_pop_dict[i] = pop

        max = 0
        comp_district = None

        for k,v in neighbor_pop_dict.items():
            diff = abs(min(smallest.values()) - v)
            #diff = abs(smallest.POP100.item() - v)
            if diff > max:
                comp_district = k
                max = diff


        eligible = [
            nabe for nabe in nabe_other_dist if df[
                df.GEOID20 == nabe
            ].dist_id.item() == comp_district]

        recent_transfer.append(eligible)
        
        df.loc[df['GEOID20'].isin(eligible), 'dist_id'] = min(smallest.keys())
        print(population_deviation(df_trade))
        #print(df_trade_pop.POP100.max() - df_trade_pop.POP100.min())

        if len(recent_transfer) > 4:
            recent_transfer.pop(0)
            if (recent_transfer[0] == recent_transfer[2]) and recent_transfer[1] == recent_transfer[3]:
                break 
            
        idx = {name: i for i, name in enumerate(list(df), start=1)}
        recapture_orphan_precincts(df, idx)
        run+=1
        run_dict[run] = (population_deviation(df_trade))
        print(run, run_dict)
        #run_dict[run] = df_trade_pop.POP100.max() - df_trade_pop.POP100.min()

def single_balance_transfer(df, neighbor_dict=None, run=run, run_dict=run_dict, allowed_deviation=70000):
    '''
    Identifies the border between the smallest population and its largest
    neighbor and trade all precincts on that border from the larger district
    to the smaller district. This is a heavy-handed approach, but
    it does a lot of balancing before a slower, more careful approach is needed.

    Inputs:
        -df (geopandas GeoDataFrame): state data by precinct/VTD. Every precinct 
        should have a dist_id assigned before calling this function.
        -allowed_deviation (int): Largest allowable difference between the 
        population of the most populous district and the population of the 
        least populous district.
    
    Returns: none, modifies df in-place.
    '''
    neighbor_dict = {
        id: n for (id, n) in zip(df.GEOID20, df.neighbors)
    }

    df_trade = pd.DataFrame(df)
    df_trade_pop = df_trade.groupby('dist_id').sum()[['POP100']].reset_index()
    recent_transfer = []

    second_choice = False
    while (df_trade_pop.POP100.max() - df_trade_pop.POP100.min()) > allowed_deviation:
    #small districts take
        df_trade = pd.DataFrame(df)
        df_trade_pop = df_trade.groupby('dist_id').sum()[['POP100']].reset_index()

        smallest = df_trade_pop[df_trade_pop.POP100 == min(df_trade_pop.POP100)]

        df_rec = df[df.dist_id == smallest.dist_id.item()]

        dist_nabes = []
        nabe_other_dist = []
        for prec in df_rec['GEOID20']:
            nabes = neighbor_dict[prec]
            for n in nabes:
                if len(n) != 22:
                    dist = df[df.GEOID20 == n].dist_id.item()
                    if dist != smallest.dist_id.item():
                        dist_nabes.append(dist)
                    
                    nabe_other_dist.append(n)


        dist_set = set(dist_nabes)

        neighbor_pop_dict = {}
        for i in dist_set:
            pop = df_trade_pop[df_trade_pop.dist_id == i]["POP100"].item()
            neighbor_pop_dict[i] = pop

        df_neighbor_pop = pd.DataFrame.from_dict(
            neighbor_pop_dict, orient = 'index').sort_values(
                0, ascending=False).reset_index()
        
        if not second_choice:
            comp_district = df_neighbor_pop.loc[0, 'index']
        else:
            print(df_neighbor_pop)
            comp_district = df_neighbor_pop.loc[1, 'index']


        eligible = [
            nabe for nabe in nabe_other_dist if df[
                df.GEOID20 == nabe
            ].dist_id.item() == comp_district]

        max_pop = 0
        transfer = None
        for e in eligible:
            if df.loc[df.GEOID20 == e, 'POP100'].item() > max_pop:
                max_pop = df.loc[3, "POP100"].item()
                transfer = e

        recent_transfer.append(transfer)


        df.loc[df['GEOID20'] == transfer, 'dist_id'] = smallest.dist_id.item()
        print(df_trade_pop.POP100.max() - df_trade_pop.POP100.min())

        # second choice mode is a way to inject some noise to prevent
        # trading precincts back and forth indefinitely

        second_choice_count = 0
        if second_choice:
            second_choice_count += 1
        
        # after 10 times trading to the second-choice district,
        # hopefully we can trade with the largest possible district again
        if second_choice_count == 10:
            second_choice = False
        if len(recent_transfer) > 4:
            recent_transfer.pop(0)
            if (
                recent_transfer[0] == recent_transfer[2]
                ) and (
                    recent_transfer[1] == recent_transfer[3]
                    ):
                if second_choice == False:
                    second_choice = True
                else:
                    second_choice = False
    
    idx = {name: i for i, name in enumerate(list(df), start=1)}
    recapture_orphan_precincts(df, idx)
    
    run+=1
    run_dict[run] = df_trade_pop.POP100.max() - df_trade_pop.POP100.min()

def balance_ethan_style(df, run=0, run_dict={}, allowed_deviation=70000):
    '''
    Ethan had this code at the end of a Jupyter notebook. Turned into a function
    by Matt Jackson.
    '''
    neighbor_dict = {
        id: n for (id, n) in zip(df.GEOID20, df.neighbors)
    }
    print(neighbor_dict)

    batch_balance_transfer(df)
    print("Switching to single-precinct approach.")
    single_balance_transfer(df)