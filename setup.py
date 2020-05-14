from setuptools import setup, find_namespace_packages

setup(
    name="geo_mapping",
    url="https://github.com/the-scouts/geo_mapping",
    version="0.2.0",
    packages=find_namespace_packages(),
    install_requires=["pandas", "numpy", "folium", "branca", "geopandas", "shapely", "dash", "pyarrow"],
    extras_require={"dev": ["pytest", "hypothesis", "pytest-cov", "pre-commit", "black"]},
    python_requires=">=3.7",
)
