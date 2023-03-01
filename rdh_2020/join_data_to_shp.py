import geopandas as gpd
import pandas as pd
from zipfile import ZipFile
import rdh_api

def get_merged_data(states):
    """
    Adds election and population data to a VTD boundaries shapefile. Adds the
    new shapefile with the merged data to the working directory.
    
    Inputs:
        states (list of strings): a list of state abbreviations for which we
            would like to collect data - not case sensitive
    """
    rdh_api.run(states = states)

    for state in states:

        state = state.lower()
        shp_filename = state + "_vtd_2020_bound_shp.zip"
        election_filekey = state + "_2020_2020_vtd"
        election_zip = election_filekey + "_csv.zip"
        election_csv = election_filekey + "/" + election_filekey + ".csv"
        census_filekey = state + "_pl2020_vtd"
        census_zip = census_filekey + "_csv.zip"
        census_csv = census_filekey + ".csv"

        gdf = gpd.read_file(shp_filename)

        e_zipfile = ZipFile(election_zip)
        election_data = pd.read_csv(e_zipfile.open(election_csv))

        c_zipfile = ZipFile(census_zip)
        census_data = pd.read_csv(c_zipfile.open(census_csv))
        census_data = census_data[["POP100", "GEOID20"]]

        add_election = gpd.GeoDataFrame(election_data.merge(gdf, on = "GEOID20"))
        final_gdf = gpd.GeoDataFrame(census_data.merge(add_election, on = "GEOID20"))

        state = state.upper()
        final_gdf.to_file(f"../merged_shps/{state}_VTD_merged.shp")

states = ["GA", "AZ", "NC", "NV"]
get_merged_data(states)