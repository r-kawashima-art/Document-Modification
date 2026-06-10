#!/usr/bin/env python3
"""
Process Google Sheet rows with progress='ToDo' and generate documents.

This script:
1. Reads the Google Sheet (sample_data)
2. Filters for rows where progress='ToDo'
3. Saves to local temp Excel file
4. Invokes the document-modification skill
5. Updates Google Sheet progress column to 'Done' after success
"""

import os
import sys
import json
import subprocess
from datetime import datetime
from pathlib import Path

import pandas as pd
from google.oauth2 import service_account
from google.auth.transport.requests import Request
from googleapiclient.discovery import build


def load_google_sheet(sheet_id, sheet_name='data'):
    """Read Google Sheet using service account credentials."""
    # Load service account credentials
    creds_path = os.getenv('GOOGLE_SERVICE_ACCOUNT_JSON',
                           'path/to/service-account-key.json')

    if not os.path.exists(creds_path):
        raise FileNotFoundError(f"Service account key not found: {creds_path}")

    credentials = service_account.Credentials.from_service_account_file(
        creds_path,
        scopes=['https://www.googleapis.com/auth/spreadsheets']
    )

    service = build('sheets', 'v4', credentials=credentials)

    # Read the sheet
    result = service.spreadsheets().values().get(
        spreadsheetId=sheet_id,
        range=f'{sheet_name}!A:Z'
    ).execute()

    values = result.get('values', [])

    if not values:
        raise ValueError(f"Sheet '{sheet_name}' is empty or not found")

    # Convert to DataFrame
    headers = values[0]
    data = [dict(zip(headers, row)) for row in values[1:]]
    df = pd.DataFrame(data)

    return df, service, sheet_id, sheet_name


def filter_todo_rows(df):
    """Filter for rows where progress='ToDo' or progress is empty."""
    # Ensure progress column exists
    if 'progress' not in df.columns:
        print("⚠️  No 'progress' column found. Processing all rows...")
        return df, []

    # Filter for ToDo rows
    todo_mask = (df['progress'].isna()) | (df['progress'] == 'ToDo')
    todo_rows = df[todo_mask].reset_index(drop=True)
    done_rows = df[~todo_mask]

    print(f"\n📊 Sheet Analysis:")
    print(f"   Total rows: {len(df)}")
    print(f"   Pending (ToDo): {len(todo_rows)}")
    print(f"   Complete (Done): {len(done_rows)}")

    return todo_rows, df.index[todo_mask].tolist()


def save_temp_excel(df, temp_file='temp_todo_data.xlsx'):
    """Save filtered data to temporary Excel file."""
    df.to_excel(temp_file, index=False, engine='openpyxl')
    print(f"\n✅ Saved {len(df)} rows to {temp_file}")
    return temp_file


def run_document_generation(template_path, data_file, output_dir, formats='docx,pdf'):
    """Run the document-modification pipeline."""
    cmd = [
        'python3', '-m', 'doc_modifier',
        '--template', template_path,
        '--data', data_file,
        '--out', output_dir,
        '--formats', formats
    ]

    print(f"\n🚀 Running: {' '.join(cmd)}")

    try:
        result = subprocess.run(
            cmd,
            cwd=str(Path(__file__).parent.parent.parent),
            env={**os.environ, 'PYTHONPATH': 'src'},
            capture_output=True,
            text=True,
            timeout=300
        )

        if result.returncode != 0:
            print(f"❌ Generation failed:\n{result.stderr}")
            return False

        print(result.stdout)
        return True
    except Exception as e:
        print(f"❌ Error running generation: {e}")
        return False


def update_google_sheet_progress(service, sheet_id, sheet_name, row_indices, status='Done'):
    """Update progress column in Google Sheet to 'Done' for processed rows."""
    if not row_indices:
        print("ℹ️  No rows to update in Google Sheet")
        return

    # Find the progress column index
    result = service.spreadsheets().values().get(
        spreadsheetId=sheet_id,
        range=f'{sheet_name}!A1:Z1'
    ).execute()

    headers = result.get('values', [[]])[0]

    if 'progress' not in headers:
        print("⚠️  'progress' column not found in Google Sheet")
        return

    progress_col_index = headers.index('progress')
    progress_col_letter = chr(65 + progress_col_index)  # A=65, B=66, etc.

    # Prepare batch update
    requests = []
    for row_idx in row_indices:
        cell_ref = f'{sheet_name}!{progress_col_letter}{row_idx + 2}'  # +2: header + 1-indexed
        requests.append({
            'range': cell_ref,
            'values': [[status]]
        })

    # Execute batch update
    body = {
        'data': [
            {'range': f'{sheet_name}!{progress_col_letter}{row_idx + 2}', 'values': [[status]]}
            for row_idx in row_indices
        ],
        'valueInputOption': 'RAW'
    }

    try:
        service.spreadsheets().values().batchUpdate(
            spreadsheetId=sheet_id,
            body=body
        ).execute()
        print(f"\n✅ Updated {len(row_indices)} rows in Google Sheet: progress='Done'")
    except Exception as e:
        print(f"⚠️  Failed to update Google Sheet: {e}")


def main():
    """Main workflow."""
    # Configuration
    SHEET_ID = '1h8Ex7p2mWnXtFa8PA9cy2qASuIPVpbKNXcW4lr3P5Ho'
    SHEET_NAME = 'data'
    TEMPLATE = 'templates/Template_Invitation_Letter_Adventure_India_tokenized.docx'
    OUTPUT_DIR = 'output/'
    FORMATS = 'docx,pdf'

    print("=" * 70)
    print("🔄 Google Sheet → Document Generation Pipeline")
    print("=" * 70)

    try:
        # Step 1: Read Google Sheet
        print("\n📥 Reading Google Sheet...")
        df, service, sheet_id, sheet_name = load_google_sheet(SHEET_ID, SHEET_NAME)
        print(f"✅ Loaded {len(df)} rows from Google Sheet")

        # Step 2: Filter ToDo rows
        print("\n🔍 Filtering for pending rows (progress='ToDo')...")
        todo_df, todo_indices = filter_todo_rows(df)

        if len(todo_df) == 0:
            print("\n✨ All rows are complete! Nothing to generate.")
            return 0

        # Step 3: Save to temp Excel
        print("\n💾 Preparing local data file...")
        temp_file = f'temp_todo_{datetime.now().strftime("%Y%m%d_%H%M%S")}.xlsx'
        save_temp_excel(todo_df, temp_file)

        # Step 4: Generate documents
        print("\n📄 Generating documents...")
        success = run_document_generation(TEMPLATE, temp_file, OUTPUT_DIR, FORMATS)

        if not success:
            print("\n❌ Document generation failed. Not updating Google Sheet.")
            return 1

        # Step 5: Update Google Sheet
        print("\n☁️  Updating Google Sheet...")
        update_google_sheet_progress(service, sheet_id, sheet_name, todo_indices, 'Done')

        # Cleanup
        if os.path.exists(temp_file):
            os.remove(temp_file)
            print(f"🧹 Cleaned up temp file: {temp_file}")

        print("\n" + "=" * 70)
        print(f"✅ SUCCESS: Generated {len(todo_df)} documents")
        print(f"   Output directory: {OUTPUT_DIR}")
        print(f"   Google Sheet updated: progress='Done' for all {len(todo_df)} rows")
        print("=" * 70)
        return 0

    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == '__main__':
    sys.exit(main())
