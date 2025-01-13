#!/usr/bin/env python3

import os
import pickle
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

# If modifying these scopes, delete the token.pickle file.
SCOPES = ['https://www.googleapis.com/auth/drive']

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

def copy_folder(service, source_folder_id, parent_id=None):
    """
    Recursively copies a folder and its contents.
    Args:
        service: Google Drive API service instance
        source_folder_id: ID of the folder to copy
        parent_id: ID of the parent folder to copy to (optional)
    Returns:
        ID of the new folder
    """
    try:
        # Get source folder metadata
        folder_metadata = service.files().get(
            fileId=source_folder_id, fields='name').execute()
        
        # Create new folder
        new_folder = {
            'name': f"Copy of {folder_metadata['name']}",
            'mimeType': 'application/vnd.google-apps.folder'
        }
        if parent_id:
            new_folder['parents'] = [parent_id]
        
        new_folder = service.files().create(
            body=new_folder, fields='id').execute()
        new_folder_id = new_folder['id']
        
        # List all files in the source folder
        results = service.files().list(
            q=f"'{source_folder_id}' in parents",
            fields="files(id, name, mimeType)").execute()
        items = results.get('files', [])
        
        # Copy each item in the folder
        for item in items:
            if item['mimeType'] == 'application/vnd.google-apps.folder':
                # Recursively copy subfolder
                copy_folder(service, item['id'], new_folder_id)
            else:
                # Copy file
                copied_file = {
                    'name': item['name'],
                    'parents': [new_folder_id]
                }
                service.files().copy(
                    fileId=item['id'],
                    body=copied_file).execute()
        
        return new_folder_id
    
    except HttpError as error:
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