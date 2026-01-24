### Run these commands for any script that needs to be invoked by systemd

`sudo chcon -t bin_t $HOME/plane-tracker-rgb-pi/scripts/start-tracker-comp.sh`

... or if that doesn't work use this (replace \`$HOME/plane-tracker-rgb-pi\` with your actual install path, e.g. \`<repo_root>\`):
`sudo semanage fcontext -a -t bin_t "$HOME/plane-tracker-rgb-pi/scripts/start-tracker-comp.sh"`
`sudo restorecon -v $HOME/plane-tracker-rgb-pi/scripts/start-tracker-comp.sh`

