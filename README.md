ckanext-hierarchy - Organization hierarchy for CKAN
===================================================

Provides a new field on the organization edit form to select a parent
organization. This new hierarchical arrangement of organizations is displayed
using templates in this extension, instead of the usual list. An organization
page also displays the section of the tree that it is part of, under the
'About' tab.

Forms (hierachy_form plugin):
* /organization/new
* /organization/edit/{id}

Templates (hierarchy_display plugin):
* /organization - now shows the organization hierarchy instead of list
* /organization/about/{id} - now also shows the relevant part of the hierarchy

You can use this extension with CKAN as it is, enabling both plugins. Or if you
use an extension to customise the form already with an IGroupForm, then you
will want to only use the hierarchy_display plugin, and copy bits of the
hierarchy_form into your own. If you have your own templates then you can use
the snippets (or logic functions) that this extension provides to display the
trees.

NB:
This extension relies on a particular feature of CKAN: https://github.com/datagovuk/ckan/tree/1038-organization-hierarchy which at the time of writing is merged into branch release-v2.2 (i.e. CKAN 2.2 beta, which is quite usable) and will be released in CKAN 2.2 (early 2014).

TODO:
* make the trees prettier with JSTree
