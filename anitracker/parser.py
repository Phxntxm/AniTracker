import json
import re
from pathlib import Path
from typing import Any, Dict, Optional, Pattern, TypedDict, List, Union

# Here's all our different regex patterns
EPISODE_REGEX = re.compile(
    r"(?:[^a-z0-9()\[\]])(s(?P<season>\d+))?((e|sp|ep)|(?P<season2>\d+)x)?(?P<episode>\d+)(?![a-uw-z0-9()])[.\-]*",
    flags=re.IGNORECASE,
)
RESOLUTION_REGEX = re.compile(
    r"(?P<pos_height>\d{3,4})([p]|[x\u00D7](?P<height>\d{3,4}))|\[(?P<alone_height>\d{3,4})\]", flags=re.IGNORECASE
)
CHECKSUM_REGEX = re.compile(r"[ -]?[\[(](?P<checksum>[A-Fa-f0-9]{8})[\])][ -]?", flags=re.IGNORECASE)
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
drop_terms = ["ONA", "OVA", "END", "FINAL"]

AUDIO_TERM_REGEX = re.compile(f"({'|'.join(audio_terms)})" + r"(?=[^\w])", flags=re.IGNORECASE)
VIDEO_TERM_REGEX = re.compile(f"({'|'.join(video_terms)})" + r"(?=[^\w])", flags=re.IGNORECASE)
SOURCE_TERM_REGEX = re.compile(f"({'|'.join(source_terms)})" + r"(?=[^\w])", flags=re.IGNORECASE)

# Step 1 parsing
parsers_step_1: List[ParserType] = [
    {"regex": CHECKSUM_REGEX, "groups": {"checksum": "checksum"}},
    {
        "regex": RESOLUTION_REGEX,
        "groups": {"height": "resolution", "pos_height": "resolution", "alone_height": "resolution"},
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


def _parse_string(name: str) -> Dict[str, Any]:
    name_to_parse = "/" + EXTENSION_REGEX.sub("", name)

    data: Dict[str, Any] = {}

    def replace_and_track(_group: Dict[str, str]):
        def inner(match: re.Match):
            for key, value in _group.items():
                try:
                    res = match.group(key)
                except IndexError:
                    continue
                else:
                    if res and value not in data:
                        data[value] = res
            return ""

        return inner

    # Parse the first-step
    for parser_type in parsers_step_1:
        name_to_parse = parser_type["regex"].sub(replace_and_track(parser_type["groups"]), name_to_parse)

    audio_terms = []
    video_terms = []
    source_terms = []

    def replace_bracket_terms(l: List[str]):
        def inner(match: re.Match):
            l.append(match.group(0))
            # Now replace it with ""
            return ""

        return inner

    # Get the audio and video terms
    name_to_parse = AUDIO_TERM_REGEX.sub(replace_bracket_terms(audio_terms), name_to_parse)
    name_to_parse = VIDEO_TERM_REGEX.sub(replace_bracket_terms(video_terms), name_to_parse)
    name_to_parse = SOURCE_TERM_REGEX.sub(replace_bracket_terms(source_terms), name_to_parse)
    # This could leave 'empty' brackets, so remove them
    name_to_parse = EMPTY_BRACKETS_REGEX.sub("", name_to_parse)
    # Now do the step-two parsers
    for parser_type in parsers_step_2:
        name_to_parse = parser_type["regex"].sub(replace_and_track(parser_type["groups"]), name_to_parse)

    # Strip off the preceeding thing we added
    name_to_parse = re.sub("^/ *", "", name_to_parse)
    # At this point replace _ with space
    name_to_parse = re.sub("_+", " ", name_to_parse)
    # Now remove ALL brackets
    name_to_parse = re.sub(r"[\[\]]", "", name_to_parse)
    # Now try to split between the anime title and the episode title
    titles = re.split(" ?- ?", name_to_parse)
    titles = [t.strip() for t in titles if t.strip() and t.strip().upper() not in drop_terms]

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

    return data


def _parse(path: Path) -> Dict[str, Any]:
    extension = path.suffix[1:]

    data: Dict[str, Any] = {"file_name": str(path.absolute()), "extension": extension}

    # First try to get the data from the file
    file_data = _parse_string(path.name)
    data.update(file_data)

    # Now if there is only an anime title but not an episode title, it's possible that
    # this is actually the episode title... and the anime title is in the folder name
    if "anime_title" in file_data and "episode_title" not in file_data:
        path_data = _parse_string(path.parent.name)

        # Now check if they differ, if they do combine
        if file_data["anime_title"] not in path_data["anime_title"]:
            data["episode_title"] = data["anime_title"]
            data["anime_title"] = path_data["anime_title"]

    # Add a nice bool checking if we think this is an actual anime
    data["is_anime"] = "anime_title" in data and (
        data.get("extension") in video_file_extensions or data.get("extension") in subtitle_file_extensions
    )

    return data
