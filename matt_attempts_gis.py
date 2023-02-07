import geopandas as gpd

#following
#https://automating-gis-processes.github.io/CSC/notebooks/L2/geopandas-basics.html

fp = "az_2020/az_2020.shp"

data = gpd.read_file(fp)
print(type(data))

for row in data.iterrows():
    print(row)

#data.plot()