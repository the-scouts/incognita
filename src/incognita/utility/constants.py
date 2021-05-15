from incognita.data import scout_census

_sections_model = scout_census.column_labels.sections
section_types = {section_model.type: section_name for section_name, section_model in _sections_model}

# EPSG values for the co-ordinate reference systems that we use
WGS_84 = 4326  # World Geodetic System 1984 (Used in GPS)
BNG = 27700  # British National Grid
