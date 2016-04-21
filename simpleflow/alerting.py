import json
import urllib
import smtplib
from email.mime.text import MIMEText


NOT_FOUND = "not found"
MESSAGE_TEMPLATE = """
SWF Console: https://console.aws.amazon.com/swf/home?{swf_params}

## Message
{message}

## Context
{context_flatten}
"""

def _make_flatten_context(context, depth=0):
    msg = ""
    for k, v in context.keys():
        if isinstance(v, dict):
            msg += " " * depth + k
            msg += _make_flatten_context(v)
        else:
            msg += " " * depth + k, " : ", v
    return msg


def make_alert_message(executor, context, message):
    msg = ""

    # Try to make the message even with missing information when the workflow
    # execution could not be retrieved.
    if executor is None:
        region_name = NOT_FOUND
        domain_name = NOT_FOUND
        workflow_id = NOT_FOUND
        raw_run_id = NOT_FOUND
        run_id = NOT_FOUND
    else:
        region_name = executor.domain.region
        domain_name = executor.domain.name
        # TODO: add workflow_id/run_id ; not exposed for now
        # workflow_id = executor.workflow_id
        # raw_run_id = executor.run_id
        # run_id = raw_run_id[:-1] + '!='
        workflow_id = NOT_FOUND
        raw_run_id = NOT_FOUND
        run_id = NOT_FOUND

    swf_params = "region={}#execution_summary:domain={};workflowId={};runId={}".format(
        region_name, domain_name, workflow_id, run_id)

    msg = MESSAGE_TEMPLATE.format(
        message=message,
        swf_params=swf_params,
        context_flatten=_make_flatten_context(context)
    )

    details = context.get('__details__')
    msg += '## Details\n\n'
    if details:
        msg += str(details)
        msg += '\n'

    msg += 'Context (JSON):\n'
    msg += json.dumps(context, indent=4)

    return msg


def alert(workflow_execution, context, message, from_email, to_emails, smtp_server):
    body = make_alert_message(workflow_execution, context, message)

    # Open a plain text file for reading.  For this example, assume that
    # the text file contains only ASCII characters.
    # Create a text/plain message
    msg = MIMEText(body)

    msg['Subject'] = 'Error on workflow {}'.format(workflow_execution.workflow_id)
    msg['From'] = from_email
    msg['To'] = to_emails

    s = smtplib.SMTP(smtp_server)
    s.sendmail(from_email, to_emails, msg.as_string())
    s.quit()
