**Overview** 

Partisan gerrymandering -- the intentional drawing of electoral districts with the intent of giving one party an advantage -- is a frequent practice in the United States. Our motivation with this project is to assess whether randomly-drawn maps are likely to be exhibit partisan fairness or be accidentally (or systematically) gerrymandered. This points towards a use case for algorithmic methods in defining, detecting, and challenging attempts at partisan gerrymandering in real redistricting processes.  

This was a team project for Computer Science With Applications II, a nine-week-long graduate level course, and is coded in Python (including geopandas and scikit-learn).

**How to run**

To run this project from the command line, type `poetry shell` to instantiate a poetry shell, then type `poetry run python redistricting_redux`. That will call `__main__.py`, which in turn calls `app.py`. If necessary, download repository to local machine using `git clone` and input command `poetry install` first to get dependencies set up.

(Do NOT use `python3 -m...`.)

When run from the command line, the program will:
1) ask the user to select a U.S. state (currently supports six states that had relatively close margins in the 2020 presidential election)
2) use shapefile, population, and 2020 election results data by precinct to draw a "random" Congressional district map of that state, using an original algorithm to select random starting precincts (as if "throwing darts" at the map) and expanding outward to fill the whole map
3) [Optionally] attempt to balance the population of the districts to within a user-set threshold, by exchanging precincts from overpopulated districts to underpopulated ones
4) Using 2020 election results data as a baseline, run a regression model to estimate the expected number of districts that would be won by Democrats and by Republicans in a typical election held under the newly drawn map. This lets the user compare the random map to the expected result, and to the partisan breakdown of the actually existing Congressional map.
5) Offer to export an image of the map (created with geopandas' built-in use of matplotlib), color-coded by two-way partisan margin in the 2020 presidential election (darker red: district voted heavily for Trump; darker blue: district voted heavily for Biden). This lets the user inspect the map visually and assess how districts join or separate real communities.

**Data**

This project was created using data from the Redistricting Data Hub, redistrictingdatahub.org.

The process to pull the data from the API and create merged shapefiles is intentionally left out of the above command. In order to run that process, type `poetry run python redistricting_redux/rdh_2020/join_data_to_shp.py` from the command line. You will need a username and password for the Redistricting Data Hub API. Since data is not consistently available/formatted for each state, please note that only some states will work. Some examples of states that will work include: AZ, FL, GA, NC, NV, OH, and TX. 
