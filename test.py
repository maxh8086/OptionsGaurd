import plotly.graph_objs as go
import pandas as pd
import yfinance as yf
import webbrowser
from http.server import HTTPServer, SimpleHTTPRequestHandler
import threading
import calendar
import time

# Fetch historical data for Nifty 50
nifty_data = yf.download('^NSEI', period='1y')['Close']

# Calculate daily closing percentage change and replace NaN with 0
nifty_data_pct = nifty_data.pct_change().fillna(0)


# Create a new DataFrame with weekdays, week numbers, and month names
heatmap_data = pd.DataFrame({
    'Date': nifty_data_pct.index.date,
    'Weekday': nifty_data_pct.index.weekday,
    'Week Number': nifty_data_pct.index.isocalendar().week,
    'Month Name': nifty_data_pct.index.strftime('%B'),
    'Percentage Change': nifty_data_pct.values
})

# Ensure 'Weekday' is less than 7 to include only days of the week
heatmap_data = heatmap_data[heatmap_data['Weekday'] < 7]

# Adjust the 'Week Number' to align with the calendar start
first_weekday_of_year = heatmap_data['Date'].min().weekday()
# Add a 'Day Name' column to your DataFrame
heatmap_data['Day Name'] = heatmap_data['Date'].apply(lambda x: calendar.day_name[x.weekday()])
pivot_table = heatmap_data.pivot_table(
    values='Percentage Change', 
    index='Day Name', 
    columns=['Month Name', 'Week Number'], 
    aggfunc='mean'
)

# Now, generate y_labels using the pivot table's MultiIndex
y_labels = [day_name for day_name in pivot_table.index.get_level_values('Day Name').unique()]

# Then use 'y_labels' for the y-axis in your heatmap
fig = go.Figure(data=go.Heatmap(
        z=pivot_table.values,
        x=pivot_table.columns,
        y=y_labels,
        colorscale='Viridis'
))

# Add month separators using shapes
month_lengths = heatmap_data.groupby('Month Name')['Week Number'].nunique()
cumulative_length = 0
shapes = []
for length in month_lengths:
    cumulative_length += length
    shapes.append({
        'type': 'line',
        'x0': cumulative_length - 0.5,
        'y0': -0.5,
        'x1': cumulative_length - 0.5,
        'y1': pivot_table.shape[0] - 0.5,
        'line': {
            'color': 'black',
            'width': 2,
        },
    })

# Update layout to include shapes and ensure weeks start on Monday
fig.update_layout(
    title='Nifty 50 Daily Closing Percentage Change',
    xaxis=dict(tickvals=[i for i in range(len(pivot_table.columns))],
               ticktext=[month_name for month_name in pivot_table.columns.get_level_values('Month Name').unique()],
               tickangle=-90),
    yaxis=dict(tickvals=[i for i in range(pivot_table.shape[0])],
               ticktext=[day_name for day_name in pivot_table.index.get_level_values('Day Name').unique()]),
    height=60 * len(pivot_table.index), # Adjust 100 to a suitable value based on your data
    shapes=shapes
)


# Save the figure to an HTML file
fig.write_html('nifty_calendar_heatmap.html')


class StoppableHTTPServer(HTTPServer):
    def run_forever(self):
        try:
            self.serve_forever()
        except KeyboardInterrupt:
            pass
        finally:
            self.server_close()

def start_server():
    server_address = ('localhost', 8000)
    httpd = StoppableHTTPServer(server_address, SimpleHTTPRequestHandler)
    webbrowser.open('http://localhost:8000/nifty_calendar_heatmap.html')
    httpd.run_forever()

# Start the server in a new thread
server_thread = threading.Thread(target=start_server)
server_thread.start()

# To stop the server, call server_thread.join() when you want to terminate it
# For example, after some time or based on some condition
time.sleep(10)  # Server will run for 10 seconds for demonstration purposes
server_thread.join()

