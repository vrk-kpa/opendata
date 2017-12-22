from ckan.lib.cli import CkanCommand
from ckan.logic import get_action
from ckan import model


class YtpTaskAdd(CkanCommand):
    """ Command to add task to schedule table """
    max_args = 4
    min_args = 4

    usage = "task_id task frequency data"
    summary = "Add task to scheduling. Frequency can be daily, weekly or monthly. Data in json format."
    group_name = "ytp_tasks"

    def __init__(self, name):
        super(YtpTaskAdd, self).__init__(name)

        self.parser.add_option("-w", "--wait",
                               action="store", dest="wait", default=None,
                               help="Execute task now and wait for task in seconds")
        self.parser.add_option("-e", "--execute",
                               action="store_true", dest="execute", default=False,
                               help="Execute task now")

    def command(self):
        self._load_config()

        task_id = self.args[0]
        task_name = self.args[1]
        task_frequency = self.args[2].upper()
        task_data = self.args[3]

        context = {'model': model, 'session': model.Session, 'ignore_auth': True}
        get_action('ytp_tasks_add')(context, {'id': task_id, 'task': task_name, 'frequency': task_frequency.upper(), 'data': task_data})

        if self.options.wait or self.options.execute:
            import uuid
            from ckan.lib.celery_app import celery

            if self.verbose:
                print u"Executing %s" % task_name
            result = celery.send_task(task_name, args=(task_data,), task_id=str(uuid.uuid4()))
            if self.options.wait:
                result.get(timeout=int(self.options.wait))


class YtpTaskExecute(CkanCommand):
    """ Simple command to execute tasks """
    max_args = 0
    min_args = 0

    usage = ""
    summary = "Execute all tasks now"
    group_name = "ytp_tasks"

    def command(self):
        self._load_config()

        import uuid
        from ckan.lib.celery_app import celery

        if self.verbose:
            print u"Executing all scheduled tasks now"
        task = celery.send_task("ckanext.ytp_tasks.execute_all", task_id=str(uuid.uuid4()))
        if self.verbose:
            print u"Task '%s' set to queue" % unicode(task)


class YtpTaskInitDatabase(CkanCommand):
    """ Init task database command """
    max_args = 0
    min_args = 0

    usage = ""
    summary = "Init task database"
    group_name = "ytp_tasks"

    def command(self):
        self._load_config()

        from ckanext.ytp_tasks.model import YtpTaskTables
        YtpTaskTables.create_tables()
