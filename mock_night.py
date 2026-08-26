from datetime import datetime

from models import (
    Night,
    NightStatus,
    Participant,
    LocationPoint,
    Venue,
    PersonalLocation,
)


PREPARTY_LAT = 57.70013
PREPARTY_LON = 11.96998

PARLOUR_LAT = 57.70201
PARLOUR_LON = 11.97318

CLUB_LAT = 57.70422
CLUB_LON = 11.97553

MAX_LAT = 57.70673
MAX_LON = 11.97904

ERIK_SIDEQUEST_1_LAT = 57.71350
ERIK_SIDEQUEST_1_LON = 11.98650

ERIK_SIDEQUEST_2_LAT = 57.71600
ERIK_SIDEQUEST_2_LON = 11.99000

SARA_EMMA_SIDE_LAT = 57.71000
SARA_EMMA_SIDE_LON = 11.98500

ANTON_HOME_LAT = 57.73000
ANTON_HOME_LON = 11.94000


participants = [
    Participant(id="wilgot", name="Wilgot"),
    Participant(id="erik", name="Erik"),
    Participant(id="sara", name="Sara"),
    Participant(id="anton", name="Anton"),
    Participant(id="emma", name="Emma"),
    Participant(id="lucas", name="Lucas"),
]


venues = [
    Venue(
        id="preparty",
        name="Preparty",
        category="preparty",
        latitude=PREPARTY_LAT,
        longitude=PREPARTY_LON,
    ),
    Venue(
        id="parlour",
        name="The Parlour Restaurant",
        category="restaurant",
        latitude=PARLOUR_LAT,
        longitude=PARLOUR_LON,
    ),
    Venue(
        id="club",
        name="Port Du Soleil",
        category="nightclub",
        latitude=CLUB_LAT,
        longitude=CLUB_LON,
    ),
    Venue(
        id="max",
        name="MAX Burgers Gothenburg",
        category="food",
        latitude=MAX_LAT,
        longitude=MAX_LON,
    ),
]


def point(
    participant_id: str,
    hour: int,
    minute: int,
    latitude: float,
    longitude: float,
):
    day = 28 if hour >= 18 else 29

    return LocationPoint(
        participant_id=participant_id,
        timestamp=datetime(
            2026,
            8,
            day,
            hour,
            minute,
        ),
        latitude=latitude,
        longitude=longitude,
    )


def nearby(
    participant_id: str,
    hour: int,
    minute: int,
    latitude: float,
    longitude: float,
    lat_offset: float = 0.0,
    lon_offset: float = 0.0,
):
    return point(
        participant_id,
        hour,
        minute,
        latitude + lat_offset,
        longitude + lon_offset,
    )


locations = [
    nearby("wilgot", 20, 0, PREPARTY_LAT, PREPARTY_LON),
    nearby("erik", 20, 0, PREPARTY_LAT, PREPARTY_LON, 0.00003, 0.00002),
    nearby("sara", 20, 0, PREPARTY_LAT, PREPARTY_LON, -0.00002, 0.00004),
    nearby("anton", 20, 0, PREPARTY_LAT, PREPARTY_LON, 0.00004, -0.00002),

    nearby("wilgot", 21, 0, PREPARTY_LAT, PREPARTY_LON),
    nearby("erik", 21, 0, PREPARTY_LAT, PREPARTY_LON, 0.00003, 0.00002),
    nearby("sara", 21, 0, PREPARTY_LAT, PREPARTY_LON, -0.00002, 0.00004),
    nearby("anton", 21, 0, PREPARTY_LAT, PREPARTY_LON, 0.00004, -0.00002),

    nearby("wilgot", 21, 30, PARLOUR_LAT, PARLOUR_LON),
    nearby("erik", 21, 30, PARLOUR_LAT, PARLOUR_LON, 0.00003, 0.00002),
    nearby("sara", 21, 30, PARLOUR_LAT, PARLOUR_LON, -0.00002, 0.00004),
    nearby("anton", 21, 30, PARLOUR_LAT, PARLOUR_LON, 0.00004, -0.00002),
    nearby("emma", 21, 30, PARLOUR_LAT, PARLOUR_LON, -0.00003, -0.00003),

    nearby("wilgot", 22, 30, CLUB_LAT, CLUB_LON),
    nearby("erik", 22, 30, CLUB_LAT, CLUB_LON, 0.00003, 0.00002),
    nearby("sara", 22, 30, CLUB_LAT, CLUB_LON, -0.00002, 0.00004),
    nearby("anton", 22, 30, CLUB_LAT, CLUB_LON, 0.00004, -0.00002),
    nearby("emma", 22, 30, CLUB_LAT, CLUB_LON, -0.00003, -0.00003),

    nearby("wilgot", 23, 15, CLUB_LAT, CLUB_LON),
    nearby("erik", 23, 15, CLUB_LAT, CLUB_LON, 0.00003, 0.00002),
    nearby("sara", 23, 15, CLUB_LAT, CLUB_LON, -0.00002, 0.00004),
    nearby("anton", 23, 15, CLUB_LAT, CLUB_LON, 0.00004, -0.00002),
    nearby("emma", 23, 15, CLUB_LAT, CLUB_LON, -0.00003, -0.00003),
    nearby("lucas", 23, 15, CLUB_LAT, CLUB_LON, 0.00001, 0.00005),

    nearby("wilgot", 0, 0, CLUB_LAT, CLUB_LON),
    nearby("erik", 0, 0, CLUB_LAT, CLUB_LON, 0.00003, 0.00002),
    nearby("sara", 0, 0, CLUB_LAT, CLUB_LON, -0.00002, 0.00004),
    nearby("anton", 0, 0, CLUB_LAT, CLUB_LON, 0.00004, -0.00002),
    nearby("emma", 0, 0, CLUB_LAT, CLUB_LON, -0.00003, -0.00003),
    nearby("lucas", 0, 0, CLUB_LAT, CLUB_LON, 0.00001, 0.00005),

    nearby("wilgot", 0, 30, CLUB_LAT, CLUB_LON),
    point("erik", 0, 30, ERIK_SIDEQUEST_1_LAT, ERIK_SIDEQUEST_1_LON),
    nearby("sara", 0, 30, CLUB_LAT, CLUB_LON, -0.00002, 0.00004),
    nearby("anton", 0, 30, CLUB_LAT, CLUB_LON, 0.00004, -0.00002),
    nearby("emma", 0, 30, CLUB_LAT, CLUB_LON, -0.00003, -0.00003),
    nearby("lucas", 0, 30, CLUB_LAT, CLUB_LON, 0.00001, 0.00005),

    nearby("wilgot", 1, 0, CLUB_LAT, CLUB_LON),
    point("erik", 1, 0, ERIK_SIDEQUEST_2_LAT, ERIK_SIDEQUEST_2_LON),
    nearby("sara", 1, 0, CLUB_LAT, CLUB_LON, -0.00002, 0.00004),
    nearby("anton", 1, 0, CLUB_LAT, CLUB_LON, 0.00004, -0.00002),
    nearby("emma", 1, 0, CLUB_LAT, CLUB_LON, -0.00003, -0.00003),
    nearby("lucas", 1, 0, CLUB_LAT, CLUB_LON, 0.00001, 0.00005),

    nearby("wilgot", 1, 20, CLUB_LAT, CLUB_LON),
    nearby("erik", 1, 20, CLUB_LAT, CLUB_LON, 0.00003, 0.00002),
    nearby("sara", 1, 20, CLUB_LAT, CLUB_LON, -0.00002, 0.00004),
    nearby("anton", 1, 20, CLUB_LAT, CLUB_LON, 0.00004, -0.00002),
    nearby("emma", 1, 20, CLUB_LAT, CLUB_LON, -0.00003, -0.00003),
    nearby("lucas", 1, 20, CLUB_LAT, CLUB_LON, 0.00001, 0.00005),

    nearby("wilgot", 1, 45, CLUB_LAT, CLUB_LON),
    nearby("erik", 1, 45, CLUB_LAT, CLUB_LON, 0.00003, 0.00002),
    point("sara", 1, 45, SARA_EMMA_SIDE_LAT, SARA_EMMA_SIDE_LON),
    nearby("anton", 1, 45, CLUB_LAT, CLUB_LON, 0.00004, -0.00002),
    point(
        "emma",
        1,
        45,
        SARA_EMMA_SIDE_LAT + 0.00003,
        SARA_EMMA_SIDE_LON + 0.00003,
    ),
    nearby("lucas", 1, 45, CLUB_LAT, CLUB_LON, 0.00001, 0.00005),

    nearby("wilgot", 2, 10, CLUB_LAT, CLUB_LON),
    nearby("erik", 2, 10, CLUB_LAT, CLUB_LON, 0.00003, 0.00002),
    point(
        "sara",
        2,
        10,
        SARA_EMMA_SIDE_LAT + 0.00020,
        SARA_EMMA_SIDE_LON + 0.00020,
    ),
    nearby("anton", 2, 10, CLUB_LAT, CLUB_LON, 0.00004, -0.00002),
    point(
        "emma",
        2,
        10,
        SARA_EMMA_SIDE_LAT + 0.00023,
        SARA_EMMA_SIDE_LON + 0.00023,
    ),
    nearby("lucas", 2, 10, CLUB_LAT, CLUB_LON, 0.00001, 0.00005),

    nearby("wilgot", 2, 30, CLUB_LAT, CLUB_LON),
    nearby("erik", 2, 30, CLUB_LAT, CLUB_LON, 0.00003, 0.00002),
    nearby("sara", 2, 30, CLUB_LAT, CLUB_LON, -0.00002, 0.00004),
    nearby("anton", 2, 30, CLUB_LAT, CLUB_LON, 0.00004, -0.00002),
    nearby("emma", 2, 30, CLUB_LAT, CLUB_LON, -0.00003, -0.00003),
    nearby("lucas", 2, 30, CLUB_LAT, CLUB_LON, 0.00001, 0.00005),

    nearby("wilgot", 2, 50, MAX_LAT, MAX_LON),
    nearby("erik", 2, 50, MAX_LAT, MAX_LON, 0.00003, 0.00002),
    nearby("sara", 2, 50, MAX_LAT, MAX_LON, -0.00002, 0.00004),
    point("anton", 2, 50, ANTON_HOME_LAT, ANTON_HOME_LON),
    nearby("emma", 2, 50, MAX_LAT, MAX_LON, -0.00003, -0.00003),
    nearby("lucas", 2, 50, MAX_LAT, MAX_LON, 0.00001, 0.00005),

    nearby("wilgot", 3, 20, MAX_LAT, MAX_LON),
    nearby("erik", 3, 20, MAX_LAT, MAX_LON, 0.00003, 0.00002),
    nearby("sara", 3, 20, MAX_LAT, MAX_LON, -0.00002, 0.00004),
    point("anton", 3, 20, ANTON_HOME_LAT, ANTON_HOME_LON),
    nearby("emma", 3, 20, MAX_LAT, MAX_LON, -0.00003, -0.00003),
    nearby("lucas", 3, 20, MAX_LAT, MAX_LON, 0.00001, 0.00005),

    nearby("wilgot", 3, 50, MAX_LAT, MAX_LON),
    nearby("erik", 3, 50, MAX_LAT, MAX_LON, 0.00003, 0.00002),
    nearby("sara", 3, 50, MAX_LAT, MAX_LON, -0.00002, 0.00004),
    point("anton", 3, 50, ANTON_HOME_LAT, ANTON_HOME_LON),
    nearby("emma", 3, 50, MAX_LAT, MAX_LON, -0.00003, -0.00003),
    nearby("lucas", 3, 50, MAX_LAT, MAX_LON, 0.00001, 0.00005),
]


personal_locations = [
    PersonalLocation(
        id="erik_home",
        owner_participant_id="erik",
        name="Erik's Apartment",
        latitude=PREPARTY_LAT,
        longitude=PREPARTY_LON,
        radius_meters=50,
    )
]


mock_night = Night(
    id="night_003",
    title="Saturday Night",
    started_at=datetime(2026, 8, 28, 20, 0),
    ended_at=datetime(2026, 8, 29, 4, 0),
    status=NightStatus.FINISHED,
    participants=participants,
    locations=locations,
    venues=venues,
    personal_locations=personal_locations,
)