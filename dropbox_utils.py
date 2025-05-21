import dropbox
from dropbox.exceptions import ApiError
import os

def get_dropbox_client(access_token):
    """Create and return a Dropbox client instance."""
    try:
        dbx = dropbox.Dropbox(access_token)
        # Verify the token is valid
        dbx.users_get_current_account()
        return dbx
    except Exception as e:
        raise Exception(f"Failed to create Dropbox client: {str(e)}")

def create_folder(dbx, folder_name):
    """Create a folder in Dropbox if it doesn't exist."""
    try:
        # Check if folder exists
        try:
            dbx.files_get_metadata(f"/{folder_name}")
            return f"/{folder_name}"
        except ApiError as e:
            if e.error.is_path() and e.error.get_path().is_not_found():
                # Folder doesn't exist, create it
                dbx.files_create_folder(f"/{folder_name}")
                return f"/{folder_name}"
            else:
                raise
    except Exception as e:
        raise Exception(f"Failed to create Dropbox folder: {str(e)}")

def upload_file_to_dropbox(dbx, file_path, folder_path):
    """Upload a file to Dropbox."""
    try:
        file_name = os.path.basename(file_path)
        dropbox_path = f"{folder_path}/{file_name}"
        
        # Check if file already exists
        try:
            dbx.files_get_metadata(dropbox_path)
            # File exists, add a number to the filename
            base, ext = os.path.splitext(file_name)
            counter = 1
            while True:
                new_name = f"{base}_{counter}{ext}"
                new_path = f"{folder_path}/{new_name}"
                try:
                    dbx.files_get_metadata(new_path)
                    counter += 1
                except ApiError:
                    dropbox_path = new_path
                    break
        except ApiError:
            # File doesn't exist, proceed with upload
            pass

        # Upload the file
        with open(file_path, 'rb') as f:
            dbx.files_upload(f.read(), dropbox_path)
        
        return dropbox_path
    except Exception as e:
        raise Exception(f"Failed to upload file to Dropbox: {str(e)}")

def list_dropbox_files(dbx, folder_path):
    """List all files in a Dropbox folder."""
    try:
        result = dbx.files_list_folder(folder_path)
        files = []
        for entry in result.entries:
            if isinstance(entry, dropbox.files.FileMetadata):
                files.append({
                    'name': entry.name,
                    'path': entry.path_display,
                    'size': entry.size,
                    'modified': entry.server_modified
                })
        return files
    except Exception as e:
        raise Exception(f"Failed to list Dropbox files: {str(e)}") 