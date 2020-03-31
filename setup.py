from setuptools import setup, find_namespace_packages

setup(
    name="geo_mapping",
    url="https://github.com/the-scouts/geo_mapping",
    packages=find_namespace_packages(),
    install_requires=['pandas', 'numpy', 'folium', 'branca', 'geopandas', 'shapely', 'dash'],
    extras_require={
        'dev': ['pytest', 'pytest-cov'],
    }
)
