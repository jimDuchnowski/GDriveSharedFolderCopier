# Google Drive Shared Folder Copier

This script allows you to copy the contents of a shared Google Drive folder to your own Google Drive account.

## Setup

1. Install the required dependencies:
```bash
pip install -r requirements.txt
```

2. Set up Google Drive API credentials:
   - Go to the [Google Cloud Console](https://console.cloud.google.com/)
   - Create a new project or select an existing one
   - Enable the Google Drive API
   - Go to Credentials
   - Create OAuth 2.0 Client ID credentials (Desktop application)
   - Download the credentials and save them as `credentials.json` in the same directory as the script

## Usage

1. Run the script:
```bash
python drive_folder_copier.py
```

2. When prompted, enter the folder ID from the shared folder URL. You can get this from the URL of the shared folder:
   - Example URL: `https://drive.google.com/drive/folders/1234567890abcdef`
   - Folder ID would be: `1234567890abcdef`

3. On first run, the script will open your browser for OAuth2 authentication. Follow the prompts to allow access.

4. The script will create a copy of the folder and its contents in your Google Drive account.

## Notes

- The script will create a new folder named "Copy of [Original Folder Name]"
- All contents, including subfolders, will be copied recursively
- The script saves authentication tokens in `token.pickle` for future use 