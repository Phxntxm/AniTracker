from dataclasses import dataclass

from anitracker.media.media import BaseManga, BaseCollection


# The BaseManga is just our base dataclass, this is where modifying stuff will go


@dataclass
class Manga(BaseManga):
    pass


@dataclass
class MangaCollection(Manga, BaseCollection):
    pass
