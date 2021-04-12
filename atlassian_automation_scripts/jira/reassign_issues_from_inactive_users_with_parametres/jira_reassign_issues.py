#!/bin/env python
# -*- coding: utf-8 -*-

__author__ = 'p_luksha'

"""
HD-87417
0. The script gets parametres from command line (see --help)
1. The script gets a list of issues from JQL, based on input parametres.
2. Chooses only those where assignee is inactive or missed.
3. Creates a dict to match project's "component - component lead" for each project among the issues chosen in step 1, by the way if component lead is inactive or missed it is replaced by project lead.
4. In the each chosen in step 1 issue assignee field is changed to correspondent component lead (or project lead) from a dict created on the step 3, but if component field is empty in the certain issue -
the message is being generated and being sent to p_luksha.
"""

from jira.client import JIRA
from datetime import datetime, timedelta, date
from email.mime.text import MIMEText
import logging
import fcntl
import os
import ConfigParser
import smtplib
import re
import base64
import httplib
import requests
import sys
import csv
import time
import argparse
import getpass

## To eliminate a A true SSLContext object warnings
import requests.packages.urllib3
requests.packages.urllib3.disable_warnings()

def get_properties(section):
    config = ConfigParser.SafeConfigParser()
    config.read(config_file)
    props = {}
    if section:
        for key, val in config.items(section):
            props[key] = val
    return props


# Settings
config_file = 'config.ini'
global_conf = get_properties('GLOBAL')
smtp_conf = get_properties('SMTP')

log_path = global_conf['log_path']
#jira_user = global_conf['jira_user']
#jira_password = global_conf['jira_password']
smtp_host = smtp_conf['smtp_host']
from_email = smtp_conf['from_email']
to_email_1 = smtp_conf['to_email_1']
to_email_2 = smtp_conf['to_email_2']
#subject = smtp_conf['subject']
#email_msg_no_components = smtp_conf['email_msg_no_components']
#email_msg_no_reassign = smtp_conf['email_msg_no_reassign']

def send_email(email_msg,to_email):
    mail_object = None
    try:
        mail_object = smtplib.SMTP(smtp_host)
        mail_object.ehlo_or_helo_if_needed()
    except Exception, e:
        logger.critical('Unable to connect to SMTP server. Detail info: %s' % e)
        exit(1)
    message = MIMEText(email_msg, _charset="UTF-8")
    message['Subject'] = subject
    message['From'] = from_email
    message['To'] = to_email
    try:
        mail_object.sendmail(from_email,to_email,message.as_string())
        logger.info('Successful sending mail to %s' % (to_email))
    except Exception, e:
        logger.critical('Error sending mail to %s: %s' % (to_email,e))

# Logging settings
logger = logging.getLogger()
logger.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
handler = logging.FileHandler(log_path)
handler.setLevel(logging.DEBUG)
handler.setFormatter(formatter)
logger.addHandler(handler)
httplib.HTTPConnection.debuglevel = 0

maxResults = 100
startPos = 0
issue_array = []
next_result = True
debug = False

projects_dict = {0:0}
count=0
reassigned_issues_lst = [['issue','summary','description','assignee','reporter','components','labels']]
no_components = []
no_reassign = []

#   Main
if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Reassign inactive or missed assignee from all issues in specified projects and statuses")
    parser.add_argument('jira_base_url', help='The base URL of jira instance (e.g. http://jira.company.com). Do not specify a trailing slash at the end.')
    parser.add_argument('--username', help='The username of a project administrator or JIRA administrator')
    parser.add_argument('--password', help='The password of the provided administrator username. If not specified, you will be prompted for a password after executing the script.')
    parser.add_argument('--projects_keys', help='The comma separated projects keys (e.g. ZZZZ,AAA,223DD)')
    parser.add_argument('--issues_in_statuses', help='The comma separated desired statuses (e.g. Open,In Progress,Reopened)')
    parser.add_argument('--issues_not_in_statuses', help='The comma separated excluded statuses (e.g. Closed,Resolved)')
    parser.add_argument('--dry_run', action='store_true', help='Don\'t actually do anything, instead show what would be done. Useful to test your command to see if it is removing only what you expect.')

    global args
    args = parser.parse_args()

    if not args.password:
        args.password = getpass.getpass()

    fp = open(global_conf['lock_path'], 'w')
    try:
        fcntl.lockf(fp, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except IOError, e:
        logger.critical('error getting lock, another instance running? Reason: %s', e)
        exit(1)
    jira = None
    try:
        #jira = JIRA({'server': global_conf['jira_url']}, basic_auth=(jira_user,jira_password))
        jira = JIRA({'server': args.jira_base_url}, basic_auth=(args.username, args.password))
    except Exception, e:
        logger.critical('JIRA instance unavailable, detail: %s' % e)
        exit(1)
    # Строим список issue потенциально требующих обработки
    while next_result:
        issue_set = []
        try:
            if args.issues_in_statuses:
                issue_set = jira.search_issues(
                    'project in (' + args.projects_keys + ') AND status in (' + args.issues_in_statuses + ')',
                    fields=global_conf['fields'],
                    startAt=startPos,
                    maxResults=maxResults,
                    # expand=global_conf['expand'],
                )
            elif args.issues_not_in_statuses:
                issue_set = jira.search_issues(
                    'project in (' + args.projects_keys + ') AND status not in (' + args.issues_not_in_statuses + ')',
                    fields=global_conf['fields'],
                    startAt=startPos,
                    maxResults=maxResults,
                    # expand=global_conf['expand'],
                )
            ## use jql from config.ini for debug
            else:
                issue_set = jira.search_issues(
                    global_conf['jql'],
                    fields=global_conf['fields'],
                    startAt=startPos,
                    maxResults=maxResults,
                    #expand=global_conf['expand'],
                )
        except Exception, e:
            logger.critical('Jira request failed, detail: %s' % e)
            exit(1)
        issue_array = issue_array + issue_set
        if len(issue_set) < maxResults:
            next_result = False
            issue_set = None
        else:
            startPos += maxResults
    logger.info('Count of issues: ' + str(len(issue_array)))

    ## print to screen what would be done if dry-run option was selected
    def dry_run_show(log):
        if args.dry_run:
            print(log)

    # Create dictionary of projects->components->and mapping components<->component_lead
    def create_dict(issue_object):
        ## Check if projects_dict is empty or not:
        if issue_object.fields.project.key in projects_dict:
            log = 'The project "%s" is in the projects_dict and have been already filled with components<->leads values' % (issue_object.fields.project.key)
            dry_run_show(log)
            logger.info(log)
        else:
        ## Just Filling the dictionary of projects->components->and mapping components<->component_lead
            log = 'The project "%s" is going to be created in the projects_dict and filled with components<->leads values' % (issue_object.fields.project.key)
            dry_run_show(log)
            logger.info(log)
            projects_dict.update({issue_object.fields.project.key: {'component-lead_mapping': {}}})
            try:
                components = jira.project_components(issue_object.fields.project.key)
            except Exception, e:
                log = 'Component_objects have not been retrieved because of: %s' % e
                dry_run_show(log)
                logger.critical(log)
                exit(1)
            ## We need identify project lead for components without project leads
            for i in components:
                try:
                    component = jira.component(i.id)
                except Exception, e:
                    log = 'Component_objects have not been retrieved because of: %s' % e
                    dry_run_show(log)
                    logger.critical(log)
                    exit(1)
                ## check whether component lead active or inactive/disabled/doesn't exist
                try:
                    if component.lead.active:
                        projects_dict[issue_object.fields.project.key]['component-lead_mapping'].update(
                            {component.name: component.lead.key})
                        log = 'The component "%s" lead user of project "%s" is ACTIVE => the issues with this component will be reassigned to component lead user "%s"' % (
                                component.name, issue_object.fields.project.key, component.lead.key)
                        dry_run_show(log)
                        logger.info(log)
                    else:
                        project = jira.project(issue_object.fields.project.key)
                        projects_dict[issue_object.fields.project.key]['component-lead_mapping'].update({component.name: project.lead.key})
                        log ='The component "%s" lead user of project "%s" is INACTIVE => the issues with this component will be reassigned to project lead user "%s"' % (
                            component.name, issue_object.fields.project.key, project.lead.key)
                        dry_run_show(log)
                        logger.info(log)
                except Exception, e:
                    project = jira.project(issue_object.fields.project.key)
                    projects_dict[issue_object.fields.project.key]['component-lead_mapping'].update(
                        {component.name: project.lead.key})
                    log = 'The component "%s" lead user of project "%s" is MISSED => the issues with this component will be reassigned to project lead user "%s"' % (
                            component.name, issue_object.fields.project.key, project.lead.key)
                    dry_run_show(log)
                    logger.info(log)

    # reassign the issue
    def reassign(issue_object):
        ## reassign the issue to the component lead of the first turned up component in the issue or to project_lead
        if issue_object.fields.components:
            try:
                ## to build list of issues those we are obliged to make reassign
                jira.assign_issue(issue_object.key,
                                  projects_dict[issue_object.fields.project.key]['component-lead_mapping'][
                                      issue_object.fields.components[0].name])
                reassigned_issues_lst.append([issue_object.key,
                                              issue_object.fields.summary.encode('utf-8').rstrip().replace('\t',
                                                                                                           '') if issue_object.fields.summary else 'The summary is missed',
                                              issue_object.fields.description.encode('utf-8').rstrip().replace('\t',
                                                                                                               '') if issue_object.fields.description else 'The description is misssed',
                                issue_object.fields.assignee.displayName if issue_object.fields.assignee else 'The assignee user has been deleted from AD',
                                issue_object.fields.reporter.displayName if issue_object.fields.reporter else 'The reporter user has been deleted from AD',
                                ",".join([i.name for i in issue_object.fields.components]),
                                ",".join([i for i in issue_object.fields.labels])])
                log = 'The issue "%s" has been just reassigned to the component "%s" lead (or project lead) - "%s"' % (
                    issue_object.key, issue_object.fields.components[0].name,projects_dict[issue_object.fields.project.key]['component-lead_mapping'][issue_object.fields.components[0].name])
                dry_run_show(log)
                logger.info(log)
            except Exception, e:
                no_reassign.append(issue_object.key)
                log = 'Reassign of the issue "%s" has not been completed because of: %s' % (issue_object.key,e)
                dry_run_show(log)
                logger.critical(log)
                #exit(1)
        else:
            no_components.append(issue_object.key)
            log = 'The issue "%s" doesn\'t have any component\'s, the email will be sent to "p_luksha","o_koval"' % (issue_object.key)
            dry_run_show(log)
            logger.info(log)

    # Processing each issue
    for issue_object in issue_array:
        ## if user whether inactive or even deleted from AD
        if not issue_object.fields.assignee:
            log = 'The assignee user has been deleted from AD => the issue "%s" must be reassigned to the component lead' % (issue_object.key)
            dry_run_show(log)
            logger.info(log)
            create_dict(issue_object)
            reassign(issue_object)
        elif not issue_object.fields.assignee.active:
            log = 'The assignee user "%s" has been disabled in AD => the issue "%s" must be reassigned to the component lead' % (issue_object.fields.assignee.key,issue_object.key)
            dry_run_show(log)
            logger.info(log)
            create_dict(issue_object)
            reassign(issue_object)
        else:
            log = 'The assignee user "%s" is active => the issue "%s" is skipped' % (issue_object.fields.assignee.key, issue_object.key)
            dry_run_show(log)
            logger.info(log)
    ## Create emails bodies
    no_components_issues=",".join(no_components)
    no_reassign_issues=",".join(no_reassign)
    subject = 'Reassign inactive or missed assignee in issues in projects: ' + args.projects_keys
    email_msg_no_components = 'There is the list of the issues in the projects ' + args.projects_keys +' with empty "Component" field:'
    email_msg_no_reassign = 'There is the list of the issues in the projects ' + args.projects_keys + ' that haven\'t been reassigned for some reasons:'
    email_msg_send_no_components = email_msg_no_components + ' ' + no_components_issues
    email_msg_send_no_reassign = email_msg_no_reassign + ' ' + no_reassign_issues
    send_email(email_msg_send_no_components + '\n' + email_msg_send_no_reassign, to_email_1)
    send_email(email_msg_send_no_components + '\n' + email_msg_send_no_reassign, to_email_2)

    # print projects_dict
    # print reassigned_issues_lst
    # print no_components_issues
    # print no_reassign_issues

    ## to create an csv file of issues those we are obliged to make reassign
    ##with open('/home/p_luksha/github/logs/HD-87417.csv','wb') as csvfile:
    ##    w = csv.writer(csvfile)
    ##    for i in reassigned_issues_lst:
    ##        w.writerow(i)

    # Remove lock file
    try:
        os.remove(global_conf['lock_path'])
    except IOError, e:
        logger.critical('error deleting lock file. Reason: %s', e)
        exit(1)