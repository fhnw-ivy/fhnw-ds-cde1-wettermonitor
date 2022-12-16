curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh ./get-docker.sh

git clone https://github.com/fhnw-ivy/fhnw-ds-cde1-wettermonitor.git
cd fhnw-ds-cde1-wettermonitor || exit

cp example.env .env

docker compose up -d

cp -fr autostart /etc/xdg/lxsession/LXDE-pi/autostart