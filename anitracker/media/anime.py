from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date
from enum import Enum, auto
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Union, TYPE_CHECKING

if TYPE_CHECKING:
    from anitracker.sync import AniList


import anitopy

from PySide6.QtWidgets import QProgressBar

__all__ = ("UserStatus", "AnimeStatus", "AnimeCollection", "AnimeFile", "SubtitleTrack")


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


@dataclass
class AnimeCollection:
    _list_id: int
    id: int
    user_status: UserStatus
    score: float
    progress: int
    repeat: int
    updated_at: Union[date, None]
    romaji_title: str
    english_title: str
    native_title: str
    preferred_title: str
    anime_status: AnimeStatus
    description: str
    notes: str
    anime_start_date: Union[date, None]
    anime_end_date: Union[date, None]
    user_start_date: Union[date, None]
    user_end_date: Union[date, None]
    episode_count: int
    average_score: int
    season: str
    genres: List[str]
    tags: List[Tuple[str, int]]
    studio: str
    episodes: Dict[int, AnimeFile] = field(default_factory=dict)

    def __repr__(self) -> str:
        return f"<AnimeCollection(id={self.id} user_status={self.user_status} title={self.english_title})>"

    __str__ = __repr__

    def __hash__(self) -> int:
        return self.id

    def __eq__(self, o: object) -> bool:
        return isinstance(o, AnimeCollection) and self.id == o.id

    @property
    def missing_eps(self) -> str:
        missing = [
            str(i + 1) for i in range(self.episode_count) if i + 1 not in self.episodes
        ]
        return ", ".join(missing)

    @property
    def progress_bar(self) -> QProgressBar:
        bar = QProgressBar()
        bar.setMinimum(0)
        bar.setMaximum(self.episode_count)
        bar.setValue(self.progress)
        bar.setFormat("%v/%m")

        return bar

    @property
    def titles(self) -> List[str]:
        return [self.english_title, self.romaji_title, self.native_title]

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
                studio = None
        inst = cls(
            data["id"],
            data["mediaId"],
            UserStatus[data["status"]],
            data["score"],
            data["progress"],
            data["repeat"],
            date.fromtimestamp(data["updatedAt"]) if data["updatedAt"] else None,
            data["media"]["title"]["romaji"],
            data["media"]["title"]["english"],
            data["media"]["title"]["native"],
            data["media"]["title"]["userPreferred"],
            AnimeStatus[data["media"]["status"]],
            data["media"]["description"],
            data["notes"],
            start,
            end,
            user_start,
            user_end,
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
                studio = None

        self._list_id = data["id"]
        self.id = data["mediaId"]
        self.user_status = UserStatus[data["status"]]
        self.score = data["score"]
        self.progress = data["progress"]
        self.repeat = data["repeat"]
        self.updated_at = (
            date.fromtimestamp(data["updatedAt"]) if data["updatedAt"] else None
        )
        self.romaji_title = data["media"]["title"]["romaji"]
        self.english_title = data["media"]["title"]["english"]
        self.native_title = data["media"]["title"]["native"]
        self.preferred_title = data["media"]["title"]["userPreferred"]
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
        payload = {"id": self._list_id}

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

    def update_episode(self, file: AnimeFile):
        self.episodes[file.episode_number] = file


class AnimeFile:
    title: str
    episode_title: str
    file: str
    episode_number: int
    subtitles: List[SubtitleTrack]

    @classmethod
    def from_data(cls, data: Dict):
        fullpath = Path(data["format"]["filename"])
        # TODO: Probably create my own parser, this fails on e.g.
        # [Samir755] Violet Evergarden - 05- You Write Letters That Bring People Together.mkv
        # (No space after the episode number)
        parsed_data = anitopy.parse(fullpath.name)

        inst = cls()
        inst.title = parsed_data.get("anime_title", "Unknown")
        inst.episode_title = parsed_data.get("episode_title", "Unknown")
        inst.episode_number = int(parsed_data.get("episode_number", 0))
        inst.file = data["format"]["filename"]
        inst.subtitles = []

        sub_id = 1

        for stream in data["streams"]:
            if stream["codec_type"] == "subtitle":
                # Insert the sub_id into the data
                stream["tags"]["id"] = sub_id
                inst.subtitles.append(SubtitleTrack.from_data(stream))
                sub_id += 1

        return inst


class SubtitleTrack:
    language: str
    title: str
    id: int

    @classmethod
    def from_data(cls, data: Dict):

        inst = cls()
        inst.language = data["tags"].get("language", "Unknown")
        inst.title = data["tags"].get("title", "Unknown")
        inst.id = data["tags"]["id"]

        return inst

    @property
    def is_songs_signs(self) -> bool:
        """A convenience property that tries to guess if this subtitle track is
        just for songs and signs, based on the name"""
        return "songs" in self.title.lower() or "signs" in self.title.lower()
