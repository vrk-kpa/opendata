import logging

from ckan.lib.base import h, BaseController, render, abort, request
from ckan import model
from ckan.common import c
from ckan.logic import check_access, get_action, clean_dict, tuplize_dict, ValidationError, parse_params
from ckan.lib.navl.dictization_functions import unflatten


log = logging.getLogger(__name__)

class CommentController(BaseController):
    def add(self, dataset_name):
        return self._add_or_reply(dataset_name)

    def _add_or_reply(self, dataset_name):
        """
       Allows the user to add a comment to an existing dataset
       """
        context = {'model':model,'user': c.user}

        # Auth check to make sure the user can see this package
        ctx = context
        ctx['id'] = dataset_name
        check_access('package_show', ctx)

        try:
            c.pkg_dict = get_action('package_show')(context, {'id': dataset_name})
            c.pkg = context['package']
        except:
            abort(403)

        errors = {}

        if request.method == 'POST':
            data_dict = clean_dict(unflatten(
                tuplize_dict(parse_params(request.POST))))
            data_dict['parent_id'] = c.parent.id if c.parent else None
            data_dict['url'] = '/dataset/%s' % c.pkg.name

            success = False
            try:
                res = get_action('comment_create')(context, data_dict)
                success = True
            except ValidationError, ve:
                errors = ve.error_dict
            except Exception, e:
                abort(403)

            if success:
                h.redirect_to(str('/dataset/%s#comment_%s' % (c.pkg.name, res['id'])))

        vars = {'errors': errors}

        return render("package/read.html")