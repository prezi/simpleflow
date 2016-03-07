import mock

from .data import raise_error
from simpleflow.workflow import Workflow


class AlertingWorkflow(Workflow):
    name = 'test_workflow'
    version = 'test_version'
    task_list = 'test_task_list'
    decision_tasks_timeout = '300'
    execution_timeout = '3600'
    tag_list = None      # FIXME should be optional
    child_policy = None  # FIXME should be optional
    alerting = {
        "from": "hello@github.com",
        "to": ["david@bowie.com"],
        "context_key": "context"
    }

    def run(self, context):
        self.context = context
        self.submit(raise_error)


def test_alerting():
    #with mock.patch(
    #        'swf.models.ActivityType.save',
    #        raise_already_exists(increment)):
    #    decisions, _ = executor.replay(history)
    workflow = AlertingWorkflow()
    workflow.run()
