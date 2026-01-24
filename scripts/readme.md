### Run these commands for any script that needs to be invoked by systemd

`sudo chcon -t bin_t /home/jackson/plane-tracker-rgb-pi/scripts/start-tracker-comp.sh`

... or if that doesn't work use this:
`sudo semanage fcontext -a -t bin_t "/home/jackson/plane-tracker-rgb-pi/scripts/start-tracker-comp.sh"`
`sudo restorecon -v /home/jackson/plane-tracker-rgb-pi/scripts/start-tracker-comp.sh`

