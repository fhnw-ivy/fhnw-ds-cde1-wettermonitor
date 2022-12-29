# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh ./get-docker.sh

# Clone repository
git clone https://github.com/fhnw-ivy/fhnw-ds-cde1-wettermonitor.git
cd fhnw-ds-cde1-wettermonitor || exit

cp example.env .env
docker compose up -d

# Configure autostart
cp -fr autostart /etc/xdg/lxsession/LXDE-pi/autostart

# Reboot
shutdown -r +2 "Server is going to reboot in two minutes"
