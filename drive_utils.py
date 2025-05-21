from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
import os
import pickle
import time

SCOPES = ['https://www.googleapis.com/auth/drive.file']

def get_google_drive_service():
    """Get or create Google Drive service with proper authentication."""
    creds = None
    if os.path.exists('token.pickle'):
        with open('token.pickle', 'rb') as token:
            creds = pickle.load(token)
    
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                'credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)
        
        with open('token.pickle', 'wb') as token:
            pickle.dump(creds, token)

    return build('drive', 'v3', credentials=creds)

def upload_file_to_drive(file_path, folder_id=None):
    """
    Upload a file to Google Drive.
    
    Args:
        file_path (str): Path to the file to upload
        folder_id (str, optional): ID of the folder to upload to
    
    Returns:
        str: ID of the uploaded file
    """
    start_time = time.time()
    
    try:
        service = get_google_drive_service()
        file_metadata = {
            'name': os.path.basename(file_path),
            'mimeType': 'application/pdf' if file_path.endswith('.pdf') else 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'
        }
        
        if folder_id:
            file_metadata['parents'] = [folder_id]
        
        media = MediaFileUpload(file_path, resumable=True)
        file = service.files().create(
            body=file_metadata,
            media_body=media,
            fields='id'
        ).execute()
        
        upload_time = time.time() - start_time
        print(f"Upload completed in {upload_time:.2f} seconds")
        
        return file.get('id')
    
    except Exception as e:
        print(f"Error uploading to Drive: {str(e)}")
        raise

def create_folder(folder_name):
    """
    Create a folder in Google Drive.
    
    Args:
        folder_name (str): Name of the folder to create
    
    Returns:
        str: ID of the created folder
    """
    try:
        service = get_google_drive_service()
        file_metadata = {
            'name': folder_name,
            'mimeType': 'application/vnd.google-apps.folder'
        }
        
        file = service.files().create(
            body=file_metadata,
            fields='id'
        ).execute()
        
        return file.get('id')
    
    except Exception as e:
        print(f"Error creating folder: {str(e)}")
        raise 