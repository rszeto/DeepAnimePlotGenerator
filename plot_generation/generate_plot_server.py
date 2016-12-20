import os
import subprocess
import re
import time
import praw
import json
import sys
from pprint import pprint
from getpass import getpass
from prawcore.exceptions import OAuthException
import pdb

'''
The command to generate plot from a trained torch-rnn model. Assumptions made about the output
of the prediction command:
- Separator lines consist entirely of "=" characters and nothing else.
- The first line in the output is a separator line.
- Everything between the separator lines is part of some plot.
- The last plot in the output is most likely incomplete.

Temperature is set lower to encourage output more similar to the training data. Start text is
"=" to encourage the output to start with a plot separator.
'''
PREDICT_CMD = 'cd ../torch-rnn; th sample.lua ' \
        '-checkpoint cv/checkpoint_59000.t7 -length 5000 -temperature 0.5 -start_text ='

# The basename of the file to load config from
CONFIG_FILE = 'config.json'
# How many times to ask for username and password before giving up
MAX_NUM_LOGIN_TRIES = 3
# How long a plot summary needs to be for submission
MIN_PLOT_LENGTH = 100
# About how long a post title should be. Only used as a guide.
APPROX_POST_TITLE_LENGTH = 140
# Characters that look bad when preceeding an ellipses. Used for generation post titles.
PUNCTUATION = [':,-!(.?;']
# Line to separate plots during server output
PLOT_SEPARATOR = '=================='
# Wait time between posts, in seconds
WAIT_TIME = 1800
# The name of the subreddit to publish to
SUBREDDIT_NAME = 'DeepAnimePlot'

'''
Function that determines whether to publish a plot under various criteria. For now, it
only checks that the plot is long enough.
@args:
    - plot (str): The plot
'''
def keep_plot(plot):
    return len(plot) > MIN_PLOT_LENGTH

'''
Function that generates the title for a post from the plot. Basically, it cuts off the
plot at a nice point and adds ellipses.
@args:
    - plot (str): The plot
'''
def post_title_from_plot(plot):
    # For short plots, set title to plot
    if len(plot) < APPROX_POST_TITLE_LENGTH:
        return plot

    # Initialize title as truncated plot
    title = plot[:plot.rfind(' ', 0, APPROX_POST_TITLE_LENGTH)]
    # If title ends with punctuation, remove it
    if title[-1] in PUNCTUATION:
        title = title[:-1]
    # Return title with ellipses 
    return title + '...'

'''
Main loop. It generates some plot summaries and publishes them to /r/DeepAnimePlot, waiting for
some time between submissions.
'''
if __name__ == '__main__':
    # Set working path to the location of this script
    os.chdir(os.path.dirname(os.path.abspath(__file__)))

    # Get information from the config JSON
    with open(CONFIG_FILE, 'r') as f:
        config = json.load(f)
    print('Found the following configuration:')
    pprint(config)
    print()

    # Request the username and password a few times until authentication works
    for i in range(MAX_NUM_LOGIN_TRIES):
        # Get username and password
        username = raw_input('Reddit username: ')
        password = getpass('Reddit password: ')
        # Create Reddit wrapper and verify proper login
        reddit = praw.Reddit(username=username, password=password, **config)
        try:
            reddit_user = reddit.user.me()
        except OAuthException:
            # Give up if too many login tries were made
            if i == MAX_NUM_LOGIN_TRIES - 1:
                print('Too many failed login attempts. Quitting')
                sys.exit(1)
            else:
                print('Invalid username and/or password, try again')
                # Login failed, so go to start of loop
                continue

        # Login succeeded, so break
        break
    
    print('\nNow launching server as /u/' + reddit_user.name)
    print(PLOT_SEPARATOR)
    pdb.set_trace()

    while True:
        # Generate plots in a subprocess and get the output
        output = subprocess.check_output(PREDICT_CMD, shell=True)
        # Divide the output according to separation lines, and strip each division (plot). Also
        # remove the first and last plots since they are empty and incomplete, respectively
        plots = [plot.strip() for plot in re.split('=+', output)][1:-1]
        # Further filter plot by the criteria specified in keep_plot()
        plots = [plot for plot in plots if keep_plot(plot)]
        # Process all but the first and last plots, which are empty and incomplete respectively
        for plot in plots:
            # Submit the post
            submission = reddit.subreddit(SUBREDDIT_NAME).submit(
                    post_title_from_plot(plot), selftext=plot)
            # Print information
            print('Post ID: ' + submission.id)
            print('Plot:')
            print(plot)
            print(PLOT_SEPARATOR)
            # Wait before posting again
            time.sleep(WAIT_TIME)
