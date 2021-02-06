#!/usr/bin/env python
# coding: utf-8

# In[1]:


import pandas as pd
import geopandas as gpd
import json
from bokeh.io import curdoc, output_notebook
from bokeh.models import Slider, HoverTool, WheelZoomTool, ResetTool, PanTool, SaveTool, Select
from bokeh.layouts import widgetbox, row, column
from bokeh.io import output_notebook, show, output_file
from bokeh.plotting import figure
from bokeh.models import GeoJSONDataSource, LinearColorMapper, ColorBar
from bokeh.palettes import brewer
from bokeh.io import export_png


# In[2]:


#SHAPEFILE

#Load in shapefile, in this case we are using Local Authorities. Shapefiles can be found by just google searching
shapefile = 'C:/Users/hayde/Data/Local_Authority_Districts__December_2017__Boundaries_GB_BUC-shp/Local_Authority_Districts__December_2017__Boundaries_GB_BUC.shp'

#Read shapefile using Geopandas
gdf = gpd.read_file(shapefile)[['LAD17CD', 'LAD17NM', 'geometry']]

#Renaming columns to make it a little easier
gdf.columns = ['area_code', 'area', 'geometry']
gdf.head()


# In[3]:


#DATAFILE

#Load in your data file and read using pandas, note this data file requires the same geographical ID as shapefile
#This is because you want to be able to merge the data and shapefile and hence need the same ID.
datafile = 'C:/Users/hayde/Data/averagepolls.csv'
df = pd.read_csv(datafile)
df.head()


# In[4]:


df_2016 = df[df['Year'] == 2016]

#Perform left merge to preserve every row in gdf
merged = gdf.merge(df_2016, left_on = 'area_code', right_on = 'id', how = 'left')

#Replace NaN values to string 'No data'
#merged.fillna('No data', inplace = True)
merged.head()


# In[5]:


#Read data to json
merged_json = json.loads(merged.to_json())

#Convert to String like object
json_data = json.dumps(merged_json)


# In[6]:


#format_data = [('average', 0, 100, '0,0', 'Average Score'),('polls', 0, 100, '0,0', 'Polling Score')]


# In[7]:


format_df = pd.DataFrame(merged, columns = ['area', 'average','geometry', 'polls', 'Year'])
format_df.head(10)


# In[8]:


#Define function that returns json_data for year selected by user
def json_data(selectedYear):
    yr = selectedYear
    df_yr = df[df['Year'] == yr]
    merged = gdf.merge(df_yr, left_on = 'area_code', right_on = 'id', how = 'left')
    #merged.fillna('No data', inplace = True)
    values = {'Year': yr, 'average': 0, 'polls': 0}
    merged = merged.fillna(value=values)
    
    merged_json = json.loads(merged.to_json())
    json_data = json.dumps(merged_json)
    return json_data
   
# Define the callback function: update_plot
def update_plot(attr, old, new):
    # The input yr is the year selected from the slider
    yr = slider.value
    new_data = json_data(yr)
    
    # The input cr is the criteria selected from the select box
    cr = select.value
    input_field = format_df.loc[format_df['area'] == cr].iloc[0]
    
    # Update the plot based on the changed inputs
    p = make_plot(input_field)
    
    # Update the layout, clear the old document and display the new document
    layout = column(p, widgetbox(select), widgetbox(slider))
    curdoc().clear()
    curdoc().add_root(layout)
    
    # Update the data
    geosource.geojson = new_data 
    
    
def make_plot(field_name):    
  # Set the format of the colorbar
  min_range = format_df.loc[format_df['field'] == field_name, 'min_range'].iloc[0]
  max_range = format_df.loc[format_df['field'] == field_name, 'max_range'].iloc[0]
  field_format = format_df.loc[format_df['field'] == field_name, 'format'].iloc[0]

  # Instantiate LinearColorMapper that linearly maps numbers in a range, into a sequence of colors.
  color_mapper = LinearColorMapper(palette = palette, low = min_range, high = max_range)
    
    
#Input GeoJSON source that contains features for plotting
geosource = GeoJSONDataSource(geojson = json_data(2016))
#Define a colour palette, this has to be a bokeh palette, cmap colours do not work here
palette = brewer['RdBu'][8]
#Use the comment below to reverse colour order if desired
#palette = palette[::-1]
#Instantiate LinearColorMapper that linearly maps numbers in a range, into a sequence of colours. Input nan_color.
color_mapper = LinearColorMapper(palette = palette, low = 0, high = 40, nan_color = '#d9d9d9')
#Define custom tick labels for colour bar.
tick_labels = {'0': '0', '5': '5', '10':'10', '15':'15', '20':'20', '25':'25', '30':'30','35':'35', '40': '> 40'}


#Add in the interactive tools
hover = HoverTool(tooltips = [ ('Local Authority','@area'),('Needs Score', '@average'), ('Polling', '@polls')])
zoom = WheelZoomTool()
reset = ResetTool()
pan = PanTool()
save = SaveTool()


#Create colour bar 
color_bar = ColorBar(color_mapper=color_mapper, label_standoff=8,width = 500, height = 20,
                     border_line_color=None,location = (0,0), orientation = 'horizontal', major_label_overrides = tick_labels)


#Create map, adds in tools, removes axis 
p = figure(title = 'Community Needs Scores, 2016', plot_height = 1300 , plot_width = 800, tools = [hover, zoom, reset, pan, save])

p.xgrid.grid_line_color = None
p.ygrid.grid_line_color = None
p.axis.visible = False
#Add patch renderer to figure. 
p.patches('xs','ys', source = geosource,fill_color = {'field' :'average', 'transform' : color_mapper},
          line_color = 'black', line_width = 0.25, fill_alpha = 1)


#Specify layout
p.add_layout(color_bar, 'below')
# Define the callback function: update_plot
#def update_plot(attr, old, new):
    #yr = slider.value
    #new_data = json_data()
    #geosource.geojson = new_data
    #p.title.text = 'Community Needs Scores' %yr
   
  

# Make a slider object
#slider = Slider(title = 'Year',start = 2000, end = 2016, step = 1, value = 2016)
#slider.on_change('value', update_plot)

# Make a selection object: select
#select = Select(title='Select Criteria:', value='Needs Score', options=['Needs Score','Polling'])
#select.on_change('value', update_plot)

# Make a column layout of widgetbox(slider) and plot, and add it to the current document
layout = column(p)
#layout = column(p, select, slider)
curdoc().add_root(layout)
#Display plot inline in Jupyter notebook
#output_notebook()
#Display plot
#show(layout)

#NOTE: The year slider only works when you embed the map on a webpage or run it via a Bokeh server. 


# In[ ]:




