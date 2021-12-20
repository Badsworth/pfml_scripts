import os

def environments():
    return (
        # 'breakfix',
        # 'infra-test',
        # 'cps-preview',
        # 'infra-test',
        # 'long',
        # 'performance',
        # 'stage',
        'test',
        'training',
        'trn2',
        'uat',
    )

def deploy_waf_to_prod():
    return

def header(message):
    print('-' * 80)
    print(message)
    print('-' * 80, '\n')

def terraform(command):
    return os.system(f'~/bin/terraform {command}')

def deploy_to(environment):
    if environment in os.listdir():
        os.system('clear')
        header(f'\tDeploying Terraform Configuration to {environment}...')
        os.chdir(environment)
        print(f'\tcurrently in {os.getcwd()}...')
        terraform('init')
        terraform('plan')
        input('\tPress Enter to continue...')
        approve_plan()
        os.chdir('..')

def approve_plan():
    if input('Approve Plan? (y)es or (n)o:') == 'y':
        terraform('apply --auto-approve')

def deploy_waf():
    for environment in environments():
        if environment in os.listdir():
            deploy_to(environment)


if __name__ == "__main__":
    deploy_waf()