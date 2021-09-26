from __future__ import annotations

from pathlib import Path
from typing import (
    TYPE_CHECKING,
    Dict,
    Generator,
    Iterator,
    List,
    Optional,
    Tuple,
    Union,
)

import requests
from aniparser import parse
from bs4 import BeautifulSoup as bs
from bs4.element import Tag
from rapidfuzz import fuzz

from anitracker import user_agent, logger
from anitracker.config import Config
from anitracker.media import AnimeCollection, AnimeFile, MangaCollection
from anitracker.media.anime import NyaaResult
from anitracker.sync import AniList
from anitracker.player import Player

if TYPE_CHECKING:
    from anitracker.__main__ import MainWindow

    EPISODE_MATCH_TYPE = Dict[int, List[Tuple[AnimeFile, int]]]

video_file_extensions = [
    "webm",
    "mkv",
    "flv",
    "flv",
    "vob",
    "ogv",
    "ogg",
    "drc",
    "gif",
    "gifv",
    "mng",
    "avi",
    "mts",
    "m2ts",
    "ts",
    "mov",
    "qt",
    "wmv",
    "yuv",
    "rm",
    "rmvb",
    "viv",
    "asf",
    "amv",
    "mp4",
    "m4p",
    "m4v",
    "mpg",
    "mp2",
    "mpeg",
    "mpe",
    "mpv",
    "mpg",
    "mpeg",
    "m2v",
    "m4v",
    "svi",
    "3gp",
    "3g2",
    "mxf",
    "roq",
    "nsv",
    "flv",
    "f4v",
    "f4p",
    "f4a",
    "f4b",
]
subtitle_file_extensions = ["ass", "cmml", "lrc", "sami", "ttml", "srt", "ssa", "usf"]


class AniTracker:
    def __init__(self) -> None:
        self._config = Config()
        self._animes: Dict[int, AnimeCollection] = {}

        self._anilist = AniList()
        self._episodes: List[AnimeFile] = []
        self.standalone_subtitles: Dict[Tuple[str, int], str] = {}
        self._anilist.from_config(self._config)

    @property
    def animes(self) -> Dict[int, AnimeCollection]:
        return self._animes.copy()

    # I'm lazy and have to test things a lot
    @classmethod
    def _test_setup(cls):
        inst = cls()
        inst._anilist.verify()
        inst._refresh_anime_folder()
        inst.refresh_from_anilist()
        return inst

    def missing_eps(self, anime: AnimeCollection) -> str:
        have = [ep.episode_number for ep in self.get_episodes(anime)]
        missing = [f"{n}" for n in range(1, anime.episode_count + 1) if n not in have]

        return ", ".join(missing)

    def get_anime(
        self,
        title: str = "",
        *,
        id: Union[int, None] = None,
        exact_name_match: bool = False,
    ) -> Union[AnimeCollection, None]:
        if id is not None:
            return self._animes[id]
        # If there's no title, just return None
        if not title:
            return None

        # Now loop through all the names
        for anime in self.animes.values():
            if exact_name_match:
                if self._anime_is_title(title, anime, ratio=100):
                    return anime
            else:
                if self._anime_is_title(title, anime):
                    return anime

        return None

    def remove_anime(self, id: int):
        del self._animes[id]

    def refresh_from_anilist(self):
        # First get all the media
        logger.debug(f"Retrieving info from anilist")
        animes = self._anilist.get_anime()
        mangas = self._anilist.get_manga()

        _animes: Dict[int, AnimeCollection] = {}
        _mangas: Dict[int, MangaCollection] = {}

        # The lists are separated by status
        for l in animes["data"]["MediaListCollection"]["lists"]:
            for entry in l["entries"]:
                _animes[entry["id"]] = AnimeCollection.from_anilist(entry)
        for l in mangas["data"]["MediaListCollection"]["lists"]:
            for entry in l["entries"]:
                _mangas[entry["id"]] = MangaCollection.from_anilist(entry)

        self._animes = _animes
        self._mangas = _mangas

    def get_episodes(self, anime: AnimeCollection) -> List[AnimeFile]:

        episodes = list(self._cull_episodes_for_anime(anime).values())

        # Sort it for ease of use
        episodes.sort(key=lambda e: e.episode_number)

        return episodes

    def get_episode(
        self, anime: AnimeCollection, episode_num: int
    ) -> Optional[AnimeFile]:
        episodes = self._cull_episodes_for_anime(anime, episode_num=episode_num)

        return episodes.get(episode_num)

    def play_episode(
        self, anime: AnimeCollection, episode_num: int, window: MainWindow
    ):
        episode = self.get_episode(anime, episode_num)

        if episode is None:
            raise TypeError(f"Could not find episode {episode_num} for {anime}")

        player = Player(anime, [episode], self, window)
        player.start()

    def start_playlist(
        self, anime: AnimeCollection, starting_episode: int, window: MainWindow
    ):
        """Starts a playlist for an anime from this episode on"""
        episodes = [
            ep
            for ep in self.get_episodes(anime)
            if ep.episode_number >= starting_episode
        ]
        episodes.sort(key=lambda e: e.episode_number)

        player = Player(anime, episodes, self, window)
        player.start()

    def _episode_is_from_anime(
        self, episode: AnimeFile, anime: AnimeCollection, *, ratio: int = 80
    ) -> bool:
        """Compares an episode to an anime's titles, using a fuzzy match to try for best
        possibility of matching. This also will check all the titles of an anime"""
        # First if this ain't the right season, don't compare
        for _title in anime.titles:
            if fuzz.ratio(episode.title, _title, processor=True) >= ratio:
                return True
            if (
                episode.alternate_title
                and fuzz.ratio(episode.alternate_title, _title, processor=True) >= ratio
            ):
                return True

        return False

    def _anime_is_title(
        self, title: str, anime: AnimeCollection, *, ratio: int = 80
    ) -> bool:
        """Compares an anime to an episode's titles, using a fuzzy match to try for best
        possibility of matching. This also will check all the titles of an anime"""
        for _title in anime.titles:
            if fuzz.ratio(title, _title, processor=True) >= ratio:
                return True

        return False

    def _refresh_anime_folder(self):
        try:
            dir = Path(self._config["animedir"]).expanduser()
        # No config setup for user, can't get anime
        except (KeyError, TypeError):
            return

        logger.info(f"Reloading anime folder: {dir}")
        # Clear the dict
        self._episodes.clear()
        # Search through directory
        self._episodes = list(self._probe_dir(dir))

    def _probe_dir(self, path: Path) -> Generator[AnimeFile, None, None]:
        # Look at every file in the path
        for file in path.rglob("*"):
            # Ignore directories, recursion is handled by rglob
            if file.is_dir():
                continue

            data = parse(file)
            # Skip if it doesn't match the format for anime
            if not data["is_anime"]:
                continue
            # Assume it's a movie
            if "episode" not in data:
                data["episode"] = "1"

            # If it's a video file just yield it
            if data.get("extension", "").lower() in video_file_extensions:
                result = AnimeFile.from_data(data)
                if isinstance(result, list):
                    for r in result:
                        yield r
                elif isinstance(result, AnimeFile):
                    yield result
            # Otherwise if it's a subtitle track, store it
            if data.get("extension", "").lower() in subtitle_file_extensions:
                self.standalone_subtitles[
                    (data["anime_title"], int(data["episode"]))
                ] = str(file)

    def _cull_episodes_for_anime(
        self,
        anime: AnimeCollection,
        *,
        episode_num: Optional[int] = None,
    ) -> Dict[int, AnimeFile]:
        culled: Dict[int, AnimeFile] = {}
        episodes = self._episodes_for_anime(anime, episode_num=episode_num)

        # Loop through each episode number we have available
        for ep_num, episodes_for_num in episodes.items():
            # This is our culled episodes for this episode number
            _culled_eps: List[AnimeFile] = []
            # Track the largest ratio that's been found
            _largest: int = 0

            # Now this is the main reason why this is needed... animes aren't
            # really in "seasons" like western shows. However, since this is what
            # people are used to... this is how the files are labelled. I can't
            # MATCH that against any data since animes aren't really saved that way.
            # If a season 2 of an anime has a different title, then the initial fuzzy
            # matching should resolve that any way, and I shouldn't even have to worry.
            # However there are many animes that are Anime Part 1, Anime Part 2, etc.
            # This culling helps with that. By appending the number to the title and
            # checking for a difference

            # Loop through the episodes
            for ep, _ in episodes_for_num:
                # Track the largest ratio for this episode
                _largest_for_ep: int = 0

                for _title in anime.titles:
                    ratio: int = fuzz.ratio(_title, f"{ep.title} {ep.season}")
                    alt_ratio: int = (
                        fuzz.ratio(_title, f"{ep.alternate_title} {ep.season}")
                        if ep.alternate_title
                        else 0
                    )

                    # Get the highest of the two
                    largest = max(ratio, alt_ratio)

                    # Now we just need to find the largest ratio for this episode
                    if largest > _largest_for_ep:
                        _largest_for_ep = largest

                # If we find a new largest ratio, clear the list and append this episode to it
                if _largest_for_ep > _largest:
                    _largest = _largest_for_ep
                    _culled_eps.clear()
                    _culled_eps.append(ep)
                # Otherwise append (so we get all files that are the exact same ratio)
                # later culling will handle exact matches that are still happening
                # which realistically *should* only be for season 1 of animes. If not...
                # then idfk, maybe the title between season 1 and 2 is the exact fuckin same?
                # If that's happening what can I really do

                elif _largest_for_ep == _largest:
                    _culled_eps.append(ep)

            # If our culling worked...great, this should be what happens most of the time
            if len(_culled_eps) == 1:
                culled[ep_num] = _culled_eps[0]
            # I don't see how it would be possible to have a situation where NONE are
            # returned, but just in case lets make sure there are more
            elif len(_culled_eps) > 1:
                # Now there's two situations we could have...
                # say we have these two animes/episodes:
                # Ascendance of a Bookworm (episode 1)
                # Ascendance of a Bookworm Part 2 (episode 1)
                # Now in the files this will end up being just called
                # Ascendance of a Bookworm S02E01 or some shit, 9/10 times.
                # For the second season's (or realistically any season but the first)
                # episode, our culling should have fixed this
                # but for the first.. it won't have. That's because the fuzzy match of
                # Anime 1 -> Anime | Anime 2 -> Anime will be the exact same ratio
                # Side note... the above point is exactly why it's safe to actually
                # do this without much of a worry. Any thing we're NOT trying to cull here
                # should really not be affected by any of this

                # So that's what we check next here
                # if only one of them is for season 1, prioritize that
                _second_culling: List[AnimeFile] = []
                _third_culling: List[AnimeFile] = []

                for ep in _culled_eps:
                    if ep.season == 1:
                        _second_culling.append(ep)

                # Now check this, if this only has one episode... it worked
                if len(_second_culling) == 1:
                    culled[ep_num] = _second_culling[0]
                # Otherwise there's really only one more guess I have, is that
                # this is "The movie" for an anime. This is pretty common that it's
                # called something like this
                else:
                    best_guess = None
                    # If this anime is a movie:
                    if anime.episode_count == 1:
                        # Try to find one that is a movie
                        for ep in _second_culling:
                            # Try to make a guess as to if this is a movie or not
                            if (
                                fuzz.ratio(
                                    ep.episode_title, "The Movie", processor=True
                                )
                                >= 85
                            ):
                                best_guess = ep
                    # Otherwise this isn't a movie, we want to now REMOVE any that are movies
                    else:
                        for ep in _second_culling:
                            if (
                                fuzz.ratio(
                                    ep.episode_title, "The Movie", processor=True
                                )
                                < 85
                            ):
                                _third_culling.append(ep)

                    # If we found a movie for our movie, use that
                    if best_guess is not None:
                        culled[ep_num] = best_guess
                    # Now... this is all the guesses I have as to why there may be no difference,
                    # try to get the first one if it exists otherwise... who knows man
                    elif _third_culling:
                        culled[ep_num] = _third_culling[0]
                    elif _second_culling:
                        culled[ep_num] = _second_culling[0]
                    # If we don't have any in either, then no idea

        return culled

    def _episodes_for_anime(
        self, anime: AnimeCollection, *, episode_num: Optional[int] = None
    ) -> EPISODE_MATCH_TYPE:
        """This is a naive method, it does a fuzzy match to see if
        it thinks the episode matches the anime. It returns a dict of
        episode number: tuples of the episode
        and the ratio that fuzzy matching returned

        If the episode kwarg is provided then this will only match for episodes
        of that number"""
        ret: EPISODE_MATCH_TYPE = {}

        for episode in self._episodes:
            # If we've specified the number to find, and this isn't that skip
            if episode_num is not None and episode_num != episode.episode_number:
                continue
            # Also skip if this episode number is higher than the max for this season
            if episode.episode_number > anime.episode_count:
                continue

            best_match: Optional[Tuple[AnimeFile, int]] = None

            for _title in anime.titles:
                # Get the ratio for both possible anime titles
                ratio: int = fuzz.ratio(_title, episode.title)
                alt_ratio: int = (
                    fuzz.ratio(_title, episode.alternate_title)
                    if episode.alternate_title
                    else 0
                )

                # Get the highest of the two
                largest = max(ratio, alt_ratio)

                # If it is over 80% then it's a "match"
                if largest >= 80:
                    # Make sure not to override the best match
                    if best_match and best_match[1] > largest:
                        best_match = (episode, largest)
                    elif best_match is None:
                        best_match = (episode, largest)

            if best_match is not None:
                if episode.episode_number not in ret:
                    ret[episode.episode_number] = []

                ret[episode.episode_number].append(best_match)

        return ret

    def search_nyaa(self, query: str) -> Iterator[NyaaResult]:
        url = "https://nyaa.si/"
        params = {"f": 0, "c": "0_0", "q": query, "s": "seeders", "o": "desc"}
        headers = {"User-Agent": user_agent}

        with requests.get(url, params=params, headers=headers) as r:
            soup = bs(r.text, features="html.parser")
            body = soup.find("tbody")

            if isinstance(body, Tag):
                for result in body.findAll("tr"):
                    yield NyaaResult.from_data(result)
