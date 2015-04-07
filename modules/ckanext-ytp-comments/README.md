ckanext-ytp-comments
====================

CKAN extension for adding comments to datasets. 

Anyone with an account can comment any public datasets. Users with modification access can delete comments from the dataset.

Some of the code is taken from [ckanext-comments](https://github.com/rossjones/ckanext-comments)


## Compatibility

Tested with CKAN 2.2 - 2.3

## Installation

Install to you ckan virtual environment

```
pip install -e  git+https://github.com/yhteentoimivuuspalvelut/ckanext-ytp-comments#egg=ckanext-ytp-comments
```

Add to ckan.ini

```
ckan.plugins = ... ytp_comments
```

Init db

```
paster --plugin=ckanext-ytp-comments initdb --config={ckan.ini}
```