#!/bin/env python
# -*- coding: utf-8 -*-

from jira.client import JIRA
from datetime import datetime, timedelta
import logging, fcntl, os
from bot_libs import JiraHdmIssue


#   Settings
jira_url = ''
user = 'arts_assistant'
password = ''
released_timeout = timedelta(days=5)

log_path = '/home/jirabot/logs/ARTS_resolve_close.log'
lock_path = '/home/jirabot/lock/ARTS_resolve_close.lock'

debug = True
maxResults = 100

logger = logging.getLogger()
logger.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
handler = logging.FileHandler(log_path)
handler.setLevel(logging.DEBUG)
handler.setFormatter(formatter)
logger.addHandler(handler)

#   Main
if __name__ == '__main__':

    fp = open(lock_path, 'w')

    try:
        fcntl.lockf(fp, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except IOError, e:
        logger.critical('error getting lock, another instance running? Reason: %s', e)
        exit(1)

    jira = None

    try:
        jira = JIRA({'server': jira_url}, basic_auth=(user, password))
    except Exception, e:
        logger.critical('JIRA instance unavailable, detail: %s' % e)
        exit(1)

    arts_issues = {}

    next_result = True
    startPos = 0

    # Строим список issue потенциально требующих обработки
    while next_result:
        issue_set = []
        try:
            issue_set = jira.search_issues(
                'project=ARTS AND status=Resolved',
                fields=[],
                startAt=startPos,
                maxResults=maxResults,
            )
        except Exception, e:
            logger.critical('Jira request failed, detail: %s' % e)
            exit(1)

        for issue_object in issue_set:
            arts_issues[issue_object.key] = issue_object.key

        if len(issue_set) < maxResults:
            next_result = False
            issue_set = None
        else:
            startPos += maxResults

    for issue_key in arts_issues:
	
	print issue_key
        issue = JiraHdmIssue(jira, issue_key)
        logger.debug('Issue %s - processing' % issue_key)

	if issue.status == 'Resolved':
	    if issue.status_time > released_timeout:
                try:
		    issue.close(None, 151)
		    logger.info('Issue %s - close' % issue.key)
		    issue.add_comment('Задача не была закрыта в максимально допустимый срок, поэтому закрывается автоматически.')
                    logger.info('Issue %s - add comment' % issue.key)
                except Exception, e:
                    logger.error('Issue %s - CloseError: %s' % (issue.key,e))
            else:
                logger.debug('All conditions are false, skipped')
        else:
            logger.warning('Something strange')

    try:
        os.remove(lock_path)
    except IOError, e:
        logger.critical('error deleting lock file. Reason: %s', e)
        exit(1)
