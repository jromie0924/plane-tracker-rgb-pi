# ADSB Plane Tracker

This repo was initially forked from [c0wsaysmoo' repository](https://github.com/c0wsaysmoo/plane-tracker-rgb-pi). I initially discovered [their reddit post on r/delta](https://www.reddit.com/r/delta/comments/1g4wsi6/weird_delta_flight_over_my_house_this_morning/) and decided to fork it. After many modifications to make it my own I decided to detach it, as it became very different on the backend from theirs, so much credit to them for getting me started here.

## Getting Started: Install System Dependencies
### pipenv
#### Ubuntu:
`sudo apt install pipenv`

#### Fedora:
`sudo dnf install pipenv`

### pyenv
#### Ubuntu:
`sudo apt install -y make build-essential libssl-dev zlib1g-dev libbz2-dev libreadline-dev libsqlite3-dev wget curl llvm libncursesw5-dev xz-utils tk-dev libxml2-dev libxmlsec1-dev libffi-dev liblzma-dev`

`curl https://pyenv.run | bash`

`export PYENV_ROOT="$HOME/.pyenv"`

`[[ -d $PYENV_ROOT/bin ]] && export PATH="$PYENV_ROOT/bin:$PATH"`

`eval "$(pyenv init -)"`

#### Fedora:
`sudo dnf builddep python3`

`curl https://pyenv.run | bash`

`export PYENV_ROOT="$HOME/.pyenv"`

`[[ -d $PYENV_ROOT/bin ]] && export PATH="$PYENV_ROOT/bin:$PATH"`

`eval "$(pyenv init -)"`

## Getting Started: Installing project dependencies
`cd plane-tracker-rgb-pi`

`pipenv shell`

`pipenv install`

`pipenv install --dev`

## Configuration
`src/config.py`
* Update your ZIP and Country code to tell the app where you are. NOTE see the bottom of the file for a note regarding this.

## Run the App*
`scripts/start-tracker.sh`

Open a browser and navigate to `localhost:8888`

## Footnotes

More work will be required if you want to get your coordinates based on ZIP code. This app is written in such a way that it depends on RapidAPI with an an API key stored in AWS Secrets. You'll need to create an account and an API key, and store it in AWS Secrets (or any cloud secrets provider, but you'll need to update the code)

If you **don't** want to utilize the RapidAPI's forward geocoding endpoint, that's okay too; you can simply update the `LOCATION_COORDINATES_OVERRIDE` value in `src/config.py` to use speific coordinates (like that of your home, for instance), and the geo service will know to use those rather than querying the API endpoint. You'll still get an error from the authentication service, but it won't cause the app to crash. It follows the same format as the `LOCATION_COORDINATES_DEFAULT` value; in fact, you can also just keep that populated, and when the auth services fails to retrieve an API token, the geo service will fall back to the default value. So you more or less have two options when it comes to avoiding the use of a 3rd party API for getting your coordinates based on your ZIP and country codes.