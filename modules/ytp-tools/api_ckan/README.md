
# CKAN API of Avoindata.fi

This directory includes documentation and demo code on how to use the CKAN API of Avoindata.fi/Yhteentoimivuuspalvelut. The web service uses CKAN to provide a catalog of open datasets. Through the API, an organization can add their datasets into the service.

In the CKAN data model, *users* and *datasets* belong to *organizations*. Organizations own datasets and mandate permissions. Datasets describe a single, logical set of open data and can hold *resources* which are files or external links.

The following code examples are provided here:

* **ckan_api_example_client_library.py:** A Python example that uses the [ckanclient][ckanclient] library in making the HTTP requests. If you are using Python, it is advisable to use this library.
* **ckan_api_example_http.py:** A lower-level Python example that uses the [requests][requests] library in making the HTTP requests. If for some reason you must form the HTTP requests by yourself, this example gives you some basic pointers.

## Getting started

First you need to acquire a user account and an API key:

1. Register to [alpha.avoindata.fi](http://alpha.avoindata.fi) (or try the direct link http://alpha.avoindata.fi/fi/user/register ).
2. Login and go to your user profile via the top bar (or try the direct link [http://alpha.avoindata.fi/data/fi/user/YOUR_USERNAME](http://alpha.avoindata.fi/data/fi/user/) ).
3. Copy-paste your API key from the user profile.

Then you can install the prequisites for the code examples:

    sudo apt-get install python-virtualenv
    virtualenv avoindata_api
    cd avoindata_api
    source bin/activate
    pip install requests
    pip install ckanclient

To try out the examples, run the scripts using your API key:

    wget https://raw.github.com/yhteentoimivuuspalvelut/ytp-tools/master/api_ckan/ckan_api_example_client_library.py
    wget https://raw.github.com/yhteentoimivuuspalvelut/ytp-tools/master/api_ckan/ckan_api_example_http.py
    python ckan_api_example_client_library.py http://alpha.avoindata.fi/data/api 12345678-90ab-f000-f000-f0d9e8c7b6aa
	python ckan_api_example_http.py http://alpha.avoindata.fi/data/api 12345678-90ab-f000-f000-f0d9e8c7b6aa

## Known issues

* Deleting an organization or dataset (organization_delete and package_delete) usually return success even though they do not actually delete the organization or dataset, but merely change their state to deleted. Successive creations using the same names will fail, complaining that there is already an entity with that name. Deleting them from the Web interface seem to delete them completely.

## Disclaimer

As this is a development version of the service, any data you import/create in the service can be lost without notice at any time. Furthermore, new software is deployed daily (sometimes several times per day) to the alpha server from the master branch, so it is excepted that the server is sometimes down and things will break. However, the API should be much more stable and less buggy than the web interface.

## Help and support

If you want a more mature and stable, but more generic CKAN playground, you can also try using the [API](http://demo.ckan.org/api) of the [CKAN demo instance](http://demo.ckan.org). If you are having trouble with our API, create an [issue at Github](https://github.com/yhteentoimivuuspalvelut/ytp/issues) or join the discussion at [avoindata.net](http://avoindata.net/).

## Further reading

* [CKAN API documentation][ckanapi]
* [CKAN API client library and CLI][ckanclient]
* [CKAN API client libraries in other languages (old docs, might be obsolete)][otherclients]

[ckanapi]: http://docs.ckan.org/en/latest/api/index.html
[ckanclient]: https://github.com/okfn/ckanclient
[requests]: http://requests.readthedocs.org/en/latest/
[otherclients]: http://docs.ckan.org/en/ckan-1.7.1/api.html#clients
