#!/usr/bin/env python3

import os
import pickle
import time
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from googleapiclient.http import MediaIoBaseDownload

# If modifying these scopes, delete the token.pickle file.
SCOPES = ['https://www.googleapis.com/auth/drive']

# Constants for retry logic
MAX_RETRIES = 5
INITIAL_RETRY_DELAY = 1  # seconds

def get_google_drive_service():
    """Gets an authorized Google Drive service instance."""
    creds = None
    
    # The token.pickle file stores the user's access and refresh tokens
    if os.path.exists('token.pickle'):
        with open('token.pickle', 'rb') as token:
            creds = pickle.load(token)
    
    # If there are no (valid) credentials available, let the user log in
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                'credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)
        
        # Save the credentials for the next run
        with open('token.pickle', 'wb') as token:
            pickle.dump(creds, token)

    return build('drive', 'v3', credentials=creds)

def execute_with_retry(request):
    """Execute a Drive API request with exponential backoff retry logic."""
    for retry in range(MAX_RETRIES):
        try:
            return request.execute()
        except (TimeoutError, HttpError) as e:
            if retry == MAX_RETRIES - 1:
                raise e
            
            delay = INITIAL_RETRY_DELAY * (2 ** retry)  # Exponential backoff
            print(f"Request failed, retrying in {delay} seconds...")
            time.sleep(delay)
    return None

def copy_folder(service, source_folder_id, parent_id=None, is_root=True):
    """
    Recursively copies a folder and its contents.
    Args:
        service: Google Drive API service instance
        source_folder_id: ID of the folder to copy
        parent_id: ID of the parent folder to copy to (optional)
        is_root: Whether this is the root/top-level folder being copied
    Returns:
        ID of the new folder
    """
    try:
        # Get source folder metadata
        folder_metadata = execute_with_retry(
            service.files().get(fileId=source_folder_id, fields='name')
        )
        
        # Create new folder
        new_folder = {
            'name': f"Copy of {folder_metadata['name']}" if is_root else folder_metadata['name'],
            'mimeType': 'application/vnd.google-apps.folder'
        }
        if parent_id:
            new_folder['parents'] = [parent_id]
        
        new_folder = execute_with_retry(
            service.files().create(body=new_folder, fields='id')
        )
        new_folder_id = new_folder['id']
        
        # List all files in the source folder
        results = execute_with_retry(
            service.files().list(
                q=f"'{source_folder_id}' in parents",
                fields="files(id, name, mimeType)",
                pageSize=1000
            )
        )
        items = results.get('files', [])
        
        # Copy each item in the folder
        for item in items:
            if item['mimeType'] == 'application/vnd.google-apps.folder':
                # Recursively copy subfolder (with is_root=False)
                copy_folder(service, item['id'], new_folder_id, is_root=False)
            else:
                # Copy file
                copied_file = {
                    'name': item['name'],
                    'parents': [new_folder_id]
                }
                execute_with_retry(
                    service.files().copy(fileId=item['id'], body=copied_file)
                )
                print(f"Copied file: {item['name']}")
        
        return new_folder_id
    
    except Exception as error:
        print(f'An error occurred: {error}')
        return None

def main():
    """Main function to copy a shared folder."""
    service = get_google_drive_service()
    
    # Get the source folder ID from the user
    source_folder_id = input("Enter the source folder ID (from the shared folder URL): ")
    
    # Copy the folder and its contents
    print("Starting folder copy process...")
    new_folder_id = copy_folder(service, source_folder_id)
    
    if new_folder_id:
        print(f"Folder copied successfully! New folder ID: {new_folder_id}")
        print(f"View it at: https://drive.google.com/drive/folders/{new_folder_id}")
    else:
        print("Failed to copy folder.")

if __name__ == '__main__':
    main() 