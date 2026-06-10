#!/usr/bin/env python3
"""
Upload documents to Google Drive using MCP Google Drive connector.
This script prepares base64-encoded file content for MCP tool upload.
"""

import json
import base64
import os
from pathlib import Path

def main():
    # Load settings
    with open('settings/sample_data.json') as f:
        settings = json.load(f)

    import re
    folder_id_match = re.search(r'/folders/([a-zA-Z0-9-_]+)',
                               settings['output_Google_drive_directory'])
    folder_id = folder_id_match.group(1)

    # Files to upload
    files_to_upload = [
        ('InvitationLetter_Yanai_v2.docx', 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'),
        ('InvitationLetter_Yanai_v2.pdf', 'application/pdf'),
        ('InvitationLetter_Suzuki_v2.docx', 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'),
        ('InvitationLetter_Suzuki_v2.pdf', 'application/pdf'),
        ('InvitationLetter_Kawashima.docx', 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'),
        ('InvitationLetter_Kawashima.pdf', 'application/pdf'),
    ]

    print("\n" + "=" * 70)
    print("📤 Google Drive MCP Upload")
    print("=" * 70)
    print(f"\nFolder ID: {folder_id}")
    print(f"Drive URL: {settings['output_Google_drive_directory']}")
    print(f"Files to upload: {len(files_to_upload)}\n")

    # Prepare upload data for each file
    upload_commands = []

    for filename, mime_type in files_to_upload:
        filepath = os.path.join('output', filename)

        if not os.path.exists(filepath):
            print(f"❌ {filename} - NOT FOUND")
            continue

        # Read and encode file
        with open(filepath, 'rb') as f:
            file_content = f.read()
            base64_content = base64.b64encode(file_content).decode('utf-8')

        # Create MCP tool parameters
        params = {
            "title": filename,
            "parentId": folder_id,
            "base64Content": base64_content,
            "contentMimeType": mime_type,
            "disableConversionToGoogleType": True
        }

        upload_commands.append({
            'filename': filename,
            'params': params,
            'size_kb': len(file_content) / 1024
        })

        print(f"✅ {filename}")
        print(f"   Size: {len(file_content) / 1024:.1f} KB")
        print(f"   Base64: {len(base64_content)} chars")
        print(f"   MIME: {mime_type}")
        print()

    # Save upload parameters to JSON for reference
    with open('upload_params.json', 'w') as f:
        json.dump({
            'folder_id': folder_id,
            'files': [
                {
                    'filename': cmd['filename'],
                    'mime_type': cmd['params']['contentMimeType'],
                    'size_kb': cmd['size_kb'],
                    'base64_length': len(cmd['params']['base64Content'])
                }
                for cmd in upload_commands
            ]
        }, f, indent=2)

    print("=" * 70)
    print(f"✅ Prepared {len(upload_commands)} files for upload")
    print("=" * 70)
    print("\n🎯 Use MCP Google Drive create_file tool to upload:")
    print("   Tool: mcp__40760251-2bd6-4a82-bcbe-0c1ef903c907__create_file")
    print("   Parameters saved to: upload_params.json")
    print("\n📝 Upload parameters JSON:")

    # Print upload parameters in a clean format
    for cmd in upload_commands:
        print(f"\n{cmd['filename']}:")
        print(f"  title: {cmd['params']['title']}")
        print(f"  parentId: {cmd['params']['parentId']}")
        print(f"  contentMimeType: {cmd['params']['contentMimeType']}")
        print(f"  base64Content: [base64 string, {len(cmd['params']['base64Content'])} chars]")

    return upload_commands

if __name__ == '__main__':
    main()
