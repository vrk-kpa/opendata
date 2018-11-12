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

Install dependencies with npm (might require sudo):

	npm install -d

Build assets with gulp:

	gulp

Check out `resources` folder for results.


## Structure

`resources` directory is deleted in the build process and generated from `src` dir. Fonts, images, templates and vendor directories are pretty much copies from src.

`styles` directory contains main.css compiled from less-files. 

`static` contains copies from static_pages with css and images inlined during build.

## Less-files

`less` directory contain all less-files used in project. It also contains upstream bootstrap and ckan sources. To modify css of YTP drupal or YTP ckan, less-files in the root of less directory are modified. It is presumed that upstream files are unmodified and can be upgraded at will at anytime.

### Exceptions

[upstream_boostrap/bootstrap.less](src/less/upstream_bootstrap/bootstrap.less) imports [YTP varibles.less](src/less/variables.less) to modify bootstrap variables before bootstrap building, similar to what [Boostrap customize](http://getbootstrap.com/customize/) does.

`upstream_ckan` contains [ytp_ckan_bootstrap.less](src/less/upstream_ckan/ytp_ckan_bootstrap.less) and [ytp_main.less](src/less/upstream_ckan/ytp_main.less) which are used to build ckan css.


## Font Awesome

* .npmrc is required for npm install to work, available in confluence
* If new modules are added to package.json, remember to update [fallback package.json](../../ansible/roles/common_webserver/files/package.json) to reflect that.
