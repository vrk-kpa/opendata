import ckan.plugins as plugins
from ckan.plugins import implements, toolkit

import datetime
import logging

log = logging.getLogger(__name__)

class YtpCommentsPlugin(plugins.SingletonPlugin):
    implements(plugins.IRoutes, inherit=True)
    implements(plugins.IConfigurer, inherit=True)
    implements(plugins.IPackageController, inherit=True)
    implements(plugins.ITemplateHelpers, inherit=True)
    implements(plugins.IActions, inherit=True)
    implements(plugins.IAuthFunctions, inherit=True)

    # IConfigurer

    def configure(self, config):
        log.debug("Configuring comments module")


    def update_config(self, config):
        toolkit.add_template_directory(config, "templates")
        toolkit.add_public_directory(config, 'public')
        toolkit.add_resource('public/javascript/', 'comments_js')


    def get_helpers(self):
        return {
            'get_comment_thread': self._get_comment_thread
        }

    def get_actions(self):
        import ckanext.ytp.comments.logic.action as actions
        return {
            "comment_create": actions.create.comment_create,
            "thread_show": actions.get.thread_show,
            "comment_update": actions.update.comment_update,
            "comment_show": actions.get.comment_show,
            "comment_delete": actions.delete.comment_delete
        }

    def get_auth_functions(self):
        import ckanext.ytp.comments.logic.auth as auths
        return {
            'comment_create': auths.create.comment_create,
            'comment_update': auths.update.comment_update,
            'comment_show': auths.get.comment_show,
            'comment_delete': auths.delete.comment_delete
        }
    # IPackageController

    def before_view(self, pkg_dict):
        # TODO: append comments from model to pkg_dict
        return  pkg_dict

    # IRoutes

    def before_map(self, map):
        """
            /dataset/NAME/comments/reply/PARENT_ID
            /dataset/NAME/comments/add
        """
        controller = 'ckanext.ytp.comments.controller:CommentController'
        map.connect('/dataset/{dataset_id}/comments/add', controller=controller, action='add')
        map.connect('/dataset/{dataset_id}/comments/{comment_id}/edit', controller=controller, action='edit')
        map.connect('/dataset/{dataset_id}/comments/{parent_id}/reply', controller=controller, action='reply')
        map.connect('/dataset/{dataset_id}/comments/{comment_id}/delete', controller=controller, action='delete')
        return map

    def _get_comment_thread(self, dataset_name):
        import ckan.model as model
        from ckan.logic import get_action
        url =  '/dataset/%s' % dataset_name
        return get_action('thread_show')({'model': model}, {'url': url})



