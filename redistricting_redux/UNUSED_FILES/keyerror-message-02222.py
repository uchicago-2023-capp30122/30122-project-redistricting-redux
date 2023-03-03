[2656 rows x 7 columns]
/home/mbjackson/.cache/pypoetry/virtualenvs/redistricting-redux-DjumEQEb-py3.8/lib/python3.8/site-packages/geopandas/geodataframe.py:1676: FutureWarning: The operation <built-in function sum> failed on a column. If any error is raised, this will raise an exception in a future version of pandas. Drop these columns to avoid this warning.
  aggregated_data = data.groupby(**groupby_kwargs).agg(aggfunc)
---------------------------------------------------------------------------
KeyError                                  Traceback (most recent call last)
File ~/.cache/pypoetry/virtualenvs/redistricting-redux-DjumEQEb-py3.8/lib/python3.8/site-packages/pandas/core/indexes/base.py:3802, in Index.get_loc(self, key, method, tolerance)
   3801 try:
-> 3802     return self._engine.get_loc(casted_key)
   3803 except KeyError as err:

File ~/.cache/pypoetry/virtualenvs/redistricting-redux-DjumEQEb-py3.8/lib/python3.8/site-packages/pandas/_libs/index.pyx:138, in pandas._libs.index.IndexEngine.get_loc()

File ~/.cache/pypoetry/virtualenvs/redistricting-redux-DjumEQEb-py3.8/lib/python3.8/site-packages/pandas/_libs/index.pyx:165, in pandas._libs.index.IndexEngine.get_loc()

File pandas/_libs/hashtable_class_helper.pxi:5745, in pandas._libs.hashtable.PyObjectHashTable.get_item()

File pandas/_libs/hashtable_class_helper.pxi:5753, in pandas._libs.hashtable.PyObjectHashTable.get_item()

KeyError: 'raw_margin'

The above exception was the direct cause of the following exception:

KeyError                                  Traceback (most recent call last)
Cell In[153], line 1
----> 1 drand.plot_dissolved_map(ga_data, "G18DGOV", "G18RGOV")

File ~/capp30122/30122-project-redistricting-redux/draw_random_maps.py:274, in plot_dissolved_map(df, dcol, rcol)
    272 print(df)
    273 df_dists = df.dissolve(by='dist_id', aggfunc=sum)
--> 274 df_dists.plot(column='raw_margin', cmap='seismic_r')
    276 timestamp = datetime.now().strftime("%m%d-%H%M%S")
    277 filepath = 'maps/ga_testmap_' + timestamp

File ~/.cache/pypoetry/virtualenvs/redistricting-redux-DjumEQEb-py3.8/lib/python3.8/site-packages/geopandas/plotting.py:968, in GeoplotAccessor.__call__(self, *args, **kwargs)
    966 kind = kwargs.pop("kind", "geo")
    967 if kind == "geo":
--> 968     return plot_dataframe(data, *args, **kwargs)
    969 if kind in self._pandas_kinds:
    970     # Access pandas plots
    971     return PlotAccessor(data)(kind=kind, **kwargs)

File ~/.cache/pypoetry/virtualenvs/redistricting-redux-DjumEQEb-py3.8/lib/python3.8/site-packages/geopandas/plotting.py:728, in plot_dataframe(df, column, cmap, color, ax, cax, categorical, legend, scheme, k, vmin, vmax, markersize, figsize, legend_kwds, categories, classification_kwds, missing_kwds, aspect, **style_kwds)
    726             values = values.reindex(df.index)
    727 else:
--> 728     values = df[column]
    730 if pd.api.types.is_categorical_dtype(values.dtype):
    731     if categories is not None:

File ~/.cache/pypoetry/virtualenvs/redistricting-redux-DjumEQEb-py3.8/lib/python3.8/site-packages/geopandas/geodataframe.py:1415, in GeoDataFrame.__getitem__(self, key)
   1409 def __getitem__(self, key):
   1410     """
   1411     If the result is a column containing only 'geometry', return a
   1412     GeoSeries. If it's a DataFrame with any columns of GeometryDtype,
   1413     return a GeoDataFrame.
   1414     """
-> 1415     result = super().__getitem__(key)
   1416     geo_col = self._geometry_column_name
   1417     if isinstance(result, Series) and isinstance(result.dtype, GeometryDtype):

File ~/.cache/pypoetry/virtualenvs/redistricting-redux-DjumEQEb-py3.8/lib/python3.8/site-packages/pandas/core/frame.py:3807, in DataFrame.__getitem__(self, key)
   3805 if self.columns.nlevels > 1:
   3806     return self._getitem_multilevel(key)
-> 3807 indexer = self.columns.get_loc(key)
   3808 if is_integer(indexer):
   3809     indexer = [indexer]

File ~/.cache/pypoetry/virtualenvs/redistricting-redux-DjumEQEb-py3.8/lib/python3.8/site-packages/pandas/core/indexes/base.py:3804, in Index.get_loc(self, key, method, tolerance)
   3802     return self._engine.get_loc(casted_key)
   3803 except KeyError as err:
-> 3804     raise KeyError(key) from err
   3805 except TypeError:
   3806     # If we have a listlike key, _check_indexing_error will raise
   3807     #  InvalidIndexError. Otherwise we fall through and re-raise
   3808     #  the TypeError.
   3809     self._check_indexing_error(key)

KeyError: 'raw_margin'