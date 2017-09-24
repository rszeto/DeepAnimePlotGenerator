import os
import subprocess
import re
import time
import praw
import json
import sys
import Queue
from pprint import pprint
from getpass import getpass
from threading import Thread
from prawcore.exceptions import OAuthException

'''
The command to generate plot from a trained torch-rnn model. Assumptions made about the output
of the prediction command:
- Separator lines consist entirely of "=" characters and nothing else.
- The first line in the output is a separator line.
- Everything between the separator lines is part of some plot.
- The last plot in the output is most likely incomplete.

Temperature is set lower to encourage output more similar to the training data. Start text is
"=" to encourage the output to start with a plot separator.

The checkpoint path is specified in the config.json file, which fills in the "%s" at runtime.
'''
PREDICT_CMD_FORMAT = 'cd ../torch-rnn; th sample.lua ' \
        '-checkpoint %s -gpu %d -length %d -temperature 0.5 -start_text ='

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
# How many plots can be in the printing queue at once
MAX_PLOT_QUEUE_SIZE = 100

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
Function used by a queue worker to add plots asynchronously.
@args:
    - cmd (str): The command that runs the torch-rnn sampling code
    - queue (Queue.Queue): The queue storing the generated plots
'''
def add_plot_worker(cmd, queue):
    while True:
        output = subprocess.check_output(cmd, shell=True)
        # Divide the output according to separation lines, and strip each division (plot). Also
        # remove the first and last plots since they are empty and incomplete, respectively
        plots = [plot.strip() for plot in re.split('=+', output)][1:-1]
        # Further filter plot by the criteria specified in keep_plot()
        plots = [plot for plot in plots if keep_plot(plot)]
        print('Generated %d plots' % len(plots))
        for plot in plots:
            queue.put(plot)
            print('Inserted into queue: "%s..."' % plot[:20])

'''
Main loop. It generates some plot summaries and publishes them to the specified subreddit,
waiting for some time between submissions.
'''
if __name__ == '__main__':
    # Set working path to the location of this script
    os.chdir(os.path.dirname(os.path.abspath(__file__)))

    # Get information from the config JSON
    with open(CONFIG_FILE, 'r') as f:
        config = json.load(f)
    print('Found the following configuration:')
    pprint(config)
    print('')
    # Set relevant variables from configuration
    wait_time = config['wait_time']
    subreddit_name = config['subreddit_name']
    model_path = config['model_path']
    gpu_id = 0 if config['use_gpu'] else -1
    sample_length = config['sample_length']

    # Request the username and password a few times until authentication works
    for i in range(MAX_NUM_LOGIN_TRIES):
        # Get username and password
        username = raw_input('Reddit username: ')
        password = getpass('Reddit password: ')
        # Create Reddit wrapper and verify proper login
        reddit = praw.Reddit(username=username, password=password, **config["praw_config"])
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
    
    print('\nNow launching server as /u/%s\n' % reddit_user.name)

    # Generate plots in a separate daemon
    cmd = PREDICT_CMD_FORMAT % (model_path, gpu_id, sample_length)
    q = Queue.Queue(maxsize=MAX_PLOT_QUEUE_SIZE)
    t = Thread(target=add_plot_worker, args=(cmd, q))
    t.daemon = True
    t.start()

    while True:
        try:
            plot = q.get(False)
            # Submit the post
            submission = reddit.subreddit(subreddit_name).submit(
                    post_title_from_plot(plot), selftext=plot)
            # Print information
            print("Submitted post: >>>")
            print('Post ID: ' + submission.id)
            print("Plot:")
            print(plot)
            print("<<<")
        except Queue.Empty as e:
            print("No plots found, sleeping...")
        
        # Wait before posting again
        time.sleep(wait_time)