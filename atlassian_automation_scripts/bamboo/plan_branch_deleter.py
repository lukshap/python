"""
Removes specified branches from specified Plan in Bamboo
"""

import sys, argparse, requests, getpass, re
# import requests.packages.urllib3
# requests.packages.urllib3.disable_warnings()

args = None
common_headers = {
    'Accept' : 'application/json',
    'X-Atlassian-Token' : 'no-check'
}

def CheckBranchEnabled(branch):
    return args.all or not branch['enabled']

def CheckMatchRegex(branch):
    return not args.matches_regex or re.match(args.matches_regex, branch['shortName'])

def ProcessPlanBranch(branch):
    if CheckBranchEnabled(branch) and CheckMatchRegex(branch):
        if args.dry_run:
            print('> Would Delete. Enabled: %s . Name: %s' %(branch['enabled'], format(branch['shortName'])))
        else:
            print('> Deleting {}'.format(branch['shortName']))

            r = requests.post(
                '{}/chain/admin/deleteChain!doDelete.action'.format(args.bamboo_base_url),
                params={'os_authType' : 'basic'},
                headers=common_headers,
                data={'buildKey' : branch['key']},
                auth=(args.username, args.password))

            r.raise_for_status()

def ProcessPlan():
    url_params = {
        'os_authType' : 'basic',
        'expand' : 'branches',
        'max-results' : args.max_results
    }

    r = requests.get(
        '{}/rest/api/latest/plan/{}'.format(args.bamboo_base_url, args.plan_key),
        params=url_params,
        headers=common_headers,
        auth=(args.username, args.password))

    r.raise_for_status()

    plan_json = r.json()

    for branch in plan_json['branches']['branch']:
        ProcessPlanBranch(branch)

def main():
    parser = argparse.ArgumentParser(description="Delete plan branches in Bamboo")
    parser.add_argument('bamboo_base_url', help='The base URL of your bamboo instance (e.g. http://bamboo.company.com). Do not specify a trailing slash at the end.')
    parser.add_argument('plan_key', help='The plan key (e.g. ABC-XYZ)')
    parser.add_argument('--username', help='The username of a plan administrator')
    parser.add_argument('--password', help='The password of the provided plan administrator username. If not specified, you will be prompted for a password after executing the script.')
    parser.add_argument('--all', action='store_true', help='Delete all plan branches, including enabled ones. By default only disabled branches are deleted.')
    parser.add_argument('--dry-run', action='store_true', help='Don\'t actually delete anything, instead show what would be deleted. Useful to test your command to see if it is removing only what you expect.')
    parser.add_argument('--max-results', type=int, default=500, help='The maximum number of plan branch results. Defaults to 500')
    parser.add_argument('--matches-regex', help='Only delete plan branches that match the specified regex')

    global args
    args = parser.parse_args()

    if not args.password:
        args.password = getpass.getpass()

    ProcessPlan()

main()
