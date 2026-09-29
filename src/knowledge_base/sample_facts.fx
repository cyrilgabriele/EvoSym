// Invented teaching data, deliberately small; values are not SBB observations.
world open.
canton_gr:Canton[designation -> "Graubünden"].
canton_ti:Canton[designation -> "Ticino"].
canton_be:Canton[designation -> "Bern"].
canton_zh:Canton[designation -> "Zürich"].
mode_train:TransportMode.
mode_tram:TransportMode.

sp_8509000:StopPoint[designation -> "Chur"; inCanton -> canton_gr;
    servesMode -> mode_train; hasWifi -> true; servedByLine -> line_900;
    servedByLine -> line_920; observedFrequency("2024") -> 28000.0].
sp_8509002:StopPoint[designation -> "Landquart"; inCanton -> canton_gr;
    servesMode -> mode_train; servedByLine -> line_900].
sp_8505300:StopPoint[designation -> "Lugano"; inCanton -> canton_ti;
    servesMode -> mode_train; hasWifi -> true; observedFrequency("2018") -> 20000.0;
    observedFrequency("2025") -> 20001.0].
sp_8507000:StopPoint[designation -> "Bern"; inCanton -> canton_be;
    servesMode -> mode_train; observedFrequency("2024") -> 50001.0;
    observedFrequency("2018") -> 20001.0; observedFrequency("2025") -> 30000.0].
sp_8503000:StopPoint[designation -> "Zürich HB"; inCanton -> canton_zh;
    servesMode -> mode_train; observedFrequency("2024") -> 50000.0].
sp_8503059:StopPoint[designation -> "Zürich Stadelhofen, Bahnhof";
    inCanton -> canton_zh; servesMode -> mode_train; servesMode -> mode_tram;
    observedFrequency("2018") -> 15000.0; observedFrequency("2025") -> 20000.0].

line_900:Line[label -> "900"].
line_920:Line[label -> "920"].
platform_zh:Platform[atStopPoint -> sp_8503000; platformNumber -> "3/4"; platformLength -> 425.0].
platform_zh_unknown:Platform[atStopPoint -> sp_8503000; platformNumber -> "5/6"].
platform_bern_long:Platform[atStopPoint -> sp_8507000; platformNumber -> "1/2"; platformLength -> 321.0].
platform_bern_boundary:Platform[atStopPoint -> sp_8507000; platformNumber -> "3/4"; platformLength -> 320.0].
platform_bern_short:Platform[atStopPoint -> sp_8507000; platformNumber -> "5/6"; platformLength -> 319.0].

hall_chur:WaitingHall[atStopPoint -> sp_8509000; status -> "BESTEHEND"].
hall_landquart_planned:WaitingHall[atStopPoint -> sp_8509002; status -> "PROJEKTIERT NEU"].
hall_bern_planned:WaitingHall[atStopPoint -> sp_8507000; status -> "PROJEKTIERT NEU"].
hall_zh_demolition:WaitingHall[atStopPoint -> sp_8503000; status -> "PROJEKTIERT ABBRUCH"].
board_3_a:SectorBoard[atStopPoint -> sp_8503000; trackNumber -> "3"; sectorFront -> "A"].
board_3_b:SectorBoard[atStopPoint -> sp_8503000; trackNumber -> "3"; sectorFront -> "B"].
board_4_c:SectorBoard[atStopPoint -> sp_8503000; trackNumber -> "4"; sectorFront -> "C"].

run_ic:TrainRun[journeyId -> "sample-ic"; operatingDay -> "2026-09-28"; category -> "IC"].
event_ic_1:StopEvent[ofRun -> run_ic; atStopPoint -> sp_8507000; nextStop -> event_ic_2].
event_ic_2:StopEvent[ofRun -> run_ic; atStopPoint -> sp_8503000; nextStop -> event_ic_3].
event_ic_3:StopEvent[ofRun -> run_ic; atStopPoint -> sp_8509000].
run_tgv:TrainRun[journeyId -> "sample-tgv"; operatingDay -> "2026-09-28"; category -> "TGV"].
event_tgv:StopEvent[ofRun -> run_tgv; atStopPoint -> sp_8503000].
run_s:TrainRun[journeyId -> "sample-s"; operatingDay -> "2026-09-28"; category -> "S"].
event_s_1:StopEvent[ofRun -> run_s; atStopPoint -> sp_8503000; nextStop -> event_s_2].
event_s_2:StopEvent[ofRun -> run_s; atStopPoint -> sp_8503059].
