#! /usr/bin/python

import fileinput,sys
import subprocess
import re

subprocess.call(["sed -i -e 's/\t/|/g' old_usersVSnew_users.txt"], shell=True)
subprocess.call(["cat old_usersVSnew_users.txt | cut -d '|' -f1,4 > old_usersVSnew_users_2.txt"], shell=True)
mapping = {}

with open('old_usersVSnew_users_2.txt', 'r+') as infile:
    for i in infile:
        old_name=i.split("|")[0]
        new_name=i.rstrip().split("|")[1]
        mapping[old_name]=new_name
for i in mapping:
    print i,mapping[i]

for line in fileinput.input("/home/p_luksha/ngt2/NGT_JSON_export_02092016.json_updated", inplace=True):
    for i in mapping.keys():
        pattern = re.compile(i)
        if pattern.findall(line):
            line=line.replace(i, mapping[i])
    sys.stdout.write(line)
