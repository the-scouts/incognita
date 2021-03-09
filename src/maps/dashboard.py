import dash
import dash_core_components as dcc
import dash_html_components as html

from src.base import Base


class Dashboard(Base):
    def __init__(self):
        super().__init__()
        self.app = dash.Dash(__name__, external_stylesheets=["https://codepen.io/chriddyp/pen/bWLwgP.css"])

        self.app.layout = html.Div(
            [
                html.H1("Central Yorkshire Scouts Uptake and IMD Decile Map"),
                html.Iframe(
                    # fmt: off
                    id="map", width="100%", height="600",
                    srcDoc=open("Example Output/central_yorkshire_uptake_imd_map.html", "r").read(),
                    # fmt: on
                ),
            ]
        )

        self.input_layout = html.Div([dcc.Upload(id="upload-scout-data", children=html.Div(["Add Census with ONS Postcode Directory", html.A("Select Files")]))])

    def run(self):
        self.app.run_server(debug=False)
