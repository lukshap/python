import groovy.json.JsonSlurper;
import groovy.json.StreamingJsonBuilder;
import groovy.json.JsonOutput;
import com.atlassian.jira.ComponentManager;
import com.atlassian.jira.issue.CustomFieldManager;
import com.atlassian.jira.issue.fields.CustomField;
import com.atlassian.jira.issue.IssueManager;
import com.atlassian.jira.component.ComponentAccessor;
import com.atlassian.jira.issue.Issue;
import com.atlassian.jira.issue.MutableIssue
import java.net.URL
import java.net.URLConnection
import org.apache.commons.codec.binary.Base64;
import javax.net.ssl.HostnameVerifier
import javax.net.ssl.HttpsURLConnection
import javax.net.ssl.SSLContext
import javax.net.ssl.TrustManager
import javax.net.ssl.X509TrustManager

// skip ssl validation
def nullTrustManager = [
    checkClientTrusted: { chain, authType ->  },
    checkServerTrusted: { chain, authType ->  },
    getAcceptedIssuers: { null }
]

def nullHostnameVerifier = [
    verify: { hostname, session -> true }
]
SSLContext sc = SSLContext.getInstance("SSL")
sc.init(null, [nullTrustManager as X509TrustManager] as TrustManager[], null)
HttpsURLConnection.setDefaultSSLSocketFactory(sc.getSocketFactory())
HttpsURLConnection.setDefaultHostnameVerifier(nullHostnameVerifier as HostnameVerifier)

// For testing via console
//IssueManager issueManager = ComponentManager.getInstance().getIssueManager();
//Issue Issue = issueManager.getIssueObject("IFRPAS-85");

// get issue key
Issue Issue = issue;
def issueID = Issue.getKey();
// define variable for custom fields
def CF = "";

CustomFieldManager customFieldManager = ComponentAccessor.getCustomFieldManager();

// define json frame
//def body_req = [ "admins" : "", "name": "","template": true,"spaceDevelopers": "","responseData": ["endpoint":"https://jira-stage.booxdev.com/","ticketId": issueID]];
def body_req = [ "admins" : "", "name": "","template": true,"spaceDevelopers": "","responseData": ["endpoint":"https://example.com/","ticketId": issueID]];

// define list from all custom fields in the issue
List all_cfl = customFieldManager.getCustomFieldObjects();	

// go through the "all_cfl" list and fill "body_req" json
for (i in all_cfl) {
   if (i.getFieldName() == 'Administrators') {
       CF = Issue.getCustomFieldValue(customFieldManager.getCustomFieldObjectByName(i.getFieldName())).replaceAll("\\s","");
       body_req['admins'] = CF.split(',')
   }
  else if (i.getFieldName() == 'Name') {
      CF = Issue.getCustomFieldValue(customFieldManager.getCustomFieldObjectByName(i.getFieldName()));
       body_req['name'] = CF
   }
   else if (i.getFieldName() == 'Developers'){
       CF = Issue.getCustomFieldValue(customFieldManager.getCustomFieldObjectByName(i.getFieldName())).replaceAll("\\s","");
       body_req['spaceDevelopers'] = CF.split(',')
   }
}

// For testing:
//def body_req = [ "key" : "luksha10", "name": "ll" + issueID,"description": ["plain":["value": "This is an","representation":"plain"]],"metadata":[:]]
//String baseURL = "https://example-stage.com/rest/api/space";

// define variables and encode credentials for BasicHTTPAuth
String baseURL = "https://example-2.com/v0/new-org";
String name = "jira";
String password = "jira";
String authString = name + ":" + password;
byte[] authEncBytes = Base64.encodeBase64(authString.getBytes());
String authStringEnc = new String(authEncBytes);
// create http connection
URL url = new URL(baseURL); 
HttpURLConnection connection = (HttpURLConnection) url.openConnection();   
connection.setDoOutput(true); 
connection.setInstanceFollowRedirects(false); 
connection.setRequestProperty("Authorization", "Basic " + authStringEnc);
connection.setRequestMethod("POST"); 
connection.setRequestProperty("Content-Type", "application/json;charset=UTF-8")
connection.setRequestProperty("charset", "utf-8");
OutputStreamWriter writer = new OutputStreamWriter(connection.getOutputStream());
connection.outputStream.withWriter("UTF-8") { new StreamingJsonBuilder(it,body_req) }
connection.connect();

//return connection.getResponseCode()
// return results of request
return "Content:" + connection.getContent() + "____" + "ResponseCode:" + connection.getResponseCode() + "____" + "getResponseMessage:" + connection.getResponseMessage()
//return JsonOutput.toJson(body_req)
//return csl
//return issueID
