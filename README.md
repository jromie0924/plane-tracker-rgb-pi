# Project Overview

This project is based on [Colin Waddell's work](https://github.com/ColinWaddell/its-a-plane-python), with some additional features I’ve added.

## Clock Screen:
- Displays time, date, current temperature, and a 3-day forecast.
- The current temperature color is based on the current humidity level on a gradient of white-blue.
- Time changes color at sunrise and sunset.
- The date shows moon phases with a purple-to-white gradient. It gradually becomes white on the right until the full moon, then fades white on the left as the moon wanes.
- The display dims at predefined times, set in the config file.
- You can switch between 12hr/24hr time and choose imperial or metric units.

## Flight Tracker Screen:
- Displays the origin and destination airport codes, with distances to both airports.
- Airport codes are color-coded based on the difference between the scheduled and actual departure times, as well as the scheduled and estimated arrival times.

  **Departure:**
  - 0-20 mins: Green
  - 20-40 mins: Yellow
  - 40-60 mins: Orange
  - 1-4 hrs: Red
  - 4-8 hrs: Purple
  - 8+ hrs: Blue
  
  **Arrival:**
  - On-time or early: Green
  - 0-30 mins late: Yellow
  - 30-60 mins late: Orange
  - 1-4 hrs late: Red
  - 4-8 hrs late: Purple
  - 8+ hrs late: Blue

- An arrow between the airport codes acts as a progress bar for the flight, starting red (just left) and turning green (almost complete).
- Below, the airline’s IATA name, flight number, abbreviated aircraft type, and the distance/direction to your location are displayed.
- The airline's ICAO code is shown in the logo, indicating which airline is operating the flight. This is especially useful for regional carriers, where an airline might operate flights for multiple brands (e.g., Republic Airways flying for American Eagle, Delta Connection, and United Express).

I've spent a LOT of time messing with this and adding things and trying to make it as easy to set up as possible. If you'd like to get me a coffee, I'd appreciate it!
[paypal.me/c0wsaysmoo](https://paypal.me/c0wsaysmoo)

---

## Hardware Overview:
- Raspberry Pi 3A+ (Pi Zero had flickering, and Pi 5 isn’t compatible)
- [Adafruit bonnet](https://www.adafruit.com/product/3211)
- [64x32 RGB P4 panel](https://www.adafruit.com/product/2278)
- MicroSD card (any size)
- [5V 4A power supply](https://www.amazon.com/Facmogu-Switching-Transformer-Compatible-5-5x2-1mm/dp/B087LY41PV) (powers both the Pi and the bonnet)
- [CPU heatsink](https://www.adafruit.com/product/3083)
- [2x20 pin extender](https://www.microcenter.com/product/480891/schmartboard-inc-schmartboard-inc-short-2x20-female-stackable-headers-qty-4) to prevent the bonnet from resting on it
- [Optional power button](https://www.microcenter.com/product/420422/mcm-electronics-push-button-switch-spst-red) (though not really necessary)
- Soldering iron only required for PWM bridge

---

# Plane Tracker RGB Pi Setup Guide

Once you get your Raspberry Pi up and running, you can follow [this guide](https://linuxconfig.org/enabling-ssh-on-raspberry-pi-a-comprehensive-guide) to set up the project.

### 1. Install Raspberry Pi OS Lite
Using the official Raspberry Pi Imager, go to `Other` and select **Raspberry Pi OS Lite**. **Note** whether the version is **Bookworm** or **Bullseye** — this will matter later.

### 2. Connect via SSH
I use **MobaXterm** on Windows to SSH into the Pi. After SSH-ing into the Pi, proceed with the following steps.

### 3. Install the Adafruit Bonnet
[Install the bonnet](https://learn.adafruit.com/adafruit-rgb-matrix-bonnet-for-raspberry-pi/driving-matrices) by following the instructions provided by Adafruit.

### 4. Install Git and Configure Your Info
You'll need Git for downloading the project files and other resources:

```bash
sudo apt-get install git
git config --global user.name "YOUR NAME"
git config --global user.email "YOUR EMAIL"
```
Clone the repository:
```
git clone https://github.com/c0wsaysmoo/plane-tracker-rgb-pi
```
If the bridge on the bonnet is not soldered, you'll need to set HAT_PWM_ENABLED=False in the config file.
After cloning the files, move everything to the main folder, as some files need to be in /home/xxx/ rather than /home/xxx/plane-tracker-rgb-pi/
```
mkdir /home/XXX/logos
mv /home/XXX/logo/* /home/path/logos/
mv /home/XXX/logo2/* /home/path/logos/
```

For Linux Bookworm:
```
sudo apt install python3-pip
sudo rm /usr/lib/python3.11/EXTERNALLY-MANAGED
pip3 install pytz requests
pip3 install FlightRadarAPI
sudo setcap 'cap_sys_nice=eip' /usr/bin/python3.11
```

For Linux Bullseye:
```
sudo apt install python3-pip
sudo pip3 install pytz requests
sudo pip3 install FlightRadarAPI
```

Make the Script Executable
```
chmod +x /home/path/its-a-plane-python/its-a-plane.py
```

Run the Script

For Bookworm
```
/home/path/its-a-plane-python/its-a-plane.py
```

For Bullseye
```
sudo /home/path/its-a-plane-python/its-a-plane.py
```

Set Up the Script to Run on Boot
To ensure the script runs on boot, use crontab -e to edit the cron jobs and add the following lines:
For Bookworm
```
@reboot sleep 60 && ./its-a-plane.py
```

For Bullseye 
```
@reboot sleep 60 && sudo ./its-a-plane.py
```

Optional: Add a Power Button
If you'd like to add a power button, you can solder the GND/SCL pins on the bonnet. Then, run the following commands:
```
git clone https://github.com/Howchoo/pi-power-button.git
./pi-power-button/script/install
```


I'm on reddit under this name if you have any questions or let me know if you make this.

![tracker](https://github.com/user-attachments/assets/534b990d-ad96-4332-ac72-9e2538048b0b)
![PXL_20241019_155956016](https://github.com/user-attachments/assets/2a2fbde8-6240-4e0c-a082-fc6db95ab368)
![PXL_20241019_165305826](https://github.com/user-attachments/assets/2a12f416-25d2-49b4-a5d0-bf9e9a4c7edb)
![PXL_20241019_165254031](https://github.com/user-attachments/assets/30cf66aa-25fb-4287-9557-3301418ea4b3)
![PXL_20241019_155500974](https://github.com/user-attachments/assets/5edae259-fbf3-4b8f-8ee7-4ec05742c6de)
![PXL_20241019_155518437](https://github.com/user-attachments/assets/a16bc27b-43ff-4bcd-bda7-aedb853f12ca)
![PXL_20241019_155629794](https://github.com/user-attachments/assets/2418ee63-a429-49c2-8c70-15f3f678ef76)
![PXL_20241019_155605121](https://github.com/user-attachments/assets/94edc647-e34e-4a70-81fa-fba3a28a2bc3)


