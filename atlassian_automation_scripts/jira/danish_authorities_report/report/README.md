Report
=============

The local JIRA user "risk_reporting" is used by the script `report.py` in order to fetch "Risk Probability" and "Risk Impact" custom fields from the tickets which are determined by the git commit log from the "sportbet" repository.

The `AssetRegisterCreator.jar` is compliled with the user's password (`licensehelper/src/main/resources/jiraconfig.properties`).

Therefore if the password is needed to be changed it should be changed in JIRA, then in `licensehelper/src/main/resources/jiraconfig.properties` and then the new `AssetRegisterCreator.jar` should be compiled.

## Build

Just checkout the source repository "licensehelper" and execute a `mvn package` in the project root folder. This will generate the `AssetRegisterCreator.jar`

