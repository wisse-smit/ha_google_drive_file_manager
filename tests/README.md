To setup the testing, we first need to set up authentication to Google Drive. A virtual environment needs to be created and the requirements need to be installed. All the steps will be outlined below:

1. Create a virtual environment in the root level, go to terminal:

   ```
   python3 -m venv venv
   ```
2. After setting up the virtual environment, activate it

   ```
   Linux: source venv/bin/activate
   Windows: venv/Scripts/activate
   ```
3. Install the requirements in the virtual environment

   ```
   pip install -r tests/requirements.txt
   ```
4. Go to *Google Cloud console > APIs and Services > Clients > OAuth 2.0 Client IDs > Your Google Drive client* and add 'http://localhost:8000' in the authorized return uri.
5. Create a .env file at root level
6. In the .env file put the following template:

   ```
   # Set these yourself from Google Cloud Console

   GOOGLE_DRIVE_CLIENT_ID="<Get from Google Cloud Console>"
   GOOGLE_DRIVE_CLIENT_SECRET="<Get from Google Cloud Console>"

   # Copy these in after running the 'Get Google Credentials' launch configuration
   # Make sure you set the correct authorized return uri: http://localhost:8000

   GOOGLE_DRIVE_ACCESS_TOKEN="<Run get_google_drive_auth_details.py using the 'Get Google credentials' in the debugger and place them here>"
   GOOGLE_DRIVE_REFRESH_TOKEN="<Run get_google_drive_auth_details.py using the 'Get Google credentials' in the debugger and place them here>"

   ```
7. Run the get_google_drive_auth_details.py using the 'Get Google credentials' configuration in the debugger. Login using your Google Drive account. The access and refresh token will be printed. Update the values in the .env file.
8. Now, when (in the virtual environment) you run 'pytest -q', the test_services.py will be run, and the output of the tests will be shown in the terminal.

