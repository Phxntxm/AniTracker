from datetime import date
from dataclasses import dataclass, fields
from typing import Dict, List, Union, Tuple

from anitracker.utilities import MediaStatus, UserStatus

# This will encompass everything any media has
@dataclass
class BaseMedia:
    id: int
    romaji_title: str
    english_title: str
    native_title: str
    preferred_title: str
    status: MediaStatus
    description: str
    start_date: Union[date, None]
    end_date: Union[date, None]
    average_score: int
    season: str
    genres: List[str]
    tags: List[Tuple[str, int]]
    studio: str
    cover_image: str

    @property
    def titles(self) -> List[str]:
        return [self.english_title, self.romaji_title, self.native_title]

    @classmethod
    def from_anilist(cls, data: Dict):
        return cls._from_dict(cls._transform_from_anilist(data))

    @classmethod
    def _from_dict(cls, data: Dict):
        _fields = [f.name for f in fields(cls)]
        vars = {key: value for key, value in data.items() if key in _fields}
        return cls(**vars)

    @staticmethod
    def _transform_from_anilist(data: Dict):
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

        return {
            "id": data["mediaId"],
            "romaji_title": data["media"]["title"]["romaji"] or "",
            "english_title": data["media"]["title"]["english"] or "",
            "native_title": data["media"]["title"]["native"] or "",
            "preferred_title": data["media"]["title"]["userPreferred"] or "",
            "status": MediaStatus[data["media"]["status"]],
            "description": data["media"]["description"],
            "start_date": start,
            "end_date": end,
            "episode_count": data["media"]["episodes"] or 0,
            "average_score": data["media"]["averageScore"],
            "season": f"{data['media']['season']} {data['media']['seasonYear']}",
            "genres": data["media"]["genres"],
            "tags": [
                (tag["name"], tag["rank"])
                for tag in data["media"]["tags"]
                if not tag["isMediaSpoiler"]
            ],
            "studio": studio,
            "cover_image": data["media"]["coverImage"]["large"],
            "_list_id": data["id"],
            "user_status": UserStatus[data["status"]],
            "score": data["score"],
            "progress": data["progress"],
            "repeat": data["repeat"],
            "updated_at": date.fromtimestamp(data["updatedAt"])
            if data["updatedAt"]
            else None,
            "notes": data["notes"],
            "user_start_date": user_start,
            "user_end_date": user_end,
            "chapters": data["media"]["chapters"],
            "volumes": data["media"]["volumes"],
        }


@dataclass
class BaseAnime(BaseMedia):
    episode_count: int


@dataclass
class BaseManga(BaseMedia):
    chapters: int
    volumes: int


# This one is just a mixin, it should not subclass the others directly
@dataclass
class BaseCollection:
    _list_id: int
    user_status: UserStatus
    score: float
    progress: int
    repeat: int
    updated_at: Union[date, None]
    notes: str
    user_start_date: Union[date, None]
    user_end_date: Union[date, None]
