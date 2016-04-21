from __future__ import absolute_import

import boto
import unittest
from mock import patch
from moto import mock_swf

from swf.models import Domain
from swf.models.history.builder import History
from simpleflow import futures
from simpleflow.swf.executor import Executor
from simpleflow.workflow import Workflow
from simpleflow.swf.helpers import get_workflow_execution

from .data import raise_on_failure
from .data.moto_utils import setup_workflow, SCHEDULE_ACTIVITY_TASK_DECISION


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
    }

    def run(self, context):
        self.context = context
        res = self.submit(raise_on_failure)
        futures.wait(res)


class TestAlerting(unittest.TestCase):
    def prepare(self):
        conn = setup_workflow()

        # add a failing task
        decision_token = conn.poll_for_decision_task("test-domain", "queue")["taskToken"]
        decision = SCHEDULE_ACTIVITY_TASK_DECISION
        decision["scheduleActivityTaskDecisionAttributes"]["activityId"] = \
            "activity-tests.data.activities.raise_on_failure-1"
        conn.respond_decision_task_completed(decision_token, decisions=[decision])
        activity_token = conn.poll_for_activity_task("test-domain", "activity-task-list")["taskToken"]

        resp = conn.respond_activity_task_failed(activity_token, reason="reason", details="long details")
        self.assertIsNone(resp) # empty response = good

        self.run_id = conn.run_id

    @mock_swf
    def test_alert_on_failure_is_called(self):
        self.prepare()

        executor = Executor(Domain("test-domain"), AlertingWorkflow)
        workflow_execution = get_workflow_execution("test-domain", "uid-abcd1234", self.run_id)

        with patch('simpleflow.alerting.alert') as alerting_mock:
            executor.replay(workflow_execution.history())

        # http://engineeringblog.yelp.com/2015/02/assert_called_once-threat-or-menace.html
        # TODO: replace those little liars with something better
        self.assertEqual(alerting_mock.call_count, 1)
        alerting_mock.assert_called_once_with(
            executor, 'Workflow execution error in task activity-tests.data.activities.raise_on_failure: "reason"',
            "hello@github.com", ["david@bowie.com"], "localhost")

    @mock_swf
    def test_alerting_is_not_triggered_when_missing_params(self):
        pass
