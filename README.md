This is an actual README for the redistricting redux project.

To run this from the command line, type `poetry shell` to instantiate a poetry shell, then type `poetry run python redistricting_redux`. That will call `__main__.py`, which in turn calls `app.py`. 

As of now, you CANNOT use `python3 -m...`; it WILL NOT work.

The process to pull the data from the API and create merged shapefiles is intentionally left out of the above command. In order to run this process, type 'poetry run python redistricting_redux/rdh_2020/join_data_to_shp.py' from the command line. You will need a username and password for the Redistricting Data Hub API. Since data is not consistently available/formatted for each state, please note that a very limited selection of states will work. Some examples of states that will work include: AZ, FL, GA, IL, NC, NV, OH, TX. It is possible that modifications in the API/merging scripts might enable a user to created merged shapefiles for other states.
