# rois to objects df module

print('initializing...')  # noqa

# Code destined to converting
# rois (fiji output) to
# objects df.

######################################################################
# imports

print('importing required libraries...')  # noqa
from os.path import join
from pandas import DataFrame
from argparse import ArgumentParser
from cet.io.dataframes import load_df
from cet.io.dataframes import save_df
from cet.io.files import get_skip_file_bool
from cet.io.files import get_files_in_folder
from cet.io.formatting import get_number_string
from cet.dataframes.df_ops import concatenate_dfs
from cet.io.files import get_image_name_from_path
from cet.measurements.position import coords_to_string
from cet.measurements.position import get_centroid_boundaries
from cet.progress_tracker.ProgressTracker import ProgressTracker
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
    description = "rois to objects df module"

    # creating a parser instance
    parser = ArgumentParser(description=description)

    # adding arguments to parser

    # input folder param
    parser.add_argument('-i', '--input-folder',
                        dest='input_folder',
                        type=str,
                        required=True,
                        help='defines path to folder containing rois files [.csv]')

    # output path param
    parser.add_argument('-o', '--output-path',
                        dest='output_path',
                        type=str,
                        required=True,
                        help='defines path to output file [.csv]')

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

        # defining current module specific attributes

        # image
        self.images_num = 0
        self.current_image = 0

        # object
        self.objects_num = 0
        self.current_object = 0

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
            progress_string += f' | images: {self.images_num}'
            progress_string += f' | objects: {self.objects_num}'
            progress_string += f' | iterations: {self.iterations_num}'
            progress_string += f' | elapsed time: {self.elapsed_time_str}'

        # if total iterations already obtained
        else:

            # updating progress string based on attributes
            progress_string += f'converting df...'
            progress_string += f' {self.wheel_symbol}'
            progress_string += f' | image: {self.current_image}/{self.images_num}'
            progress_string += f' | object: {self.current_object}/{self.objects_num}'
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
        # getting input folder
        input_folder = args_dict['input_folder']

        # getting files in input folder
        files = get_files_in_folder(input_folder=input_folder,
                                    extension='.csv')

        # iterating over files in input folder
        for file_name in files:

            # updating progress tracker attributes
            self.images_num += 1

            # getting current input path
            current_input_path = join(input_folder,
                                      file_name)

            # loading df
            df = load_df(input_path=current_input_path)  # noqa

            # getting df rows num/range
            df_rows_num = len(df)
            df_rows_range = range(df_rows_num)

            # iterating over df rows
            for _ in df_rows_range:

                # updating progress tracker attributes
                self.objects_num += 1
                self.iterations_num += 1

        # updating totals string
        totals_string = f'totals...'
        totals_string += f' | images: {self.images_num}'
        totals_string += f' | objects: {self.objects_num}'
        totals_string += f' | iterations: {self.iterations_num}'
        self.totals_string = totals_string

        # signaling totals updated
        self.signal_totals_updated()

######################################################################
# defining auxiliary functions


def get_image_df(input_path: str,
                 progress_tracker: ModuleProgressTracker
                 ) -> DataFrame:
    """
    Given a path to a rois df,
    returns its respective objects df.

    Args:
        input_path (str): The path to the rois df to convert.
        progress_tracker (ModuleProgressTracker): The current module's progress tracker instance.

    Returns:
        DataFrame: The converted objects df.
    """
    # loading df
    df = load_df(input_path=input_path)

    # defining placeholder value for dicts list
    dicts_list = []

    # getting df rows
    df_rows = df.iterrows()

    # getting current object count
    objects_num = len(df)
    objects_num_str = str(objects_num)
    objects_num_str_len = len(objects_num_str)

    # updating progress tracker attributes
    progress_tracker.objects_num = objects_num

    # resetting progress tracker attributes
    progress_tracker.current_object = 0

    # iterating over df rows
    for row_index, row_data in df_rows:

        # updating progress tracker attributes
        progress_tracker.current_iteration += 1
        progress_tracker.current_object += 1

        # getting image name
        image_name = get_image_name_from_path(image_path=input_path)

        # getting current row info
        x_left = row_data['X']
        y_top = row_data['Y']
        z = row_data['Z']
        width = row_data['Width']
        height = row_data['Height']
        depth = 10
        description = 'nuc'

        # getting radius from dims
        y_radius = height // 2
        x_radius = width // 2

        # getting centroid coords
        y = y_top + y_radius
        x = x_left + x_radius

        # assembling coords/bounding tuples
        centroid = (z, y, x)
        bounding_dims = (depth, height, width)

        # getting current object boundaries
        boundaries = get_centroid_boundaries(coords=centroid,
                                             bounding_dims=bounding_dims)

        # getting indices
        image_index = progress_tracker.current_image
        object_id = progress_tracker.current_object

        # getting crop name
        crop_index_str = get_number_string(num=object_id,
                                           digits=objects_num_str_len)
        crop_ext = f'_{description}{crop_index_str}.tif'
        crop_name = image_name.replace('.tif', crop_ext)

        # converting data types
        centroid = coords_to_string(coords=centroid)
        boundaries = coords_to_string(coords=boundaries)

        # assembling current object dict
        current_dict = {'image_name': image_name,
                        'image_index': image_index,
                        'description': description,
                        'object_id': object_id,
                        'crop_name': crop_name,
                        'centroid': centroid,
                        'boundaries': boundaries}

        # appending current dict to dicts list
        dicts_list.append(current_dict)

        # sleeping
        progress_tracker.wait(0.001)

    # assembling final df from dicts list
    final_df = DataFrame(dicts_list)

    # returning final df
    return final_df


def rois_to_objects_df(input_folder: str,
                       output_path: str,
                       overwrite_output: bool,
                       progress_tracker: ModuleProgressTracker
                       ) -> None:
    """
    Given a path to a folder containing
    rois fiji files, converts them to
    objects df format, saving output
    to given output path.

    Args:
        input_folder (str): The path to the folder containing rois files to convert.
        output_path (str): The path to save the converted objects df to.
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

    # getting files in input folder
    files = get_files_in_folder(input_folder=input_folder,
                                extension='.csv')

    # defining placeholder value for dfs list
    dfs_list = []

    # iterating over files in input folder
    for file_name in files:

        # updating progress tracker attributes
        progress_tracker.current_image += 1

        # getting current input path
        current_input_path = join(input_folder,
                                  file_name)

        # getting current df
        current_objects_df = get_image_df(input_path=current_input_path,
                                          progress_tracker=progress_tracker)

        # appending current df to dfs list
        dfs_list.append(current_objects_df)

    # concatenating dfs in dfs list
    final_df = concatenate_dfs(dfs_list)

    # saving df
    save_df(save_path=output_path,
            df=final_df)


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
    # getting input folder
    input_folder = args_dict['input_folder']

    # getting output path
    output_path = args_dict['output_path']

    # getting overwrite output
    overwrite_output = args_dict['overwrite_output']

    # running rois_to_objects_df function
    rois_to_objects_df(input_folder=input_folder,
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
