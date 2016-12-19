import os

# Where plot summaries were saved
PLOT_FOLDER = os.path.abspath(os.path.join('..', 'plot_summaries'))
# Name of the combined plot text file
COMBINED_FILE_NAME = 'combined.txt'
# Files inside the plot directory to ignore
IGNORE_FILES = ['README.md', COMBINED_FILE_NAME]
# Line to separate plot
PLOT_SEPARATOR = '=================='

combined_file_path = os.path.join(PLOT_FOLDER, COMBINED_FILE_NAME)
with open(combined_file_path, 'w') as combined_file_fd:
    for basename in os.listdir(PLOT_FOLDER):
        if basename in IGNORE_FILES:
            continue

        plot_path = os.path.join(PLOT_FOLDER, basename)
        with open(plot_path, 'r') as plot_fd:
            plot = plot_fd.read()
            combined_file_fd.write(plot)
            combined_file_fd.write('\n%s\n' % PLOT_SEPARATOR)