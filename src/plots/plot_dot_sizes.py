# plot dot sizes module

print('initializing...')  # noqa

# Code destined to plotting dot sizes
# based on dots dataframe.

######################################################################
# imports

print('importing required libraries...')  # noqa
from os.path import join
from seaborn import boxplot
from seaborn import barplot
from pandas import DataFrame
from seaborn import stripplot
from cet.constants import FIG_SIZE
from argparse import ArgumentParser
from matplotlib import pyplot as plt
from cet.io.dataframes import load_df
from cet.plots.plot_ops import get_axis_label
from matplotlib.legend_handler import HandlerTuple
from cet.progress_tracker.ProgressTracker import ProgressTracker
from cet.dataframes.generate_dot_sizes_df import get_subgroups_df
print('all required libraries successfully imported.')  # noqa

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
    description = "plot dot sizes module"

    # creating a parser instance
    parser = ArgumentParser(description=description)

    # adding arguments to parser

    # input path param
    parser.add_argument('-i', '--input-path',
                        dest='input_path',
                        type=str,
                        required=True,
                        help='defines path to dot sizes summary df [.csv]')

    # output folder param
    parser.add_argument('-o', '--output-folder',
                        dest='output_folder',
                        type=str,
                        required=True,
                        help='defines output folder (folder that will contain plots)')

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
            progress_string += f' | plots: {self.iterations_num}'
            progress_string += f' | iterations: {self.iterations_num}'
            progress_string += f' | elapsed time: {self.elapsed_time_str}'

        # if total iterations already obtained
        else:

            # updating progress string based on attributes
            progress_string += f'plotting data...'
            progress_string += f' {self.wheel_symbol}'
            progress_string += f' | plots: {self.current_iteration}/{self.iterations_num}'
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
        totals_string += f' | plots: {self.iterations_num}'
        totals_string += f' | iterations: {self.iterations_num}'
        self.totals_string = totals_string

        # signaling totals updated
        self.signal_totals_updated()

######################################################################
# defining auxiliary functions


def plot_boxpoints(df: DataFrame,
                   var: str,
                   output_folder: str
                   ) -> None:
    """
    Plots dot size data as combined box and
    strip plots, grouped by condition.

    Args:
        df (DataFrame): A dot sizes dataframe.
        var (str): The variable name to normalize and plot.
        output_folder (str): The directory where the plot will be saved.

    Returns:
        None.
    """
    # setting figure size
    plt.figure(figsize=FIG_SIZE)

    # defining plots/statistics params
    x_col = 'time'
    y_col = f'normalized_{var}'
    hue_col = 'condition'
    hue_order = ['-', '+']
    hue_colors = {'-': 'gray',
                  '+': 'green'}

    # plotting data
    ax = boxplot(data=df,
                 x=x_col,
                 y=y_col,
                 hue=hue_col,
                 hue_order=hue_order,
                 palette=hue_colors,
                 showfliers=False,
                 boxprops={'alpha': 0.4})
    stripplot(data=df,
              x=x_col,
              y=y_col,
              size=3,
              hue=hue_col,
              hue_order=hue_order,
              palette=hue_colors,
              dodge=True,
              ax=ax)
    handles, labels = ax.get_legend_handles_labels()
    ax.legend(handles=[(handles[0], handles[2]), (handles[1], handles[3])],
              labels=hue_order,
              loc='upper left',
              handlelength=4,
              handler_map={tuple: HandlerTuple(ndivide=2)})

    # updating axis names/font sizes
    x_label = get_axis_label(col_name=x_col)
    y_label = get_axis_label(col_name=y_col)
    plt.xlabel(x_label, fontsize=16)
    plt.ylabel(y_label, fontsize=16)

    # saving plot
    save_name = f'{y_col}_by_{x_col}.png'
    save_path = join(output_folder,
                     save_name)
    plt.savefig(save_path)

    # closing plot
    plt.close()


def plot_global_subgroups(df: DataFrame,
                          var: str,
                          output_folder: str
                          ) -> None:
    """
    Plots global subgroup data from a dot
    sizes dataframe.

    Args:
        df (DataFrame): A dot sizes dataframe.
        var (str): The variable name to plot.
        output_folder (str): The directory where the plot will be saved.

    Returns:
        None.
    """
    # setting figure size
    plt.figure(figsize=FIG_SIZE)

    # getting col names
    x_col = 'treatment_group'
    y_col = f'normalized_{var}'
    hue_col = f'{var}_subgroup'

    # plotting data
    stripplot(data=df,
              x=x_col,
              y=y_col,
              size=3,
              hue=hue_col,
              dodge=True)

    # updating axis names/font sizes
    x_label = get_axis_label(col_name=x_col)
    y_label = get_axis_label(col_name=y_col)
    plt.xlabel(x_label, fontsize=16)
    plt.ylabel(y_label, fontsize=16)

    # saving plot
    save_name = f'{y_col}_by_{x_col}.png'
    save_path = join(output_folder,
                     save_name)
    plt.savefig(save_path)

    # closing plot
    plt.close()


def plot_subgroup(df: DataFrame,
                  group_name: str,
                  output_folder: str
                  ) -> None:
    """
    Plots a single subgroup from a dot
    sizes dataframe.

    Args:
        df (DataFrame): A dot sizes dataframe.
        group_name (str): The name of the subgroup being plotted.
        output_folder (str): The directory where the plot will be saved.

    Returns:
        None.
    """
    # setting figure size
    plt.figure(figsize=FIG_SIZE)

    # getting col names
    x_col = 'group'
    y_col = 'count'
    hue_col = f'subgroup'

    # plotting data
    barplot(data=df,
            x=x_col,
            y=y_col,
            hue=hue_col)

    # updating axis names/font sizes
    x_label = get_axis_label(col_name=x_col)
    y_label = get_axis_label(col_name=y_col)
    plt.xlabel(x_label, fontsize=16)
    plt.ylabel(y_label, fontsize=16)

    # saving plot
    save_name = f'{y_col}_by_{x_col}_{group_name}.png'
    save_path = join(output_folder,
                     save_name)
    plt.savefig(save_path)

    # closing plot
    plt.close()


def plot_subgroups(df: DataFrame,
                   var: str,
                   output_folder: str
                   ) -> None:
    """
    Plots multiple subgroups from a dot
    sizes dataframe.

    Args:
        df (DataFrame): A dot sizes dataframe.
        var (str): The variable name to plot.
        output_folder (str): The directory where the plot will be saved.

    Returns:
        None.
    """
    # setting figure size
    plt.figure(figsize=FIG_SIZE)

    # getting col names
    x_col = 'group'
    y_col = 'ratio'
    hue_col = 'subgroup'
    hue_order = ['low',
                 'med',
                 'high']
    x_order = ['t0-',
               't15-',
               't15+',
               't30-',
               't30+',
               't45-',
               't45+']

    # plotting data
    barplot(data=df,
            x=x_col,
            y=y_col,
            hue=hue_col,
            hue_order=hue_order,
            order=x_order)

    # updating axis names/font sizes
    x_label = get_axis_label(col_name=x_col)
    y_label = get_axis_label(col_name=y_col)
    plt.xlabel(x_label, fontsize=16)
    plt.ylabel(y_label, fontsize=16)

    # saving plot
    save_name = f'{var}_subgroups_{y_col}.png'
    save_path = join(output_folder,
                     save_name)
    plt.savefig(save_path)

    # closing plot
    plt.close()

    # # defining group col
    # group_col = 'group'
    #
    # # grouping df
    # df_groups = df.groupby(group_col)
    #
    # # iterating over df groups
    # for df_name, df_group in df_groups:
    #
    #     # getting current group info
    #     group_name = str(df_name)  # noqa
    #
    #     # plotting current group data
    #     plot_subgroup(df=df_group,
    #                   group_name=group_name,
    #                   var=var,
    #                   output_folder=output_folder)


def plot_dot_sizes(input_path: str,
                   output_folder: str,
                   progress_tracker: ModuleProgressTracker
                   ) -> None:
    """
    Plots dot size analysis data and saves
    plots to the output folder.

    Args:
        input_path (str): Path to the dot sizes summary CSV dataframe.
        output_folder (str): The directory where plots will be saved.
        progress_tracker (ModuleProgressTracker): Tracker for progress reporting.

    Returns:
        None.
    """
    # loading df
    df = load_df(input_path=input_path)

    # updating progress tracker attributes
    progress_tracker.current_iteration += 1

    # getting subgroups dfs
    volume_subgroups_df = get_subgroups_df(df=df,
                                           var='volume')
    intensity_subgroups_df = get_subgroups_df(df=df,
                                              var='intensity')

    # plotting data
    plot_boxpoints(df=df,
                  var='volume',
                  output_folder=output_folder)
    plot_boxpoints(df=df,
                  var='intensity',
                  output_folder=output_folder)
    plot_global_subgroups(df=df,
                          var='volume',
                          output_folder=output_folder)
    plot_global_subgroups(df=df,
                          var='intensity',
                          output_folder=output_folder)
    plot_subgroups(df=volume_subgroups_df,
                  var='volume',
                  output_folder=output_folder)
    plot_subgroups(df=intensity_subgroups_df,
                  var='intensity',
                  output_folder=output_folder)

    # # running statistical analysis
    # run_statistical_analysis(df=df,
    #                          variable_col='normalized_volume',
    #                          group_col='treatment_group')
    # run_statistical_analysis(df=df,
    #                          variable_col='normalized_intensity',
    #                          group_col='treatment_group')


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

    # getting output folder
    output_folder = args_dict['output_folder']

    # running plot_dot_sizes function
    plot_dot_sizes(input_path=input_path,
                   output_folder=output_folder,
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
