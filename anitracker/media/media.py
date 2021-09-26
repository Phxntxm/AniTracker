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
        print(data)
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

        return {
            "id": data["id"],
            "romaji_title": data["title"]["romaji"] or "",
            "english_title": data["title"]["english"] or "",
            "native_title": data["title"]["native"] or "",
            "preferred_title": data["title"]["userPreferred"] or "",
            "status": MediaStatus[data["status"]],
            "description": data["description"],
            "start_date": start,
            "end_date": end,
            "episode_count": data["episodes"] or 0,
            "average_score": data["averageScore"],
            "season": f"{data['season']} {data['seasonYear']}",
            "genres": data["genres"],
            "tags": [
                (tag["name"], tag["rank"])
                for tag in data["tags"]
                if not tag["isMediaSpoiler"]
            ],
            "studio": studio,
            "cover_image": data["coverImage"]["large"],
            "chapters": data["chapters"],
            "volumes": data["volumes"],
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

    @staticmethod
    def _transform_from_anilist(data: Dict):
        base = BaseMedia._transform_from_anilist(data["media"])

        start = (
            date(**data["startedAt"])
            if all(value for value in data["startedAt"].values())
            else None
        )
        end = (
            date(**data["completedAt"])
            if all(value for value in data["completedAt"].values())
            else None
        )

        base.update(
            {
                "_list_id": data["id"],
                "user_status": UserStatus[data["status"]],
                "score": data["score"],
                "progress": data["progress"],
                "repeat": data["repeat"],
                "updated_at": date.fromtimestamp(data["updatedAt"])
                if data["updatedAt"]
                else None,
                "notes": data["notes"],
                "user_start_date": start,
                "user_end_date": end,
            }
        )

        return base
