# Deep Anime Plot Generator

The Deep Anime Plot Generator is a system that uses a Recurrent Neural Network (RNN) to generate novel anime plot summaries and posts them to Reddit. This code base consists of three major parts:

* **Plot scraper**: Anime plot summaries are scraped from MyAnimeList, and collected into a form that can be fed to the RNN for training.
* **Torch-RNN**: The code used to train an RNN and generate new text. This is simply a submodule for `torch-rnn` developed by Justin Johnson.
* **Reddit bot**: Using a trained RNN, the bot generates new plot summaries and posts them to Reddit. It acts as a server that continuously publishes summaries until you kill it.

This code was tested on Ubuntu 14.04 64-bit.


## Step 0: Pre-Requisites

### Node.js

Node.js is required to run the plot scraper. Installation instructions for a wide variety of OSs can be found [here](https://nodejs.org/en/download/package-manager/).

### Python 2.7

The plot scraper and Reddit bot are written for Python 2.7 (I do not guarantee that it runs on Python 3). The version that is pre-installed on Ubuntu 14.04 should be sufficient. You can also install it from [the official website](https://www.python.org/downloads/).

### torch-rnn

There are additional requirements for `torch-rnn`. Please follow the installation instructions in their repository.

### Reddit Development

You need to create an application with the Reddit user that will act as your bot. To do this, go to the [Reddit App Management page](https://www.reddit.com/prefs/apps/) and press the button to create a new app. Enter whatever you want to the _name_, _description_, and _about uri_ fields. For the type of app, choose _script_. For the _redirect uri_ field, enter some valid URL (it doesn't matter which; I used `http://www.example.com/unused/redirect/uri`).

After submitting, you will see information about your app under _developed applications_. Expand the area by clicking _edit_ and make note of the following information, which is needed to run the Reddit bot:

* Client ID: This is a 14-character string that can be found directly under _personal use script_ (e.g. SI8pN3DSbt0zor).
* Client secret: This is a 28-character string listed under _secret_ (e.g. _xaxkj7HNh8kwg8e5t4m6KvSrbTI)


## Step 0.1: Optional Installations

I recommend installing [pip](https://pip.pypa.io//en/latest/installing/) and [virtualenv](https://virtualenv.pypa.io/en/stable/installation/), which respectively make installation and management of Python modules convenient. The following steps, as well as `torch-rnn`, assume you have both installed.


## Step 1: Run Plot Scraper

The first step is to download plot summaries to your computer and combine them into one file for processing in `torch-rnn`. To do this, open up a terminal in the root directory of this project and run the lines below.

```
DAPG_ROOT=$(pwd)
cd scraper
# Install required Node modules
npm install -d
# Run the scraper. This takes about 3 hours.
node scraper.js
# Combine the downloaded plots
python combine_plots.py
```

Individual plot summaries, as well as the combined text file to feed to `torch-rnn`, will be saved in the `plot_summaries` folder under the root project directory.


## Step 2: Run torch-rnn

Next, we need to train an RNN on the plot summaries we just downloaded. First, pre-process the combined plot summaries:

```
cd $DAPG_ROOT
cd torch-rnn
python scripts/preprocess.py --input_txt ../plot_summaries/combined.txt --output_h5 my_data.h5 --output_json my_data.json
```

Then train the model, which can take several hours depending on how complex your model is. The parameters I used below will give a relatively strong model, but you can drop `rnn_size` and `num_layers` if you wish:

```
th train.lua -input_h5 my_data.h5 -input_json my_data.json -rnn_size 512 -num_layers 3 -print_every 200
```

Afterwards, you'll have several checkpoints in `$DAPG_ROOT/torch-rnn/cv`; the last checkpoint I got was named `checkpoint_59000.t7`, which I use in the Reddit bot.


### Step 3: Run the Reddit bot

With our trained model, we can flood the world with new anime ideas using our Reddit bot! First, go into the bot folder, copy or rename the example config file, and modify the fields as needed:

```
cd $DAPG_ROOT
cd plot_generation
cp config.json.example config.json
# Edit the config file
```

To fill in the config file, copy the client ID and client secret from Step 0 and paste them into the fields for `client_id` and `client_secret`, respectively. Replace the bits in angle brackets as appropriate.

Then, install the required Python modules in a virtual environment with `pip`. If you don't have `virtualenv`, you can skip that line, but modules will be installed globally. If you don't have `pip`, use the corresponding installer for your Python distribution (e.g. `conda`, `easy_install`, or your package manager).

```
virtualenv .env
source .env/bin/activate
pip install -r requirements.txt
```

Next, start the bot server by running the command below:

```
python generate_plot_server.py
```

It will ask for a Reddit username and password, which are the credentials for the bot account. If everything worked, your Reddit bot will post a new anime plot summary every half-hour. And oh, what amazing summaries they shall be!

When you're ready to turn off the server, just kill it (`Ctrl+C` on Linux). Then, deactivate your virtual environment:

```
deactivate
```


## Acknowledgements

I would like to thank Andrej Karpathy, Justin Johnson, and the developers of the [Python Reddit API Wrapper (PRAW)](https://github.com/praw-dev/praw) for creating accessible code for training RNNs and interacting with Reddit, respectively. I also want to thank the MyAnimeList community for providing such a great resource for anime and manga information. Finally, I want to thank my friends for encouraging me to do these stupid side projects in my free time.