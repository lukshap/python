Summary
=============

The script generates and sends to the certain recipients two csv report files.

These report files represent lists of global orphaned spaces.

We consider global spaces to be unnecessary or orphaned if:
1. the space contains less than 10 pages, excluding pages in trash ("less_10_pages.csv" report file)
OR
2. there were no page edits for the last 6 months ("six_month.csv" report file)

