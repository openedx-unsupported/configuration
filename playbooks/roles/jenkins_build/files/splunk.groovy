//send job metadata and junit reports with page size set to 50 (each event contains max 50 test cases)
splunkins.sendTestReport(50)


// Send paver timing logs to Splunk
splunkins.archive("**/timing*.log", null, false, "10MB")
