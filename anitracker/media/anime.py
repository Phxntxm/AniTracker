from __future__ import annotations
import json

import re
import subprocess
import sys
from dataclasses import dataclass
from datetime import date
from enum import Enum, auto
from typing import TYPE_CHECKING, Any, Dict, List, Optional, Tuple, Union

from anitracker import logger, frozen_path

if TYPE_CHECKING:
    from anitracker.sync import AniList

__all__ = (
    "UserStatus",
    "Anime",
    "AnimeStatus",
    "AnimeCollection",
    "AnimeFile",
    "SubtitleTrack",
)


class UserStatus(Enum):
    CURRENT = auto()
    PLANNING = auto()
    COMPLETED = auto()
    DROPPED = auto()
    PAUSED = auto()
    REPEATING = auto()


class AnimeStatus(Enum):
    FINISHED = auto()
    RELEASING = auto()
    NOT_YET_RELEASED = auto()
    CANCELLED = auto()
    HIATUS = auto()


ffprobe_cmd = "ffprobe"

if frozen_path is not None:
    if sys.platform.startswith("win32"):
        ffprobe_cmd = f"{frozen_path}\\ffprobe.exe"  # type: ignore
    elif sys.platform.startswith("linux"):
        ffprobe_cmd = f"{frozen_path}/ffprobe"  # type: ignore


def ffprobe_data(file: str) -> Dict:
    args = [ffprobe_cmd, "-show_format", "-show_streams", "-of", "json", file]
    logger.info(f"Running ffprobe command {args}")
    p = subprocess.Popen(
        args,
        stdout=subprocess.PIPE,
        stderr=subprocess.DEVNULL,
        stdin=subprocess.DEVNULL,
        shell=True,
    )
    out, _ = p.communicate()

    if p.returncode == 0:
        return json.loads(out.decode("utf-8"))
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
class Anime:
    id: int
    romaji_title: str
    english_title: str
    native_title: str
    preferred_title: str
    anime_status: AnimeStatus
    description: str
    anime_start_date: Union[date, None]
    anime_end_date: Union[date, None]
    episode_count: int
    average_score: int
    season: str
    genres: List[str]
    tags: List[Tuple[str, int]]
    studio: str
    cover_image: str

    def __repr__(self) -> str:
        return f"<Anime id={self.id} title={self.english_title}>"

    __str__ = __repr__

    def __hash__(self) -> int:
        return self.id

    def __eq__(self, o: object) -> bool:
        return isinstance(o, AnimeCollection) and self.id == o.id

    @property
    def titles(self) -> List[str]:
        return [self.english_title, self.romaji_title, self.native_title]

    @classmethod
    def from_data(cls, data: Dict) -> Anime:
        start = (
            date(**data["startDate"])
            if all(value for value in data["startDate"].values())
            else None
        )
        end = (
            date(**data["endDate"])
            if all(value for value in data["endDate"].values())
            else None
        )
        studios = [
            e["node"]["name"]
            for e in data["studios"]["edges"]
            if e["node"]["isAnimationStudio"]
        ]
        if studios:
            studio = studios[0]
        else:
            # Just get the first studio if we can't find an animation studio
            if data["studios"]["edges"]:
                studio = data["studios"]["edges"][0]
            else:
                studio = ""

        inst = cls(
            data["id"],
            data["title"]["romaji"] or "",
            data["title"]["english"] or "",
            data["title"]["native"] or "",
            data["title"]["userPreferred"] or "",
            AnimeStatus[data["status"]],
            data["description"],
            start,
            end,
            data["episodes"] or 0,
            data["averageScore"],
            f"{data['season']} {data['seasonYear']}",
            data["genres"],
            [
                (tag["name"], tag["rank"])
                for tag in data["tags"]
                if not tag["isMediaSpoiler"]
            ],
            studio,
            data["coverImage"]["large"],
        )

        return inst

    def edit(self, sync: AniList, *, status: UserStatus):
        sync.gql("update_entry", {"mediaId": self.id, "status": status.name})


@dataclass
class AnimeCollection(Anime):
    _list_id: int
    user_status: UserStatus
    score: float
    progress: int
    repeat: int
    updated_at: Union[date, None]
    notes: str
    user_start_date: Union[date, None]
    user_end_date: Union[date, None]

    def __repr__(self) -> str:
        return f"<AnimeCollection(id={self.id} user_status={self.user_status} title={self.english_title})>"

    __str__ = __repr__

    @classmethod
    def from_data(cls, data: Dict) -> AnimeCollection:
        start = (
            date(**data["media"]["startDate"])
            if all(value for value in data["media"]["startDate"].values())
            else None
        )
        end = (
            date(**data["media"]["endDate"])
            if all(value for value in data["media"]["endDate"].values())
            else None
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
        studios = [
            e["node"]["name"]
            for e in data["media"]["studios"]["edges"]
            if e["node"]["isAnimationStudio"]
        ]
        if studios:
            studio = studios[0]
        else:
            # Just get the first studio if we can't find an animation studio
            if data["media"]["studios"]["edges"]:
                studio = data["media"]["studios"]["edges"][0]
            else:
                studio = ""
        inst = cls(
            data["mediaId"],
            data["media"]["title"]["romaji"] or "",
            data["media"]["title"]["english"] or "",
            data["media"]["title"]["native"] or "",
            data["media"]["title"]["userPreferred"] or "",
            AnimeStatus[data["media"]["status"]],
            data["media"]["description"],
            start,
            end,
            data["media"]["episodes"] or 0,
            data["media"]["averageScore"],
            f"{data['media']['season']} {data['media']['seasonYear']}",
            data["media"]["genres"],
            [
                (tag["name"], tag["rank"])
                for tag in data["media"]["tags"]
                if not tag["isMediaSpoiler"]
            ],
            studio,
            data["media"]["coverImage"]["large"],
            data["id"],
            UserStatus[data["status"]],
            data["score"],
            data["progress"],
            data["repeat"],
            date.fromtimestamp(data["updatedAt"]) if data["updatedAt"] else None,
            data["notes"],
            user_start,
            user_end,
        )

        return inst

    def update_data(self, data: Dict):
        start = (
            date(**data["media"]["startDate"])
            if all(value for value in data["media"]["startDate"].values())
            else None
        )
        end = (
            date(**data["media"]["endDate"])
            if all(value for value in data["media"]["endDate"].values())
            else None
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
        studios = [
            e["node"]["name"]
            for e in data["media"]["studios"]["edges"]
            if e["node"]["isAnimationStudio"]
        ]
        if studios:
            studio = studios[0]
        else:
            # Just get the first studio if we can't find an animation studio
            if data["media"]["studios"]["edges"]:
                studio = data["media"]["studios"]["edges"][0]
            else:
                studio = ""

        self._list_id = data["id"]
        self.id = data["mediaId"]
        self.user_status = UserStatus[data["status"]]
        self.score = data["score"]
        self.progress = data["progress"]
        self.repeat = data["repeat"]
        self.updated_at = (
            date.fromtimestamp(data["updatedAt"]) if data["updatedAt"] else None
        )
        self.romaji_title = data["media"]["title"]["romaji"] or ""
        self.english_title = data["media"]["title"]["english"] or ""
        self.native_title = data["media"]["title"]["native"] or ""
        self.preferred_title = data["media"]["title"]["userPreferred"] or ""
        self.anime_status = AnimeStatus[data["media"]["status"]]
        self.description = data["media"]["description"]
        self.notes = data["notes"]
        self.anime_start_date = start
        self.anime_end_date = end
        self.user_start_date = user_start
        self.user_end_date = user_end
        self.episode_count = data["media"]["episodes"] or 0
        self.average_score = data["media"]["averageScore"]
        self.season = f"{data['media']['season']} {data['media']['seasonYear']}"
        self.genres = data["media"]["genres"]
        self.tags = [
            (tag["name"], tag["rank"])
            for tag in data["media"]["tags"]
            if not tag["isMediaSpoiler"]
        ]
        self.studio = studio

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
    episode_title: str
    file: str
    episode_number: int
    subtitles: List[SubtitleTrack]

    def __repr__(self) -> str:
        return f"<AnimeFile title={self.title} episode_number={self.episode_number}>"

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
            inst.episode_title = data.get("episode_title", "Unknown")
            inst.file = data["file_name"]
            inst.episode_number = int(_episode)
            inst.subtitles = []

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
