import requests
import json
import os
import sys
import re

# Ignoring a task requires adding its name minus "pfml-api-<environment>-" to
# the TASKS_TO_IGNORE list below
TASKS_TO_IGNORE = [
    # DOR Fineos ETL tasks.
    # The pfml-api-<environment>-dor-fineos-etl step function handles retries and failure notifications
    ".*dor-import",
    ".*dor-import-exempt",
    ".*dor-pending-filing-response-import",
    ".*load-employers-to-fineos",
    ".*fineos-eligibility-feed-export",
    ".*fineos-import-employee-updates",
    # The Leave Admin registration job will only be run ad hoc for manual LA verification
    ".*register-leave-admins-with-fineos",
    # The PFML API is a service that will rotate containers when health checks
    # are failing. We should know about issues due to deployment failures.
    "pfml-api(-[a-z0-9]+){1,2}$",
]

# --------------------------------------------------------------------------- #
#                        Format teams message                                 #
# --------------------------------------------------------------------------- #
def teams_message(teams_uri, event_detail):
    # Pulls data from the cloudwatch event rule
    task_name = event_detail["group"][event_detail["group"].rindex(":") + 1 :]
    cluster_name = event_detail["clusterArn"][
        event_detail["clusterArn"].rindex("/") + 1 :
    ]
    stopped_reason = event_detail["stoppedReason"]

    message_block = {
        "@type": "MessageCard",
        "themeColor": "FF0000",
        "title": "ECS Task Failure",
        "text":  f"ECS task **{task_name}** failed to start",
        "sections": [
            {"text": f"Reason for failure:\n >{stopped_reason}"},
            {"text": f"Cluster:\n {cluster_name}"}
            ]
    }

    return message_block
# --------------------------------------------------------------------------- #
#                          Send teams message                                 #
# --------------------------------------------------------------------------- #
def terriyay_message(event_detail):
    teams_uri = os.environ["TEAMS_URI"]
    message_json = teams_message(teams_uri, event_detail)

    try:
        response = requests.post(
            teams_uri,
            data=json.dumps(message_json),
            headers={"Content-Type": "application/json"}
        )
        return response
    except requests.exceptions.RequestException as error:
        sys.exit(error)

# --------------------------------------------------------------------------- #
#                                Lambda Handler                               #
# --------------------------------------------------------------------------- #


def lambda_handler(event, context=None):

    event_detail = event["detail"]

    # event['detail']['group'] (or event_detail['group']) looks like 'system:pfml-api-<environment>-<task name>'
    # Removes all but task name from the event_detail['group']
    task_name = event_detail["group"][event_detail["group"].rindex(":") + 1 :]

    if any(re.match(task_to_ignore, task_name) for task_to_ignore in TASKS_TO_IGNORE):
        return {"ECSTaskFailureIgnored": f"{task_name}"}

    # Send event detail to teams and capture response
    response = terriyay_message(event_detail)

    json_response = json.loads(response.text)

    status_message = (
        "Teams post successful"
        if json_response == 1
        else f"Teams error: {json_response['error']}"
    )

    return status_message
