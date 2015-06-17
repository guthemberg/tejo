#!/bin/sh

install_mongodb()
{
	#	sudo ln -s /bin/whiptail /usr/bin/whiptail
	sudo apt-key adv --keyserver keyserver.ubuntu.com --recv 7F0CEB10
	echo 'deb http://downloads-distro.mongodb.org/repo/debian-sysvinit dist 10gen'| sudo tee /etc/apt/sources.list.d/mongodb.list
	sudo apt-get -q -y update
	sudo DEBIAN_FRONTEND=noninteractive apt-get -q -y install mongodb-org
	sudo pip install pymongo
}

###main

printf "Installing mongodb..."
install_mongodb
printf " done.\n"
