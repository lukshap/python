#!/usr/bin/python3

import requests
import argparse
import getpass
import textwrap
conf_url = 'https://conf.booxdev.com'
jira_url = 'https://jira.booxdev.com'

parser = argparse.ArgumentParser(formatter_class = argparse.RawDescriptionHelpFormatter,
                                            description = textwrap.dedent('''\
                                            The tool creates a page in the "https://conf.booxdev.com" contained "Agile Sprint Burndown Gadget", "Agile Sprint Health Gadget" gadgets which pulls data from a certain JIRA board
                                            as well as "Time distribution" chart and link to the JIRA boards Velocity Chart. 
                                             -------------------------------------------------------------------------------------------------------------------------------
                                             Example: 
                                             to create page "CTP-Masters Sprint 76" in the space "BXEN" underneath the page "Team Masters - Sprints" please use the command:
                                             python3 createpage.py "CTP-Masters Scrum Board" "BXEN" "CTP-Masters Sprint 76" "Team Masters - Sprints"  <your_Confluence_username>
                                             '''))
parser.add_argument('board_name', help='The Jira board name(e.g. "CTP-Masters Scrum Board")')
parser.add_argument('space_key', help='The Confluence space name where a page will be created (e.g. "BXEN")')
parser.add_argument('page_name', help='The name of the newly created page in Confluence (e.g. "CTP-Masters Sprint 76")')
parser.add_argument('parent_page_name', help='The name of the parent page for the newly created page in Confluence (e.g. "Team Masters - Sprints")')
parser.add_argument('username', help='The username of a JIRA and Confluence user')
parser.add_argument('--password', help='The password of the provided username. If not specified, you will be prompted for a password.')
parser.add_argument('--attachment_space', help='The name of the space where the attachment for "Time distribution" paragraph is stored (e.g. "BXEN").')
parser.add_argument('--attachment_page', help='The name of the page where the attachment for "Time distribution" paragraph is stored (e.g. "CTP Current logged hours statistics").')
parser.add_argument('--attachment_name', help='The name of the attachment for "Time distribution" paragraph (e.g. "CTP-Masters Sprint 75.png").')
parser.add_argument('--dry_run', action='store_true', help='Don\'t actually do anything, instead show what would be done.')

global args
args = parser.parse_args()
if not args.password:
    args.password = getpass.getpass()

user = args.username
password = args.password
board_name = args.board_name
space_key = args.space_key
page_name = args.page_name
parent_page_name = args.parent_page_name
attachment_name = args.attachment_name
dry_run = args.dry_run
attachment_space = args.attachment_space
attachment_page = args.attachment_page
attachment_name = args.attachment_name

# set header and payload for requests
headers = {'Content-Type': 'application/json'}

if not dry_run:
    # getting Confluence parent_page_id
    try:
        r = requests.get(conf_url + '/rest/api/content?spaceKey=' + space_key + '&title=' + parent_page_name + '', headers=headers, auth=(user, password)).json()
        parent_page_id = r['results'][0]['id']
    except Exception as e:
        print('The error "{}" happens while trying to get Confluence parent page id "{}"'.format(e, parent_page_name))
        exit(1)

    # getting all boards from jira and then define the id of the certain board
    try:
        r = requests.get(jira_url + '/rest/greenhopper/1.0/rapidview', headers=headers, auth=(user, password)).json()
        a = [i['id'] for i in r['views'] if i['name'] == board_name]
        board_id = str(a[0])
    except Exception as e:
        print('The error "{}" happens while trying to get board_id of the board "{}"'.format(e, board_name))
        exit(1)

    ## creating the page underneath the certain parent page
    # define a velocity link value
    velocity = jira_url + '/secure/RapidBoard.jspa?rapidView=' + board_id + '&view=reporting&chart=velocityChart'
    # define a Burndown gadget value
    burndown = "{gadget:width=450|border=true|url=https://jira.booxdev.com/rest/gadgets/1.0/g/com.pyxis.greenhopper.jira:greenhopper-gadget-sprint-burndown/gadgets/greenhopper-sprint-burndown.xml}" \
               " rapidViewId=" + board_id + "&showRapidViewName=false&sprintId=auto&showSprintName=false&isConfigured=true&refresh=false&=false {gadget}"
    # define a Scope gadget value
    scope = "{gadget:width=450|border=true|url=https://jira.booxdev.com/rest/gadgets/1.0/g/com.pyxis.greenhopper.jira:greenhopper-gadget-sprint-health/gadgets/greenhopper-sprint-health.xml}" \
            " rapidViewId=" + board_id + "&showRapidViewName=true&sprintId=auto&showSprintName=true&showAssignees=false&isConfigured=true&refresh=false&=false {gadget}"
    # define a time_distribution attachment value
    if attachment_space and attachment_page and attachment_name:
        time_distr = "!" + attachment_space + ":" + attachment_page + "^" + attachment_name + "|align=left,border=2,width=450!"
        value = 'h2. Velocity' + '\\n' + velocity + '\\n' + 'h2. Burndown' + '\\n' + burndown + '\\n' + 'h2. Scope' + '\\n' + scope + '\\n' + 'h2. Time distribution' + '\\n' + time_distr
    else:
        value = 'h2. Velocity' + '\\n' + velocity + '\\n' + 'h2. Burndown' + '\\n' + burndown + '\\n' + 'h2. Scope' + '\\n' + scope
    payload = '{"type": "page","title": "' + page_name + '","ancestors": [{"id": "' + parent_page_id + '"}], "space":{"key":"' + space_key + '"},"body": {"storage": {"value": "' + value + '", "representation": "wiki"}}}'
    # create a page in Confluence
    try:
        p = requests.post(conf_url + '/rest/api/content', headers=headers, data=payload, auth=(user, password)).json()
        print('The page "{}" has been just successfully created in the Confluence space "{}". Please follow the link - "{}"'.format(page_name, space_key,p['_links']['base'] + p['_links']['webui']))
    except Exception as e:
        print('The error "{}" happens while trying to create Confluence page "{}"'.format(e, page_name))
        exit(1)
else:
    print('The page "{}" will be created as a child of the page "{}" in the space "{}"'.format(page_name, parent_page_name, space_key))
