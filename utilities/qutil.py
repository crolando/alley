# Some utilities to give tclbrep users a more familiar experience
# with qgis, since it's so different.  This really only makes sense
# to load in qgis 3.6 in the python console.  To import this into
# the console, make sure this py file is on the search path like this:
# https://docs.python.org/3/tutorial/modules.html#the-module-search-path
#
# and then you simply type in "import qutil", then execute the functions
# using qutil.func_name()

from qgis.core import *
from qgis.utils import *
import processing
import sys
import os

# This lets you load a shapefile for editing in a non-destructive way
def load_shape_to_mem_layer(shapefile_path: str, add_to_project: bool = True):
	layer_name = os.path.split(shapefile_path)[1]
	shp_layer = QgsVectorLayer(shapefile_path, layer_name, "ogr")
	if not shp_layer.isValid():
		print(shapefile_path + "Layer failed to load!")
		return
	shp_layer.selectAll()	
	mem_layer = processing.run("native:saveselectedfeatures", {'INPUT': shp_layer, 'OUTPUT': 'memory:'})['OUTPUT']	
	mem_layer.setName("mem " + layer_name)
	if add_to_project:
		QgsProject.instance().addMapLayer(mem_layer)
	return mem_layer

# Takes a mem layer and saves it to a shapefile.
def save_mem_layer_to_shape(mem_layer: QgsVectorLayer, shapefile_path: str, add_to_project: bool = True):
	error = QgsVectorFileWriter.writeAsVectorFormat(mem_layer, shapefile_path , "UTF-8", mem_layer.crs() , "ESRI Shapefile")
	if error[0] != QgsVectorFileWriter.NoError: 
		print("Failed to write shapefile: " + shapefile_path)
		print(error)
		return
	if add_to_project:
		layer_name = os.path.split(shapefile_path)[1]
		shape_layer = QgsVectorLayer(shapefile_path, layer_name , "ogr")
		if not shape_layer.isValid():
			print("Layer failed to load!")
			return
		else:
			QgsProject.instance().addMapLayer(shape_layer)
			return shape_layer
