#! /usr/bin/python
"""
The script should be run every 15 min.
The script gets indexing message from a certain Fisheye repo, then updates the page in Confluence with this info.
Also it reads description.txt file and updates the page in Confluence with this info.
Each time script updates page in Confluence it increments page version.
If there are more than 20 page versions - they are removed.
If script somehow finishes with an error - the message is being sent to the
"""
import ConfigParser
import logging
import requests
import re
from xmlrpclib import Server
import time
from datetime import tzinfo, timedelta, datetime
import smtplib
from email.mime.text import MIMEText
# import requests.packages.urllib3
# requests.packages.urllib3.disable_warnings()

def get_properties(section):
    config = ConfigParser.SafeConfigParser()
    config.read(config_file)
    props = {}
    if section:
        for key, val in config.items(section):
            props[key] = val
    return props

# Settings
config_file = '/home/p_luksha/python_scripts/WOTD/FISHEYE_CONFLUENCE_wotdev3/config.ini'
global_conf = get_properties('GLOBAL')
fisheye_conf = get_properties('FISHEYE')
confluence_conf = get_properties('CONFLUENCE')
smtp_conf = get_properties('SMTP')

log_path = global_conf['log_path']

fisheye_user = fisheye_conf['fisheye_user']
fisheye_password = fisheye_conf['fisheye_password']
fisheye_url=fisheye_conf['fisheye_url']
fisheye_get_uri=fisheye_conf['fisheye_get_uri']
fisheye_repo=fisheye_conf['fisheye_repo']
fisheye_message_description_file = fisheye_conf['fisheye_message_description_file']

confluence_user = confluence_conf['confluence_user']
confluence_password = confluence_conf['confluence_password']
confluence_url = confluence_conf['confluence_url']
confluence_page_id = confluence_conf['confluence_page_id']
confluence_page_title = confluence_conf['confluence_page_title']
confluence_get_uri = confluence_conf['confluence_get_uri']
confluence_put_uri = confluence_conf['confluence_put_uri']
confluence_get_uri_xmlrpc = confluence_conf['confluence_get_uri_xmlrpc']
confluence_remove_page_versions_count = confluence_conf['confluence_remove_page_versions_count']

smtp_host= smtp_conf['smtp_host']
from_email= smtp_conf['from_email']
to_email = smtp_conf['to_email']
subject = smtp_conf['subject']
email= smtp_conf['email']

message_description = ''

# Logging settings
logger = logging.getLogger()
logger.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
handler = logging.FileHandler(log_path)
handler.setLevel(logging.DEBUG)
handler.setFormatter(formatter)
logger.addHandler(handler)

def send_email(email_msg):
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

if __name__ == '__main__':
    headers = {'Content-Type': 'application/json'}
    ## add a offset +3 hours from UTC, because control server runs in UTC timezone
    class UTC3(tzinfo):
        def utcoffset(self, dt):
            return timedelta(hours=+3)
        def tzname(self, dt):
            return "UTC+3"
        def dst(self, dt):
            return timedelta(0)
    utc3 = UTC3()
    ## removing page history pages if verisons>confluence_remove_page_versions_count value
    ## use xmlrpc, because there is not any REST API methods to remove page versions
    try:
        s = Server(confluence_url+confluence_get_uri_xmlrpc)
        token = s.confluence1.login(confluence_user, confluence_password)
        a=s.confluence1.getPageHistory(token, confluence_page_id)
        b=[s.confluence1.removePageVersionByVersion(token, confluence_page_id, 1) for i in range(len(a)) if len(a)>int(confluence_remove_page_versions_count)]
        logger.info('Removing old page (pageid=%s) versions from Confluence' % confluence_page_id)
    except Exception, e:
        logger.critical('Critical error: %s' % e)
        email = re.sub('\[error\]', str(e), email)
        send_email(email)
        exit(1)
    ## Get revision index data from Fisheye
    try:
        fisheye_get = requests.get(fisheye_url + fisheye_get_uri + fisheye_repo, auth=(fisheye_user, fisheye_password)).json()
        logger.info('Getting info from Fisheye repo "%s" ...' % fisheye_repo)
    except Exception, e:
        logger.critical('Fisheye connecting error: %s' % e)
        email = re.sub('\[error\]', str(e), email)
        send_email(email)
        exit(1)
    ## Get current page version
    try:
        conf_get = requests.get(confluence_url + confluence_get_uri + confluence_page_id,auth=(confluence_user, confluence_password)).json()
        logger.info('Getting info from Confluence page (pageid=%s) ...' % confluence_page_id)
    except Exception, e:
        logger.critical('Confluence GET request error: %s' % e)
        email = re.sub('\[error\]', str(e), email)
        send_email(email)
        exit(1)
    ## Create description for fisheye statuses to post it to Confluence
    try:
        with open(fisheye_message_description_file, 'r') as payload:
            for i in payload:
                message_description = message_description + i.strip()
    except Exception, e:
        logger.critical('Critical error: %s' % e)
        email = re.sub('\[error\]', str(e), email)
        send_email(email)
        exit(1)
    ## create body page, and also increment page version relying on the current page version from previous GET query(conf_get)
    ## if repo is RUNNING and index is not 100%
    if fisheye_get['state'] == 'RUNNING' and 'message' in fisheye_get['indexingStatus'].keys():
        value = '<table><tbody><tr><th>Repository</th><th>Current indexing status</th><th>Last time script run</th></tr><tr><td><a href=\\"' + fisheye_url + '/browse/' + fisheye_repo + '\\">' + fisheye_repo + '</a></td><td>' + fisheye_get['indexingStatus']['message'] + '</td><td>' + datetime.now(utc3).ctime() + '</td></tr></tbody></table>'
        payload = '{"version":{"number": ' + str(conf_get["version"]["number"]+1) + '}, "title": "' + confluence_page_title + '", "type": "page","body": {"storage": {"value":"' + value + message_description + '","representation": "storage"}}}'
        ## Put index state from Fisheye to the page in Confluence
        try:
            p = requests.put(confluence_url + confluence_put_uri + confluence_page_id,headers=headers,data = payload,auth=(confluence_user, confluence_password))
            logger.info('PUT in the Confluence page (pageid=%s) info: Fisheye repo "%s" current indexing status is "%s"' % (confluence_page_id,fisheye_repo,fisheye_get['indexingStatus']['message']))
        except Exception, e:
            logger.critical('Confluence PUT (not 100 index) request error: %s' % e)
            email = re.sub('\[error\]', str(e), email)
            send_email(email)
            exit(1)
    ##  if repo is RUNNING and index is 100%
    elif fisheye_get['state'] == 'RUNNING' and not 'message' in fisheye_get['indexingStatus'].keys():
        value = '<table><tbody><tr><th>Repository</th><th>Current indexing status</th><th>Last time script run</th></tr><tr><td><a href=\\"' + fisheye_url + '/browse/' + fisheye_repo + '\\">' + fisheye_repo + '</a></td><td>100%</td><td>' + datetime.now(utc3).ctime() + '</td></tr></tbody></table>'
        payload = '{"version":{"number": ' + str(conf_get["version"]["number"] + 1) + '}, "title": "' + confluence_page_title + '", "type": "page","body": {"storage": {"value":"' + value + message_description + '","representation": "storage"}}}'
        try:
            ## Put index state is 100% to the page in Confluence
            p = requests.put(confluence_url + confluence_put_uri + confluence_page_id,headers=headers,data = payload,auth=(confluence_user, confluence_password))
            logger.info('PUT in the Confluence page (pageid=%s) info: Fisheye repo "%s" current indexing status is 100' % (confluence_page_id,fisheye_repo))
        except Exception, e:
            logger.critical('Confluence PUT (100 index) request error: %s' % e)
            email = re.sub('\[error\]', str(e), email)
            send_email(email)
            exit(1)
    else:
        ## Put Fisheye state information (stopping,starting,stoppped) to the page in Confluence
        value = '<table><tbody><tr><th>Repository</th><th>Current indexing status</th><th>Last time script run</th></tr><tr><td><a href=\\"' + fisheye_url + '/browse/' + fisheye_repo + '\\">' + fisheye_repo + '</a></td><td>' + fisheye_get['state'] + '</td><td>' + datetime.now(utc3).ctime() + '</td></tr></tbody></table>'
        payload = '{"version":{"number": ' + str(conf_get["version"]["number"] + 1) + '}, "title": "' + confluence_page_title + '", "type": "page","body": {"storage": {"value": "' + value + message_description + '","representation": "storage"}}}'
        try:
            p = requests.put(confluence_url + confluence_put_uri + confluence_page_id, headers=headers, data=payload, auth=(confluence_user, confluence_password))
            logger.info('PUT in the Confluence page (pageid=%s) info: Fisheye repo "%s" state is "%s"' % (confluence_page_id,fisheye_repo, fisheye_get['state']))
        except:
            logger.critical('Confluence PUT (stopping,starting,stoppped repo state) request error: %s' % e)
            email = re.sub('\[error\]', str(e), email)
            send_email(email)
            exit(1)
