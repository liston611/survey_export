# survey_export tool

## Description
survey_export is a project used to query, organize, backup, compress, syncronize, and clean remote data attachements in AGOL.

## Files
**1. main.py**\
Creates GUI that calls functions from functions_export_multithread.py\
**2. functions_export_multithread.py**\
Contains functions allowing a user to query, backup, and delete AGOL attachments\
**3. environment.yml**\
File to set up conda myenv\
**4. abbr_rename.py**\
Simple utility used to modify folder/file names

## Folders
**1. specialized**\
Contains some some forks of functions_export used for certain AGOL layers with different table structures.\
**2. test**\
Test versions (at the moment contains a beta test for IWA authentication).\
