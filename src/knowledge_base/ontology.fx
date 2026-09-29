// Vocabulary for all 18 hackathon questions. Source semantics: docs/adrs/.
// Syntax: https://unisg-ics-dsnlp.github.io/FrameX-Doc/syntax/classes-subclasses.html
world open.

Entity {}.
Place extends Entity.
Canton extends Place.
Canton { designation: String }.
StopPoint extends Place.
StopPoint { designation: String, inCanton: Canton, servesMode: TransportMode,
            hasWifi: Boolean, hasWaitingHall: Boolean, servedByLine: Line,
            servedByCategory: String, nonStopTo: StopPoint }.
TransportMode extends Entity.
Facility extends Entity.
Facility { atStopPoint: StopPoint }.
Platform extends Facility.
Platform { platformNumber: String, platformLength: Float }.
WaitingHall extends Facility.
WaitingHall { status: String }.
SectorBoard extends Facility.
SectorBoard { trackNumber: String, sectorFront: String, sectorBack: String }.
Line extends Entity.
Line { label: String, lineName: String }.
TrainRun extends Entity.
TrainRun { journeyId: String, operatingDay: String, category: String }.
StopEvent extends Entity.
StopEvent { atStopPoint: StopPoint, ofRun: TrainRun, nextStop: StopEvent,
            scheduledArrival: String, scheduledDeparture: String }.

LongPlatform extends Platform.
Junction extends StopPoint.
LongDistanceStation extends StopPoint.
Interchange extends StopPoint.

// Parameterized relations: observedFrequency("YYYY") -> DTV (Float),
// busyIn("YYYY") -> Boolean. DTV counts daily boardings plus alightings.
// Missing observations, facilities and WiFi evidence remain unknown.
