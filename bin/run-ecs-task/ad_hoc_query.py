#!/usr/bin/env python
# coding: utf-8
import json
import pwd
import os
import logging
from datetime import datetime, timedelta
from webbrowser import open_new as open_browser_window
import subprocess
from inspect import stack
import re
from getpass import getpass
from shutil import rmtree
from jira import JIRA
from jira.exceptions import JIRAError
from time import sleep
from sys import stdout

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s %(levelname)s %(funcName)s %(message)s"
)
logger = logging.getLogger("ad_hoc_query")

# Get FIRST.LAST name to use in FINEOS request from local system username 
firstname_lastname = lambda: ".".join(pwd.getpwuid(os.getuid()).pw_gecos.rstrip(",").upper().split())


def print_function(*args):
    """Prints the calling function and its arguments to the console"""

    # Use inspect.stack to name the calling function
    calling_function = stack()[1][3]

    print(f"{calling_function}{args}\n")


def send_command(command: list) -> dict:
    """Uses subprocess library to run shell command and capture output"""

    # Use inspect.stack to name the calling function
    calling_function = stack()[1][3]

    # Show user that progress is being made
    logger.info(
        f"sending command to AWS from {stack()[1][3]}: \n\n\"{' '.join(command)}\"\n"
    )

    # Send command using shell and capture output
    process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    # Blocks until command output is complete
    result = process.communicate()

    # Subprocess.Popen commands return tuple with (message_on_success, error_message)
    success_message, error_message = result

    if process.returncode == 0:
        message = success_message.decode("UTF-8")
        print(f"\n{calling_function} command was a success!\n")

        return {"message": message, "success": True}

    elif len(error_message) > 0:
        error_message = error_message.decode("UTF-8")
        print(error_message)

        return {"message": error_message, "success": False}

    else:
        print(f"major error: {result}")

        return {"message": None, "success": False}


def test_aws_credentials() -> dict:
    """Sends simple AWS command to test connection to AWS api"""

    command = ["aws", "sts", "get-caller-identity"]

    return send_command(command)


def get_username() -> str:
    """Returns user's Atlassian-login username"""

    return input("Enter your login username for atlassian:  ")


def get_api_token() -> str:
    """Returns user's Atlassian-login API Key or directs user to web page for creating one"""

    # Get API Key from user. Input will not be displayed.
    user_input = getpass("Enter your Jira API Token or enter '?' to create one:  ")

    # User is sent to the "API Token page" in Jira if user enters '?' above
    if user_input == "?":
        open_browser_window(
            "https://id.atlassian.com/manage-profile/security/api-tokens"
        )
        return 1

    return user_input


def jira_issue() -> str:
    """Returns the name of the Jira ticket user wishes to interact with"""

    return input("Enter the name of the originating Jira ticket (ex. 'PSD-2022')")


def jira_attachment_id(attachments: list) -> str:
    """Returns id for desired file"""

    # Dictionary to capture file ids
    config_file_ids = {}

    # Grab the attachment id for any files with 'config' in the name
    for attachment in attachments:
        if "config" in attachment.filename:
            config_file_ids[attachment.filename] = attachment.id

    # Pull only the filenames to present to the user
    filenames = list(config_file_ids.keys())
    number_of_files = len(filenames)

    # Some of these tickets contain more than one file, requiring some extra work
    # If there is more than one file, offer choice of which file to run.
    if number_of_files == 1:

        return config_file_ids[filenames[0]]

    elif number_of_files < 1:
        print("No config files found in that ticket")

        return None

    else:
        # Retrieve and return attachment id
        filename = pick_config_file(filenames)
        attachment_id = config_file_ids[filename]

        return attachment_id


def get_env(environments: dict) -> dict:
    """Returns the environment abbreviations for where this query is to be run"""

    env_names = list(environments.keys())
    env_choices = {x: env_names[x] for x in range(len(env_names))}

    env_choice = env_choices[
        int(
            input(
                f"Choose the environment in which you would like to run this query: \n{env_choices}"
            )
        )
    ]

    return environments[env_choice]


def pick_config_file(filenames) -> str:
    """Returns name of desired file to use in query"""

    # Make dictionary to display file choices to user
    numbered_names = {x: filenames[x] for x in range(len(filenames))}
    # Display file choices to user
    print(numbered_names)
    # Get user's choice of file to use
    response = int(input(f"which file? {numbered_names}"))

    return numbered_names[response]


def json_from_config_file(query_filepath: str) -> str:
    """Returns json without common json->python translation errors"""

    print_function()

    with open(query_filepath, "r") as query_file:
        query = query_file.read()

    actual_json = json.loads(
        re.sub(
            r"--(.*?)([a-z0-9]{3,4}\.)",
            r" \2",
            query.replace("\n", "").replace("\t", "").replace(",}", "}"),
        )
    )

    return actual_json


def fix_json(bad_json: str) -> str:
    """Returns json without common errors found in config.json file"""

    print_function()

    # removes large whitespaces, newlines, and trailing commas
    fixed_json = re.sub(r"\s+", " ", bad_json.replace("\n", " ").replace(",}", "}"))

    return fixed_json


def upload_file_to_s3(filepath: str, environment: dict) -> bool:
    """Uploads given file to s3://massgov-pfml-prod-agency-transfer/payments/ as config.json"""

    print_function(filepath)

    mass_env = environment["mass"]

    # Command to copy local file to S3 as config.json
    command = [
        "aws",
        "s3",
        "cp",
        f"{filepath}",
        f"s3://massgov-pfml-{mass_env}-agency-transfer/payments/config.json",
    ]

    return send_command(command)["success"]


def run_query(environment: dict) -> bool:
    """Copies file from massgov S3 to FINEOS S3 which triggers FINEOS to run query"""

    mass_env = environment["mass"]
    fineos_env = environment["fineos"]
    fineos_bucket = environment["fineos_bucket"]

    # Command to copy file from our S3 to FINEOS S3
    command = [
        "./run-task.sh",
        f"{mass_env}",
        "fineos-bucket-tool",
        firstname_lastname(),
        "fineos-bucket-tool",
        "--copy",
        f"s3://massgov-pfml-{mass_env}-agency-transfer/payments/config.json",
        "--to",
        f"s3://fin-{fineos_bucket}-data-export/{fineos_env}/dataExtracts/AdHocExtract/config/config.json",
    ]

    return send_command(command)["success"]


def list_fineos_s3_contents(environment: dict) -> dict:
    """Runs the 'ls' command on s3://fin-somprod-data-export/PRD/dataExtracts/AdHocExtract/ results are found in ECS task logs"""

    mass_env = environment["mass"]
    fineos_env = environment["fineos"]
    fineos_bucket = environment["fineos_bucket"]

    # Command that initiates the ____ ECS task to send 'ls' command to FINEOS
    command = [
        "./run-task.sh",
        f"{mass_env}",
        "fineos-bucket-tool",
        firstname_lastname(),
        "fineos-bucket-tool",
        "--list",
        f"s3://fin-{fineos_bucket}-data-export/{fineos_env}/dataExtracts/AdHocExtract/",
    ]

    return send_command(command)


def get_task_arn_identifier(ls_task_message) -> str:
    """Returns json string from resulting message from list_fineos_s3_contents"""

    # This return value relies on very specific formatting from AWS CloudWatch
    # If AWS changes the format, this will fail.
    return json.loads(
        fix_json(ls_task_message.partition("Started task:\n")[-1].partition("ECS")[0])
    )["tasks"][0]["taskArn"].split("/")[-1]


def find_target_file_path(logs: str, results_file_name: str) -> str:
    """Looks through logs of most recent fineos tool ECS task to find filename in output"""

    print_function("logs_from_ls_command", results_file_name)

    print(f"Searching logs for {results_file_name} in the ECS task logs")

    # Compile a list of candidate files. The last entry is the most recent
    files = []
    for event in json.loads(logs)["events"]:
        message = event["message"]
        if results_file_name in message:
            files.append(
                re.sub("\s+", " ", json.loads(message)["message"]).split(" ")[-1]
            )

    # Return None if no matching files are found
    if len(files) < 1:
        return None

    # Return the most recent entry matching the target file name
    return files[-1]


def get_logs(task_arn_number: str, environment: dict) -> str:
    """Returns logs from ECS task"""

    print_function(task_arn_number)

    mass_env = environment["mass"]

    # Command to pull logs from task with task_arn_number in arn
    command = [
        "aws",
        "logs",
        "get-log-events",
        "--log-group-name",
        f"service/pfml-api-{mass_env}/ecs-tasks",
        "--log-stream-name",
        f"{mass_env}/fineos-bucket-tool/{task_arn_number}",
    ]

    command_result = send_command(command)

    if command_result["success"]:

        # Python json doesn't like the format these logs arrive in so some fixes are made
        fixed_message = fix_json(command_result["message"])

        return fixed_message

    else:

        return None


def fetch_results(target_file_name, environment: dict) -> str:
    """Retry searching logs for latest query results until found"""

    # Set up formatted string representing today's date and tomorrow's
    # Since these queries are often run later in the evening, and the file's
    # timestamp is in Ireland time, they are occasionally timestamped for the
    # next day from a US timezone point of view
    date_today = datetime.now()
    today = date_today.strftime("%Y-%m-%d")
    date_tomorrow = date_today + timedelta(days=1)
    tomorrow = date_tomorrow.strftime("%Y-%m-%d")

    # It sometimes takes a while for the results of a query to appear in FINEOS's S3
    # This while-loop will search for the results file until one from today or
    # 'tomorrow' (Ireland time) is found.
    while True:
        print("\nLooking for query results\n\n")

        # Use bucket tool ECS task to call 'ls' on FINEOS S3. Results appear in task logs
        ls_result = list_fineos_s3_contents(environment)

        # Get the alphanumeric string at the end of the arn for the task above
        # This will be used to query the logs for that task
        task_arn_id = get_task_arn_identifier(ls_result["message"])

        # Query the logs for the task that ran 'ls' on FINEOS
        logs = get_logs(task_arn_id, environment)

        # Find the exact filename that will be downloaded.
        # It will contain the filename from the query, but will have a
        # down-to-the-second timestamp affixed to the name.
        target_file_prefix = find_target_file_path(logs, target_file_name)

        # Return target_file_prefix if its from today or tomorrow.
        if target_file_prefix is not None and any(
            re.search(day, target_file_prefix) for day in [today, tomorrow]
        ):

            return target_file_prefix

        print("\nResults not yet populated. Trying again in 2 minutes\n")

        for remaining in range(120, 0, -1):
            stdout.write("\r")
            stdout.write(f"{remaining} seconds remaining. ")
            stdout.flush()
            sleep(1)


def copy_target_file_from_fineos(target_file_prefix: str, environment: dict) -> dict:
    """Copies file from FINEOS S3 to massgov-pfml S3"""

    print_function(target_file_prefix)

    mass_env = environment["mass"]
    fineos_bucket = environment["fineos_bucket"]

    # Pull file name from prefix as it needs to be used seperately in the next command
    file_name = target_file_prefix.split("/")[-1]

    # Command to send to AWS
    command = [
        "./run-task.sh",
        f"{mass_env}",
        "fineos-bucket-tool",
        firstname_lastname(),
        "fineos-bucket-tool",
        "--to",
        f"s3://massgov-pfml-{mass_env}-agency-transfer/payments/{file_name}",
        "--copy",
        f"s3://fin-{fineos_bucket}-data-export/{target_file_prefix}",
    ]

    return send_command(command)


def download_target_file(
    target_file_name: str, destination: str, environment: dict
) -> bool:
    """Downloads file from massgov S3 to local system"""

    print_function(target_file_name, destination)

    # Create the directory for the query results if one doesn't already exist
    if os.path.isdir(destination) is False:
        os.mkdir(destination)

    mass_env = environment["mass"]

    # Command to copy (download) the query results file to user's local system
    command = [
        "aws",
        "s3",
        "cp",
        f"s3://massgov-pfml-{mass_env}-agency-transfer/payments/{target_file_name}",
        f"{destination}/{target_file_name}",
    ]

    command_result = send_command(command)

    success = "successful" if command_result["success"] else "not successful"

    print(f"\nDowload of {target_file_name} from the massgov-pfml S3 was {success}\n")

    return command_result["success"]


def run_query_sequence(
    query_filepath: str, query_env: dict, temp_dir: str, destination: str
) -> bool:
    """Takes one filepath and runs the query contained inside file"""

    print_function(query_filepath, temp_dir, destination)

    # Upload file with single query to massgov S3
    if not upload_file_to_s3(query_filepath, environment=query_env):
        return False

    # Copies file uploaded above from massgov S3 to FINEOS S3
    # Once the copy is complete, FINEOS automatically runs query contained in file
    if not run_query(environment=query_env):
        return False

    target_filename = json_from_config_file(query_filepath)[0]["filename"]
    target_file_prefix = fetch_results(target_filename, environment=query_env)
    result_file_name = target_file_prefix.split("/")[-1]

    # Copy file resulting from query from FINEOS S3 to massgov S3
    result = copy_target_file_from_fineos(target_file_prefix, environment=query_env)

    query_success = result["success"]

    if query_success:

        # Download resultant file from massgov S3 to local computer
        download_target_file(result_file_name, destination, environment=query_env)

        return query_success

    else:

        return False


def satisfying_overview(ad_hoc_query_procedure) -> bool:
    """Gives user an idea of what to expect from script and allows for an opt-out"""

    satisfying_overview = input(
        f"""
        This utility replicate the manual actions taken when running an ad-hoc-query.
        The manual procedure is located at

        {ad_hoc_query_procedure}

        and is worth looking over to know what this script is doing. Keep in mind
        that these queries can sometimes take a long time, so be sure to wait at
        least ten minutes per query before wondering if the program has failed.
        the subprocess.Popen module (which is run in the send_command() function)
        is blocking, so there's no way to show that progress is being made.
        This script must be run in a shell that has authenticated with aws, and
        it must be able to authenticate with the Jira API, which requires a Jira
        API Key. If you don't have a Jira API Key, go ahead and continue in the
        script, and you will be sent to the Jira page in which to create one.

        This script is going to:


        - Create a ~/Downloads/ad-hoc-query-tmp/ directory in your filesystem

        - Download a config file of your choosing from Jira to the new directory

        - Initiate the transfer of the config file from your system to the
        appropriate massgov-pfml S3 bucket

        - Initiate the trasfer of that file from that S3 bucket to the
        appropriate fineos bucket

        - Wait for a file containing the query results to populate in fineos

        - Transfer the file from fineos S3 to the massgov-pfml S3 bucket

        - Create a new directory ~/Downloads/ad-hoc-query-results

        - Download the file into the new directory created in the last step

        - Delete the ~/Downloads/ad-hoc-query-tmp directory created in the first
        step


        At that point, you can send the file to its desired location, which should
        be found in the initiating Jira ticket.

        Are you ready to continue? y/n:
        """
    )

    satisfied = True if satisfying_overview == "y" else False

    return satisfied


def main():

    environments = {
        "prod": {"mass": "prod", "fineos": "PRD", "fineos_bucket": "somprod"},
        "perf": {
            "mass": "performance",
            "fineos": "DT2",
            "fineos_bucket": "somdev",
        },  # For testing this script
    }

    query_env = get_env(environments)

    ad_hoc_query_procedure = "https://lwd.atlassian.net/wiki/spaces/API/pages/1345945701/2021+Ad-Hoc+SQL+runs"

    # Give the user an idea of what to expect from this script
    satisfied = satisfying_overview(ad_hoc_query_procedure)

    # Give user the option to opt out
    if satisfied:
        pass
    else:

        return 0

    # Test connection to aws
    if test_aws_credentials()["success"] is False:

        return None

    # Build path for incoming config file
    home_directory = os.path.expanduser("~")
    default_filename = "config.json"
    default_directory = f"{home_directory}/Downloads"

    # Add subfolder for files containing query results (should make them easier to find)
    destination_directory = f"{default_directory}/ad-hoc-query-results"
    if os.path.isdir(destination_directory) is False:
        os.mkdir(destination_directory)

    # Make a temporary directory that user has access to (so not '/tmp')
    # The queries will be sentfrom a temporary directory. This directory is
    # removed upon script completion.
    temp_dir = f"{default_directory}/ad-hoc-query-tmp"
    query_filepath = f"{temp_dir}/{default_filename}"

    if os.path.isdir(temp_dir) is False:
        os.mkdir(temp_dir)

    # URL user authenticates with (company's Atlassian site)
    url = "https://lwd.atlassian.net"

    # Authenticate user for Jira API
    try:
        jira = JIRA(server=url, basic_auth=(get_username(), get_api_token()))
    except JIRAError as error:
        print(
            f"""
            Be sure your API Key is entered correctly, and that you're not
            using your login password.
            JIRAError: {error.text}
            """
        )

        return 1

    # Pull Jira ticket from which to download config.json file(s)
    try:
        ticket = jira.issue(jira_issue())
    except JIRAError as error:
        print(
            f"""
            {error.text}
            This is likely due to an incorrect ticket name.
            """
        )

        return error

    # Get names of files attached to the above Jira ticket
    attachments = ticket.fields.attachment

    # The Jira API uses the attachment's file's 'id' to download
    attachment_id = jira_attachment_id(attachments)

    # Uses file id from above to download file
    file = jira.attachment(attachment_id).get()

    if type(file) == bytes:
        file = file.decode("utf-8")

    # Write file contents to 'config.json' in the default directory
    with open(query_filepath, "w") as outfile:
        outfile.write(file)

    print(
        """

        ------------------------------------------------------------------------
                  This query should take about ten mintues to complete
        ------------------------------------------------------------------------

        """
    )

    # Loop through queries found in query file
    query_success = run_query_sequence(
        query_filepath=query_filepath,
        query_env=query_env,
        temp_dir=temp_dir,
        destination=destination_directory,
    )

    if not query_success:
        print("The query was unsuccessful")
        return 1

    # Clean up temporary directory
    rmtree(temp_dir)
    print(f"Look in `{destination_directory}` for query results")


if __name__ == "__main__":
    main()
