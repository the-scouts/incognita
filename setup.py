from setuptools import setup, find_namespace_packages

setup(
    name="geo_mapping",
    packages=find_namespace_packages(),
    install_requires=['pandas', 'numpy', 'folium', 'branca', 'geopandas', 'shapely']
)
