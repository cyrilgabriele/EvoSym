"""Pydantic contracts for the SBB fields consumed by the adapter.

Unknown source fields are allowed to evolve. Consumed fields must be present;
nullable values remain missing evidence. No derived classifications live here.
"""

from datetime import date, datetime
from decimal import Decimal, InvalidOperation
from typing import Annotated, Literal

from pydantic import BaseModel, BeforeValidator, ConfigDict, Field, ValidationError


def identifier(value):
    if value is None or value == "":
        return None
    if isinstance(value, bool):
        raise ValueError("a boolean is not an identifier")
    try:
        number = Decimal(str(value))
    except InvalidOperation as exc:
        raise ValueError("invalid numeric identifier") from exc
    if not number.is_finite() or number != number.to_integral_value() or number <= 0:
        raise ValueError("identifier must be a positive whole number")
    return int(number)


def missing_text(value):
    return None if value == "" else value


Identifier = Annotated[int, Field(gt=0), BeforeValidator(identifier)]
OptionalIdentifier = Annotated[int | None, BeforeValidator(identifier)]
Nonnegative = Annotated[float, Field(ge=0, allow_inf_nan=False)]
OptionalText = Annotated[str | None, BeforeValidator(missing_text)]


class SourceRow(BaseModel):
    model_config = ConfigDict(extra="ignore", str_strip_whitespace=True, allow_inf_nan=False)


class ServicePoint(SourceRow):
    number: Identifier
    designationofficial: Annotated[str, Field(min_length=1)]
    isocountrycode: OptionalText
    stoppoint: bool
    meansoftransport: OptionalText
    cantonabbreviation: OptionalText
    cantonname: OptionalText


class WifiStation(SourceRow):
    bpuic: OptionalIdentifier
    standort: str


class Platform(SourceRow):
    fid: Identifier
    bpuic: OptionalIdentifier
    bps_name: str
    p_nr: OptionalText
    p_lange: Nonnegative | None


class WaitingHall(SourceRow):
    bpuic: OptionalIdentifier
    bezeichnung_offiziell: str
    linie: Identifier | None
    km: float | None
    gebaudename: OptionalText
    geopos: dict[str, float] | None
    status: Literal["BESTEHEND", "PROJEKTIERT NEU", "PROJEKTIERT ABBRUCH"] | None


class SectorBoard(SourceRow):
    fid: Identifier
    bpuic: OptionalIdentifier
    bps_name: str
    kundengleisnummer: OptionalText
    sektor_vorderseite: OptionalText
    sektor_ruckseiter: OptionalText


class PassengerCount(SourceRow):
    uic: OptionalIdentifier
    bahnhof_gare_stazione: str
    jahr_annee_anno: Annotated[str, Field(pattern=r"^\d{4}$")] | None
    dtv_tjm_tgm: Nonnegative | None


class LineStop(SourceRow):
    bpuic: OptionalIdentifier
    bezeichnung_offiziell: str
    linie: Identifier


class Line(SourceRow):
    linie: Identifier
    linienname: OptionalText


class TrainEvent(SourceRow):
    betriebstag: date
    fahrt_bezeichner: Annotated[str, Field(min_length=1)]
    bpuic: OptionalIdentifier
    haltestellen_name: str
    verkehrsmittel_text: Annotated[str, Field(min_length=1)]
    ankunftszeit: datetime | None
    abfahrtszeit: datetime | None
    faellt_aus_tf: bool
    durchfahrt_tf: bool


MODELS = {
    "stations": ServicePoint,
    "wifi": WifiStation,
    "platforms": Platform,
    "waiting_halls": WaitingHall,
    "sector_boards": SectorBoard,
    "passenger_counts": PassengerCount,
    "line_stops": LineStop,
    "lines": Line,
    "train_runs": TrainEvent,
}


def validate_rows(name: str, rows: list[dict]) -> list[dict]:
    """Fail with dataset and one-based source row, never silently discard invalid input."""
    if not isinstance(rows, list):
        raise ValueError(f"{name}: expected a JSON array")
    result = []
    for index, row in enumerate(rows, start=1):
        try:
            result.append(MODELS[name].model_validate(row).model_dump())
        except ValidationError as exc:
            raise ValueError(f"{name}, row {index}: {exc}") from exc
    return result
