#!/usr/bin/python3

"""
1. Script gets the projects in json from Bitbucket
2. For each project in json checks if tool_user is a member of the certain role
2.1 If not - add tool_user to the certain role to each project from json
2.2 If yes - just text the relevant message to the log
"""

import requests
import os
import logging
import configparser

# Get script_name and config file
script_name = os.path.basename(__file__)    # get script_name
basedir = os.path.dirname(os.path.abspath(__file__))    # get absolute directory path to the script
config_file = basedir + '/server.conf'   # set absolute path to the script
log_file = ('{}/{}.log'.format(basedir, script_name))   # set absolute path to the log

# Get properties from config file
def getConfig(section):
    config = configparser.ConfigParser()
    config.read(config_file)
    props = {}
    if section:
        for key, val in config.items(section):
            props[key] = val
    return props

# Get configs
credetials_conf = getConfig('CREDENTIALS')
jira_conf = getConfig('JIRA')
bitbucket_conf = getConfig('BITBUCKET')

# set variables
user = credetials_conf['user']
password = credetials_conf['password']
jira_url = jira_conf['jira_url']
tool_user = jira_conf['tool_user']
role_name = jira_conf['role_name']
bitbucket_url = bitbucket_conf['bitbucket_url']
bitbucket_projects_json_url = bitbucket_conf['bitbucket_projects_json_url']

# logging settings
logging.basicConfig(filename=log_file, level=logging.DEBUG, format='%(asctime)s %(levelname)s:  %(message)s')

# set header and payload for requests
header = {'Content-type': 'application/json'}
payload = '{"user": ["risk_reporting"]}'

try:
    logging.info('The information about all JIRA\'s roles is getting from "{}"...'.format(jira_url))
    rj = requests.get(jira_url + '/rest/api/2/role', auth=(user, password)).json()   # get all roles info
except Exception as e:
    logging.error('Error while getting the information about all JIRA\'s roles from "{}": {}'.format(jira_url, e))
    exit(1)
role_id = [i['id'] for i in rj if i['name'] == role_name]    # get role id of certain role
try:
    logging.info('The list of all projects is getting from "{}"...'.format(bitbucket_projects_json_url))
    rb = requests.get(bitbucket_projects_json_url, auth=(user, password)).json()    # get projects from bitbucket in json
except Exception as e:
    logging.error('Error while getting the list of all projects from "{}": {}'.format(bitbucket_projects_json_url, e))
    exit(1)
projects = [j for i in rb for j in rb[i]]   # create projects' list from json
# for each project check if tool_user is a member of the certain role and add it if not
for i in projects:
    # get users from the each project from the json list in the bitbucket
    try:
        logging.info('The users from the "{}({})" role are being retrieved from "{}" project...'.format(role_name, role_id[0], i))
        rj = requests.get(jira_url + '/rest/api/2/project/' + i + '/role/' + str(role_id[0]), auth=(user, password)).json()
    except Exception as e:
        logging.error('Error while retrieving users from the "{}({})" role from "{}" project: {}'.format(role_name, role_id[0], i, e))
        exit(1)
    # put users from the each project from the json list in the bitbucket to the "role_users_per_project" list
    role_users_per_project = [j['name'] for j in rj['actors'] if j['type'] == 'atlassian-user-role-actor']
    # put the "tool_user" to the role in each project if it is not already exists
    if tool_user not in role_users_per_project:
        try:
            pj = requests.post(rj['self'], data=payload, headers=header, auth=(user, password))
            logging.info('Tool_user "{}" has been just ADDED to the "{}" project role in the "{}" project'.format(tool_user, role_name, i))
        except Exception as e:
            logging.error('Error while adding tool_user to the certain project role in Jira projects: {}'.format(e))
            exit(1)
    else:
        logging.info('Tool_user "{}" is already the member of the "{}" project role in the "{}" project'.format(tool_user, role_name, i))
