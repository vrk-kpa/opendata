import json
import datetime
import html
import reports

import ckan.lib.dictization.model_dictize as model_dictize
import ckan.model as model
import ckan.plugins as p
import ckan.lib.celery_app as celery_app

resource_dictize = model_dictize.resource_dictize
send_task = celery_app.celery.send_task


class QAPlugin(p.SingletonPlugin):

    p.implements(p.IConfigurer, inherit=True)
    p.implements(p.IConfigurable)
    p.implements(p.IRoutes, inherit=True)
    p.implements(p.IDomainObjectModification, inherit=True)
    p.implements(p.IResourceUrlChange)
    p.implements(p.ITemplateHelpers)

    def configure(self, config):
        self.site_url = config.get('ckan.site_url')

    def update_config(self, config):
        # check if new templates
        if p.toolkit.check_ckan_version(min_version='2.0'):
            if not p.toolkit.asbool(config.get('ckan.legacy_templates', False)):
                # add the extend templates
                p.toolkit.add_template_directory(config, 'templates_extend')
            else:
                # legacy templates
                p.toolkit.add_template_directory(config, 'templates')
            # templates for helper functions
            p.toolkit.add_template_directory(config, 'templates_new')
        else:
            # FIXME we don't support ckan < 2.0
            p.toolkit.add_template_directory(config, 'templates')
        p.toolkit.add_public_directory(config, 'public')

    def before_map(self, map):
        qa_controller = 'ckanext.qa.controller:QAController'
        res = 'ckanext.qa.controllers.qa_resource:QAResourceController'

        map.connect('/qa', controller=qa_controller, action='index')

        map.connect('/qa/dataset',
                    controller=qa_controller, action='package_index')
        map.connect('/qa/dataset/five_stars',
                    action='five_stars',
                    controller=qa_controller)

        map.connect('/qa/dataset/broken_resource_links',
                    action='dataset_broken_resource_links',
                    controller=qa_controller)

        map.connect('/qa/organisation/',
                    controller=qa_controller, action='organisation_index')

        map.connect('/qa/organisation/broken_resource_links',
                    action='broken_resource_links',
                    controller=qa_controller)

        map.connect('/qa/organisation/broken_resource_links/:id',
                    action='broken_resource_links',
                    controller=qa_controller)

        map.connect('qa_resource_checklink', '/qa/link_checker',
                    conditions=dict(method=['GET']),
                    controller=res,
                    action='check_link')

        map.connect('qa_api', '/api/2/util/qa/{action}',
                    conditions=dict(method=['GET']),
                    requirements=dict(action='|'.join([
                        'dataset_five_stars',
                        'broken_resource_links_by_dataset',
                    ])),
                    controller=qa_controller)
        map.connect('/api/2/util/qa/{action}.:(format)',
                    conditions=dict(method=['GET']),
                    requirements=dict(action='|'.join([
                        'broken_resource_links_by_dataset',
                    ])),
                    controller=qa_controller)
        map.connect('/api/2/util/qa/{action}/:(id).:(format)',
                    conditions=dict(method=['GET']),
                    requirements=dict(action='|'.join([
                        'organisations_with_broken_resource_links',
                        'broken_resource_links_by_dataset_for_organisation',
                    ])),
                    controller=qa_controller)

        return map

    def notify(self, entity, operation=None):
        if not isinstance(entity, model.Resource):
            return

        if operation:
            if operation == model.DomainObjectOperation.new:
                self._create_task(entity)
        else:
            # if operation is None, resource URL has been changed, as the
            # notify function in IResourceUrlChange only takes 1 parameter
            self._create_task(entity)

    def _create_task(self, resource):
        user = p.toolkit.get_action('get_site_user')(
            {'model': model, 'ignore_auth': True, 'defer_commit': True}, {}
        )
        context = json.dumps({
            'site_url': self.site_url,
            'apikey': user.get('apikey')
        })

        resource_dict = resource_dictize(resource, {'model': model})

        related_packages = resource.related_packages()
        if related_packages:
            resource_dict['is_open'] = related_packages[0].isopen()

        data = json.dumps(resource_dict)

        task_id = model.types.make_uuid()
        task_status = {
            'entity_id': resource.id,
            'entity_type': u'resource',
            'task_type': u'qa',
            'key': u'celery_task_id',
            'value': task_id,
            'error': u'',
            'last_updated': datetime.datetime.now().isoformat()
        }
        task_context = {
            'model': model,
            'user': user.get('name'),
        }

        p.toolkit.get_action('task_status_update')(task_context, task_status)
        send_task('qa.update', args=[context, data], task_id=task_id)

    @classmethod
    def get_star_html(cls, resource_id):
        report = reports.resource_five_stars(resource_id)
        stars = report.get('openness_score', -1)
        if stars >= 0:
            reason = report.get('openness_score_reason')
            return html.get_star_html(stars, reason)
        return None

    @classmethod
    def new_get_star_html(cls, resource_id):
        report = reports.resource_five_stars(resource_id)
        stars  = report.get('openness_score', -1)
        reason = p.toolkit._('Not Rated')
        if stars >= 0:
            reason = report.get('openness_score_reason')
        extra_vars = {'stars': stars, 'reason': reason}
        return p.toolkit.literal(p.toolkit.render('qa/snippets/stars_module.html',
                                 extra_vars=extra_vars))

    @classmethod
    def get_star_info_html(cls, stars):
        extra_vars = {'stars': stars}
        return p.toolkit.literal(p.toolkit.render('qa/snippets/stars_info.html',
                                 extra_vars=extra_vars))

    @classmethod
    def get_star_rating_html(cls, stars, reason):
        extra_vars = {'stars': stars, 'reason': reason}
        return p.toolkit.literal(p.toolkit.render('qa/snippets/stars.html',
                                 extra_vars=extra_vars))

    def get_helpers(self):
        return {'qa_stars': self.new_get_star_html,
                'qa_stars_rating': self.get_star_rating_html,
                'qa_stars_info': self.get_star_info_html}
