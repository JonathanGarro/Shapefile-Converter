#!/usr/bin/env python3

#!/usr/bin/env python3
"""
Shapefile to CSV Converter

Script reads a shapefile (.shp) and converts it to a CSV file,
handling different geometry types and extracting coordinate information.

Requirements:
- geopandas
- pandas
- fiona
- shapely

Install with pip install geopandas pandas fiona shapely
"""

import os
import sys
import argparse
import geopandas as gpd
import pandas as pd
from pathlib import Path


def convert_shapefile_to_csv(shp_path, csv_path=None, include_geometry=True, coord_format='separate'):
		"""
		Convert a shapefile to CSV format.
		
		Parameters:
		-----------
		shp_path : str
				Path to the input shapefile (.shp)
		csv_path : str, optional
				Path for output CSV file. If None, uses same name as shp file
		include_geometry : bool, default True
				Whether to include geometry information in the output
		coord_format : str, default 'separate'
				How to handle coordinates:
				- 'separate': Create separate lat/lon columns for points
				- 'wkt': Include geometry as Well-Known Text
				- 'centroid': Use centroid coordinates for polygons/lines
				- 'none': Exclude geometry entirely
		
		Returns:
		--------
		str: Path to the created CSV file
		"""
	
		if not os.path.exists(shp_path):
				raise FileNotFoundError(f"Shapefile not found: {shp_path}")
			

		try:
				gdf = gpd.read_file(shp_path)
				print(f"Successfully loaded {len(gdf)} features")
				print(f"Geometry type(s): {gdf.geometry.geom_type.unique()}")
				print(f"Coordinate Reference System: {gdf.crs}")
		except Exception as e:
				raise Exception(f"Error reading shapefile: {e}")
			
		if csv_path is None:
				csv_path = str(Path(shp_path).with_suffix('.csv'))
			
		# handle coordinate system and convert to WGS84 if needed
		if gdf.crs and gdf.crs.to_epsg() != 4326:
				gdf = gdf.to_crs('EPSG:4326')
			
		# create working copy
		df = gdf.copy()
	
		# handle geometry based on coord_format parameter
		if coord_format == 'none' or not include_geometry:
				df = df.drop(columns=['geometry'])
			
		elif coord_format == 'separate':
				geom_types = df.geometry.geom_type.unique()
			
				if 'Point' in geom_types:
						# for points snag X and Y coordinates
						df['longitude'] = df.geometry.x
						df['latitude'] = df.geometry.y
				else:
						# for polygons/lines use centroid
						centroids = df.geometry.centroid
						df['longitude'] = centroids.x
						df['latitude'] = centroids.y
						df['geometry_type'] = df.geometry.geom_type
					
				df = df.drop(columns=['geometry'])
			
		elif coord_format == 'centroid':
				centroids = df.geometry.centroid
				df['longitude'] = centroids.x
				df['latitude'] = centroids.y
				df['geometry_type'] = df.geometry.geom_type
				df = df.drop(columns=['geometry'])
			
		elif coord_format == 'wkt':
				# convert geometry to Well-Known Text format
				# not sure if this is the best way to handle conversion?
				df['geometry_wkt'] = df.geometry.to_wkt()
				df['geometry_type'] = df.geometry.geom_type
				df = df.drop(columns=['geometry'])
			
		# clean up any remaining geometry columns that pandas can't read
		for col in df.columns:
				if df[col].dtype == 'object':
						try:
								if hasattr(df[col].iloc[0], 'geom_type'):
										df[col] = df[col].astype(str)
						except (IndexError, AttributeError):
								pass
							
		# save output
		try:
				df.to_csv(csv_path, index=False)
				print(f"Successfully saved CSV to: {csv_path}")
				print(f"CSV shape: {df.shape}")
				print(f"Columns: {list(df.columns)}")
				return csv_path
		except Exception as e:
				raise Exception(f"Error saving CSV file: {e}")
			
			
def main():
		"""Command line interface for the shapefile converter."""
		parser = argparse.ArgumentParser(
				description="Convert shapefile to CSV format",
				formatter_class=argparse.RawDescriptionHelpFormatter,
				epilog="""
Examples:
	# Basic conversion
	python shapefile_reader.py input.shp
	
	# Specify output file
	python shapefile_reader.py input.shp -o output.csv
	
	# Use centroid coordinates for all geometries
	python shapefile_reader.py input.shp --coord-format centroid
	
	# Include geometry as WKT
	python shapefile_reader.py input.shp --coord-format wkt
	
	# Exclude geometry entirely
	python shapefile_reader.py input.shp --coord-format none
				"""
		)
	
		parser.add_argument('shapefile', help='Path to input shapefile (.shp)')
		parser.add_argument('-o', '--output', help='Output CSV file path')
		parser.add_argument('--coord-format', 
												choices=['separate', 'wkt', 'centroid', 'none'],
												default='separate',
												help='How to handle coordinates (default: separate)')
		parser.add_argument('--no-geometry', action='store_true',
												help='Exclude geometry information entirely')
	
		args = parser.parse_args()
	
		try:
				include_geometry = not args.no_geometry
				csv_path = convert_shapefile_to_csv(
						args.shapefile, 
						args.output,
						include_geometry=include_geometry,
						coord_format=args.coord_format
				)
			
				print(f"\nConversion completed successfully!")
				print(f"Output file: {csv_path}")
			
				df = pd.read_csv(csv_path)
				print(f"\nPreview of first 5 rows:")
				print(df.head().to_string())
			
		except Exception as e:
				print(f"Error: {e}")
				sys.exit(1)
			
			
if __name__ == "__main__":
		main()