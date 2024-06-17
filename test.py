packages = ['numpy','pandas','matplotlib','plotly']

def import_or_install(packages):
    import pip
    for package in packages:
        try:
            __import__(package)
        except ImportError:
            pip.main(['install', package])

import plotly.graph_objs as go
# import plotly.express as px
from sklearn.preprocessing import MinMaxScaler
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
nifty_data_pct = nifty_data.pct_change()*100

month_order = {"January": 1, "February": 2, "March": 3, "April": 4, "May": 5, "June": 6,
               "July": 7, "August": 8, "September": 9, "October": 10, "November": 11, "December": 12}

# Create a new DataFrame with weekdays, week numbers, and month names
heatmap_data = pd.DataFrame({
    'Date': nifty_data_pct.index.date,
    'Weekday': nifty_data_pct.index.weekday,
    'Week Number': nifty_data_pct.index.isocalendar().week,
    'Month Name': nifty_data_pct.index.strftime('%B'),
    'Percentage Change': nifty_data_pct.values
})

# heatmap_data = heatmap_data.sort_values(by='Week Number', ascending=True)

heatmap_data = heatmap_data.sort_values(by='Week Number', ascending=False)

# Ensure 'Weekday' is less than 7 to include only days of the week
heatmap_data = heatmap_data[heatmap_data['Weekday'] < 7]

# Adjust the 'Week Number' to align with the calendar start
first_weekday_of_year = heatmap_data['Date'].min().weekday()
# Add a 'Day Name' column to your DataFrame
heatmap_data['Day Name'] = heatmap_data['Date'].apply(lambda x: calendar.day_name[x.weekday()])

# Sort heatmap_data by 'Month Name' and 'Week Number'
heatmap_data.sort_values(by=['Month Name', 'Week Number'], key=lambda x: heatmap_data['Month Name'].map(month_order), inplace=True)

# Reset the index of the sorted DataFrame
heatmap_data.reset_index(drop=True, inplace=True)

# This assumes that 'Week Number' and 'Date' are both columns in heatmap_data
week_to_date = heatmap_data[['Week Number', 'Date']].drop_duplicates().set_index('Week Number')['Date'].to_dict()

# Convert 'Percentage Change' to percentage format
# heatmap_data['Percentage Change'] = (heatmap_data['Percentage Change'] * 100).apply(lambda x: f'{x:.2f}%')

pivot_table = heatmap_data.pivot_table(
    values='Percentage Change', 
    index='Day Name', 
    columns=['Month Name', 'Week Number'], 
    aggfunc='mean'
)


# Create a temporary 'sort_key' based on 'Month Name' and 'Week Number'
sort_key = pivot_table.columns.to_frame(index=False)
sort_key['Month Sort'] = sort_key['Month Name'].map(month_order)
sort_key['Week Sort'] = sort_key['Week Number'].astype(int)
sort_key.sort_values(by=['Month Sort', 'Week Sort'], inplace=True)

# Use the sorted 'sort_key' to reindex the columns of the pivot table
pivot_table = pivot_table.reindex(columns=sort_key.set_index(['Month Name', 'Week Number']).index)

month_names = pivot_table.columns.get_level_values('Month Name').unique()

truncated_month_names = [name[:3] for name in month_names]

month_positions = []
cumulative_length = 0

for month_name in month_names:
    # Get the group for the current month
    group = heatmap_data[heatmap_data['Month Name'] == month_name]
    
    # Calculate the position based on the minimum week number for the current month
    cumulative_length = group['Week Number'].median() -1.5
    
    # Append the position to the list
    month_positions.append(cumulative_length)

# Assuming 'week_to_date' is a dictionary mapping week numbers to dates
# x_labels = [week_to_date.get(week, '') for week in pivot_table.columns.get_level_values('Week Number')]
# x_labels = [date.strftime('%b W%U') for date in x_labels]
# combined aboe 2 lines in to single line below
x_labels = [week_to_date.get(week, '').strftime('%b W%U') for week in pivot_table.columns.get_level_values('Week Number')]
y_labels = ['Friday', 'Thursday', 'Wednesday', 'Tuesday', 'Monday']

fig = go.Figure(data=go.Heatmap(
        z=pivot_table.values,
        x=x_labels,  # Use the list of dates as x-axis labels
        y=y_labels,
        colorscale='Viridis'
))

cumulative_length = 0
shapes = []

for month_name, group in heatmap_data.groupby('Month Name', sort=False):
    # Get the minimum week number for the current month
    # Calculate the cumulative length based on the minimum week number
    cumulative_length = group['Week Number'].min()-1    
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
# Now, use the 'shapes' list to update your plot with the month separators


fig.update_layout(
    title='Nifty 50 Daily Closing Percentage Change',
    xaxis=dict(
        tickmode='array',
        tickvals=month_positions,
        ticktext=truncated_month_names,
        tickangle=0
    ),
    yaxis=dict(
        tickvals=[i for i in range(pivot_table.shape[0])],
        # ticktext=[day_name for day_name in pivot_table.index.get_level_values('Day Name').unique()]
        ticktext=y_labels
    ),
    height=60 * len(pivot_table.index), # Adjust 60 to a suitable value based on your data
    shapes=shapes
)


# Assuming 'nifty_data_pct' is your DataFrame with percentage change values
scaler = MinMaxScaler()

# Reshape data for the scaler if it's a Series
if isinstance(nifty_data_pct, pd.Series):
    nifty_data_pct = nifty_data_pct.values.reshape(-1, 1)

normalized_data = scaler.fit_transform(nifty_data_pct)

# Convert back to DataFrame
normalized_df = pd.DataFrame(normalized_data, columns=['Normalized Values'])

print(normalized_df)
# Assuming 'normalized_df' is your DataFrame with the normalized values
mean = normalized_df['Normalized Values'].mean()
std_dev = normalized_df['Normalized Values'].std()

# Data within 1 standard deviation
data_within_1_std_dev = normalized_df[(normalized_df['Normalized Values'] > (mean - std_dev)) & (normalized_df['Normalized Values'] < (mean + std_dev))]

# Data within 2 standard deviations
data_within_2_std_dev = normalized_df[(normalized_df['Normalized Values'] > (mean - 2*std_dev)) & (normalized_df['Normalized Values'] < (mean + 2*std_dev))]

print("Data within 1 Standard Deviation:\n", data_within_1_std_dev)
print("Data within 2 Standard Deviations:\n", data_within_2_std_dev)

# Assuming 'normalized_df' is your DataFrame with the normalized values
fig = px.line(normalized_df, x=normalized_df.index, y='Normalized Values', title='Normalized Data Plot')

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

