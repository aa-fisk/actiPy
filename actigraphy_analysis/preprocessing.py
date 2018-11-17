import pandas as pd
# This script contains functions which are useful for preprocessing of
# actigraphy data

# function to remove column if object
def remove_object_col(data, return_cols=False):
    """
    Function to check the data type in each column
    and drop it if it is an object
    does not distinguish between float, int, strings
    :param data: pandas dataframe to check
    :param return_cols: Boolean - default False, returns columns as a list
    :return: pandas dataframe without object columns
    :return: if return_cols is true, returns list of dropped columns
    """

    # Check each column type
    # drop the columns that are objects
    # return the dataframe

    dropped_cols = []
    if hasattr(data, "name"):
        name = data.name
    else:
        name = "NaN"
    for column in data.columns:
        column_data = data.loc[:, column]
        if column_data.dtype == 'O':
            current_col = data.loc[:, column]
            dropped_cols.append(current_col)
            data = data.drop(column, axis=1)
    data.name = name
    
    if return_cols:
        return data, dropped_cols
    else:
        return data


# Function to split dataframe into periods based on label_column
def separate_by_condition(data, label_col=-1):
    """
    Function to separate activity data based upon the condition
    defined by a label column. e.g. separate into "Baseline",
    "Disrupted", "Post_Baseline"
    :param data: Dataframe to split, requires label column
    :param label_col: int, which column to select based upon, default -1
    :return: list of dataframes, length of list determined by
        number of unique labels
    """

    # select the unique values in the label column
    # slice the data based upon the label column values
    # append to list and return list of separated dataframes

    unique_conditions = data.iloc[:, label_col].unique()
    # remove nan values
    unique_conditions = unique_conditions[~pd.isnull(unique_conditions)]
    list_of_dataframes_by_condition = []
    for condition in unique_conditions:
        temporary_sliced_data = data[data.iloc[:, label_col] == condition]
        temporary_sliced_data.name = condition
        list_of_dataframes_by_condition.append(temporary_sliced_data)

    return list_of_dataframes_by_condition


# Function to read files in as a pandas dataframe in standard way
def read_file_to_df(file_name,
                    index_col=0,
                    header=0):
    """
    function to take given csv file name and turn it into a df
    :param file_name:
    :return:
    """

    # quick error handling to see if is a csv file
    if file_name.suffix != ".csv":
        raise ValueError("Not a csv file")
    df = pd.read_csv(file_name,
                     index_col=index_col,
                     header=header,
                     parse_dates=True)
    name = file_name.stem
    df.name = name
    return df


# Function to check subdirectory and create if doesn't exist
def create_subdir(input_directory, subdir_name):
    """
    Function takes in Path object of input_directory
    and string of subdir name, adds them together, checks if it
    exists and if it doesn't creates new directory

    :param input_directory:
    :param subdir_name:
    :return:
    """

    # create path name
    # check if exists
    # create it if it doesn't exist
    # return path name

    sub_dir_path = input_directory / subdir_name
    if not sub_dir_path.exists():
        sub_dir_path.mkdir()
    return sub_dir_path


# Function to create file_name_path
def create_file_name_path(directory, file, save_suffix):
    """
    Simple function to put together directory, file.stem,
    and suffix to create path
    :param directory:
    :param file:
    :param save_suffix:
    :return:
    """
    # define the file name
    if isinstance(file, str):
        name = file
    else:
        name = file.stem
    
    # combine directory, name and save suffix
    file_path = directory / (name + save_suffix)
    return file_path


# Create save_pipeline class with objects
# for saving csv and plots depending on the method used
class SaveObjectPipeline:
    """
    Class object for saving data to a file.
    Main object used for processing data and saving it to a directory
    Separate methods for saving dataframes to csv files
    and for creating
    and saving plots to a file

    init method globs all the files in the input_directory
    and creates a df_list with dataframes of all the files in
    the input_directory

    Takes the arguments initially of
    Input_directory - place to search for files to process
    Subdir_name - name for subdirectory to be created
        in input_directory to hold new files
    search_suffix - default .csv, name to glob for files in input_directory

    """

    # init method to create attributes
    def __init__(self,
                 input_directory="",
                 save_directory="",
                 subdir_name="",
                 func=(globals(),
                       "read_file_to_df"),
                 search_suffix=".csv",
                 readfile=True,
                 **kwargs):
        
        # create the lists to be used later and save the arguments as
        # object attributes
        self.input_directory = input_directory
        self.search_suffix = search_suffix
        self.save_directory = save_directory
        self.subdir_name = subdir_name
        self.processed_list = []
        self.processed_file_list = []

        # create the file list by globbing for the search suffix
        self.file_list = sorted(
            self.input_directory.glob("*" +
            self.search_suffix)
        )
        
        # create the subdirectory in the save dir
        self.subdir_path = create_subdir(
            self.save_directory,
            subdir_name=self.subdir_name
        )

        # read all the dfs into a list
        self.object_list = []
        if readfile:
            read_fx = getattr(func[0], func[1])
            for file in self.file_list:
                temp_df = read_fx(file,
                                  **kwargs)
                self.object_list.append(temp_df)

    # method for saving a csv file
    def process_file(self,
                     function=(),
                     save_suffix='.csv',
                     savecsv=False,
                     object_list=None,
                     file_list=None,
                     **kwargs):
        """
        Method that applies a defined function to all the
        dataframes in the df_list and saves them to the subdir that
        is also created

        :param function_name:
        :param save_suffix:
        :param subdir_name
        :return:
        """
        
        # define the function to be used for processing
        func = getattr(function[0], function[-1])
        
        # set the default lists to iterate through
        if not object_list:
            object_list = self.object_list
        if not file_list:
            file_list = self.file_list
            
        # iterate through the objects and call the function on each one
        for object, file in zip(object_list, file_list):
            temp_df = func(object,**kwargs)
            self.processed_list.append(temp_df)
            # create the file name path and put in attribute list
            file_name_path = create_file_name_path(
                self.subdir_path,
                file,
                save_suffix
            )
            self.processed_file_list.append(file_name_path)
            # save the csv to the subdirectory if asked to do so
            if savecsv:
                temp_df.to_csv(file_name_path)

    # method for saving a plot
    def create_plot(self,
                    function=(),
                    save_suffix='.png',
                    data_list=None,
                    file_list=None,
                    remove_col=True,
                    subdir_path=None,
                    **kwargs):
        """
        Method to take each df and apply given plot function and save to file
        Default parameters of showfig = False
        and savefig = True but can be changed

        :type save_suffix: str
        :param save_suffix:
        :param dpi:
        :param function_name:
        :param showfig:
        :param savefig:
        :return:
        """

        # grab the function as an attribute so can properly call
        # if called as a string does odd things
        func = getattr(function[0], function[1])
        
        # define the lists to iterate through
        if data_list is None:
            data_list = self.object_list
        if file_list is None:
            file_list = self.file_list
        if subdir_path is None:
            subdir_path = self.subdir_path
        
        # loop through the dfs and pass to plotting function
        for df, file in zip(data_list, file_list):
            file_name_path = create_file_name_path(
                subdir_path,
                file,
                save_suffix
            )
            if remove_col:
                temp_df = remove_object_col(df, return_cols=False)
            else:
                temp_df = df.copy()
            func(temp_df,
                 fname=file_name_path,
                 **kwargs)


######### Group of functions for split by period function ##########

def create_period_index(data, period=None):
    """
    Function to create a list of timestamps
    that vary by the given period
    which can then be used to slice a dataframe by
    :param data: timestamp indexed data
        so can grab the start and end for the period range
    :param period: in "%H %T" format
        defaults to 24H 0T if not given
    :return: list of timestamps a given period apart
    """

    # set the default value for period if not given

    if not period:
        period = "24H 0T"

    # grab the start and the end of the data
    # index and use this to create the range
    start, end = data.index[0], data.index[-1]

    # create period range using these parameters
    period_index_list = pd.date_range(start=start,
                                      end=end,
                                      freq=period)

    return period_index_list


def slice_dataframe_by_index(data_series, index_list):
    """
    Function that takes a timestamp indexed
    series and slices according to the indexes
    provided in the index list
    Returns a dataframe of generically indexed values
    with each period in a separate column
    :param data_series: datetimeindex series
    :param index_list: output of create_period_index expected,
        list of datetimes to slice by
    :return: generically indexed dataframe with each period in
        a separate column
    """

    # loop through each day and append the values to a list
    data_by_day_list = []
    for day_start, day_end in zip(index_list[:-1], index_list[1:]):
        day_data = data_series.loc[day_start:day_end].values
        data_by_day_list.append(day_data)

    # append the final day of data as well
    final_day_start = index_list[-1]
    final_day_data = data_series.loc[final_day_start:].values
    data_by_day_list.append(final_day_data)

    # concat into one large dataframe
    period_sliced_dataframe = pd.DataFrame(data_by_day_list).T

    return period_sliced_dataframe

def create_ct_based_index(period_sliced_data, CT_period=None):
    """
    Create new index for data based on a given length of circadian time
    given want the dataframe to be indexed to be
    equivalent to 24 hours, needs to be reindexed
    at a frequency of seconds and miliseconds to
    get required accuracy
    :param period_sliced_data: data sliced by period with generic index
        used to get length of new bins
    :param CT_period: defaults to "24H 0T" can change if required
    :return: datetimeindex
    """

    # set the default CT value
    if not CT_period:
        CT_period = "24H 0M"

    # create new index frequency from how close the
    # old dataframe is in seconds to 24 hours
    CT_seconds = pd.Timedelta(CT_period).total_seconds()
    dataframe_seconds = len(period_sliced_data)
    ratio_seconds = CT_seconds/dataframe_seconds
    int_seconds = int(ratio_seconds)
    miliseconds = round((ratio_seconds - int_seconds)*1000)
    new_frequency = str(int_seconds) + "S " + str(miliseconds) + "ms"

    # create new index from frequency and length of dataframe
    new_index = pd.timedelta_range(start="0S",
                                   freq=new_frequency,
                                   periods=dataframe_seconds)

    return new_index

def split_dataframe_by_period(data,
                              animal_number,
                              period=None,
                              CT_period=None):
    """
    Function to split a long dataframe into
    each day given by period as a different column
    indexed by *circadian* time
    :param data: datetimeindexed dataframe
    :param animal_number: which column to slice
    :param period: default 24H, period to slice by
    :param CT_period: default 24H, circadian period to index final 
        dataframe by
    :return: CT period datetime indexed dataframe   
        with each day in a subsequent column
    """

    # create index of days to slice by
    period_based_index = create_period_index(data, period)

    # select just the animal we want and slice that
    animal_data_series = data.iloc[:, animal_number]
    period_sliced_data = slice_dataframe_by_index(animal_data_series,
                                                  period_based_index)

    # create the new index and re-index the data
    new_index = create_ct_based_index(period_sliced_data, CT_period)
    period_sliced_data.index = new_index

    # tidy up columns to equal day numbers
    # and name to equal animal name
    number_of_days = len(period_sliced_data.columns)
    period_sliced_data.columns = range(number_of_days)
    animal_label = data.columns[animal_number]
    period_sliced_data.name = animal_label

    return period_sliced_data

def split_entire_dataframe(data,
                           period=None,
                           CT_period=None):
    """
    applies split_dataframe_by_period to each animal in turn in the dataframe
    :param data: dataframe
    :param period: default none
    :param CT_period: default none.
    :param label col: not using as assuming already dropped before coming
        into this function
    :return: list of split dataframes
    """
    
    # apply split to each column
    # and save in a list
    # return the list
    split_df_list = []
    for num, column in enumerate(data.columns):
        temp_split_df = split_dataframe_by_period(data,
                                                  num,
                                                  period=period,
                                                  CT_period=CT_period)
        temp_split_df.name = column
        split_df_list.append(temp_split_df)
    return split_df_list

def remap_LDR(data, LDR_col=-1, invert=True):
    """
    Function to remap LDR values from light = high to
    light = low - allows easier plotting of actigraphy data
    because colouring in the light phase is UGLY
    :param light_data:
    :return:
    """
    # remap the LDR data to 150 as max then take 150
    # from the values to code darkness
    light_data = data.iloc[:,LDR_col].copy()
    # select from the first value >1 and
    # the last value > 1
    high_light_index = light_data.loc[light_data>150].index
    start = data.index.get_loc(high_light_index[0])
    end = data.index.get_loc(high_light_index[-1])
    light_data.loc[light_data>150] = 150
    if invert:
        light_data = 150 - light_data
    data_new = data.iloc[:,:].copy()
    data_new.iloc[start:end,LDR_col] = light_data
    return data_new


def slice_by_label_col(data,
                       label_col=-1,
                       section_label="disrupted",
                       baseline_length="6D",
                       post_length="16D"):
    """
    Function to slice the dataframe into a shorter period based on the
    label column. Primary use for defining times to use for
    creating pretty actograms
    :param data:
    :param label_col:
    :param section_label:
    :param baseline_length: how many days before disruption
        starts to slice
    :param post_length: how many days (or just time period
        generally) to slice afterwards
    :return:
    """
    
    start_timeshift = pd.Timedelta(baseline_length)
    end_timeshift = pd.Timedelta(post_length)
    disrupted_index = data[data.iloc[:,label_col]==section_label].index
    start = disrupted_index[0] - start_timeshift
    end = disrupted_index[-1] + end_timeshift
    data_new = data.loc[start:end].copy()
    return data_new