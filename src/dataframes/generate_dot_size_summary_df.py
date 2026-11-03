# generate dot size summary df module

print('initializing...')  # noqa

# Code destined to generating
# dot size summary df.

######################################################################
# imports

print('importing required libraries...')  # noqa
from copy import copy
from pandas import concat
from pandas import Series
from pandas import DataFrame
from pandas import read_excel
from argparse import ArgumentParser
from cet.io.dataframes import load_df
from cet.io.dataframes import save_df
from cet.dataframes.df_ops import add_col
from cet.io.files import get_skip_file_bool
from cet.dataframes.df_ops import get_normalizer
from cet.dataframes.df_ops import concatenate_dfs
from cet.dataframes.df_ops import add_constant_col
from cet.dataframes.df_ops import get_normalized_value
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
    description = "generate dot size summary df module"

    # creating a parser instance
    parser = ArgumentParser(description=description)

    # images df path param
    parser.add_argument('-i', '--images-df-path',
                        dest='images_df_path',
                        type=str,
                        required=True,
                        help='defines path to images df [.csv]')

    # dots df path param
    parser.add_argument('-d', '--dots-df-path',
                        dest='dots_df_path',
                        type=str,
                        required=True,
                        help='defines path to dots summary df [.csv]')

    # experiments df path param
    parser.add_argument('-e', '--experiments-df-path',
                        dest='experiments_df_path',
                        type=str,
                        required=True,
                        help='defines path to experiments description df [.xlsx]')

    # output path param
    parser.add_argument('-o', '--output-path',
                        dest='output_path',
                        type=str,
                        required=True,
                        help='defines path to output file [.csv]')

    # dataset param
    parser.add_argument('-ds', '--dataset',
                        dest='dataset',
                        type=str,
                        required=False,
                        default='dataset01',
                        help='defines dataset "id" (dataset01, dataset02, ...) - must match data in experiments.xlsx')

    # top n param
    parser.add_argument('-t', '--top-n',
                        dest='top_n',
                        type=int,
                        required=False,
                        default=2,
                        help='defines top n largest elements to be considered in analysis')

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
            progress_string += f' | images: {self.iterations_num}'
            progress_string += f' | iterations: {self.iterations_num}'
            progress_string += f' | elapsed time: {self.elapsed_time_str}'

        # if total iterations already obtained
        else:

            # updating progress string based on attributes
            progress_string += f'generating dfs...'
            progress_string += f' {self.wheel_symbol}'
            progress_string += f' | image: {self.current_iteration}/{self.iterations_num}'
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
        # getting images df path
        images_df_path = args_dict['images_df_path']

        # loading df
        images_df = load_df(input_path=images_df_path)

        # defining group cols
        group_cols = ['image_name',
                      'image_index']

        # grouping df
        df_groups = images_df.groupby(group_cols)

        # getting df groups num/range
        df_groups_num = len(df_groups)
        df_groups_range = range(df_groups_num)

        # iterating over df groups
        for _ in df_groups_range:

            # updating progress tracker attributes
            self.iterations_num += 1

        # updating totals string
        totals_string = f'totals...'
        totals_string += f' | images: {self.iterations_num}'
        totals_string += f' | iterations: {self.iterations_num}'
        self.totals_string = totals_string

        # signaling totals updated
        self.signal_totals_updated()

######################################################################
# defining auxiliary functions


def find_largest_dots(df: DataFrame,
                      image_name: str,
                      image_index: int,
                      size_col: str,
                      top_n: int
                      ) -> DataFrame:
    """
    Given a dots size df, returns
    filtered df by top X largest
    dots, according to specified
    column.

    Args:
        df (DataFrame): The dots size df to filter.
        image_name (str): The image name to fill padding rows with.
        image_index (int): The image index to fill padding rows with.
        size_col (str): The column name to sort by.
        top_n (int): The number of largest dots to keep.

    Returns:
        DataFrame: The filtered df, padded with empty rows if needed to reach top_n.
    """
    # defining placeholder value for filtered df
    filtered_df = copy(df)

    # resetting index
    filtered_df.reset_index(inplace=True)

    # defining base values
    int_zero = 0
    float_zero = 0.0

    # defining empty dict
    empty_dict = {'image_name': image_name,
                  'image_index': image_index,
                  'description': 'empty_dot',
                  'object_id': int_zero,
                  'uid': 'ed0',
                  'crop_name': 'crop_ed0',
                  'crop_index': int_zero,
                  'pixel_volume': int_zero,
                  'volume': float_zero,
                  'centroid': '(0, 0, 0)',
                  'boundaries': '(0, 0, 0, 0, 0, 0)',
                  'radius_ratio': float_zero,
                  'surface_area': float_zero,
                  'area_vol_ratio': float_zero,
                  'bounding_volume': float_zero,
                  'sphericity': float_zero,
                  'min_intensity': float_zero,
                  'max_intensity': float_zero,
                  'mean_intensity': float_zero,
                  'median_intensity': float_zero,
                  'std_intensity': float_zero,
                  'background_mean_intensity': float_zero}

    # getting current group dot count
    dot_count = len(filtered_df)

    # getting number of empty rows needed to reach top_n
    rows_needed = max(0, top_n - dot_count)

    # checking whether df needs padding to reach at least n (from top_n) values
    if rows_needed > 0:

        # building pad df with empty rows (one dict per row, all identical)
        pad_df = DataFrame([empty_dict] * rows_needed)

        # appending pad df to filtered df in a single operation
        filtered_df = concat([filtered_df, pad_df],
                             ignore_index=True)

        # updating dot count
        dot_count = len(filtered_df)

    # checking if current group contains more dots than specified
    while dot_count > top_n:

        # sorting df by size col
        sorted_df = filtered_df.sort_values(by=size_col)

        # getting group indices
        indices = sorted_df.index

        # getting smallest object index
        smallest_dot_index = indices[0]

        # dropping smallest dot from group
        filtered_df.drop(index=smallest_dot_index,
                         inplace=True)

        # updating dot count
        dot_count = len(filtered_df)

    # returning filtered df
    return filtered_df


def get_dot_size_summary_df(dots_df: DataFrame,
                            images_df: DataFrame,
                            top_n: int,
                            progress_tracker: ModuleProgressTracker
                            ) -> DataFrame:
    """
    Given a dots/images dfs,
    returns dot size summary df.

    Args:
        dots_df (DataFrame): The dots summary df.
        images_df (DataFrame): The images df.
        top_n (int): The number of largest dots to keep per image.
        progress_tracker (ModuleProgressTracker): The current module's progress tracker instance.

    Returns:
        DataFrame: The dot size summary df.
    """
    # defining placeholder value for dfs list
    dfs_list = []

    # defining group col
    group_cols = ['image_name',
                  'image_index']

    # grouping df
    df_groups = images_df.groupby(group_cols)

    # iterating over df groups
    for df_name, df_group in df_groups:

        # updating progress tracker attributes
        progress_tracker.current_iteration += 1

        # getting current image name
        image_name, image_index = df_name

        # getting current image dots df
        current_dots_df = dots_df[dots_df['image_name'] == image_name]

        # getting current image largest dots df
        current_dots_df = find_largest_dots(df=current_dots_df,
                                            image_name=image_name,
                                            image_index=image_index,
                                            size_col='volume',
                                            top_n=top_n)

        # getting current merged df
        current_merged_df = df_group.merge(right=current_dots_df,
                                           on='image_name',
                                           how='outer')

        # resetting image index col
        current_merged_df.drop(columns=['index'],
                               inplace=True)
        current_merged_df.drop(columns=['image_index_y'],
                               inplace=True)
        current_merged_df.rename(columns={'image_index_x': 'image_index'},
                                 inplace=True)

        # appending current df to dfs list
        dfs_list.append(current_merged_df)

    # concatenating dfs in dfs list
    final_df = concatenate_dfs(dfs_list)

    # returning updated df
    return final_df


def get_control_keyword(df: DataFrame,
                        dataset: str
                        ) -> str:
    """
    Given a dot size experiment df,
    and a dataset id, returns its
    respective control keyword.

    Args:
        df (DataFrame): The experiments description df.
        dataset (str): The dataset id to look up.

    Returns:
        str: The dataset's control keyword.
    """
    # getting current dataset df
    current_df = df[df['DS_ID'] == dataset]

    # getting current df row data
    row_data = current_df.iloc[0]

    # getting current control keyword
    control_keyword = row_data['CONTROL']

    # returning current control keyword
    return control_keyword


def get_condition(row_data: Series) -> str:
    """
    Given a dot size df row data,
    returns condition group.

    Args:
        row_data (Series): The dot size df row to extract from.

    Returns:
        str: The row's condition group.
    """
    # getting current row info
    image_name = row_data['image_name']

    # getting image name split
    image_name_split = image_name.split(' ')

    # getting current condition
    condition = image_name_split[0]

    # returning current condition
    return condition


def get_treatment_group(row_data: Series,
                        control_keyword: str
                        ) -> str:
    """
    Given a dots size df row data,
    returns treatment group.

    Args:
        row_data (Series): The dots size df row to extract from.
        control_keyword (str): The keyword identifying the control condition.

    Returns:
        str: The row's treatment group ("CTR" or "TRT").
    """
    # defining placeholder value for treatment group
    treatment_group = 'TRT'

    # getting current row info
    condition = row_data['condition']

    # getting control bool
    is_control = (control_keyword in condition)

    # checking control bool
    if is_control:

        # updating treatment group
        treatment_group = 'CTR'

    # returning treatment group
    return treatment_group


def get_rescaled_intensity(row_data: Series,
                           intensity_col: str,
                           intensity_rescaler_col: str
                           ) -> float:
    """
    Given a dots size df row data,
    returns rescaled intensity.

    Args:
        row_data (Series): The dots size df row to extract from.
        intensity_col (str): The column name holding the intensity value.
        intensity_rescaler_col (str): The column name holding the intensity rescaler value.

    Returns:
        float: The row's rescaled intensity.
    """
    # getting current row info
    intensity = row_data[intensity_col]
    intensity_rescaler = row_data[intensity_rescaler_col]

    # getting rescaled intensity
    rescaled_intensity = intensity - intensity_rescaler

    # returning rescaled intensity
    return rescaled_intensity


def get_ctr_values(df: DataFrame,
                   col: str
                   ) -> Series:
    """
    Given a dots size df, returns
    control values of given col.

    Args:
        df (DataFrame): The dots size df to filter.
        col (str): The column name whose control values to return.

    Returns:
        Series: The control group's values for the given col.
    """
    # getting current control group df
    control_group_df = df[df['treatment_group'] == 'CTR']

    # getting current control group values
    control_values = control_group_df[col]

    # returning control values
    return control_values


def get_integrated_intensity(row_data: Series) -> float:
    """
    Given a dots size df row data,
    returns integrated intensity.

    Args:
        row_data (Series): The dots size df row to extract from.

    Returns:
        float: The row's integrated intensity.
    """
    # getting current row info
    volume = row_data['volume']
    rescaled_intensity = row_data['rescaled_intensity']

    # getting integrated intensity
    integrated_intensity = volume * rescaled_intensity

    # returning integrated intensity
    return integrated_intensity


def get_limits(values: Series,
               std_multiplier: float = 1.0
               ) -> tuple:
    """
    Given a col values, returns tuple
    representing min/max values
    according to median +- multiplier
    * std.

    Args:
        values (Series): The values to compute limits for.
        std_multiplier (float): The multiplier applied to the standard deviation.

    Returns:
        tuple: The (lower_limit, upper_limit) values.
    """
    # getting values median/std
    values_median = values.median()
    values_std = values.std()

    # getting std addend
    std_addend = (values_std * std_multiplier)

    # getting values limits
    lower_limit = (values_median - std_addend)
    upper_limit = (values_median + std_addend)

    # assembling limits tuple
    limits = (lower_limit, upper_limit)

    # returning limits
    return limits


def get_subgroup(row_data: Series,
                 value_col: str,
                 limits: tuple
                 ) -> str:
    """
    Given a dots size df row data,
    returns subgroup.

    Args:
        row_data (Series): The dots size df row to extract from.
        value_col (str): The column name holding the value to classify.
        limits (tuple): The (lower_limit, upper_limit) values.

    Returns:
        str: The row's subgroup ("low", "med" or "high").
    """
    # getting current row info
    value = row_data[value_col]

    # extracting values from tuple
    lower_limit, upper_limit = limits

    # defining placeholder value for subgroup
    subgroup = 'low'

    # getting data bools
    above_lower = (value >= lower_limit)
    above_upper = (value >= upper_limit)

    # checking if value is above lower limit
    if above_lower:

        # updating subgroup
        subgroup = 'med'

    # checking if value is above upper limit
    if above_upper:

        # updating subgroup
        subgroup = 'high'

    # returning subgroup
    return subgroup


def add_analysis_cols(df: DataFrame,
                      control_keyword: str
                      ) -> None:
    """
    Given a dot sizes df, adds
    all new columns required for
    subsequent analysis.

    Args:
        df (DataFrame): The dot sizes df to add analysis cols to (modified in-place).
        control_keyword (str): The keyword identifying the control condition.

    Returns:
        None.
    """
    # adding condition col
    add_col(df=df,
            col_name='condition',
            func=get_condition)

    # adding treatment group col
    add_col(df=df,
            col_name='treatment_group',
            func=get_treatment_group,
            func_kwargs={'control_keyword': control_keyword})

    # adding rescaled intensity col
    add_col(df=df,
            col_name='rescaled_intensity',
            func=get_rescaled_intensity,
            func_kwargs={'intensity_col': 'mean_intensity',
                         'intensity_rescaler_col': 'background_mean_intensity'})

    # adding integrated intensity col
    add_col(df=df,
            col_name='integrated_intensity',
            func=get_integrated_intensity)

    # getting volume/intensity control values
    volume_ctr_values = get_ctr_values(df=df,
                                       col='volume')
    intensity_ctr_values = get_ctr_values(df=df,
                                          col='integrated_intensity')

    # getting volume/intensity normalizers (control means)
    volume_normalizer = get_normalizer(values=volume_ctr_values)
    intensity_normalizer = get_normalizer(values=intensity_ctr_values)

    # adding volume/intensity normalizers cols
    add_constant_col(df=df,
                     col_name='volume_normalizer',
                     value=volume_normalizer)
    add_constant_col(df=df,
                     col_name='intensity_normalizer',
                     value=intensity_normalizer)

    # adding normalized volume/intensity cols
    add_col(df=df,
            col_name='normalized_volume',
            func=get_normalized_value,
            func_kwargs={'value_col': 'volume',
                         'reference_col': 'volume_normalizer'})
    add_col(df=df,
            col_name='normalized_intensity',
            func=get_normalized_value,
            func_kwargs={'value_col': 'integrated_intensity',
                         'reference_col': 'intensity_normalizer'})

    # getting volume/intensity subgroup limits
    volume_subgroup_limits = get_limits(values=volume_ctr_values)
    intensity_subgroup_limits = get_limits(values=intensity_ctr_values)

    # adding volume/intensity subgroup cols
    add_col(df=df,
            col_name='volume_subgroup',
            func=get_subgroup,
            func_kwargs={'value_col': 'volume',
                         'limits': volume_subgroup_limits})
    add_col(df=df,
            col_name='intensity_subgroup',
            func=get_subgroup,
            func_kwargs={'value_col': 'integrated_intensity',
                         'limits': intensity_subgroup_limits})


def generate_dot_size_summary_df(images_df_path: str,
                                 dots_df_path: str,
                                 experiments_df_path: str,
                                 output_path: str,
                                 dataset: str,
                                 top_n: int,
                                 overwrite_output: bool,
                                 progress_tracker: ModuleProgressTracker
                                 ) -> None:
    """
    Given images/dots/experiments dfs,
    saves dot size summary df to
    given output path.

    Args:
        images_df_path (str): The path to the images df.
        dots_df_path (str): The path to the dots summary df.
        experiments_df_path (str): The path to the experiments description df.
        output_path (str): The path to save the dot size summary df to.
        dataset (str): The dataset id (must match data in experiments.xlsx).
        top_n (int): The number of largest dots to keep per image.
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

    # loading dfs
    images_df = load_df(input_path=images_df_path)
    dots_df = load_df(input_path=dots_df_path)
    experiments_df = read_excel(experiments_df_path)

    # getting current dataset control keyword
    control_keyword = get_control_keyword(df=experiments_df,
                                          dataset=dataset)

    # getting summary df
    summary_df = get_dot_size_summary_df(images_df=images_df,
                                         dots_df=dots_df,
                                         top_n=top_n,
                                         progress_tracker=progress_tracker)

    # adding analysis cols
    add_analysis_cols(df=summary_df,
                      control_keyword=control_keyword)

    # saving dfs
    save_df(save_path=output_path,
            df=summary_df)


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
    # getting images df path
    images_df_path = args_dict['images_df_path']

    # getting dots df path
    dots_df_path = args_dict['dots_df_path']

    # getting experiments df path
    experiments_df_path = args_dict['experiments_df_path']

    # getting output path
    output_path = args_dict['output_path']

    # getting dataset
    dataset = args_dict['dataset']

    # getting top n
    top_n = args_dict['top_n']

    # getting overwrite output
    overwrite_output = args_dict['overwrite_output']

    # running generate_dot_size_summary_df function
    generate_dot_size_summary_df(images_df_path=images_df_path,
                                 dots_df_path=dots_df_path,
                                 experiments_df_path=experiments_df_path,
                                 output_path=output_path,
                                 dataset=dataset,
                                 top_n=top_n,
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
