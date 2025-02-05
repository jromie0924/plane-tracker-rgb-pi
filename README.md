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

## Run the App*
`scripts/start-tracker.sh`

Open a browser and navigate to `localhost:8888`

*More work will be required. This app is written in such a way that it depends on RapidAPI with an an API key stored in AWS Secrets. See below.