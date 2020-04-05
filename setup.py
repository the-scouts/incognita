from setuptools import setup, find_namespace_packages

setup(
    name="geo_mapping",
    url="https://github.com/the-scouts/geo_mapping",
    version="2.0.0",
    packages=find_namespace_packages(),
    install_requires=["pandas", "numpy", "folium", "branca", "geopandas", "shapely", "dash"],
    extras_require={"dev": ["pytest", "pytest-cov", "pre-commit"]},
    python_requires=">=3.7",
)
