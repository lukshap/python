Summary
=============
1. Script copies access log file tomcat-confluence-access."YYYY-mm-dd".log from the "/var/atlassian/confluence/logs" on live Confluence server (bxconf01.example.local).
2. Then composes data in order to INSERT it to the "conf_removed_pages" table in the "bxe_info" database scheme on "bxjcsdb01.example.local" server.
While composing the data script runs SELECT querry to the "confdb" database scheme on "bxjcsdb01.example.local" server.
3. Then script runs INSERT sql query and stops to run.
