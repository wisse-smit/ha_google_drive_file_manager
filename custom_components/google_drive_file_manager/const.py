DOMAIN = "google_drive_file_manager"

# OAuth2 endpoints for Google
OAUTH2_AUTHORIZE = "https://accounts.google.com/o/oauth2/v2/auth"
OAUTH2_TOKEN = "https://oauth2.googleapis.com/token"

# Scope to read drive metadata
SCOPES = ["https://www.googleapis.com/auth/drive"]

# Default MIME type for media files
EXTENSION_MIME_MAP = {
    # Video
    "mp4":  "video/mp4",
    "mov":  "video/quicktime",
    "avi":  "video/x-msvideo",
    "mkv":  "video/x-matroska",
    "webm": "video/webm",
    "3gp":  "video/3gpp",
    "3g2":  "video/3gpp2",

    # Audio
    "mp3":  "audio/mpeg",
    "wav":  "audio/wav",
    "flac": "audio/flac",
    "ogg":  "audio/ogg",
    "m4a":  "audio/mp4",
    "aac":  "audio/aac",

    # Image
    "jpg":  "image/jpeg",
    "jpeg": "image/jpeg",
    "png":  "image/png",
    "gif":  "image/gif",
    "bmp":  "image/bmp",
    "tiff": "image/tiff",
    "svg":  "image/svg+xml",
    "webp": "image/webp",
}