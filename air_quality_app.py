import pandas as pd
import plotly.express as px
from dash import Dash, dcc, html, Input, Output
import os

# Disable Flask's dotenv loading
os.environ["FLASK_SKIP_DOTENV"] = "1"

# Load and prepare data *******************************************
la_pm25 = pd.read_csv("laPMTwoFive.csv")
la_ozone = pd.read_csv("laOzone.csv")

la_pm25["Date"] = pd.to_datetime(la_pm25["Date"], format="%m/%d/%Y")
la_ozone["Date"] = pd.to_datetime(la_ozone["Date"], format="%m/%d/%Y")

# Rest of your code...

# App Layout ******************************************************
stylesheets = ["https://codepen.io/chriddyp/pen/bWLwgP.css"]
app = Dash(__name__, external_stylesheets=stylesheets)


app.layout = html.Div([
    html.H1("Los Angeles Air Quality Analysis", style={"textAlign": "center"}),

    dcc.Dropdown(
        id="pollutant-dropdown",
        options=[
            {"label": "PM2.5 Levels", "value": "pm2.5"},
            {"label": "Ozone Levels", "value": "ozone"}
        ],
        value="pm2.5",
        clearable=False
    ),

    dcc.Graph(id="air-quality-graph"),
])


# Callbacks *******************************************************
@app.callback(
    Output("air-quality-graph", "figure"),
    [Input("pollutant-dropdown", "value")]
)
def update_graph(selected_pollutant):
    if selected_pollutant == "pm2.5":
        df = la_pm25
        y_axis = "Daily Mean PM2.5 Concentration"  # Update this to match your actual column name
        title = "PM2.5 Levels Over Time"
    else:
        df = la_ozone
        y_axis = "Ozone"  # Update this to match your actual column name in the ozone CSV
        title = "Ozone Levels Over Time"

    fig = px.line(
        df,
        x="Date",  # Changed from "date" to "Date"
        y=y_axis,
        title=title,
        labels={"Date": "Date", y_axis: "Concentration"}
    )
    return fig


if __name__ == "__main__":
    app.run_server(debug=True)
