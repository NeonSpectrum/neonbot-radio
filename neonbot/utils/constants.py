TIMEZONE = "Asia/Manila"
LOG_FORMAT = (
    "%(asctime)s [%(levelname)s] [%(module)s.%(funcName)s:%(lineno)d]: %(message)s"
)

YOUTUBE_TMP_DIR = "./tmp/youtube_dl"

PERMISSIONS = 3145728

ICONS = {
    "music": "https://i.imgur.com/SBMH84I.png",
}

FFMPEG_OPTIONS = (
    "-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5 -err_detect ignore_err"
)

YOUTUBE_REGEX = r"^(http(s)?:\/\/)?(((w){3}|music).)?youtu(be|.be)?(\.com)?\/.+"
SPOTIFY_REGEX = r"^(spotify:|https:\/\/[a-z]+\.spotify\.com\/)"

LOGO = """\
 __    _  _______  _______  __    _  _______  _______  _______
|  |  | ||       ||       ||  |  | ||  _    ||       ||       |
|   |_| ||    ___||   _   ||   |_| || |_|   ||   _   ||_     _|
|       ||   |___ |  | |  ||       ||       ||  | |  |  |   |
|  _    ||    ___||  |_|  ||  _    ||  _   | |  |_|  |  |   |
| | |   ||   |___ |       || | |   || |_|   ||       |  |   |
|_|  |__||_______||_______||_|  |__||_______||_______|  |___|
"""
