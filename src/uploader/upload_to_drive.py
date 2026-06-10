#!/usr/bin/env python3
"""Upload generated documents to Google Drive folder specified in settings.json"""

import json
import os
import sys
import re
from pathlib import Path

def main():
    # Load settings
    with open('settings/sample_data.json') as f:
        settings = json.load(f)

    # Extract folder ID from URL
    drive_url = settings['output_Google_drive_directory']
    folder_id_match = re.search(r'/folders/([a-zA-Z0-9-_]+)', drive_url)
    if not folder_id_match:
        print(f"❌ Could not extract folder ID from: {drive_url}")
        return 1

    FOLDER_ID = folder_id_match.group(1)
    SERVICE_ACCOUNT_JSON = os.getenv('GOOGLE_SERVICE_ACCOUNT_JSON')
    OUTPUT_DIR = 'output'

    # Validate service account
    if not SERVICE_ACCOUNT_JSON or not os.path.exists(SERVICE_ACCOUNT_JSON):
        print(f"❌ Error: Service account key not found")
        print(f"\nSet environment variable:")
        print(f"  export GOOGLE_SERVICE_ACCOUNT_JSON=/path/to/service-account-key.json")
        print(f"\nOr place key at:")
        print(f"  ~/service-account-key.json")
        return 1

    # Import Google libraries
    try:
        from google.oauth2 import service_account
        from googleapiclient.discovery import build
        from googleapiclient.http import MediaFileUpload
    except ImportError:
        print("❌ Missing Google libraries. Install with:")
        print("   pip install google-auth-oauthlib google-auth-httplib2 google-api-python-client")
        return 1

    # Authenticate
    try:
        credentials = service_account.Credentials.from_service_account_file(
            SERVICE_ACCOUNT_JSON,
            scopes=['https://www.googleapis.com/auth/drive']
        )
        service = build('drive', 'v3', credentials=credentials)
    except Exception as e:
        print(f"❌ Authentication failed: {e}")
        return 1

    # Files to upload (the 3 newly generated documents)
    files_to_upload = [
        'InvitationLetter_Yanai_v2.docx',
        'InvitationLetter_Yanai_v2.pdf',
        'InvitationLetter_Suzuki_v2.docx',
        'InvitationLetter_Suzuki_v2.pdf',
        'InvitationLetter_Kawashima.docx',
        'InvitationLetter_Kawashima.pdf'
    ]

    print("\n" + "=" * 70)
    print("📤 Uploading Documents to Google Drive")
    print("=" * 70)
    print(f"\nFolder ID: {FOLDER_ID}")
    print(f"Folder URL: {drive_url}\n")

    uploaded = []
    failed = []

    for filename in files_to_upload:
        filepath = os.path.join(OUTPUT_DIR, filename)

        if not os.path.exists(filepath):
            print(f"⚠️  {filename} - FILE NOT FOUND")
            failed.append(filename)
            continue

        try:
            # Create file metadata
            file_metadata = {
                'name': filename,
                'parents': [FOLDER_ID]
            }

            # Upload file
            media = MediaFileUpload(filepath, resumable=True)
            request = service.files().create(
                body=file_metadata,
                media_body=media,
                fields='id, webViewLink, mimeType'
            )

            file = request.execute()
            file_id = file.get('id')
            file_url = file.get('webViewLink')

            print(f"✅ {filename}")
            print(f"   ID: {file_id}")
            print(f"   🔗 {file_url}")
            print()

            uploaded.append((filename, file_url))

        except Exception as e:
            print(f"❌ {filename} - ERROR: {str(e)[:80]}")
            failed.append(filename)

    # Summary
    print("=" * 70)
    print("📊 Upload Summary")
    print("=" * 70)
    print(f"✅ Uploaded: {len(uploaded)}/{len(files_to_upload)} files")

    if failed:
        print(f"❌ Failed: {len(failed)} files")
        for f in failed:
            print(f"   • {f}")
        return 1

    if uploaded:
        print(f"\n🎉 Success! All documents uploaded to Google Drive")
        print(f"\n📁 Folder: {drive_url}")
        print(f"\n📄 Documents:")
        for filename, url in uploaded:
            print(f"   • {filename}")

    return 0

if __name__ == '__main__':
    sys.exit(main())
