from __future__ import unicode_literals

import os
import shutil
import time
from random import randint

from .api_photo import get_image_size, stories_shaper, rupload_igphoto


def download_story(self, filename, story_url, username):
    path = "stories/{}".format(username)
    if not os.path.exists(path):
        os.makedirs(path)
    fname = os.path.join(path, filename)
    if os.path.exists(fname):  # already exists
        self.logger.info("Stories already downloaded...")
        return os.path.abspath(fname)
    response = self.session.get(story_url, stream=True)
    if response.status_code == 200:
        with open(fname, "wb") as f:
            response.raw.decode_content = True
            shutil.copyfileobj(response.raw, f)
        return os.path.abspath(fname)


def upload_story_photo(self, photo, upload_id=None, options={}):
    options = dict({"configure_timeout": 15, "rename": True}, **(options or {}))
    photo = stories_shaper(photo)

    upload_id = rupload_igphoto(self.session, photo, upload_id=upload_id)
    if type(upload_id) == bool:
        return upload_id

    configure_timeout = options.get("configure_timeout")
    for attempt in range(4):
        if configure_timeout:
            time.sleep(configure_timeout)

        if self.configure_story(upload_id, photo):
            media = self.last_json.get("media")
            self.expose()
            if options.get("rename"):
                os.rename(photo, "{fname}.REMOVE_ME".format(fname=photo))
            return media
    return False


def configure_story(self, upload_id, photo):
    (w, h) = get_image_size(photo)
    data = self.json_data(
        {
            "source_type": 4,
            "upload_id": upload_id,
            "story_media_creation_date": str(int(time.time()) - randint(11, 20)),
            "client_shared_at": str(int(time.time()) - randint(3, 10)),
            "client_timestamp": str(int(time.time())),
            "configure_mode": 1,  # 1 - REEL_SHARE, 2 - DIRECT_STORY_SHARE
            "device": self.device_settings,
            "edits": {
                "crop_original_size": [w * 1.0, h * 1.0],
                "crop_center": [0.0, 0.0],
                "crop_zoom": 1.3333334,
            },
            "extra": {"source_width": w, "source_height": h},
        }
    )
    return self.send_request("media/configure_to_story/?", data)
