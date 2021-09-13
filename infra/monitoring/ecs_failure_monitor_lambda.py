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
    ".*load-employers-to-fineos",
    ".*fineos-eligibility-feed-export",
    ".*fineos-import-employee-updates",
    # The Leave Admin registration job runs every 15 minutes, so we avoid spamming
    # and will use PagerDuty for notifications as defined in INFRA-ABC.
    ".*register-leave-admins-with-fineos",
    # The PFML API is a service that will rotate containers when health checks
    # are failing. We should know about issues due to deployment failures.
    "pfml-api(-[a-z]+){1,2}$",
]

# --------------------------------------------------------------------------- #
#                       Format slackbot message                               #
# --------------------------------------------------------------------------- #


def slackbot_message(channel_id, event_detail):

    task_name = event_detail["group"][event_detail["group"].rindex(":") + 1 :]
    cluster_name = event_detail["clusterArn"][
        event_detail["clusterArn"].rindex("/") + 1 :
    ]
    stopped_reason = event_detail["stoppedReason"]

    message_block = {
        "channel": channel_id,
        "text": "ECS Task Failure",
        "blocks": [
            {"type": "divider"},
            {
                "type": "section",
                "fields": [
                    {
                        "type": "mrkdwn",
                        "text": f'*ECS task* `"{task_name}"` *failed to start*',
                    }
                ],
            },
            {
                "type": "section",
                "fields": [
                    {
                        "type": "mrkdwn",
                        "text": f"*Reason for failure:*\n>{stopped_reason}",
                    }
                ],
            },
            {
                "type": "section",
                "text": {"type": "mrkdwn", "text": f"*Cluster:*\n{cluster_name}"},
            },
            {"type": "divider"},
        ],
    }

    return message_block


# --------------------------------------------------------------------------- #
#                          Send slackbot message                              #
# --------------------------------------------------------------------------- #
def terriyay_message(event_detail):

    slack_api_address = "https://slack.com/api/chat.postMessage"
    slack_channel_id = os.environ["SLACK_CHANNEL_ID"]
    slack_api_key = os.environ["SLACK_API_KEY"]

    message_json = slackbot_message(slack_channel_id, event_detail)

    try:
        response = requests.post(
            slack_api_address,
            data=json.dumps(message_json),
            headers={
                "Content-Type": "application/json",
                "Authorization": "Bearer {}".format(slack_api_key),
            },
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

    # Send event detail to slackbot, capture response from slackbot API
    response = terriyay_message(event_detail)

    json_response = json.loads(response.text)

    status_message = (
        "Slack call successful"
        if json_response["ok"]
        else f"Error from slackbot: {json_response['error']}"
    )

    return {"slackCallStatus": status_message}
