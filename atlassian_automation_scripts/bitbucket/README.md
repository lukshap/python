Summary
=============

Script removes from the certain bitbcket repository branches:
1. which names contain either feature or bugfix or hotfix words.
2. where the last action was commited early then defined in the 'days_all' variable.
3. if a branch was already merged and the last action was commited early then defined in the 'days_merged' variable.
