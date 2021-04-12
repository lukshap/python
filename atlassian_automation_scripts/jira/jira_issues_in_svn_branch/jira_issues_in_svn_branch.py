#! /usr/bin/python
"""
The script gets svn log from particular branch, parses each comment from each commit and getы from comments pattern "[A-Z]+-[0-9]+" (match JIRA issue key, i.e. "AFSV-90"),
then makes list of all matched patterns => remove duplicate entries (using set()) and makes jql from all unique issues.
"""
import subprocess
import re
import fileinput,sys
import ConfigParser
import logging

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
local_conf = get_properties('LOCAL')

log_path = global_conf['log_path']
svn_url_path = local_conf['svn_url_path']
svn_log_file_path = local_conf['svn_log_file_path']
issue_key_pattern = "[A-Z]+-[0-9]+"
jql=[]

# Logging settings
logger = logging.getLogger()
logger.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
handler = logging.FileHandler(log_path)
#handler = logging.StreamHandler()
handler.setLevel(logging.DEBUG)
handler.setFormatter(formatter)
logger.addHandler(handler)

if __name__ == '__main__':
    subprocess.call(["svn log --stop-on-copy " + svn_url_path + "| egrep '[A-Z]+-[0-9]+' >" + svn_log_file_path ], shell=True)
    pattern = re.compile(issue_key_pattern)
    with open(svn_log_file_path, 'r+') as infile:
        for line in infile:
            if pattern.findall(line):
                line = pattern.findall(line)
                for i in line:
                    jql.append(i)
    print len(jql)
    print len(set(jql))
    print "issue in (" + ",".join(set(jql)) + ")"