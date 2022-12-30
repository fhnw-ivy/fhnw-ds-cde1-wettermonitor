# Install Docker
echo "Installing Docker"
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh ./get-docker.sh
echo "Docker installed"

# Clone repository
echo "Cloning repository"
git clone https://github.com/fhnw-ivy/fhnw-ds-cde1-wettermonitor.git
cd fhnw-ds-cde1-wettermonitor || exit
echo "Repository cloned"

# Configure autostart
echo "Configuring autostart"
cp -fr autostart /etc/xdg/lxsession/LXDE-pi/autostart
echo "Autostart configured"

# Configure Docker
echo "Configuring Docker"
cp example.env .env
docker compose up -d
echo "Docker configured"

echo "Installation finished. Rebooting device..."
sudo shutdown -r now