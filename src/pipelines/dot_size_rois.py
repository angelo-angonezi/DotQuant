# dot size rois pipeline module

pipeline_name = 'dot size rois'

print(f'starting {pipeline_name} pipeline...')

# imports
from sys import argv
from os.path import join
from pydantic import BaseModel
from cet.pipelines import modules
from cet.io.cli import run_commands
from cet.io.Settings import Settings
from cet.io.files import get_vars_dict
from cet.io.cli import assemble_command
from cet.io.files import create_subfolders
from cet.io.files import delete_subfolders
from cet.io.files import get_subfolders_list

######################################################################
# settings definition


class DotSizeSettings(BaseModel):
    """
    Stores the settings specific to the
    dot size rois pipeline, which have no
    place in the shared cet Settings schema.

    Attributes:
        experiments_df_path (str): Path to the experiments table.
        dataset (str): Dataset identifier in the experiments table.
        top_n (int): Number of largest dots per image to summarize.
    """
    experiments_df_path: str
    dataset: str
    top_n: int = 2


class DotSizeRoisSettings(Settings):
    """
    Shared cet Settings plus the
    dot size rois specific block.

    Attributes:
        dot_size (DotSizeSettings): Dot size rois settings.
    """
    dot_size: DotSizeSettings


# getting settings file
SETTINGS_FILE = argv[1]

# loading and validating settings with Pydantic
SETTINGS = DotSizeRoisSettings.from_yaml(input_path=SETTINGS_FILE)

##############################
# getting execution params
##############################

# experiment
EXPERIMENT_SETTINGS = SETTINGS.experiment

BASE_FOLDER = EXPERIMENT_SETTINGS.base_folder
IMAGES_EXTENSION = EXPERIMENT_SETTINGS.image_extension

# microscopy
MICROSCOPY_SETTINGS = SETTINGS.microscopy

SCALES_STR = MICROSCOPY_SETTINGS.scales_str

# dot size
DOT_SIZE_SETTINGS = SETTINGS.dot_size

EXPERIMENTS_DF_PATH = DOT_SIZE_SETTINGS.experiments_df_path
DATASET = DOT_SIZE_SETTINGS.dataset
TOP_N = DOT_SIZE_SETTINGS.top_n

# segmentation (dots only, embryos/nuclei are not segmented by this pipeline)
DOTS_SETTINGS = SETTINGS.segmentation.dots

# toggles
PIPELINE_TOGGLES = SETTINGS.pipeline_toggles

RUN_PREPROCESSING = PIPELINE_TOGGLES.initial_preprocessing
DOTS_TOGGLES = PIPELINE_TOGGLES.dots

# runtime
RUNTIME_SETTINGS = SETTINGS.runtime

SKIP_ENTER = RUNTIME_SETTINGS.skip_enter
OVERWRITE_OUTPUT = RUNTIME_SETTINGS.overwrite_output
SIMULATE_RUN = RUNTIME_SETTINGS.simulate_run
CLEAR_INTERMEDIATE_FILES = RUNTIME_SETTINGS.clear_intermediate_files

##############################
# assembling paths and vars
##############################

IMGS_FOLDER = join(BASE_FOLDER, 'imgs')
TIFS_FOLDER = join(BASE_FOLDER, 'tifs')
PLOTS_FOLDER = join(BASE_FOLDER, 'plots')
LOG_FOLDER = join(BASE_FOLDER, 'logs')

CHANNELS_FOLDER = join(BASE_FOLDER, 'channels')

NUCLEI_CHANNEL_FOLDER = join(
    CHANNELS_FOLDER,
    'nuclei'
)

##############################
# crops folders
##############################

CROPS_FOLDER = join(BASE_FOLDER, 'crops')

EMBRYOS_CROPS_FOLDER = join(
    CROPS_FOLDER,
    'embryos'
)

NUCLEI_CROPS_FOLDER = join(
    CROPS_FOLDER,
    'nuclei'
)

##############################
# masks
##############################

MASKS_FOLDER = join(BASE_FOLDER, 'masks')

EMBRYOS_MASKS_FOLDER = join(
    MASKS_FOLDER,
    'embryos'
)

EMBRYOS_MASKS_DIL_FOLDER = join(
    MASKS_FOLDER,
    'embryos_dil'
)

EMBRYOS_MASKS_CROPS_FOLDER = join(
    MASKS_FOLDER,
    'embryos_crops'
)

NUCLEI_MASKS_FOLDER = join(
    MASKS_FOLDER,
    'nuclei'
)

NUCLEI_MASKS_DIL_FOLDER = join(
    MASKS_FOLDER,
    'nuclei_dil'
)

NUCLEI_MASKS_CROPS_FOLDER = join(
    MASKS_FOLDER,
    'nuclei_crops'
)

DOTS_MASKS_FOLDER = join(
    MASKS_FOLDER,
    'dots'
)

##############################
# dataframes
##############################

DFS_FOLDER = join(BASE_FOLDER, 'dataframes')

OBJECTS_DFS_FOLDER = join(
    DFS_FOLDER,
    'objects'
)

JOINED_DFS_FOLDER = join(
    DFS_FOLDER,
    'joined'
)

SUMMARY_DFS_FOLDER = join(
    DFS_FOLDER,
    'summary'
)

ROIS_FOLDER = join(
    DFS_FOLDER,
    'rois'
)

DOTS_OBJECTS_DFS_FOLDER = join(
    OBJECTS_DFS_FOLDER,
    'dots'
)

OBJECT_CROPS_DF_PATH = join(
    JOINED_DFS_FOLDER,
    'nuclei_filtered.csv'
)

DOTS_JOINED_DF_FOLDER = join(
    JOINED_DFS_FOLDER,
    'dots'
)

##############################
# renaming
##############################

RENAME_PATTERN = 'Overlay Elements of '

##############################
# modules
##############################

convert_images_module = modules.convert_images_modules[IMAGES_EXTENSION]
rename_files_module = modules.rename_files_module
rois_to_objects_df_module = modules.rois_to_objects_df_module
crop_images_module = modules.crop_images_module
split_channels_module = modules.split_channels_module
difference_of_gaussians_module = modules.difference_of_gaussians_module
generate_binary_masks_module = modules.generate_binary_masks_module
generate_segmentation_masks_module = modules.generate_segmentation_masks_module
optimize_bit_depth_module = modules.optimize_bit_depth_module
generate_images_df_module = modules.generate_images_df_module
generate_objects_dfs_module = modules.generate_objects_dfs_module
join_dfs_module = modules.join_dfs_module
filter_df_module = modules.filter_df_module
generate_dot_size_summary_df_module = modules.generate_dot_size_summary_df_module

##############################
# defining commands
##############################

# rename files
rename_files = assemble_command(module=rename_files_module,
                                args={'-i': ROIS_FOLDER,
                                      '-p': f'#{RENAME_PATTERN}#'})

# convert images
convert_images = assemble_command(module=convert_images_module,
                                  args={'-i': IMGS_FOLDER,
                                        '-o': TIFS_FOLDER})

# rois to object df
rois_to_objects_df = assemble_command(module=rois_to_objects_df_module,
                                      args={'-i': ROIS_FOLDER,
                                            '-o': OBJECT_CROPS_DF_PATH})

# crop images
crop_tifs = assemble_command(module=crop_images_module,
                             args={'-d': OBJECT_CROPS_DF_PATH,
                                   '-i': TIFS_FOLDER,
                                   '-o': CROPS_FOLDER})

# split channels
split_channels = assemble_command(module=split_channels_module,
                                  args={'-i': CROPS_FOLDER,
                                        '-o': CHANNELS_FOLDER})

# dots (looped over every configured dot - supports any number of dots)

# defining placeholders for per-dot folder/path collectors (flattened by get_subfolders_list)
DOT_CHANNEL_FOLDERS = {}
DOT_BLUR_CHANNEL_FOLDERS = {}
DOT_MASKS_FOLDERS = {}
DOT_OBJECTS_DFS_FOLDERS = {}

# defining placeholders for commands lists
dots_segmentation_commands = []
dots_dataframes_commands = []

# getting dots settings dict items
dots_settings_dict_items = DOTS_SETTINGS.items()

# iterating over dots
for dot_settings_item in dots_settings_dict_items:

    # getting current dot key and settings
    dot_key, dot_settings = dot_settings_item

    # getting current dot toggles
    dot_toggles = DOTS_TOGGLES[dot_key]

    # getting current dot settings values
    dot_description = dot_settings.description
    dot_channel = dot_settings.segmentation_channel
    dot_dog = dot_settings.dog
    dot_blur_sigma_low = dot_settings.blur_sigma_low
    dot_blur_sigma_high = dot_settings.blur_sigma_high
    dot_lower_threshold = dot_settings.lower_threshold
    dot_segmentation_mode = dot_settings.segmentation_mode
    dot_filters = dot_settings.filters

    # getting current dot toggles values
    run_dot_segmentation = dot_toggles.segmentation
    run_dot_create_tables = dot_toggles.create_tables

    # getting current dot channel strings
    dot_channel_str = f'ch{dot_channel}'
    dot_blur_channel_str = f'ch{dot_channel}_blur'

    # getting current dot channel folders
    dot_channel_folder = join(NUCLEI_CHANNEL_FOLDER, dot_channel_str)
    dot_blur_channel_folder = join(NUCLEI_CHANNEL_FOLDER, dot_blur_channel_str)

    # getting current dot segmentation input folder (the difference of gaussians output, when dog is enabled)
    dot_segment_input_channel_folder = dot_blur_channel_folder if dot_dog else dot_channel_folder

    # getting current dot masks, objects dfs and joined df paths
    dot_masks_folder = join(DOTS_MASKS_FOLDER, dot_description)
    dot_objects_dfs_folder = join(DOTS_OBJECTS_DFS_FOLDER, dot_description)
    dot_images_df_path = join(JOINED_DFS_FOLDER, f'{dot_description}_images_joined.csv')
    dot_joined_df_path = join(DOTS_JOINED_DF_FOLDER, f'{dot_description}_joined.csv')
    dot_size_summary_df_path = join(SUMMARY_DFS_FOLDER, f'{dot_description}_size_summary_df.csv')

    # updating per-dot folder collectors
    current_dict = {dot_key: dot_channel_folder}
    DOT_CHANNEL_FOLDERS.update(current_dict)
    current_dict = {dot_key: dot_blur_channel_folder}
    DOT_BLUR_CHANNEL_FOLDERS.update(current_dict)
    current_dict = {dot_key: dot_masks_folder}
    DOT_MASKS_FOLDERS.update(current_dict)
    current_dict = {dot_key: dot_objects_dfs_folder}
    DOT_OBJECTS_DFS_FOLDERS.update(current_dict)

    # defining dot measurements string (intensity stats over its own channel)
    dot_measurements_str = ','.join([f'min_intensity#min@{dot_channel_folder}',
                                     f'max_intensity#max@{dot_channel_folder}',
                                     f'mean_intensity#mean@{dot_channel_folder}',
                                     f'median_intensity#median@{dot_channel_folder}',
                                     f'std_intensity#std@{dot_channel_folder}',
                                     f'background_mean_intensity#background_mean@{dot_channel_folder}'])

    # difference of gaussians (only used when dog is enabled)
    dog_dot = assemble_command(module=difference_of_gaussians_module,
                               args={'-i': dot_channel_folder,
                                     '-o': dot_blur_channel_folder,
                                     '-lg': dot_blur_sigma_low,
                                     '-hg': dot_blur_sigma_high})

    # generate binary masks (positives only when thresholding difference of gaussians images)
    binary_masks_flags = ['-p'] if dot_dog else None
    generate_binary_masks_dot = assemble_command(module=generate_binary_masks_module,
                                                 args={'-i': dot_segment_input_channel_folder,
                                                       '-o': dot_masks_folder,
                                                       '-m': dot_segmentation_mode,
                                                       '-lt': dot_lower_threshold},
                                                 flags=binary_masks_flags)

    # generate segmentation masks
    generate_segmentation_masks_dot = assemble_command(module=generate_segmentation_masks_module,
                                                       args={'-i': dot_masks_folder,
                                                             '-o': dot_masks_folder},
                                                       flags=['-ow'])

    # optimizing bit depth
    optimize_bit_depth_dot = assemble_command(module=optimize_bit_depth_module,
                                              args={'-i': dot_masks_folder,
                                                    '-o': dot_masks_folder},
                                              flags=['-ow'])

    # generate images df
    generate_images_df_dot = assemble_command(module=generate_images_df_module,
                                              args={'-i': dot_channel_folder,
                                                    '-o': dot_images_df_path})

    # generate objects dfs
    generate_objects_dfs_dot = assemble_command(module=generate_objects_dfs_module,
                                                args={'-sd': SCALES_STR,
                                                      '-i': dot_masks_folder,
                                                      '-p': dot_description,
                                                      '-o': dot_objects_dfs_folder,
                                                      '-c': dot_measurements_str})

    # join dfs
    join_dfs_dot = assemble_command(module=join_dfs_module,
                                    args={'-i': dot_objects_dfs_folder,
                                          '-o': dot_joined_df_path})

    # filter dfs (one command per configured filter, applied in place)
    filter_df_dot_commands = []
    dot_filters_items = dot_filters.items()
    for dot_filter_item in dot_filters_items:

        # getting current filter column and condition
        filter_column, filter_condition = dot_filter_item

        # assembling current filter command
        current_command = assemble_command(module=filter_df_module,
                                           args={'-i': dot_joined_df_path,
                                                 '-cn': filter_column,
                                                 '-co': filter_condition,
                                                 '-o': dot_joined_df_path},
                                           flags=['-ow'])

        # appending current filter command
        filter_df_dot_commands.append(current_command)

    # generate dot size summary df
    generate_dot_size_summary_df = assemble_command(module=generate_dot_size_summary_df_module,
                                                    args={'-i': dot_images_df_path,
                                                          '-d': dot_joined_df_path,
                                                          '-e': EXPERIMENTS_DF_PATH,
                                                          '-ds': DATASET,
                                                          '-t': TOP_N,
                                                          '-o': dot_size_summary_df_path})

    # assembling current dot segmentation commands (difference of gaussians goes before binary masks)
    dot_segmentation_commands = [generate_binary_masks_dot,
                                 generate_segmentation_masks_dot,
                                 optimize_bit_depth_dot]
    if dot_dog:
        dot_segmentation_commands.insert(0, dog_dot)

    # assembling current dot dataframes generation commands
    dot_dataframes_commands = [generate_images_df_dot,
                               generate_objects_dfs_dot,
                               join_dfs_dot]
    dot_dataframes_commands.extend(filter_df_dot_commands)
    dot_dataframes_commands.append(generate_dot_size_summary_df)

    # extending commands lists based on current dot toggles
    if run_dot_segmentation:
        dots_segmentation_commands.extend(dot_segmentation_commands)
    if run_dot_create_tables:
        dots_dataframes_commands.extend(dot_dataframes_commands)

# assembling base commands list
preprocessing_commands = [
                          rename_files,
                          convert_images,
                          rois_to_objects_df,
                          crop_tifs,
                          split_channels]

# defining placeholder for commands list
commands_list = []

# extending list based on conditionals
if RUN_PREPROCESSING:
    commands_list.extend(preprocessing_commands)
commands_list.extend(dots_segmentation_commands)
commands_list.extend(dots_dataframes_commands)

# getting vars dict
vars_dict = get_vars_dict()

# defining vars to skip
vars_to_skip = ['BASE_FOLDER']

# defining intermediate subfolders (could be safely deleted)
intermediate_subfolders = [TIFS_FOLDER,
                           CROPS_FOLDER]

# getting subfolder list
subfolders_list = get_subfolders_list(vars_dict=vars_dict,
                                      vars_to_skip=vars_to_skip)

# creating subfolders
create_subfolders(base_folder=BASE_FOLDER,
                  subfolders_list=subfolders_list)

# running commands
run_commands(commands_list=commands_list,
             overwrite_output=OVERWRITE_OUTPUT,
             skip_enter=SKIP_ENTER,
             simulate=SIMULATE_RUN,
             log_folder=LOG_FOLDER)

# checking if intermediate files should be cleared
if CLEAR_INTERMEDIATE_FILES:

    # deleting subfolders
    delete_subfolders(subfolders_list=intermediate_subfolders)

# printing execution message
print(f'finished {pipeline_name} pipeline run.')

######################################################################
# end of current module
