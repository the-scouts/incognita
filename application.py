from pathlib import Path

import dash
import dash_core_components as dcc
import dash_html_components as html

dashboard = dash.Dash(__name__, external_stylesheets=["https://codepen.io/chriddyp/pen/bWLwgP.css"])

dashboard.layout = html.Div(
    [
        html.H1("Central Yorkshire Scouts Uptake and IMD Decile Map"),
        html.Iframe(
            id="map",
            width="100%",
            height="600",
            srcDoc=Path("Example Output/central_yorkshire_uptake_imd_map.html").read_text(),
        ),
    ]
)

dashboard.input_layout = html.Div([dcc.Upload(id="upload-scout-data", children=html.Div(["Add Census with ONS Postcode Directory", html.A("Select Files")]))])

if __name__ == "__main__":
    dashboard.run_server(debug=False)
else:
    app = dashboard.server
