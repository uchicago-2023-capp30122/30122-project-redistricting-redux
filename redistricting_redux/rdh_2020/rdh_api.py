# This code comes from instructions provided by the Redistricting Data Hub
# Slight modifications/additions were made by Sarik Goyal to adapt the code to
# suit our project purposes.

#PARAMETERS TO SET

#username or email associated with your RDH account
username_or_email = "mbjackson-capp"

#password for your RDH account
password = "bahfoq-hawWuf-9roszu" 

#You can retrieve datasets by state by typing out the full state name or postal code abbreviation (e.g. "Alabama" or "alabama" or "AL" or "al").
#If you would like data for multiple states, please separate by comma (e.g. "Wisconsin, mn").'
#Because of the limits of WordPress API, it can only retrieve a list of datasets for one state at a time (since many states have nearly 1,000 datasets), so if you are requesting data from multiple states this step may take several minutes, please be patient.
#You may re-run again for any additional desired states (the script will ask you if you would like to re-run and you do not need to restart the script.
#list your states as string "AL, minnesota, Kentucky" or in a list ["alabama","MN","kentucky"]. In either the list or string, please separate using commas.
states = None

#You can filter datasets in the state(s) you designated with the criteria listed below. All filter options are case insensitive.
#You may search by year as YYYY for all years from 2010 to 2021.
#You may search by dataset type with the following names: ACS5, CVAP, Projection, election results, voter file, incumbent, disag.
#You may search by geogrpahy with the following: precinct, block, block group, census tract, vtd, county, state, aiannh, zctas, senate districts, legislative districts, congressional districts, house of represenative districts (or other district names for the SLDL or SLDU for a given state -- "districts" will retrieve all district boundaries).
#'***Please note that if you would like to retrieve the official redistricting dataset for your state, please use "official" (no quotations) in your query. Not all states will produce an offical dataset.
#You may search by file type as CSV or SHP.
additional_filtering = None
#Import the four libraries needed to run the script. If you do not have these, you may need to install.
import pandas as pd
import requests
import io
from getpass import getpass
import numpy as np
#Below is the baseurl used to retrieve the list of datasets on the website.
baseurl = 'https://redistrictingdatahub.org/wp-json/download/list'
"""This function retrieves a list of all datasets on the RDH site. In order to run, you must be an API user and registered with the RDH site.
Inputs: username (string), password (string)
Optional Inputs: baseurl"""

def get_list(username, password, states, baseurl=baseurl):
    print('Retrieving list of datasets on RDH Website...')
    if type(states)!=type([]):
        states = [states]
    dfs = []
    for i in states:
        params = {}
        params['username'] = username
        params['password'] = password
        params['format'] = 'csv'
        params['states'] = i
        r = requests.get(baseurl, params=params)
        data = r.content
        try:
            df = pd.read_csv(io.StringIO(data.decode('utf-8')))
        except:
            print('There was an error retrieving the list of datasets, please check that you have the correct password and username')
            return 
        dfs.append(df)
    df = pd.concat(dfs)
    return df
def check_string(string_list, row):
    if len(string_list)==0:
        return True
    for i in string_list:
        if i not in row:
            return False
    return True
def check_states(state_list, row):
    check_state = []
    if state_list == ['']:
        return True
    else:
        for i in state_list:
            if i == row:
                check_state.append(True)
                return True
            else:
                check_state.append(False)
        if any('True') in check_state:
            return True
        else:
            return False
def assign_fullname(state):
    state = state.lower()
    keys = ['al','ak','az','ar','ca','co','ct','de','fl',
              'ga','hi','id','il','in','ia','ks','ky','la','me',
              'md','ma','mi','mn','ms','mo','mt','ne',
              'nv','nh','nj','nm','ny','nc','nd','oh',
              'ok','or','pa','ri','sc','sd','tn','tx',
              'ut','vt','va','wa','wv','wi','wy']
    values = ['Alabama','Alaska','Arizona','Arkansas','California','Colorado','Connecticut','Delaware','Florida',
            'Georgia','Hawaii','Idaho','Illinois','Indiana','Iowa','Kansas','Kentucky','Louisiana','Maine',
            'Maryland','Massachusetts','Michigan','Minnesota','Mississippi','Missouri','Montana','Nebraska',
            'Nevada','New Hampshire','New Jersey','New Mexico','New York','North Carolina','North Dakota','Ohio',
            'Oklahoma','Oregon','Pennsylvania','Rhode Island','South Carolina','South Dakota','Tennessee','Texas',
            'Utah','Vermont','Virginia','Washington','West Virginia','Wisconsin','Wyoming']
    values = [i.lower() for i in values]
    dictionary = dict(zip(keys,values))
    for k, v in dictionary.items():
        if k == state:
            return v
        else:
            continue
    return state
def run_state_name(list_of_states):
    new_list = []
    for i in list_of_states:
        state = assign_fullname(i)
        new_list.append(state)
    return new_list
'''This function extracts the data that meets input specifications to the current working directory. In order to run, you must be an API user and registered with the RDH site.
Inputs: username or email (string), password (string), states (string/list), additional_filtering (string)
Output: N/A'''
def get_data(username_or_email, password, states,additional_filtering):
    df = get_list(username_or_email, password,states)
    #read in the list of data
    for i in df.columns:
        if 'Filter by state found 0 states or unknown states' in i:
            print('*You did not specify the necessary states parameter.*')
            return
    if df.shape[0]<10:
        print('\nYou either have an incorrect username/password or you are not a designated API user. To try again, please re-run.')
        print('If you continue to have problems or would like to become an API user, please email info@redistrictingdatahub.org')
        return
    params = {
    'username': username_or_email,
    'password': password}
    # The below code (lines 128-138) were added by Sarik Goyal
    filenames = []
    for state in states:
        state = state.lower()
        filename1 = state + "_2020_2020_vtd.zip"
        filenames.append(filename1)
        filename2 = state + "_vtd_2020_bound.zip"
        filenames.append(filename2)
        filename3 = state + "_pl2020_vtd.zip"
        filenames.append(filename3)
    df = df[df.Filename.isin(filenames)]
    df = df[(df.Filename.str.contains("pl2020")) | (df.Format == "CSV")]
    #take all of the urls in the subset df and split them to just get the baseurl of the dataset (no params)
    urls = list(df['URL'])
    new_urls = []
    id_dict = {}
    for i in urls:
        print(i)
        new = i.split('?')[0]
        dataset_id = i.split('&datasetid=')[1]
        id_dict.update({new:dataset_id})
        new_urls.append(new)
    ftype = list(df['Format'])
    data = dict(zip(new_urls,ftype))
    counter = 1
    #iterate over all of the new urls and retrieve the data
    for i in new_urls:
        print('Retrieving', str(counter), 'of',str(len(new_urls)),'files')
        #get the data from the url and the params listed above
        params.update({'datasetid':id_dict.get(i)})
        response = requests.get(i,params)
        #get the file name of the dataset
        file_name = i.split('%2F')[-1]
        file_name = file_name.split('/')[-1]
        file_name_no_zip = file_name.split('.')[0]
        zipdot = '.'+file_name.split('.')[1]
        #because we have multiple datasets with the same name (for CSV and SHP), but we may want SHP or CSV, we need to make them unique filenames
        for k,v in data.items():
            if k == i:
                dtype = '_'+v.lower()
            else:
                continue
        #new filename
        if dtype in file_name_no_zip:
            dtype = ''
        file_name = file_name_no_zip+dtype+zipdot
        print('Retrieving ', file_name)
        #write the data
        file = open(file_name, "wb")
        file.write(response.content)
        file.close()
        counter = counter+1
    print('\nDone extracting datasets to current working directory.')
    print('Please re-run to extract additional data.')
def check_versions():
    pd_check = str((pd.__version__))=='1.3.1'
    req_check = str(requests.__version__) == '2.25.1'
    np_check = str(np.__version__)=='1.20.3'
    if pd_check == False:
        print('WARNING: You do not have the correct version of pandas to run this script. You may need to install pandas version 1.3.1 for this script to work.')
    if req_check == False:
        print('WARNING: You do not have the correct version of requests to run this script. You may need to install requests version 2.25.1 for this script to work.')
    if np_check == False:
        print('WARNING: You do not have the correct version of numpy to run this script. You may need to install numpy version 1.20.3 for this script to work.')
def run(username_or_email = username_or_email,password = password,states=states,additional_filtering=additional_filtering):
    check_versions()
    get_data(username_or_email, password, states,additional_filtering)
run()