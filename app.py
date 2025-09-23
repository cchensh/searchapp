import json
import logging
import os
from enum import Enum
from typing import TypedDict, List, Optional, NotRequired

from slack_bolt import Ack, App, Complete, Fail
from slack_bolt.adapter.socket_mode import SocketModeHandler
from slack_sdk import WebClient

logging.basicConfig(level=logging.INFO)

#----------------------
# MODELS
#----------------------

class FilterType(Enum):
    MULTI_SELECT = "multi_select"
    TOGGLE = "toggle"

class EntityReference(TypedDict):
    id: str
    type: Optional[str]

class SearchResult(TypedDict):
    id: str
    title: str
    description: str
    link: str
    date_updated: str
    entity_reference: EntityReference
    content: NotRequired[str]


class FilterOptions(TypedDict):
    name: str
    value: str


class SearchFilter(TypedDict):
    name: str
    display_name: str
    type: FilterType
    options: Optional[List[FilterOptions]]

class Song(TypedDict):
    id: str
    title: str
    description: str
    link: str
    band: str
    is_single: bool
    date_updated: str

class LinkSharedEventLink(TypedDict):
    url: str
    domain: str

class ExternalRef(TypedDict):
    id: str
    type: Optional[str]


class EntityDetailsRequestedEvent(TypedDict):
    type: str = "entity_details_requested"
    user: str
    external_ref: ExternalRef
    trigger_id: str
    link: LinkSharedEventLink


class EntityDetailsRequestedBody(TypedDict):
    team_id: str
    event: EntityDetailsRequestedEvent

#----------------------
# DATA
#----------------------

SONGS: List[Song] = [
    {
        "id": "pf-001",
        "title": "Comfortably Numb",
        "description": "From the album 'The Wall' (1979), features one of David Gilmour's most famous guitar solos",
        "link": "https://example.com/pinkfloyd/comfortably-numb",
        "band": "Pink Floyd",
        "is_single": False,
        "date_updated": "2023-01-01",
        "content": "Comfortably Numb is a song by the English rock band Pink Floyd, released on their eleventh studio album, The Wall (1979). It was released as a single in 1980, with \"Hey You\" as the B-side.The lyrics were written by the bassist, Roger Waters, who recalled his experience of being injected with tranquilisers before a performance in 1977; the music was composed by the band's guitarist, David Gilmour. Waters and Gilmour argued during the recording, with Waters seeking an orchestral arrangement and Gilmour preferring a more stripped-down arrangement. They compromised by combining both versions, and Gilmour said the song was the last time he and Waters were able to work together constructively.",
    },
    {
        "id": "pf-002",
        "title": "Wish You Were Here",
        "description": "Title track from the 1975 album, written as a tribute to former band member Syd Barrett",
        "link": "https://example.com/pinkfloyd/wish-you-were-here",
        "band": "Pink Floyd",
        "is_single": False,
        "date_updated": "2023-02-01",
    },
    {
        "id": "pf-003",
        "title": "Time",
        "description": "From the album 'The Dark Side of the Moon' (1973), known for its iconic clock sound effects",
        "link": "https://example.com/pinkfloyd/time",
        "band": "Pink Floyd",
        "is_single": False,
        "date_updated": "2023-03-01",
    },
    {
        "id": "rs-001",
        "title": "Paint It Black",
        "description": "Released as a single in 1966, reaching number one on both UK and US charts",
        "link": "https://example.com/rollingstones/paint-it-black",
        "band": "Rolling Stones",
        "is_single": True,
        "date_updated": "2023-04-15",
    },
    {
        "id": "rs-002",
        "title": "Sympathy for the Devil",
        "description": "From the album 'Beggars Banquet' (1968), one of their most controversial songs",
        "link": "https://example.com/rollingstones/sympathy-for-the-devil",
        "band": "Rolling Stones",
        "is_single": False,
        "date_updated": "2023-05-20",
    },
    {
        "id": "beatles-001",
        "title": "Hey Jude",
        "description": "Released as a single in 1968, became one of their biggest hits",
        "link": "https://example.com/beatles/hey-jude",
        "band": "The Beatles",
        "is_single": True,
        "date_updated": "2023-06-10",
    },
    {
        "id": "beatles-002",
        "title": "Let It Be",
        "description": "From the album 'Let It Be' (1970), one of their final singles",
        "link": "https://example.com/beatles/let-it-be",
        "band": "The Beatles",
        "is_single": True,
        "date_updated": "2023-07-05",
    },
    {
        "id": "lz-001",
        "title": "Stairway to Heaven",
        "description": "From the album 'Led Zeppelin IV' (1971), often cited as one of greatest rock songs of all time",
        "link": "https://example.com/ledzeppelin/stairway-to-heaven",
        "band": "Led Zeppelin",
        "is_single": False,
        "date_updated": "2023-08-12",
    },
    {
        "id": "queen-001",
        "title": "Bohemian Rhapsody",
        "description": "From the album 'A Night at the Opera' (1975), pioneering song with no chorus",
        "link": "https://example.com/queen/bohemian-rhapsody",
        "band": "Queen",
        "is_single": True,
        "date_updated": "2023-09-18",
        "content": "Bohemian Rhapsody can refer to two distinct entities: the iconic song by the British rock band Queen, and the 2018 biographical film about the band and its lead singer, Freddie Mercury."
    },
    {
        "id": "acdc-001",
        "title": "Back in Black",
        "description": "Title track from the 1980 album, written as a tribute to deceased singer Bon Scott",
        "link": "https://example.com/acdc/back-in-black",
        "band": "AC/DC",
        "is_single": True,
        "date_updated": "2023-10-25",
        "content": "Back in Black is the seventh studio album by Australian rock band AC/DC, released on 25 July 1980, by Albert Productions and Atlantic Records. It was the band's first album to feature Brian Johnson as lead singer, following the death of their previous vocalist Bon Scott. After the commercial breakthrough of their 1979 album Highway to Hell, AC/DC was planning to record a follow-up, but in February 1980, Scott died from alcohol poisoning after a drinking binge. The remaining members of the group considered disbanding, but ultimately chose to continue on and recruited Johnson, who had previously been the vocalist for Geordie."
    },
]

#----------------------
# APPLICATION
#----------------------

client = WebClient(token=os.environ.get("SLACK_BOT_TOKEN"), base_url="https://dev.slack.com/api/")
app = App(client=client)


@app.function("search", auto_acknowledge=False)
def handle_search_step_event(
    ack: Ack, inputs: dict, body: dict, fail: Fail, complete: Complete, logger: logging.Logger
):
    # logger.info("Search Function inputs received:")
    # logger.info(f"inputs: {json.dumps(inputs, indent=2)}")

    singles_filter = inputs["filters"].get("is_single", False)
    bands_filter = inputs["filters"].get("bands", [])

    try:
        filtered_songs = SONGS

        if singles_filter:
            filtered_songs = [song for song in filtered_songs if song["is_single"]]

        if bands_filter:
            filtered_songs = [song for song in filtered_songs if song["band"] in bands_filter]

        results: List[SearchResult] = [
            {"title": song["title"], "description": song["description"], "link": song["link"], "date_updated": song["date_updated"], "external_ref": {"id": song["id"]}, **({"content": song["content"]} if "content" in song else {}) }
            for song in filtered_songs
        ]

        logger.info(f"Generated results: {json.dumps(results, indent=2)}")
        complete(outputs={"search_result": results})
    finally:
        ack()


@app.function("filters", auto_acknowledge=False)
def handle_filters_step_event(
    ack: Ack, inputs: dict, fail: Fail, complete: Complete, logger: logging.Logger
):
    # logger.info("Function inputs received:")
    # logger.info(f"inputs: {json.dumps(inputs, indent=2)}")

    try:
        unique_bands = {song["band"] for song in SONGS}

        filters: List[SearchFilter] = [
            {
                "name": "bands",
                "display_name": "Bands",
                "type": FilterType.MULTI_SELECT.value,
                "options": [{"name": band, "value": band} for band in unique_bands],
            },
            {
                "name": "is_single",
                "display_name": "Singles Only",
                "type": FilterType.TOGGLE.value,
            },
        ]

        complete(outputs={"filters": filters})
    finally:
        ack()

@app.event("entity_details_requested")
def handle_flexpane_event(event, body, client, logger):
    logger.info(f"entity_details_requested body: {json.dumps(body, indent=2)}")
    logger.info(f"entity_details_requested event: {json.dumps(event, indent=2)}")

    payload = {
        "trigger_id": event["trigger_id"],
        "metadata": {
            "entity_type": "slack#/entities/item",
            "url": event["link"]["url"],
            "external_ref": {"id": "123"},
            "entity_payload": {
                "attributes": {
                    "title": {
                        "text": "hello world",
                        "edit": {
                            "enabled": True,
                            "text": {
                                "max_length": 50
                            }
                        }
                    },
                },
                "custom_fields": [
                    {
                        "key": "description",
                        "label": "Description",
                        "type": "string",
                        "value": "This is a description",
                    },
                ]
            },
        },
    }

    try:
        client.api_call(
            api_method="entity.presentDetails",
            json=payload,
        )
    except Exception as e:
        logger.error(f"Error calling entity.presentDetails: {str(e)}")

if __name__ == "__main__":
    SocketModeHandler(app, os.environ.get("SLACK_APP_TOKEN")).start()
