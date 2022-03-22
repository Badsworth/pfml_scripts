# Iterates thru all the lambdas accessible to your current AWS credentials,
# and deletes all but the $LATEST version of each lambda this script discovers.
# Ignores Lambda@Edge functions. # TODO: adapt this script to work on Lambda@Edge functions.
# This script requires "Infrastructure-Admin" AWS permissions or better to run.
# Adapted from https://gist.github.com/tobywf/6eb494f4b46cef367540074512161334.

# from __future__ import absolute_import, print_function, unicode_literals
import boto3

def clean_old_lambda_versions():
    lambda_client = boto3.client('lambda')
    functions_paginator = lambda_client.get_paginator('list_functions')
    version_paginator = lambda_client.get_paginator('list_versions_by_function')

    for function_page in functions_paginator.paginate():
        for function in function_page['Functions']:
            print(function['FunctionName'])
            for version_page in version_paginator.paginate(FunctionName=function['FunctionArn']):
                for version in version_page['Versions']:
                    arn = version['FunctionArn']
                    if version['Version'] != function['Version']:
                        if 'cloudfront_handler' in arn:
                            print('Cannot delete an edge lambda like this')
                        else:
                            print('  🥊 {}'.format(arn))
                            # lambda_client.delete_function(FunctionName=arn) # uncomment me once you've checked
                    else:
                        print('  💚 {}'.format(arn))


if __name__ == '__main__':
    clean_old_lambda_versions()
