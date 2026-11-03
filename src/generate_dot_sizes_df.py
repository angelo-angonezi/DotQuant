# generate dot sizes df module

print('initializing...')  # noqa

# Code destined to generating
# a dot sizes summary df, adding
# time/condition/subgroup analysis
# cols to a joined dots dataframe.

######################################################################
# imports

print('importing required libraries...')  # noqa
from pandas import Series
from pandas import DataFrame
from argparse import ArgumentParser
from cet.io.dataframes import load_df
from cet.io.dataframes import save_df
from cet.dataframes.df_ops import add_col
from cet.io.files import get_skip_file_bool
from cet.dataframes.df_ops import add_constant_col
from cet.progress_tracker.ProgressTracker import ProgressTracker
from cet.dataframes.df_ops import filter_pandas_performance_warnings
print('all required libraries successfully imported.')  # noqa

# filtering Pandas Performance Warnings
filter_pandas_performance_warnings()

######################################################################
# argument parsing related functions


def get_args_dict() -> dict:
    """
    Parses command-line arguments and returns
    them as a dictionary.

    Returns:
        dict: A dictionary containing all parsed command-line arguments.
    """
    # defining program description
    description = "generate dot sizes df module"

    # creating a parser instance
    parser = ArgumentParser(description=description)

    # adding arguments to parser

    # input path param
    parser.add_argument('-i', '--input-path',
                        dest='input_path',
                        type=str,
                        required=True,
                        help='defines path to joined dots df [.csv]')

    # output path param
    parser.add_argument('-o', '--output-path',
                        dest='output_path',
                        type=str,
                        required=True,
                        help='defines path to output dot sizes summary df [.csv]')

    # overwrite output param
    parser.add_argument('-ow', '--overwrite-output',
                        dest='overwrite_output',
                        action='store_true',
                        required=False,
                        help='defines whether overwrite files in output folder (skips existing output by default)')

    # skip enter param
    parser.add_argument('-s', '--skip-enter',
                        dest='skip_enter',
                        action='store_true',
                        required=False,
                        help='defines whether to suppress "Enter to continue" input before execution')

    # creating arguments dictionary
    args_dict = vars(parser.parse_args())

    # returning the arguments dictionary
    return args_dict

######################################################################
# progress tracking related functions


class ModuleProgressTracker(ProgressTracker):
    """
    Defines ModuleProgressTracker class.
    """
    # defining ProgressTracker init
    def __init__(self) -> None:
        """
        Initializes a ModuleProgressTracker
        instance and defines class attributes.
        """
        # inheriting attributes and methods from ProgressTracker
        super().__init__()

    # overwriting class methods (using current module specific attributes)

    def get_progress_string(self) -> str:
        """
        Returns a formatted progress
        string, based on current progress
        attributes.

        Returns:
            str: The current progress string.
        """
        # assembling current progress string
        progress_string = f''

        # checking if iterations total has already been obtained
        if not self.totals_updated.is_set():

            # updating progress string based on attributes
            progress_string += f'calculating totals...'
            progress_string += f' {self.wheel_symbol}'
            progress_string += f' | dfs: {self.iterations_num}'
            progress_string += f' | iterations: {self.iterations_num}'
            progress_string += f' | elapsed time: {self.elapsed_time_str}'

        # if total iterations already obtained
        else:

            # updating progress string based on attributes
            progress_string += f'adding analysis cols...'
            progress_string += f' {self.wheel_symbol}'
            progress_string += f' | dfs: {self.current_iteration}/{self.iterations_num}'
            progress_string += f' | progress: {self.progress_percentage_str}'
            progress_string += f' | elapsed time: {self.elapsed_time_str}'
            progress_string += f' | ETC: {self.etc_str}'

        # returning progress string
        return progress_string

    def update_totals(self,
                      args_dict: dict
                      ) -> None:
        """
        Implements module specific method
        to update total iterations num.

        Args:
            args_dict (dict): A dictionary containing all parsed command-line arguments.

        Returns:
            None.
        """
        # updating progress tracker attributes
        self.iterations_num += 1

        # updating totals string
        totals_string = f'totals...'
        totals_string += f' | dfs: {self.iterations_num}'
        totals_string += f' | iterations: {self.iterations_num}'
        self.totals_string = totals_string

        # signaling totals updated
        self.signal_totals_updated()

######################################################################
# defining auxiliary functions


def get_time(row_data: Series) -> str:
    """
    Given a dots size df row data,
    returns time group.

    Args:
        row_data (Series): The dots size df row to extract from.

    Returns:
        str: The row's time group.
    """
    # getting current row info
    image_name = row_data['image_name']

    # splitting name by space
    name_split = image_name.split(' ')

    # getting first part of split
    name_split = name_split[0]

    # splitting name by underscore
    name_split = name_split.split('_')

    # getting current time
    current_time = name_split[0]

    # returning current time
    return current_time


def get_condition(row_data: Series) -> str:
    """
    Given a dots size df row data,
    returns condition group.

    Args:
        row_data (Series): The dots size df row to extract from.

    Returns:
        str: The row's condition group.
    """
    # getting current row info
    image_name = row_data['image_name']

    # getting current condition
    condition = '+' if 'plus' in image_name else '-'

    # returning current condition
    return condition


def get_control_bool(row_data: Series) -> bool:
    """
    Given a dots size df row data,
    returns control group.

    Args:
        row_data (Series): The dots size df row to extract from.

    Returns:
        bool: Whether the row belongs to the control group.
    """
    # getting current row info
    time = row_data['time']
    condition = row_data['condition']

    # getting control bools
    time_zero = (time == 't0')
    condition_minus = (condition == '-')

    # getting current control
    control = (time_zero and condition_minus)

    # returning current control
    return control


def get_treatment_group(row_data: Series) -> str:
    """
    Given a dots size df row data,
    returns treatment group.

    Args:
        row_data (Series): The dots size df row to extract from.

    Returns:
        str: The row's treatment group.
    """
    # getting current row info
    time = row_data['time']
    condition = row_data['condition']

    # getting current treatment group
    treatment = f'{time}{condition}'

    # returning current treatment group
    return treatment


def get_t0_mean(df: DataFrame,
                col: str
                ) -> float:
    """
    Given a dots size df, returns
    mean value of specified column
    in time zero group.

    Args:
        df (DataFrame): The dots size df to filter.
        col (str): The column name to average.

    Returns:
        float: The mean value of the given col within the time zero group.
    """
    # filtering df
    filtered_df = df[df['time'] == 't0']

    # getting interest col values
    col_values = filtered_df[col]

    # getting col values mean
    col_mean = col_values.mean()

    # returning col values mean
    return col_mean


def get_normalized_volume(row_data: Series) -> float:
    """
    Given a dots size df row data,
    returns normalized volume.

    Args:
        row_data (Series): The dots size df row to extract from.

    Returns:
        float: The row's normalized volume.
    """
    # getting current row info
    current_volume = row_data['volume']
    volume_normalizer = row_data['volume_normalizer']

    # getting current normalized volume
    normalized_volume = (current_volume / volume_normalizer)

    # returning normalized volume
    return normalized_volume


def get_normalized_intensity(row_data: Series) -> float:
    """
    Given a dots size df row data,
    returns normalized intensity.

    Args:
        row_data (Series): The dots size df row to extract from.

    Returns:
        float: The row's normalized intensity.
    """
    # getting current row info
    mean_intensity = row_data['mean_intensity']
    image_mean = row_data['image_mean']

    # getting current normalized value
    normalized_intensity = (mean_intensity / image_mean)

    # returning normalized intensity
    return normalized_intensity


def get_subgroup(value: float,
                 mean: float,
                 std: float,
                 multiplier: float
                 ) -> str:
    """
    Given a row volume/intensity value,
    returns subgroup, based on given
    mean and std values.

    Args:
        value (float): The value to classify.
        mean (float): The reference mean.
        std (float): The reference standard deviation.
        multiplier (float): The multiplier applied to std when computing thresholds.

    Returns:
        str: The subgroup ("low", "med" or "high").
    """
    # getting low/med thresholds
    low_threshold = mean - (std * multiplier)
    med_threshold = mean + (std * multiplier)

    # getting greater than bools
    greater_than_low = (value > low_threshold)
    greater_than_med = (value > med_threshold)

    # defining placeholder value for subgroup
    subgroup = 'low'

    # checking if value is greater than low threshold
    if greater_than_low:

        # updating subgroup
        subgroup = 'med'

    # checking if value is greater than low threshold
    if greater_than_med:

        # updating subgroup
        subgroup = 'high'

    # returning subgroup
    return subgroup


def get_group_stats(df: DataFrame,
                    group_col: str
                    ) -> dict:
    """
    Given a dots size df and a group col,
    returns dict mapping each group to
    its volume/intensity mean/std values.

    Args:
        df (DataFrame): The dots size df to group.
        group_col (str): The column name to group by.

    Returns:
        dict: A dictionary mapping each group name to its volume/intensity mean/std values.
    """
    # defining placeholder value for group stats dict
    group_stats = {}

    # grouping df
    df_groups = df.groupby(group_col)

    # iterating over df groups
    for group_name, df_group in df_groups:

        # getting current group mean/std values
        volume_mean = df_group['normalized_volume'].mean()
        volume_std = df_group['normalized_volume'].std()
        intensity_mean = df_group['normalized_intensity'].mean()
        intensity_std = df_group['normalized_intensity'].std()

        # storing current group stats
        group_stats[group_name] = {'volume_mean': volume_mean,
                                   'volume_std': volume_std,
                                   'intensity_mean': intensity_mean,
                                   'intensity_std': intensity_std}

    # returning group stats dict
    return group_stats


def get_volume_subgroup(row_data: Series,
                        group_stats: dict,
                        group_col: str,
                        multiplier: float
                        ) -> str:
    """
    Given a dots size df row and a dict
    of group stats, returns current row's
    volume subgroup.

    Args:
        row_data (Series): The dots size df row to extract from.
        group_stats (dict): A dictionary mapping each group name to its volume/intensity mean/std values.
        group_col (str): The column name identifying the row's group.
        multiplier (float): The multiplier applied to std when computing thresholds.

    Returns:
        str: The row's volume subgroup.
    """
    # getting current group stats
    current_group_stats = group_stats[row_data[group_col]]

    # getting current subgroup info
    value = row_data['volume']
    mean = current_group_stats['volume_mean']
    std = current_group_stats['volume_std']

    # getting current row volume subgroup
    current_subgroup = get_subgroup(value=value,
                                    mean=mean,
                                    std=std,
                                    multiplier=multiplier)

    # returning current row volume subgroup
    return current_subgroup


def get_intensity_subgroup(row_data: Series,
                           group_stats: dict,
                           group_col: str,
                           multiplier: float
                           ) -> str:
    """
    Given a dots size df row and a dict
    of group stats, returns current row's
    intensity subgroup.

    Args:
        row_data (Series): The dots size df row to extract from.
        group_stats (dict): A dictionary mapping each group name to its volume/intensity mean/std values.
        group_col (str): The column name identifying the row's group.
        multiplier (float): The multiplier applied to std when computing thresholds.

    Returns:
        str: The row's intensity subgroup.
    """
    # getting current group stats
    current_group_stats = group_stats[row_data[group_col]]

    # getting current subgroup info
    value = row_data['normalized_intensity']
    mean = current_group_stats['intensity_mean']
    std = current_group_stats['intensity_std']

    # getting current row intensity subgroup
    current_subgroup = get_subgroup(value=value,
                                    mean=mean,
                                    std=std,
                                    multiplier=multiplier)

    # returning current row intensity subgroup
    return current_subgroup


def add_subgroup_cols(df: DataFrame) -> None:
    """
    Given a dots size df, adds
    subgroup columns, based on
    volume/intensity mean/std.

    Args:
        df (DataFrame): The dots size df to add subgroup cols to (modified in-place).

    Returns:
        None.
    """
    # defining group col
    group_col = 'treatment_group'

    # defining std multiplier
    multiplier = 2.0

    # getting group stats dict (built once, reused for both cols below)
    group_stats = get_group_stats(df=df,
                                  group_col=group_col)

    # adding subgroup cols
    add_col(df=df,
            col_name='volume_subgroup',
            func=get_volume_subgroup,
            func_kwargs={'group_stats': group_stats, 'group_col': group_col, 'multiplier': multiplier})
    add_col(df=df,
            col_name='intensity_subgroup',
            func=get_intensity_subgroup,
            func_kwargs={'group_stats': group_stats, 'group_col': group_col, 'multiplier': multiplier})


def add_analysis_cols(df: DataFrame) -> None:
    """
    Given a dots size df, adds
    all new columns required for
    subsequent analysis.

    Args:
        df (DataFrame): The dots size df to add analysis cols to (modified in-place).

    Returns:
        None.
    """
    # adding time col
    add_col(df=df,
            col_name='time',
            func=get_time)

    # adding condition col
    add_col(df=df,
            col_name='condition',
            func=get_condition)

    # # adding control bool col
    add_col(df=df,
            col_name='control',
            func=get_control_bool)

    # adding treatment group col
    add_col(df=df,
            col_name='treatment_group',
            func=get_treatment_group)

    # # getting volume normalizer
    volume_normalizer = get_t0_mean(df=df,
                                    col='volume')

    # adding volume normalizer col
    add_constant_col(df=df,
                     col_name='volume_normalizer',
                     value=volume_normalizer)

    # adding normalized volume col
    add_col(df=df,
            col_name='normalized_volume',
            func=get_normalized_volume)

    # adding normalized intensity col
    add_col(df=df,
            col_name='normalized_intensity',
            func=get_normalized_intensity)

    # adding subgroup cols
    add_subgroup_cols(df=df)


def get_subgroups_df(df: DataFrame,
                     var: str
                     ) -> DataFrame:
    """
    Given a dots size df, returns
    subgroups df, with summary
    information per treatment
    time/condition.

    Args:
        df (DataFrame): The dots size df to summarize.
        var (str): The variable whose subgroup column ("{var}_subgroup") to summarize.

    Returns:
        DataFrame: The subgroups summary df.
    """
    # defining placeholder value for dicts list
    dicts_list = []

    # defining group col
    group_col = 'treatment_group'

    # defining analysis col
    analysis_col = f'{var}_subgroup'

    # grouping df
    df_groups = df.groupby(group_col)

    # iterating over df groups
    for df_name, df_group in df_groups:

        # getting current group info
        group_name = str(df_name)  # noqa
        group_count = len(df_group)

        # getting current group subgroups
        subgroups = ['low',
                     'med',
                     'high']

        # iterating over subgroups
        for subgroup in subgroups:

            # getting current subgroup df
            subgroup_df = df_group[df_group[analysis_col] == subgroup]

            # getting current subgroup count/ratio
            subgroup_count = len(subgroup_df)
            subgroup_ratio = (subgroup_count / group_count)

            # assembling current dict
            current_dict = {'group': group_name,
                            'subgroup': subgroup,
                            'count': subgroup_count,
                            'ratio': subgroup_ratio}

            # appending current dict to dicts list
            dicts_list.append(current_dict)

    # assembling final df from dicts list
    final_df = DataFrame(dicts_list)

    # returning final df
    return final_df


def generate_dot_sizes_df(input_path: str,
                          output_path: str,
                          overwrite_output: bool,
                          progress_tracker: ModuleProgressTracker
                          ) -> None:
    """
    Given a path to a joined dots df,
    adds time/condition/subgroup
    analysis cols, saving result to
    given output path.

    Args:
        input_path (str): The path to the joined dots df.
        output_path (str): The path to save the updated dots df to.
        overwrite_output (bool): Whether to overwrite an existing output file.
        progress_tracker (ModuleProgressTracker): The current module's progress tracker instance.

    Returns:
        None.
    """
    # getting skip file bool
    skip_file = get_skip_file_bool(file_path=output_path,
                                   overwrite_output=overwrite_output)

    # checking whether to skip current file
    if skip_file:

        # sleeping
        progress_tracker.wait(0.05)

        # updating progress tracker attributes
        progress_tracker.current_iteration += progress_tracker.iterations_num
        progress_tracker.skipped_iterations += progress_tracker.iterations_num

        # skipping
        return None

    # loading df
    df = load_df(input_path=input_path)

    # adding analysis cols
    add_analysis_cols(df=df)

    # updating progress tracker attributes
    progress_tracker.current_iteration += 1

    # saving df
    save_df(save_path=output_path,
            df=df)


def parse_and_run(args_dict: dict,
                  progress_tracker: ModuleProgressTracker
                  ) -> None:
    """
    Extracts args from args_dict
    and runs module function.

    Args:
        args_dict (dict): A dictionary containing all parsed command-line arguments.
        progress_tracker (ModuleProgressTracker): The current module's progress tracker instance.

    Returns:
        None.
    """
    # getting input path
    input_path = args_dict['input_path']

    # getting output path
    output_path = args_dict['output_path']

    # getting overwrite output
    overwrite_output = args_dict['overwrite_output']

    # running generate_dot_sizes_df function
    generate_dot_sizes_df(input_path=input_path,
                          output_path=output_path,
                          overwrite_output=overwrite_output,
                          progress_tracker=progress_tracker)

######################################################################
# defining main function


def main():
    """
    Runs main code.
    """
    # initializing current module progress tracker instance
    progress_tracker = ModuleProgressTracker()

    # running code in separate thread
    progress_tracker.run(function=parse_and_run,
                         args_parser=get_args_dict)

######################################################################
# running main function


if __name__ == '__main__':
    main()

######################################################################
# end of current module
