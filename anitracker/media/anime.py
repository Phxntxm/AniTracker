from __future__ import annotations

import json
import re
from subprocess import DEVNULL, PIPE
import sys
import tempfile
from dataclasses import dataclass
from datetime import date
from typing import TYPE_CHECKING, Any, Dict, List, Optional, Tuple, Union

from anitracker import logger, ffprobe_cmd, ffmpeg_cmd
from anitracker.media.media import BaseAnime, BaseCollection
from anitracker.utilities import UserStatus
from anitracker.utilities import subprocess

if TYPE_CHECKING:
    from anitracker.sync import AniList

__all__ = (
    "Anime",
    "AnimeCollection",
    "AnimeFile",
    "SubtitleTrack",
)


def ffprobe_data(file: str) -> Dict:
    args = [ffprobe_cmd, "-show_format", "-show_streams", "-of", "json", file]
    logger.info(f"Running ffprobe command {args}")
    # I hate windows
    stdin = None
    shell = False
    if sys.platform.startswith("win32"):
        stdin = DEVNULL
        shell = True

    out, _ = subprocess.run(
        args,
        stdout=PIPE,
        stdin=stdin,
        shell=shell,
    )

    if out:
        return json.loads(out)
    else:
        return {}


@dataclass
class NyaaResult:
    title: str
    link: str
    magnet: str
    size: str
    upload_date: str
    seeders: int
    leechers: int
    downloads: int

    def __repr__(self) -> str:
        return (
            f"<NyaaResult "
            "title={self.title} "
            "size={self.size} "
            "upload_date={self.upload_date} "
            "seeders={self.seeders} "
            "leechers={self.leechers} "
            "downloads={self.downloads}>"
        )

    __str__ = __repr__

    @classmethod
    def from_data(cls, result) -> NyaaResult:
        children = result.findAll("td")
        link = children[2].find("a", href=re.compile(r"^\/download\/.*$")).get("href")
        magnet = children[2].find("a", href=re.compile(r"^magnet:.*$")).get("href")

        return cls(
            children[1].find("a", href=re.compile(r"^/view/\d+$")).text,
            link,
            magnet,
            children[3].text,
            str(date.fromtimestamp(int(children[4]["data-timestamp"]))),
            int(children[5].text),
            int(children[6].text),
            int(children[7].text),
        )


@dataclass
class Anime(BaseAnime):
    def __repr__(self) -> str:
        return f"<Anime id={self.id} title={self.english_title}>"

    __str__ = __repr__

    def __hash__(self) -> int:
        return self.id

    def __eq__(self, o: object) -> bool:
        return isinstance(o, Anime) and self.id == o.id

    def edit(self, sync: AniList, *, status: UserStatus):
        sync.gql("update_entry", {"mediaId": self.id, "status": status.name})


@dataclass
class AnimeCollection(BaseCollection, Anime):
    def __repr__(self) -> str:
        return f"<AnimeCollection(id={self.id} user_status={self.user_status} title={self.english_title})>"

    __str__ = __repr__

    def edit(
        self,
        sync: AniList,
        *,
        status: Optional[UserStatus] = None,
        score: Optional[float] = None,
        progress: Optional[int] = None,
        repeat: Optional[int] = None,
        notes: Optional[str] = None,
        started_at: Optional[date] = None,
        completed_at: Optional[date] = None,
    ):
        payload: Dict[str, Any] = {"id": self._list_id}

        if status is not None:
            payload["status"] = status.name
        if score is not None:
            payload["score"] = score
        if progress is not None:
            payload["progress"] = progress
        if repeat is not None:
            payload["repeat"] = repeat
        if notes is not None:
            payload["notes"] = notes
        if completed_at is not None:
            payload["completedAt"] = {
                "year": completed_at.year,
                "month": completed_at.month,
                "day": completed_at.day,
            }
        if started_at is not None:
            payload["startedAt"] = {
                "year": started_at.year,
                "month": started_at.month,
                "day": started_at.day,
            }

        ret = sync.gql("update_entry", payload)
        self.update_user_data(ret["data"]["SaveMediaListEntry"])

    def update_user_data(self, data: Dict):
        self.user_status = UserStatus[data["status"]]
        self.score = data["score"]
        self.notes = data["notes"]
        self.progress = data["progress"]
        self.repeat = data["repeat"]
        self.updated_at = (
            date.fromtimestamp(data["updatedAt"]) if data["updatedAt"] else None
        )

        user_start = (
            date(**data["startedAt"])
            if all(value for value in data["startedAt"].values())
            else None
        )
        user_end = (
            date(**data["completedAt"])
            if all(value for value in data["completedAt"].values())
            else None
        )

        self.user_start_date = user_start
        self.user_end_date = user_end

    def delete(self, sync: AniList):
        sync.gql("delete_entry", {"id": self._list_id})


class AnimeFile:
    title: str
    season: int
    episode_title: str
    file: str
    episode_number: int
    subtitles: List[SubtitleTrack]
    alternate_title: Optional[str]
    _thumbnail: Optional[bytes]

    def __repr__(self) -> str:
        return f"<AnimeFile title={self.title} season={self.season} episode_number={self.episode_number}>"

    __str__ = __repr__

    @classmethod
    def from_data(cls, data: Dict) -> Union[List[AnimeFile], AnimeFile]:
        # TODO: Probably create my own parser, this fails on e.g.
        # [Samir755] Violet Evergarden - 05- You Write Letters That Bring People Together.mkv
        # (No space after the episode number)
        episode = data["episode"]

        def ret_file(_episode: str) -> AnimeFile:
            inst = cls()
            inst.title = data["anime_title"]
            inst.season = int(data.get("season", 1))
            inst.episode_title = data.get("episode_title", "Unknown")
            inst.alternate_title = data.get("alternate_title")
            inst.file = data["file_name"]
            inst.episode_number = int(_episode)
            inst.subtitles = []
            inst._thumbnail = None

            return inst

        # We want to return a list of files, one for each episode
        if isinstance(episode, list):
            results = []

            for ep in episode:
                results.append(ret_file(ep))

            return results
        elif isinstance(episode, str):
            return ret_file(episode)
        else:
            raise TypeError(
                f"Could not parse data, expected list or string as episode, got {type(episode)}"
            )

    @property
    def thumbnail(self):
        if self._thumbnail is None:
            with tempfile.NamedTemporaryFile(suffix=".jpg") as f:
                cmd = [
                    ffmpeg_cmd,
                    "-ss",
                    "00:03:30.00",
                    "-i",
                    self.file,
                    "-vframes",
                    "1",
                    "-y",
                    f.name,
                ]
                subprocess.run(cmd)
                f.seek(0)
                image = f.read()

            self._thumbnail = image

        return self._thumbnail

    def load_subtitles(self, standalone_subs: Dict[Tuple[str, int], str]):
        self.subtitles = []

        sub_id = 1

        for stream in ffprobe_data(self.file).get("streams", []):
            if stream["codec_type"] == "subtitle":
                # Insert the sub_id into the data
                stream["tags"]["id"] = sub_id
                self.subtitles.append(SubtitleTrack.from_data(stream))
                sub_id += 1

        # Now find all the matching standalone ones
        for (title, episode_number), track in standalone_subs.items():
            if title == self.title and episode_number == self.episode_number:
                self.subtitles.append(SubtitleTrack.from_file(track))


class SubtitleTrack:
    language: str
    title: str
    id: int
    file: Optional[str]

    def __repr__(self) -> str:
        return f"<SubtitleTrack lang='{self.language}' title='{self.title}'>"

    __str__ = __repr__

    @classmethod
    def from_data(cls, data: Dict):
        inst = cls()
        inst.language = data.get("tags", {}).get("language", "Unknown")
        inst.title = data.get("tags", {}).get("title", "Unknown")
        inst.id = data.get("tags", {}).get("id", 0)

        if "file_name" in data:
            inst.file = data["file_name"]
        else:
            inst.file = None

        return inst

    @classmethod
    def from_file(cls, file: str):
        data = ffprobe_data(file)["streams"][0]
        data["file_name"] = file
        return cls.from_data(data)

    @property
    def is_songs_signs(self) -> bool:
        """A convenience property that tries to guess if this subtitle track is
        just for songs and signs, based on the name"""
        return "songs" in self.title.lower() or "signs" in self.title.lower()
