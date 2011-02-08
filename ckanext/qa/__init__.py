# this is a namespace package
try:
    import pkg_resources
    pkg_resources.declare_namespace(__name__)
except ImportError:
    import pkgutil
    __path__ = pkgutil.extend_path(__path__, __name__)

import os
from logging import getLogger
from ckan.plugins import implements, SingletonPlugin

log = getLogger(__name__)

class QA(SingletonPlugin):
    pass
