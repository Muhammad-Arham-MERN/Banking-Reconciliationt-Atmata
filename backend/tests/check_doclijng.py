# بِسْمِ اللّٰهِ الرَّحْمٰنِ الرَّحِيمِ
"""
Extract data from a PDF using the Nanonets v4 Python SDK.

Follows https://docs.nanonets.com/v4/reference/setup exactly:
- client = NanonetsClient(api_key='...')
- client.workflows.create(...)
- client.workflows.upload_document(...)
"""
import os

from dotenv import load_dotenv
from nanonetsclient import NanonetsClient

load_dotenv()

API_KEY = os.getenv("NANONETS_API_KEY") or "3d6ac69f-655b-11ef-98ab-ca1b41c7e175"
WORKFLOW_ID = "6e393117-5c1f-4541-8b1e-87d8eaaa795e"  # trained Instant Learning model
FILE_PATH = "../assets_dev/getjobid4620060.pdf"

# Initialize client
client = NanonetsClient(api_key=API_KEY)

# Verify the workflow exists (get returns a dict; list() has an SDK bug)
workflow = client.workflows.get(WORKFLOW_ID)
print(f"Workflow: {workflow['id']} — {workflow.get('description')}")

# Process a document
result = client.workflows.upload_document(
    workflow_id=WORKFLOW_ID,
    file_path=FILE_PATH,
    async_mode=False,
)
print(result)

# Get results
if result.get("status") == "completed":
    print(f"Extracted data: {result.get('data')}")

# وَإِنَّ اللَّهَ لَهُوَ خَيْرُ الرَّازِقِينَ
