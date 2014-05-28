# ytp-assets-common

Common assets (theme, fonts, JavaScript modules) for YTP Drupal and CKAN instances.

## How to Develop

Install node.js (version 0.8 or higher) and other tools

PPA is only required if node.js version is lower than 0.8

	sudo add-apt-repository ppa:chris-lea/node.js
	sudo apt-get update

	sudo apt-get install nodejs

Install gulp:

	sudo npm install -g gulp

Get a copy of this repo:

	git clone https://github.com/yhteentoimivuuspalvelut/ytp-assets-common.git
	cd ytp-assets-common

Install dependencies with npm (might require sudo):

	npm install -d

Build assets with gulp:

	gulp

Check out `resources` folder for results.

Note: `resources/styles`, `resources/images` and `resources/templates` are generated from `less`, `images` and `templates` paths. 
