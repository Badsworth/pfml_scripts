#!/usr/bin/env python3

# For now, this file will only initiate a scan of all images in the ECR. In the future it can also
# retrieve scan results and send alerts depending on results. For the time being
# the results will need to be manually checked in AWS console.

import boto3
from botocore.exceptions import ClientError

ecr_client = boto3.client("ecr")


def get_repository_names():
    """Retrieve names of all repositories in ECR"""

    # Retreive names of all repositories
    aws_response = ecr_client.describe_repositories()

    # Make list of repository names only
    repository_names = [x["repositoryName"] for x in aws_response["repositories"]]

    return repository_names


def list_all_images(repository_names):
    """returns data structure {repository name: {full AWS response to 'list-images' command}}"""

    repository_images = {
        name: ecr_client.list_images(repositoryName=name) for name in repository_names
    }

    return repository_images


def get_image_digests(repository_images):
    """
    returns data structure {repository name : [list of image-digests of the images in the repo]}
    """

    # requires data structure from list_all_images function
    repository_names = repository_images.keys()
    repository_image_digests = {
        name: [x["imageDigest"] for x in repository_images[name]["imageIds"]]
        for name in repository_names
    }

    return repository_image_digests


def scan_all_images(repository_image_digests):
    """starts image scan in all images in all repositories. No return value"""

    # Shorten this parameter
    images = repository_image_digests

    # requires {repository name : [repository_image_digests]} data structure
    for repository_name in images.keys():
        for image_digest in images[repository_name]:
            try:
                ecr_client.start_image_scan(
                    repositoryName=repository_name, imageId={"imageDigest": image_digest}
                )
            except ClientError as error:
                if error.response["Error"]["Code"] == "LimitExceededException":
                    print(f"LimitExceededException on {image_digest} in {repository_name}")
                else:
                    print(error)


def image_scan_result(repository_name, image_digest):
    """Retrieves results of one image scan for one image"""

    aws_response = ecr_client.describe_image_scan_findings(
        repositoryName=repository_name, imageId={"imageDigest": image_digest}
    )

    return aws_response


def get_all_scan_results(repository_images):
    """
    Returns data structure {repository-name: [list of AWS responses for each image in repository]}
    """

    scan_results = {
        repository_name: [
            image_scan_result(repository_name, image_digest)
            for image_digest in repository_images[repository_name]
        ]
        for repository_name in repository_images.keys()
    }

    return scan_results


def format_image_list():
    """Gathers all information for get_image_digests function and calls it"""

    repositories = get_repository_names()
    repository_images = list_all_images(repositories)
    repository_digests = get_image_digests(repository_images)

    return repository_digests


def start_scan():
    """Starts scan of all images in all ECR repositories. Error printed to stdout"""

    repository_digests = format_image_list()
    scan_all_images(repository_digests)


if __name__ == "__main__":
    start_scan()
