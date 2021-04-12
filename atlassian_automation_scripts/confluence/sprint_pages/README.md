Summary
=============

1. For each board which is described in the json file from the bitbucket repo script gets all sprints
2. Defines an active sprint from the sprints above
3. If the end sprint date for an active sprint is today anf if the page doesn't alreasy exists script composes page's content(velocity link, Burndown gadget, Scope gadget, time distribution attachment)
4. Creates the page with the content above in the space and underneath the page whose names and uri retrieved from the json file from the bitbucket repo

