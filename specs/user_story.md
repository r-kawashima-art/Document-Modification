# User Story

**As a**: representative from the administrative department
**I want to**: automate the process of changing the document in the designated format.
**So that**: I can avoid making mistakes in the modification and changing unnecesary fields.

## Detailed User Story

1. A person enters his or her peronal information in a slack channel.
2. The slack channel sends a request of approval to create the documents to the person in charge in another slack channel.
3. when the person permits the request, Claude Cowork creates the documents from the template, saving the outputs in designate local directories and Google Drive folders.
4. The slack channel sends the notification of completing creating the documents. 

## Acceptance Criteria

- Do not modify the line breaks of the original document.
- Do not change the fonts of the origianl document.
- The automation solution should be applicable to multiple styles of documents.

## Example

Inviatation Letter

Required fields for replacement:

- Name
- Date of birth
- Nationality
- Passport No.
- Passport issuing country
- Date of Issue
- Date of Expiry
- Mobile No.
