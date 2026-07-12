# Database Upadte

## Get File Info Endpoint
In this one you need to implement one API endpoint in the backend called `get_file_info`. This particular `GET` endpoint is used to retrieve reconciliation data from the database.

- The table will be called users
- users contains a specific field that references an external field called "files" in List[str] format
- The above List[str] will be returned

Database will be a Serverless Cloud-Based PostgreSQL Database Called Cockroach DB
You will connect it via SQLModel and also query using SQLModel (https://sqlmodel.tiangolo.com/)

## Update File Info Endpoint
Here you will be using a different API endpoint called update_file_info. This endpoint will be using a POST request. 

- The table will be caleld reconciliation_data
- The POST will require 2 arguments "file_name" and "file_data"
- file_name will be string name of file
- file_data will be List[Dictionaries] with structure {"name": "string","description": "string","debit_credit_value": 0.0,"category": "string"}
- The file_data in List[Dictionaries] format will be added to data base as is, without modification

You will connect it via SQLModel and also query using SQLModel (https://sqlmodel.tiangolo.com/) and also Request via SQLModel

## Replace SQLlite3 Processing
Here I will first explain current method and the revised method

### Current Implementation:

- User selects a particular history reconciliation file stored locally just above the Upload XLSX and PDF section
- These particular files are then retrieved locally and processed using sqlite3

### New Implementation

- Now with the help of get_file_info endpoint, we can retrieve all the "past historical files" stored on cloud to user
- user can select the file and perform processing
- This time instead of sqlite3, the discrepancies are loaded automatically from cloud tables

# KEY CONSTRAINTS *MUST NOT SURPASS THESE BOUNDARIES*

- You are not designated for frontend related work
- This specification is specifically targetted for backend API integration and NOT Frontend
- The last part of my implementation is just explaination, it is frontend based and will be practically handled later on
- The Frontend will be tackled in a different specification
- (Repeating) Current concern is proper implementation of Backend APIs

