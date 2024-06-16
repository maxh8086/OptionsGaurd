# Ensure you have the necessary packages installed
packages = ['numpy', 'pandas', 'yfinance', 'plotly']

def import_or_install(packages):
    import pip
    for package in packages:
        try:
            __import__(package)
        except ImportError:
            pip.main(['install', package])

import_or_install(packages)

import yfinance as yf
import pandas as pd
import plotly.figure_factory as ff
import webbrowser
from http.server import HTTPServer, SimpleHTTPRequestHandler
import threading

# Fetch historical data for Nifty 50
nifty_data = yf.download('^NSEI', period='1y')['Close']

# Calculate daily closing percentage change
nifty_data_pct = nifty_data.pct_change().dropna()

# Convert the index to a datetime index
nifty_data_pct.index = pd.to_datetime(nifty_data_pct.index)

# Create a dictionary of dates and their corresponding values
data = dict(zip(nifty_data_pct.index, nifty_data_pct.values))

# Create a Plotly figure for the calendar heatmap
fig = ff.create_calendar_heatmap(data, colorscale='Viridis')

# Save the figure to an HTML file
fig.write_html('nifty_calendar_heatmap.html')

# Define a function to serve files on localhost
def start_server():
    server_address = ('localhost', 8000)
    httpd = HTTPServer(server_address, SimpleHTTPRequestHandler)
    webbrowser.open('http://localhost:8000/nifty_calendar_heatmap.html')
    httpd.serve_forever()

# Start the server in a new thread
threading.Thread(target=start_server).start()
