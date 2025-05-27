import voluptuous as vol
from homeassistant.helpers import config_validation as cv

# Define schemas for each service
SCHEMAS = {
    "list_mp4_files": vol.Schema({}),
    "upload_media_file": vol.Schema({
        vol.Required("local_file_path"): cv.string,
        vol.Required("mime_type", default="video/mp4"): cv.string,
        vol.Required("remote_file_name"): cv.string,
        vol.Optional("remote_folder_path", default=""): cv.string,
    }),
    "cleanup_drive_files": vol.Schema({
        vol.Required("pattern"): cv.string,
        vol.Required("days_ago"): cv.positive_int,
        vol.Optional("preview", default=False): cv.boolean,
    }),
    "list_files_by_pattern": vol.Schema({
        vol.Required("query"): cv.string,
        vol.Optional("fields", default="id,name"): cv.string,
        vol.Required("sensor_name"): cv.string,
    }),
}