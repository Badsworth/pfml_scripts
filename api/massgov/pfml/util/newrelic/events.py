import gzip
import json
import os
import sys
from datetime import datetime
from types import TracebackType
from typing import Dict, Optional, Tuple, Union

import newrelic.agent
import requests

import massgov.pfml.util.logging

logger = massgov.pfml.util.logging.get_logger(__name__)


def log_newrelic_event(import_log: dict) -> None:
    try:
        formatted_report = generate_etl_report(import_log)
        send_custom_nr_event(json.dumps(formatted_report))
    except Exception as e:
        logger.exception(f"Error parsing or sending EtlReport event -- {type(e)} - {e}")


def send_custom_nr_event(event_json: str) -> None:
    api_key = os.environ.get("NR_INSERT_API_KEY")
    if not api_key:
        logger.info("New Relic Insert API Key is not configured. Skipping event.")
        return

    try:
        logger.info("Uploading event data to New Relic")
        nr_event_response = requests.post(
            "https://insights-collector.newrelic.com/v1/accounts/2837112/events",
            data=gzip.compress(event_json.encode("utf-8")),
            headers={
                "Content-Type": "application/json",
                "Content-Encoding": "gzip",
                "X-Insert-Key": api_key,
            },
        )
    except Exception as e:
        logger.exception(
            f"Unexpected error when sending event data to New Relic -- {type(e)} - {e}"
        )
        return

    if nr_event_response.status_code != 200:
        logger.exception(
            f"Event not sent to New Relic; got {nr_event_response.status_code} response from collector. For more information, visit New Relic and run NRQL against the 'NrIntegrationError' bucket."
        )
    else:
        logger.info("Finished uploading event data to New Relic")


def generate_etl_report(report):
    """
    Generates an ETL report object from a combination of a dict-casted ImportLog object and ECS task metadata.
    The Events API accepts only int/float/str as data types. The presence of any other data rejects the entire event.
    :return: dict: The generated report, suitably enriched.
    """

    task_duration = None
    # Some tasks report start/end in their report object; others only have it as a first class attr of ImportLog.
    # Account for both, or just use None if neither format is present.
    if {"end", "start"} <= report.keys():
        task_duration = (
            datetime.fromisoformat(report["end"]) - datetime.fromisoformat(report["start"])
        ).total_seconds() * 1000
    elif {"job.start", "job.end"} <= report.keys():
        task_duration = (
            datetime.fromisoformat(report["job.end"]) - datetime.fromisoformat(report["job.start"])
        ).total_seconds() * 1000

    formatted_report = {
        k: (v if type(v) in (int, float, str) else str(v)) for k, v in report.items()
    }

    formatted_report.update(
        {
            "eventType": "EtlReport",
            "environment": os.environ.get("ENVIRONMENT", "local"),
            "task.durationMillis": task_duration,
        }
    )

    ecs_metadata = get_task_metadata()
    if ecs_metadata:
        ecs_task_name = ecs_metadata["Name"]
        sfn_id = ":".join(
            os.environ.get("SFN_EXECUTION_ID", "Nobody:Nonesuch:NoStepFunction").split(":")[-2:]
        )  # just the state machine name and its execution ID; don't include any region or account data
        ecs_task_id = ecs_metadata["Labels"]["com.amazonaws.ecs.task-arn"].split("/")[-1]
        ecs_taskdef = ":".join(
            [
                ecs_metadata["Labels"]["com.amazonaws.ecs.task-definition-family"],
                ecs_metadata["Labels"]["com.amazonaws.ecs.task-definition-version"],
            ]
        )
        cloudwatch_log_group = ecs_metadata["LogOptions"]["awslogs-group"]
        cloudwatch_log_stream = ecs_metadata["LogOptions"]["awslogs-stream"]

        formatted_report.update(
            {
                "aws.ecs.task_name": ecs_task_name,
                "aws.ecs.task_id": ecs_task_id,
                "aws.ecs.task_definition": ecs_taskdef,
                "aws.cloudwatch.log_group": cloudwatch_log_group,
                "aws.cloudwatch.log_stream": cloudwatch_log_stream,
                "aws.step_function.id": sfn_id,
            }
        )

    logger.info("Done formatting ETL report")
    return formatted_report


def get_task_metadata(url_suffix: str = "") -> dict:
    """
    Retrieves ECS metadata from an AWS-provided metadata URI. This URI is injected to all ECS tasks by AWS as an envar.
    See https://docs.aws.amazon.com/AmazonECS/latest/userguide/task-metadata-endpoint-v4-fargate.html for more.
    :param url_suffix: Acceptable URL suffixes are '/task', '/stats', or '/task/stats'.
    :return: The ECS metadata (if run on ECS) or empty dict (if run locally, or in an environment w/o metadata URI).
    """
    ecs_metadata_uri = os.environ.get("ECS_CONTAINER_METADATA_URI_V4")

    if os.environ.get("ENVIRONMENT", "local") != "local" and ecs_metadata_uri is not None:
        task_metadata = requests.get(f"{ecs_metadata_uri}{url_suffix}")
        logger.info("Retrieved task metadata from ECS")
        return task_metadata.json()
    else:
        logger.warning(
            "ECS metadata not available for local environments. Run this task on ECS to see metadata."
        )
        return {}


def log_and_capture_exception(msg: str, extra: Optional[Dict] = None) -> None:
    """
    Sometimes we want to record custom messages that do not match an exception message. For example, when a ValidationError contains
    multiple issues, we want to log and record each one individually in New Relic. Injecting a new exception with a
    human-readable error message is the only way for errors to receive custom messages.
    This does not affect the traceback or any other visible attribute in New Relic. Everything else, including
    the original exception class name, is retained and displayed.
    """

    info = sys.exc_info()
    info_with_readable_msg: Union[
        BaseException, Tuple[type, BaseException, Optional[TracebackType]]
    ]

    if info[0] is None:
        exc = Exception(msg)
        info_with_readable_msg = (type(exc), exc, exc.__traceback__)
    else:
        info_with_readable_msg = (info[0], Exception(msg), info[2])

    logger.error(msg, extra=extra, exc_info=info_with_readable_msg)

    newrelic.agent.record_exception(
        exc=info_with_readable_msg[0],
        value=info_with_readable_msg[1],
        tb=info_with_readable_msg[2],
        params=extra,
    )
