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
            return {'status': 'not run', 'last_run': None, 'job_id': None}

        created = j.get('created')
        started = j.get('gather_started')
        finished = j.get('finished')
        errors = j.get('stats', {}).get('errored', 0)

        if j.get('status') == 'Finished' or finished is not None:
            status = 'finished'
        elif started is not None:
            status = 'running'
        else:
            status = 'pending'

        return {'status': status,
                'errors': errors,
                'started': created,
                'finished': finished,
                'job_id': j.get('id')}

    def include_source(source):
        # Only include periodically run harvesters unless otherwise requested
        if source.get('frequency') == 'MANUAL' and not data_dict.get('include_manual'):
            return False

        # Don't include never run harvesters unless otherwise requested
        if source.get('last_job_status') is None and not data_dict.get('include_never_run'):
            return False

        return True

    status = {s.get('title', 'untitled'): last_job_status(s) for s in sources if include_source(s)}

    return status
