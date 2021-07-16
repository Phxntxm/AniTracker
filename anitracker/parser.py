import functools
import re
from rapidfuzz import fuzz
from pathlib import Path
from typing import Any, Dict, Pattern, TypedDict, List, Union

# Here's all our different regex patterns
EPISODE_REGEX = re.compile(
    r"(?:[^a-z0-9()\[\]])(s(?P<season>\d+))?((e|sp|ep)|(?P<season2>\d+)x)?(?P<episode>\d+)(?![a-uw-z0-9()])[.\-]*",
    flags=re.IGNORECASE,
)
RESOLUTION_REGEX = re.compile(
    r"(?P<pos_height>\d{3,4})([p]|[x\u00D7](?P<height>\d{3,4}))|\[(?P<alone_height>\d{3,4})\]",
    flags=re.IGNORECASE,
)
CHECKSUM_REGEX = re.compile(
    r"[ -]?[\[(](?P<checksum>[A-Fa-f0-9]{8})[\])][ -]?", flags=re.IGNORECASE
)
BRACKET_TERMS_REGEX = re.compile(r"\[(?P<terms>[\w \-_.]*)\]", flags=re.IGNORECASE)
YEAR_REGEX = re.compile(r"[\[\( \-](?P<year>\d{4})[\]\) \-]", flags=re.IGNORECASE)
EXTENSION_REGEX = re.compile(r"(\.(?:(?:[a-z]+)|\[\w+\]))")
RELEASE_VERSION_REGEX = re.compile(r"(?P<release>v\d+)", flags=re.IGNORECASE)
RELEASE_GROUP_REGEX = re.compile(r"[\[\(](?P<release_group>[\w\s\- ]+)[\]\)]")
EMPTY_BRACKETS_REGEX = re.compile(r"[\[\(][_\-. ]*[\]\)]")


class ParserType(TypedDict):
    regex: Pattern[str]
    groups: Dict[str, str]


# TypedDict sucks. Can't make certain keys optional. I'll use this once it doesn't suck ass
# class AnimeType(TypedDict, total=False):
#     file_name: str
#     extension: str
#     is_anime: bool
#     season: Optional[str]
#     episode: Optional[str]
#     anime_title: Optional[str]
#     episode_title: Optional[str]
#     video_terms: Optional[List[str]]
#     audio_terms: Optional[List[str]]
#     source_terms: Optional[List[str]]
#     checksum: Optional[str]
#     resolution: Optional[str]
#     year: Optional[str]
#     release_version: Optional[str]
#     release_group: Optional[str]


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
audio_terms = [
    r"[25](\.[01])?(CH)",
    r"DTS(5\.1|-ES)*?",
    r"TRUEHD5\.1",
    r"AAC(X[234])*?",
    r"(E|E-)?AC-?3",
    r"FLAC(X[234])*?",
    "LOSSLESS",
    "MP3",
    "OGG",
    "VORBIS",
    r"DUAL[\- ]?AUDIO",
]
video_terms = [
    r"\d+(\.\d+)?FPS",
    r"(8|10)[\- ]?BITS*?",
    r"HI(10|444)P?P*?",
    r"[HX]\.?26[45]",
    r"HEVC2*?",
    r"DIVX[56]",
    r"AV[CI]",
    r"WMV[39]",
    "XVID",
    "RMVB",
    r"[HL]Q",
    r"[HS]D",
]
source_terms = [
    r"BD(RIP)*?",
    r"BLU[\- ]?RAY",
    r"DVD-?([59]|R2J|RIP)*?",
    r"R2J?(DVD)*?(RIP)*?",
    r"HDTV(RIP)*?",
    r"HDTV",
    r"TV-?RIP",
    r"WEB(CAST|RIP)",
]
drop_terms = ["", "ONA", "OVA", "END", "FINAL"]

AUDIO_TERM_REGEX = re.compile(
    f"({'|'.join(audio_terms)})" + r"(?=[^\w])", flags=re.IGNORECASE
)
VIDEO_TERM_REGEX = re.compile(
    f"({'|'.join(video_terms)})" + r"(?=[^\w])", flags=re.IGNORECASE
)
SOURCE_TERM_REGEX = re.compile(
    f"({'|'.join(source_terms)})" + r"(?=[^\w])", flags=re.IGNORECASE
)

# Step 1 parsing
parsers_step_1: List[ParserType] = [
    {"regex": CHECKSUM_REGEX, "groups": {"checksum": "checksum"}},
    {
        "regex": RESOLUTION_REGEX,
        "groups": {
            "height": "resolution",
            "pos_height": "resolution",
            "alone_height": "resolution",
        },
    },
    {"regex": YEAR_REGEX, "groups": {"year": "year"}},
    {"regex": RELEASE_VERSION_REGEX, "groups": {"release": "release_version"}},
]

# Step 2 parsing, happens after getting bracketed data
parsers_step_2: List[ParserType] = [
    {
        "regex": EPISODE_REGEX,
        "groups": {"episode": "episode", "season": "season", "season2": "season"},
    },
    {"regex": RELEASE_GROUP_REGEX, "groups": {"release_group": "release_group"}},
]


def parse(path: Union[str, Path]) -> Dict[str, Any]:
    if isinstance(path, str):
        path = Path(path)

    return _parse(path)


# This data ain't big, pretty tiny dict per filename. Seriously, by estimation
# it would take about 2,000,000 DIFFERENT files to hit a GB of memory. I think we're safe
# setting this cache size to unlimited
@functools.lru_cache(maxsize=None)
def _parse_string(name: str) -> Dict[str, Any]:
    """Takes a particlar string and uses a bunch
    of regex to pull anime data from it"""

    # Add a / to the front, this helps handle the regexes that can match at the beginning
    # a few regexes have a negative lookbehind, but that fails at the *start* of the line
    # As far as I know there's no "start of string, or negative lookbehind" in regex, so this
    # is our solution
    name_to_parse = "/" + EXTENSION_REGEX.sub("", name)

    # This is going to be our data we modify through the function that gets returned
    data: Dict[str, Any] = {}

    # A function to pass to re.sub, handling throwing matches we want into the data
    # and replacing with '' to remove it
    def replace_and_track(_group: Dict[str, str]):
        def inner(match: re.Match):
            for key, value in _group.items():
                try:
                    res = match.group(key)
                except IndexError:
                    continue
                else:
                    # Only include if it's not in there already, this makes sure
                    # that we prioritize first matches, but still remove matches
                    if res and value not in data:
                        data[value] = res
            return ""

        return inner

    # Use the first step parsers
    for parser_type in parsers_step_1:
        name_to_parse = parser_type["regex"].sub(
            replace_and_track(parser_type["groups"]), name_to_parse
        )

    audio_terms = []
    video_terms = []
    source_terms = []

    # Appends to the specified list and replaces with ''
    def replace_bracket_terms(l: List[str]):
        def inner(match: re.Match):
            l.append(match.group(0))
            return ""

        return inner

    # Get the audio, video, and source terms
    name_to_parse = AUDIO_TERM_REGEX.sub(
        replace_bracket_terms(audio_terms), name_to_parse
    )
    name_to_parse = VIDEO_TERM_REGEX.sub(
        replace_bracket_terms(video_terms), name_to_parse
    )
    name_to_parse = SOURCE_TERM_REGEX.sub(
        replace_bracket_terms(source_terms), name_to_parse
    )
    # This could leave 'empty' brackets, so remove them
    name_to_parse = EMPTY_BRACKETS_REGEX.sub("", name_to_parse)
    # Now do the step-two parsers
    for parser_type in parsers_step_2:
        name_to_parse = parser_type["regex"].sub(
            replace_and_track(parser_type["groups"]), name_to_parse
        )

    # Strip off the preceeding / we added
    name_to_parse = re.sub("^/ *", "", name_to_parse)
    # At this point replace _ with space
    name_to_parse = re.sub("_+", " ", name_to_parse)
    # Now remove ALL brackets
    name_to_parse = re.sub(r"[\[\]]", "", name_to_parse)
    # Now remove some stuff that could be left at the end
    name_to_parse = re.sub(r" ?-$", "", name_to_parse)
    # Now try to split between the anime title and the episode title
    titles = [t for t in re.split(" ?- ", name_to_parse) if t.upper() not in drop_terms]

    # If there are two titles, the episode should be the second
    if len(titles) == 2:
        data["episode_title"] = titles[1]
    # The first will always be the anime title
    if titles:
        data["anime_title"] = titles[0]

    # Throw in the bracketed things
    if video_terms:
        data["video_terms"] = video_terms
    if audio_terms:
        data["audio_terms"] = audio_terms
    if source_terms:
        data["source_terms"] = source_terms

    # And return the data
    return data


def _parse(path: Path) -> Dict[str, Any]:
    """Takes a path and tries to parse out anime data from it. This will first try to
    parse the data from the file itself. If it isn't sure if the anime title was found
    in it, it will check the parent directory's name as well."""
    extension = path.suffix[1:]

    data: Dict[str, Any] = {"file_name": str(path.absolute()), "extension": extension}

    # First try to get the data from the file
    file_data = _parse_string(path.name)
    data.update(file_data)

    # Now if there is only an anime title but not an episode title, it's possible that
    # this is actually the episode title... and the anime title is in the folder name
    if "anime_title" in file_data and "episode_title" not in file_data:
        path_data = _parse_string(path.parent.name)

        # Special check to handle common folder names that might be general
        # containers that we want to ignore
        if path_data["anime_title"].lower() not in [
            "anime",
            "videos",
            "torrents",
            "downloads",
            "documents",
        ]:
            # Now check if they differ, if they do combine
            if (
                fuzz.ratio(
                    file_data["anime_title"], path_data["anime_title"], processor=True
                )
                < 95
            ):
                data["episode_title"] = data["anime_title"]
                data["anime_title"] = path_data["anime_title"]

    # Add a nice bool checking if we think this is an actual anime
    data["is_anime"] = "anime_title" in data and (
        data.get("extension") in video_file_extensions
        or data.get("extension") in subtitle_file_extensions
    )

    return data
