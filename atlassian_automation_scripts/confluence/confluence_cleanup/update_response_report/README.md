Summary
=============
This script does the following:
1. Checks the table conf_orphaned_pages and loads all records for which emails have been sent already(column message_sent=1):
2. For each record:
    1. checks if the page has been updated meanwhile
    2. If page has been updated removes record from the table conf_orphaned_pages
3. Sends a quantitative report, that shows how many pages have been updated this week (and how many have not), to the following recipients - cod@example.de, dl-confluence-gardeners@example.de




