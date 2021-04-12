Summary
============
1. Script searches for Confluence pages (in spaces with "current" status) that haven't been updated for two years in the "conf_orphaned_pages" table in the confdb" database on the "bxjcsdb01.expmple.local" host.
2. Checks if the same entries already exist in the "conf_orphaned_pages" table in "bxe_info" database on the "bxjcsdb01.example.local" host.
    1. If not - populates "conf_orphaned_pages" table with the data, keeping in mind that recipient address is:
        * if creator is an active user, use creator's email
        * if creator is inactive use, last_editor's email
        * if last_editor is also inactive, use confluence gardener_email address
        * if the email address of the user is empty or devnull@booxware.de the gardener_email address should be used.

	
