"""All 18 questions from docs/hackathon01/HA1_FrameX_SBB_Test_Queries.pdf."""

from dataclasses import dataclass


@dataclass(frozen=True)
class Question:
    id: str
    title: str
    query: str
    datasets: tuple[str, ...]
    compared: tuple[str, ...]


QUESTIONS = (
    Question("1.1", "Does Chur have WiFi?",
             '?- sp_8509000[hasWifi -> ?W].', ("wifi",), ("W",)),
    Question("1.2", "Platforms at Zürich HB and their lengths",
             '?- ?P[atStopPoint -> sp_8503000] AND ?P:Platform AND ?P[platformLength -> ?L].',
             ("platforms",), ("L",)),
    Question("1.3", "Stations in Graubünden with a standing waiting hall",
             '?- ?S[inCanton -> canton_gr] AND ?S[hasWaitingHall -> true] AND ?S[designation -> ?N].',
             ("stations", "waiting_halls"), ("S",)),
    Question("1.4", "Train categories that stopped in Bern",
             '?- sp_8507000[servedByCategory -> ?C].', ("train_runs",), ("C",)),
    Question("1.5", "Stations above 50,000 daily passengers in 2024",
             '?- ?S[observedFrequency("2024") -> ?V] AND ?V > 50000 AND ?S[designation -> ?N].',
             ("stations", "passenger_counts"), ("S", "V")),
    Question("1.6", "Destinations from Bern with no intermediate stop",
             '?- sp_8507000[nonStopTo -> ?B] AND ?B[designation -> ?N].',
             ("stations", "train_runs"), ("B",)),
    Question("1.7", "Long-distance stations without WiFi (open-world test)",
             '?- ?S:LongDistanceStation AND NOT ?S[hasWifi -> true].',
             ("stations", "wifi", "train_runs"), ()),
    Question("2.1", "Stations in Ticino with WiFi",
             '?- ?S[inCanton -> canton_ti] AND ?S[hasWifi -> true] AND ?S[designation -> ?N].',
             ("stations", "wifi"), ("S",)),
    Question("2.2", "Platforms at Bern longer than 320 metres",
             '?- ?P:LongPlatform AND ?P[atStopPoint -> sp_8507000] AND ?P[platformNumber -> ?No] AND ?P[platformLength -> ?L].',
             ("platforms",), ("No", "L")),
    Question("2.3", "Sector letters on track 3 at Zürich HB",
             '?- ?B:SectorBoard AND ?B[atStopPoint -> sp_8503000] AND ?B[trackNumber -> "3"] AND ?B[sectorFront -> ?F].',
             ("sector_boards",), ("F",)),
    Question("2.4", "Planned new waiting halls in canton Bern",
             '?- ?F:WaitingHall AND ?F[status -> "PROJEKTIERT NEU"] AND ?F[atStopPoint -> ?S] AND ?S[inCanton -> canton_be] AND ?S[designation -> ?N].',
             ("stations", "waiting_halls"), ("S",)),
    Question("2.5", "Waiting halls planned for demolition in canton Zürich",
             '?- ?F:WaitingHall AND ?F[status -> "PROJEKTIERT ABBRUCH"] AND ?F[atStopPoint -> ?S] AND ?S[inCanton -> canton_zh] AND ?S[designation -> ?N].',
             ("stations", "waiting_halls"), ("S",)),
    Question("2.6", "Daily passengers at stations on line 900 in 2024",
             '?- ?S[servedByLine -> line_900] AND ?S[observedFrequency("2024") -> ?V] AND ?S[designation -> ?N].',
             ("stations", "line_stops", "passenger_counts"), ("S", "V")),
    Question("3.1", "Junctions in Graubünden and their infrastructure lines",
             '?- ?S:Junction AND ?S[inCanton -> canton_gr] AND ?S[servedByLine -> ?L] AND ?L[label -> ?LL] AND ?S[designation -> ?N].',
             ("stations", "line_stops", "lines"), ("S", "LL")),
    Question("3.2", "Busy in 2025, at most 20,000 daily passengers in 2018",
             '?- ?S[busyIn("2025") -> true] AND ?S[observedFrequency("2018") -> ?V] AND ?V <= 20000 AND ?S[designation -> ?N].',
             ("stations", "passenger_counts"), ("S", "V")),
    Question("3.3", "Long-distance stations reachable non-stop from Zürich HB",
             '?- sp_8503000[nonStopTo -> ?B] AND ?B:LongDistanceStation AND ?B[designation -> ?N].',
             ("stations", "train_runs"), ("B",)),
    Question("3.4", "Swiss stations with TGV service",
             '?- ?S[servedByCategory -> "TGV"] AND ?S[designation -> ?N].',
             ("stations", "train_runs"), ("S",)),
    Question("3.5", "Service points shared by train and tram",
             '?- ?S:Interchange AND ?S[servesMode -> mode_tram] AND ?S[designation -> ?N].',
             ("stations",), ("S",)),
)
BY_ID = {question.id: question for question in QUESTIONS}
