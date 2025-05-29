import voluptuous as vol
from homeassistant.helpers import config_validation as cv

# Define schemas for each service
SCHEMAS = {
    "upload_media_file": vol.Schema({
        vol.Required("local_file_path"): cv.string,
        vol.Optional("mime_type", default =""): cv.string,
        vol.Optional("remote_file_name", default =""): cv.string,
        vol.Optional("remote_folder_path", default=""): cv.string,
        vol.Optional("save_to_sensor", default=False): cv.boolean,
        vol.Optional("sensor_name", default="Latest uploaded file"): cv.string,
        vol.Optional("fields", default="id,name,webViewLink,webContentLink"): cv.string,
    }),
    "cleanup_older_files_by_pattern": vol.Schema({
        vol.Required("pattern"): cv.string,
        vol.Required("days_ago"): cv.positive_int,
        vol.Optional("preview", default=False): cv.boolean,
        vol.Optional("save_to_sensor", default=False): cv.boolean,
        vol.Optional("sensor_name", default="Latest deleted files"): cv.string,
        vol.Optional("fields", default="id,name,createdTime"): cv.string,
    }),
    "list_files_by_pattern": vol.Schema({
        vol.Required("query"): cv.string,
        vol.Optional("sensor_name", default="List files"): cv.string,
        vol.Optional("fields", default="id,name,createdTime"): cv.string,
        vol.Optional("sort_by_recent", default=True): cv.boolean,
        vol.Optional("maximum_files", default=0): cv.positive_int,
    }),
}