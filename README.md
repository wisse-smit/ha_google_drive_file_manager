# Google Drive Media Integration for Home Assistant

This custom integration allows you to interact with Google Drive to upload media files, list files by pattern, and clean up older files matching a pattern directly from Home Assistant.

More functionality will be added later.

---

## Installation (Custom Repository)

1. In Home Assistant, go to **Settings ➔ Integrations**.
2. Click the **⋯** menu in the top-right corner and select **Custom repositories**.
3. In the **Add Custom Repository** dialog:

   * **Repository URL**: `https://github.com/wisse-smit/ha_google_drive_file_manager`
   * **Category**: **Integration**
4. Click **Add**. Home Assistant will fetch the repository and list the integration in HACS.
5. Go to **HACS ➔ Integrations**, find **Google Drive Media Integration**, and click **Install**.
6. Restart Home Assistant when prompted.

---

## Google Cloud: Setting Up the OAuth Consent Screen & Credentials

To use the integration, you need a Google OAuth Client ID and Secret. Follow these steps carefully:

### 1. Create a Google Cloud Project

1. Open [Google Cloud Console](https://console.cloud.google.com/).
2. Click the **Project** dropdown in the top bar and select **New Project**.
3. Give it a descriptive name (e.g., `Home Assistant Drive Integration`) and click **Create**.

### 2. Enable the Google Drive API

1. In the Cloud Console, navigate to **APIs & Services ➔ Library**.
2. Search for **Google Drive API** and click it.
3. Click **Enable**.

### 3. Configure the OAuth Consent Screen

1. Go to **APIs & Services ➔ OAuth consent screen**.
2. Under **User Type**, choose **External** and click **Create**.
3. Fill in the required fields:

   * **App name**: e.g., `Home Assistant Drive Integration`
   * **User support email**: your email address
   * **Developer contact email(s)**: your email address
4. Click **Save and Continue**.
5. **Scopes**: Click **Add or Remove Scopes**.

   * Filter by typing `drive`.
   * `https://www.googleapis.com/auth/drive`: Grants full, permissive scope to access all of a user’s files, needed to read all files and use all services.
   * Click **Update** and then **Save and Continue**.
6. **Test Users**: Add the Google account(s) you will use to authenticate (your own email).

   * Enter the email and click **Add**, then **Save and Continue**.
7. Review and click **Back to Dashboard**.

### 4. Create OAuth 2.0 Credentials

1. In **APIs & Services ➔ Credentials**, click **Create Credentials ➔ OAuth client ID**.
2. **Application type**: Select **Web application**.
3. **Name**: `Home Assistant Drive Auth` (or similar).
4. **Authorized redirect URIs**: Add the following Home Assistant callback URL:

   ```text
   https://my.home-assistant.io/redirect/oauth
   ```
5. Click **Create**.
6. Copy the **Client ID** and **Client secret**. You’ll need these in Home Assistant.

---

## Configuration in Home Assistant

1. In Home Assistant, go to **Settings ➔ Integrations**.
2. Click the **+ Add Integration** button and search for **Google Drive file manager**.
3. Enter the **Client ID** and **Client Secret** you obtained.
4. Follow the on-screen authentication flow to grant access to your Google Drive account.
5. Once completed, the integration will be added and you can start using its services.

---

## Services

Use these services in automations, scripts, or the Developer Tools ➔ Services UI.

Throughout the services specific files can be searched and queried. The queries have to be defined according to the structure used in the Google Drive API, examples and documentation can be found here: [Search for files and folders](https://developers.google.com/workspace/drive/api/guides/search-files).

When retrieving files, specific fields can also be set to be included in the output (for example: filename, file id, creation time etc.), all possible fields can be found here: [Google Drive files documentation](https://developers.google.com/workspace/drive/api/reference/rest/v3/fileshttps:/) in the 'fields' table.

Fields are always provided in a comma seperated string. Depending on the type of integration this string will be integrated in the full fields query.

### 1. `google_drive_file_manager.upload_media_file`

Upload a local media file to Drive.


| Parameter            | Type    | Required | Description                                                                                                                                               |
| ---------------------- | --------- | ---------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `local_file_path`    | string  | yes      | Path to the file on your Home Assistant host (e.g.,`/config/www/video.mp4`).                                                                              |
| `mime_type`          | string  | no       | MIME type of the file (e.g.,`video/mp4`). Auto-detected if omitted.                                                                                       |
| `remote_file_name`   | string  | no       | Filename to use in Drive. Defaults to the source file’s name.                                                                                            |
| `remote_folder_path` | string  | no       | Drive folder path (e.g.,`camera/outdoor`). Split the path by `/`. If the path does not exist, the folders will be created. Leave the path blank for root. |
| `save_to_sensor`     | boolean | no       | If`true`, write upload results to a sensor entity. State will be the filename, the attributes are the fields specified in the `fields` parameter.         |
| `sensor_name`        | string  | no       | Name of the sensor entity (defaults to`Google Drive uploaded file`).                                                                                      |
| `fields`             | string  | no       | Comma-separated Drive fields to return in the sensor (default:`id,name,webContentLink,webViewLink`).                                                      |

**Example**:

```yaml
service: google_drive_file_manager.upload_media_file
data:
  local_file_path: "/config/www/images/photo.jpg"
  remote_folder_path: "my_album"
  save_to_sensor: true
  sensor_name: "Drive Photo"
```

---

### 2. `google_drive_file_manager.cleanup_older_files_by_pattern`

Delete files matching a filename pattern older than *N* days in a Drive folder.


| Parameter        | Type    | Required | Description                                                                                                                                                                                                                  |
| ------------------ | --------- | ---------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| `pattern`        | string  | yes      | Query substring to match filenames (e.g.,`name contains 'outdoor'`).                                                                                                                                                         |
| `days_ago`       | integer | yes      | Minimum age in days; files modified more than this many days ago will be deleted.                                                                                                                                            |
| `preview`        | boolean | no       | This parameter allows you to test if your filter deletes the correct files. If`true`, only list matching files without deleting them. Enable the `save_to_sensor` parameter to store the preview results in a sensor entity. |
| `save_to_sensor` | boolean | no       | If`true`, write deletion results to a sensor entity.                                                                                                                                                                         |
| `sensor_name`    | string  | no       | Name of the sensor entity (defaults to`Latest deleted files`).                                                                                                                                                               |
| `fields`         | string  | no       | Comma-separated Drive fields to return in the sensor (default:`id,name,createdTime`).                                                                                                                                        |

**Example**:

```yaml
service: google_drive_file_manager.cleanup_older_files_by_pattern
data:
  pattern: "name contains 'outdoor'"
  days_ago: 30
  preview: true
  save_to_sensor: true
  sensor_name: Most recent deleted Google Drive files
  fields: id,name,createdTime
```

---

### 3. `google_drive_file_manager.list_files_by_pattern`

List files in a Drive folder matching a query and return them in a sensor entity.


| Parameter        | Type    | Required | Description                                                                                                                    |
| ------------------ | --------- | ---------- | -------------------------------------------------------------------------------------------------------------------------------- |
| `query`          | string  | yes      | Drive API query string (e.g.,`name contains 'backup'`).                                                                        |
| `sensor_name`    | string  | no       | Name of the sensor entity (default:`Google Drive files list`).                                                                 |
| `fields`         | string  | no       | Comma-separated Drive fields to return (default:`id,name`).                                                                    |
| `sort_by_recent` | boolean | no       | If`true`, sort results by modifiedTime descending (newest first). If `false` sort results by the name ascending (from A to Z). |
| `maximum_files`  | integer | no       | Max number of files to return (set to`0` for all matching files).                                                              |

**Example**:

```yaml
service: google_drive_file_manager.list_files_by_pattern
data:
  query: "name contains 'image_'"
  sort_by_recent: true
  maximum_files: 10
```

The output will be stored in the sensor entity where the state is the number of matched files, and the attributes a json, containing a files key with the list of files. Each file object has the fields specified in the `fields` parameter.

```json
{
  "files": [
    {"id": "...", "name": "image_1.png", "modifiedTime": "2025-05-15T12:34:56Z"},
    ...
  ]
}
```

---

For detailed usage, examples, and troubleshooting, please refer to the [Integration Documentation](https://github.com/yourusername/your-repo-name/blob/main/README.md).
