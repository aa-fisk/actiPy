# scripts to plot mean activity +/- sem

import pandas as pd
idx = pd.IndexSlice
import numpy as np
import matplotlib.pyplot as plt
import actiPy.preprocessing as prep
from actiPy.plots import multiple_plot_kwarg_decorator, set_title_decorator

@set_title_decorator
@multiple_plot_kwarg_decorator
def plot_means(data, **kwargs):
    
    """
    Function to plot the mean wave form from a split df
    :param grouped:
    :param kwargs:
    :return:
    """
    
    ## TODO  Refactor so can plot mean of individual separately

    # find the conditions
    vals = data.index.get_level_values(0).unique()
    no_conditions = len(vals)

    # plot each condition on a separate subplot
    fig, ax = plt.subplots(nrows=no_conditions,
                           sharey=True,
                           sharex=True)
    for val, axis in zip(vals, ax):
        df = data.loc[val]
        mean = df.mean(axis=1)
        sem = df.sem(axis=1)

        axis.plot(mean)
        axis.fill_between(df.index, mean-sem, mean+sem, alpha=0.5)
        
        axis.set_ylabel(val)

    fig.subplots_adjust(hspace=0)
    
    params_dict = {
        "timeaxis": True,
        "interval": 6,
        "title": "Mean activity for each condition",
        "ylabel": "Mean activity +/- sem",
        "xlabel": "Circadian Time",
        "xlim": [df.index[0], (df.index[0] + pd.Timedelta('24H'))]
    }
    
    return fig, axis, params_dict

def plot_wave_from_df(data,
                      level: int=0,
                      **kwargs):
    """
    Takes input, groupsby values of level and passes split df to plot_means
    :param data:
    :param level:
    :return:
    """

    grouped = data.groupby(level=level).apply(prep.split_all_animals, **kwargs)
    
    grouped_cols = grouped.groupby(axis=1, level=level).mean()
    
    plot_means(grouped_cols, **kwargs)


def group_mean_df(df: pd.DataFrame,
                  col_name: str="Individual means"):
    """
    Takes in a long form dataframe with 4 level multiindex
    takes individual means of all columns
    then takes mean and sem of level 3
    :param df:
    :param col_name:
    :return:
    """
    # get values of each level we will loop through to select right animal
    condition_names = df.index.get_level_values(0).unique()
    light_periods = df.index.get_level_values(1).unique()
    animal_numbers = df.index.get_level_values(2).unique()

    # create new df with same index and single column
    mean_df = pd.DataFrame(index=df.index,
                           columns=[col_name])

    # loop through all the parts and get the individual means and put in new mean df
    for condition in condition_names:
        for section in light_periods:
            for animal in animal_numbers:
                temp_mean = df.loc[idx[condition, section, animal]].mean(axis=1)
                mean_df.loc[idx[condition, section, animal], col_name] = \
                    temp_mean.values
     
    mean_df = mean_df.astype(np.float64)

    # swap the animal level to the columns, then take the group means and sems
    # from there
    mean_swap = mean_df.unstack(level=2)
    mean_swap.columns = mean_swap.columns.droplevel(0)
    mean_swap_hourly = mean_swap.groupby(level=[0,1]
                                         ).resample("H", level=2,
                                                   loffset=pd.Timedelta("30M")
                                                   ).mean()
    mean_animals = mean_swap_hourly.mean(axis=1)
    sem_animals = mean_swap_hourly.sem(axis=1)

    # put the mean and sem values into a new df
    group_mean_df = pd.DataFrame(mean_animals)
    group_mean_df.columns = ['Group mean']
    group_mean_df["sem"] = sem_animals
    
    return group_mean_df
