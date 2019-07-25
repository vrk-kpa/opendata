import ckan.plugins as p
import ckan.logic as logic


class HarvesterStatusPlugin(p.SingletonPlugin):
    p.implements(p.IActions, inherit=True)

    def get_actions(self):
        return {'harvester_status': harvester_status}


@logic.side_effect_free
def harvester_status(context=None, data_dict=None):
    sources = logic.get_action('harvest_source_list')(context, {'return_last_job_status': True})

    def last_job_status(source):
        j = source.get('last_job_status')

        if j is None:
            return {'status': 'not run', 'last_run': None}

        errors = j.get('stats', {}).get('errored')
        if errors is None:
            status = 'unknown'
        elif errors == 0:
            status = 'ok'
        else:
            status = 'error'

        return {
            'last_run': j.get('finished'),
            'status': status
            }

    status = {s.get('title', 'untitled'): last_job_status(s) for s in sources}

    return status
