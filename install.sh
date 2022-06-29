#!/bin/bash
if [[ $EUID -ne 0 ]]; then
   echo "This script must be run as root" 
   exit 1
fi

apt-get install -y python3-pip python-dev i2c-tools git

cd /

rm -r schedulePi

git clone https://github.com/Azazel101/schedulePi.git

cd schedulePi

pip3 install -r requirements.txt
python3 run.py


# Orange PI

# add to crontab
# sudo crontab -e
#@reboot sh /schedulePi/launcher.sh >/schedulePi/cronlog 2>&1

# set fix IP address
# nmtui