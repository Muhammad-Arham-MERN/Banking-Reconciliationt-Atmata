# This specification is being created to update the front end. 

# API 1
## Current Approach:
Currently, what our front end does is that if the user opens the application, it will contain:

*A list of histories. The histories will be just file names, and they will be imported from the local directory.*

## New Implementation:

- since we are shifting to a cloud-based approach, this loading methodology is going to change. 
- Instead of now calling the files and their names from the local directories

1. we are going to be using a new API that has been created in the backend called load_files_cloud. This API is going to return the file names that a user processes in a list of strings and name of user
2. The first step is that, on the first page of the user after sign-in is complete, the main application must display at the top with a very beautiful "Assalamu Alaikum" and the name of the user. 
3. Below where they choose the history, the history should be loaded now from the new load_files_cloud API.


# API 2 
## Current Approach:
Currently, when a user completes reconciliation, they can tell the name of the file and it will:

*save the 'final' reconciled historcail file data, in local storage folder*

## New Implementation

1. Use the save_files_cloud API endpoint, which is a new cloud based API endpoint
2. It is a POST API Endpoint so it will expect a request + body
3. The request gives user_id
4. The body gives file_name & file_data, the file_name is the same one provided by user, from input
5. file_data will contain a list of dictionaries, the data will be same as before that is the name, details, debit/credit amounts and cateogory which was saved in local storage

*In general the entire process remains almost the same, just the local file storage method is transfered to cloud approach*
