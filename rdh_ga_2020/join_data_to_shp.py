import geopandas as gpd
import pandas as pd
from zipfile import ZipFile

def merge_data(shp_filename, election_zip_filename, election_csv_filename, \
  pop_filename):
    """
    Adds election and demographic data to a VTD boundaries shapefile. Adds the
    new shapefile with the merged data to the working directory.
    
    Inputs:
        shp_filename (string): the name of the zipped file that contains the
            contents of the VTD boundaries shapefile
        election_zip_filename (string): the name of the zipped file that 
            contains a csv of election results by VTD
        election_csv_filename (string): the name of the csv file within the
            zipfile
        pop_filename (string): the name of the csv file that contains
            population and demographic values by VTD
    """
    gdf = gpd.read_file(shp_filename)

    zipfile = ZipFile(election_zip_filename)
    election_data = pd.read_csv(zipfile.open(election_csv_filename))

    pop_data = pd.read_csv(pop_filename)

    add_election = gpd.GeoDataFrame(election_data.merge(gdf, on = "GEOID20"))
    final_gdf = gpd.GeoDataFrame(pop_data.merge(add_election, on = "GEOID20"))

    final_gdf.to_file("../merged_shps/GA_VTD_merged.shp")

merge_data("ga_vtd_2020_bound_shp.zip", "ga_2020_2020_vtd_csv.zip", \
    "ga_2020_2020_vtd/ga_2020_2020_vtd.csv", \
    "../vtd_data/2020_VTD/GA/2020_census_GA3.csv")
