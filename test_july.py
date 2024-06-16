packages = ['numpy','july','warnings','matplotlib']

def import_or_install(packages):
    import pip
    for package in packages:
        try:
            __import__(package)
        except ImportError:
            pip.main(['install', package])


import_or_install(packages)

import numpy as np
import july
from july.utils import date_range
import warnings
import matplotlib

warnings.filterwarnings("ignore", category=matplotlib.MatplotlibDeprecationWarning)
warnings.filterwarnings("ignore", category=DeprecationWarning)

dates = date_range("2020-01-01", "2020-12-31")
data = np.random.randint(0, 14, len(dates))
july.heatmap(dates, data, title='Github Activity', cmap="github")

july.heatmap(
    osl_df.date, # Here, osl_df is a pandas data frame.
    osl_df.temp, 
    cmap="golden", 
    colorbar=True, 
    title="Average temperatures: Oslo , Norway"
)
