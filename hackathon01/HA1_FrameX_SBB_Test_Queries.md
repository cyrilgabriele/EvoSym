# FrameX × SBB Open Data — Test Queries

These test queries help you develop and check your rule-based system. Each one has:

- a natural-language question
- a FrameX query
- the reference solution from our reference system
- the SBB dataset(s) the answer comes from, as listed on data.sbb.ch

> **Disclaimer: your queries and results may look different.**
>
> The FrameX queries below were written for our reference system. How you write the same query in your own system depends on how you built it: your class and property names (e.g. `hasWifi`, `atStopPoint`, `nonStopTo`), how you name identifiers (e.g. `sp_8503000`), your semantics (open vs. closed world, how you treat cancelled trains or planned facilities), and how you define derived classes (e.g. `LongPlatform`, `Junction`, `LongDistanceStation`, `Interchange`).
>
> Use the reference solutions as a guide, not an exact target. Generated IDs such as `platform_3107…` are internal to our system and will not match yours. The entities and values (stations, lengths, counts) are what should match.
>
> **Live data:** "Target/Actual Comparison SBB departure/arrival times: (previous day)" only ever contains the previous day. It is replaced every morning. The reference solutions for those queries are based on **27 September 2026**, so your results on another day may differ.

## Datasets used

All datasets are on data.sbb.ch. Search for the title to find them.

| Dataset | Used in |
| --- | --- |
| Wifi@Station | 1.1, 1.7, 2.1 |
| Stop: platform length (body) | 1.2, 2.2 |
| Stop: waiting rooms | 1.3, 2.4, 2.5 |
| Target/Actual Comparison SBB departure/arrival times: (previous day) | 1.4, 1.6, 1.7, 3.3, 3.4 |
| Ein- und Aussteigende an Bahnhöfen (= passengers boarding and alighting at stations) | 1.5, 2.6, 3.2 |
| Service Points (Didok) based on opentransportdata.swiss | 1.3, 2.1, 2.4, 2.5, 3.1, 3.5 |
| Stop: sector boards | 2.3 |
| Line (Operation Points) | 2.6, 3.1 |
| SBB’s route network | 3.1 |

## Level 1: Single dataset lookups

### 1.1 Does Chur have WiFi?

```framex
?- sp_8509000[hasWifi -> ?W].
```

**Solution**

```text
W = true
```

**Dataset:** "Wifi@Station"

### 1.2 List every platform at Zürich HB with its length.

```framex
?- ?P[atStopPoint -> sp_8503000] AND ?P:Platform AND ?P[platformLength -> ?L].
```

**Solution (9 platforms)**

```text
L = 418.0, P = platform_3107450b7a1078509da548dbb7c1f2c7
L = 424.0, P = platform_daee0a2635bc7d4e0de52344d80c3a65
L = 425.0, P = platform_c52665d4f06582a8c947dbff5c38cb1c
L = 425.0, P = platform_d91f8485fc1cc4ca6339b86e7e4ffd65
L = 426.0, P = platform_6c69110a0bbc54aeb45ee8e69fd1ac00
L = 426.0, P = platform_d530ee5465f4d066c26d56f80625ad78
L = 427.0, P = platform_928d1e02cae5d6fe595a8715843046e6
L = 428.0, P = platform_bddf15120d8baeee1844c4483b3307ae
L = 433.0, P = platform_68df83a05780d4d6ffff696d69d392f0
```

**Dataset:** "Stop: platform length (body)"

> **Note:** Each result is one physical platform, not one track: island platform "10/11" serves two tracks. The underground stations Löwenstrasse (`8516144`) and Museumstrasse (`8515163`) are separate stop points, so they are not included.

### 1.3 Which stations in Graubünden have a waiting hall?

```framex
?- ?S[inCanton -> canton_gr] AND ?S[hasWaitingHall -> true] AND ?S[designation -> ?N].
```

**Solution**

```text
N = "Chur", S = sp_8509000
N = "Landquart", S = sp_8509002
N = "Maienfeld", S = sp_8509003
```

**Datasets:** "Stop: waiting rooms". The canton comes from its `kanton` field, or from "Service Points (Didok) based on opentransportdata.swiss".

### 1.4 Which train categories (IC, IR, S…) actually stopped in Bern?

```framex
?- sp_8507000[servedByCategory -> ?C].
```

**Solution (operating day 27 Sept 2026)**

```text
C = "EC"
C = "IC"
C = "ICE"
C = "IR"
C = "TER"
```

**Dataset:** "Target/Actual Comparison SBB departure/arrival times: (previous day)"

> **Note:** "Actually stopped" means excluding cancelled trains (`faellt_aus_tf`) and trains passing through (`durchfahrt_tf`). The dataset only contains SBB trains, which is why there is no S-Bahn.

### 1.5 Which stations had more than 50,000 daily passengers in 2024?

```framex
?- ?S[observedFrequency("2024") -> ?V] AND ?V > 50000 AND ?S[designation -> ?N].
```

**Solution (12 stations)**

```text
N = "Basel SBB", S = sp_8500010, V = 100500.0
N = "Bern", S = sp_8507000, V = 177800.0
N = "Genève", S = sp_8501008, V = 80600.0
N = "Lausanne", S = sp_8501120, V = 102800.0
N = "Luzern", S = sp_8505000, V = 103500.0
N = "Olten", S = sp_8500218, V = 78900.0
N = "Winterthur", S = sp_8506000, V = 101800.0
N = "Zürich Flughafen", S = sp_8503016, V = 51100.0
N = "Zürich HB", S = sp_8503000, V = 410700.0
N = "Zürich Hardbrücke", S = sp_8503020, V = 52400.0
N = "Zürich Oerlikon", S = sp_8503006, V = 84600.0
N = "Zürich Stadelhofen", S = sp_8503003, V = 73000.0
```

**Dataset:** "Ein- und Aussteigende an Bahnhöfen"

> **Note:** The solution uses DTV (`dtv_tjm_tgm`, the average over all days of the week). With the weekday average (DWV), Biel/Bienne would also qualify. The values count people boarding plus alighting, not unique passengers.

### 1.6 Where could a train take me from Bern with no stop in between?

```framex
?- sp_8507000[nonStopTo -> ?B] AND ?B[designation -> ?N].
```

**Solution (operating day 27 Sept 2026)**

```text
B = sp_8500218, N = "Olten"
B = sp_8502001, N = "Zofingen"
B = sp_8503000, N = "Zürich HB"
B = sp_8504100, N = "Fribourg/Freiburg"
B = sp_8504103, N = "Flamatt"
B = sp_8504414, N = "Lyss"
B = sp_8507006, N = "Münsingen"
B = sp_8507100, N = "Thun"
B = sp_8508005, N = "Burgdorf"
```

**Dataset:** "Target/Actual Comparison SBB departure/arrival times: (previous day)"

### 1.7 Which long-distance stations have no WiFi? (open-world test)

```framex
?- ?S:LongDistanceStation AND NOT ?S[hasWifi -> true].
```

**Solution**

```text
unknown
```

**Datasets:** "Wifi@Station" + "Target/Actual Comparison SBB departure/arrival times: (previous day)" (to define `LongDistanceStation`)

> **Note:** The expected answer is unknown. The world is open and no dataset is declared complete for `hasWifi`, so a missing WiFi record does not prove that a station has no WiFi. This query shows how the open-world assumption works.

## Level 2: Joins across datasets

### 2.1 Which stations in Ticino have WiFi?

```framex
?- ?S[inCanton -> canton_ti] AND ?S[hasWifi -> true] AND ?S[designation -> ?N].
```

**Solution**

```text
N = "Bellinzona", S = sp_8505213
N = "Locarno", S = sp_8505400
N = "Lugano", S = sp_8505300
```

**Datasets:** "Wifi@Station" + "Service Points (Didok) based on opentransportdata.swiss" (for the canton)

> **Note:** "Wifi@Station" has no canton field. Join on the stop-point number (`bpuic` = `number`).

### 2.2 Which platforms at Bern are longer than 320 m? Give the platform number and length.

```framex
?- ?P:LongPlatform AND ?P[atStopPoint -> sp_8507000] AND ?P[platformNumber -> ?No] AND ?P[platformLength -> ?L].
```

**Solution (7 platforms)**

```text
L = 362.0, No = "12/13", P = platform_b59ffde62ae2b782e4228b7995c02c9a
L = 368.0, No = "49/50", P = platform_14af45e646ab9eccbd45b83b27e9e918
L = 369.0, No = "9/10", P = platform_9b962c759b1d713b387339316f46fc01
L = 506.0, No = "5/6", P = platform_aa0b04fdfb0ac2ef34939d52dfa6ef1f
L = 510.0, No = "3/4", P = platform_dd92174a5181ae5452c1f64da6eb73fd
L = 521.0, No = "7/8", P = platform_695594f9869c0fdc5122290b8c9855ed
L = 539.0, No = "1/2", P = platform_934726eff0382c9ab3c5bf70cee6e73c
```

**Dataset:** "Stop: platform length (body)"

> **Note:** `LongPlatform` is a derived class (length > 320 m). All platforms listed for Bern exceed that threshold.

### 2.3 Which sector letters are signed on track 3 at Zürich HB?

```framex
?- ?B:SectorBoard AND ?B[atStopPoint -> sp_8503000] AND ?B[trackNumber -> "3"] AND ?B[sectorFront -> ?F].
```

**Solution (7 boards, letters A–D)**

```text
B = sectorboard_525d71545e26c6099d1a220fa267360b, F = "D"
B = sectorboard_646f9a6a8d5844a05df1003dd1d38052, F = "C"
B = sectorboard_880862013b865aa5590c5971378e2a8d, F = "B"
B = sectorboard_9ad31eedce6a29c6897a6ef0ae786d5e, F = "C"
B = sectorboard_b062e6a23af4293b7a022e2efaba138d, F = "A"
B = sectorboard_d13c933a04fdafd72d1c167e55727ae9, F = "B"
B = sectorboard_d3f85a02213933b0bee6f521f11a3c29, F = "A"
```

**Dataset:** "Stop: sector boards"

### 2.4 Which stations in canton Bern have a waiting hall that is planned but not built yet?

```framex
?- ?F:WaitingHall AND ?F[status -> "PROJEKTIERT NEU"] AND ?F[atStopPoint -> ?S] AND ?S[inCanton -> canton_be] AND ?S[designation -> ?N].
```

**Solution (8 stations)**

```text
F = waitinghall_0702bde03f234f24b9fe4791190ec8c2, N = "Brügg BE", S = sp_8504416
F = waitinghall_106c0b5e73262bbc2ac1b6550172cc35, N = "Kallnach", S = sp_8504402
F = waitinghall_124c0226864b9873a480969a722f3d49, N = "Neuenegg", S = sp_8504192
F = waitinghall_6685757fb1a47f1fc2fd62c76d9c6e21, N = "Uttigen", S = sp_8507009
F = waitinghall_c118077c4fa1267fd15c40e9e42ab45a, N = "Twann", S = sp_8504228
F = waitinghall_cc5e644d7879743f82f310a0dc8700fc, N = "Herzogenbuchsee", S = sp_8508008
F = waitinghall_e0f9c521c18b9c6481c8f259ee2a65e6, N = "Hindelbank", S = sp_8508003
F = waitinghall_f95cebbb03869ff2d424af958450fafb, N = "St-Imier", S = sp_8504310
```

**Datasets:** "Stop: waiting rooms". The canton comes from its `kanton` field, or from "Service Points (Didok) based on opentransportdata.swiss".

### 2.5 Which waiting halls in canton Zürich are planned for demolition?

```framex
?- ?F:WaitingHall AND ?F[status -> "PROJEKTIERT ABBRUCH"] AND ?F[atStopPoint -> ?S] AND ?S[inCanton -> canton_zh] AND ?S[designation -> ?N].
```

**Solution (8 halls at 7 stations)**

```text
F = waitinghall_327e2ca4df41dfddbc616ba14c261da4, N = "Wallisellen", S = sp_8503129
F = waitinghall_7e77303fdae9125b1fe7cee16b8ff95f, N = "Stäfa", S = sp_8503107
F = waitinghall_9448cb1fe0e4a3f027dc2b474869dab3, N = "Zürich Seebach", S = sp_8503007
F = waitinghall_adcd16a7c79a4da1d0a0929282b00143, N = "Stäfa", S = sp_8503107
F = waitinghall_af33de5ed54d665d1b05e0c35beb94e5, N = "Dietlikon", S = sp_8503306
F = waitinghall_bbdc6f9cedab81c878c3c47aa9172752, N = "Bassersdorf", S = sp_8503307
F = waitinghall_c65fff2227625e3f925b86660c88dd13, N = "Stettbach", S = sp_8503147
F = waitinghall_cb616c4a15f50eb9a26c8b3407ec8ee3, N = "Aathal", S = sp_8503124
```

**Datasets:** "Stop: waiting rooms". The canton comes from its `kanton` field, or from "Service Points (Didok) based on opentransportdata.swiss".

### 2.6 How many people used each station on line 900 in 2024?

```framex
?- ?S[servedByLine -> line_900] AND ?S[observedFrequency("2024") -> ?V] AND ?S[designation -> ?N].
```

**Solution**

```text
N = "Bad Ragaz", S = sp_8509004, V = 3100.0
N = "Chur", S = sp_8509000, V = 28500.0
N = "Landquart", S = sp_8509002, V = 18600.0
N = "Maienfeld", S = sp_8509003, V = 980.0
```

**Datasets:** "Line (Operation Points)" + "Ein- und Aussteigende an Bahnhöfen"

> **Note:** Zizers SBB is on line 900 but has no 2024 passenger count, so it drops out of the join.

## Level 3: Derived classes and comparisons

### 3.1 Which stations are junctions in Graubünden, and which lines meet there?

```framex
?- ?S:Junction AND ?S[inCanton -> canton_gr] AND ?S[servedByLine -> ?L] AND ?L[label -> ?LL] AND ?S[designation -> ?N].
```

**Solution:** Chur (lines 900, 920) and Landquart (lines 900, 910, 920)

```text
L = line_900, LL = "900", N = "Chur", S = sp_8509000
L = line_900, LL = "900", N = "Landquart", S = sp_8509002
L = line_910, LL = "910", N = "Landquart", S = sp_8509002
L = line_920, LL = "920", N = "Chur", S = sp_8509000
L = line_920, LL = "920", N = "Landquart", S = sp_8509002
```

**Datasets:** "Line (Operation Points)" + "Service Points (Didok) based on opentransportdata.swiss" (for the canton) + "SBB’s route network" (for line labels)

> **Note:** `Junction` = a stop point served by at least 2 lines.

### 3.2 Which stations were busy in 2025 (over 20,000 passengers a day) but had 20,000 or fewer in 2018?

```framex
?- ?S[busyIn("2025") -> true] AND ?S[observedFrequency("2018") -> ?V] AND ?V <= 20000 AND ?S[designation -> ?N].
```

**Solution (V = 2018 value)**

```text
N = "Arth-Goldau", S = sp_8505004, V = 14200.0
N = "Bellinzona", S = sp_8505213, V = 16000.0
N = "Brig", S = sp_8501609, V = 16700.0
N = "Lugano", S = sp_8505300, V = 16300.0
N = "Renens VD", S = sp_8501118, V = 18300.0
N = "Schaffhausen", S = sp_8503424, V = 18900.0
```

**Dataset:** "Ein- und Aussteigende an Bahnhöfen"

> **Note:** `busyIn(Year)` is a parameterised derived property (DTV > 20,000 in that year).

### 3.3 Which long-distance stations can you reach from Zürich HB without stopping?

```framex
?- sp_8503000[nonStopTo -> ?B] AND ?B:LongDistanceStation AND ?B[designation -> ?N].
```

**Solution (18 stations, operating day 27 Sept 2026)**

```text
B = sp_8500010, N = "Basel SBB"
B = sp_8500218, N = "Olten"
B = sp_8500309, N = "Brugg AG"
B = sp_8502113, N = "Aarau"
B = sp_8502119, N = "Lenzburg"
B = sp_8502204, N = "Zug"
B = sp_8502206, N = "Baar"
B = sp_8503001, N = "Zürich Altstetten"
B = sp_8503006, N = "Zürich Oerlikon"
B = sp_8503016, N = "Zürich Flughafen"
B = sp_8503202, N = "Thalwil"
B = sp_8503206, N = "Wädenswil"
B = sp_8503424, N = "Schaffhausen"
B = sp_8503504, N = "Baden"
B = sp_8506000, N = "Winterthur"
B = sp_8506302, N = "St. Gallen"
B = sp_8507000, N = "Bern"
B = sp_8509411, N = "Sargans"
```

**Dataset:** "Target/Actual Comparison SBB departure/arrival times: (previous day)"

> **Note:** `LongDistanceStation` = a station served by at least one long-distance category (IC, IR, EC, ICE, TGV, NJ, RJX…). Winterthur and St. Gallen appear only because of a single night train (NJ).

### 3.4 Which stations had TGV service?

```framex
?- ?S[servedByCategory -> "TGV"] AND ?S[designation -> ?N].
```

**Solution (operating day 27 Sept 2026)**

```text
N = "Basel SBB", S = sp_8500010
N = "Genève", S = sp_8501008
N = "Lausanne", S = sp_8501120
N = "Vallorbe", S = sp_8501103
N = "Zürich HB", S = sp_8503000
```

**Dataset:** "Target/Actual Comparison SBB departure/arrival times: (previous day)"

> **Note:** The dataset also contains TGV stops in France (Paris Gare de Lyon, Dijon, Mulhouse…). The reference solution lists only the Swiss ones.

### 3.5 Which stations are interchanges to the tram?

```framex
?- ?S:Interchange AND ?S[servesMode -> mode_tram] AND ?S[designation -> ?N].
```

**Solution (6 stations)**

```text
N = "Worb Dorf", S = sp_8507063
N = "Zürich Stadelhofen, Bahnhof", S = sp_8503059
N = "Zürich, Balgrist", S = sp_8530811
N = "Zürich, Hegibachplatz", S = sp_8530812
N = "Zürich, Rehalp", S = sp_8591315
N = "Zürich, Wetlistrasse", S = sp_8591429
```

**Dataset:** "Service Points (Didok) based on opentransportdata.swiss"

> **Note:** `Interchange` = a service point whose `meansoftransport` contains both TRAIN and TRAM. Big stations such as Zürich HB are not included because their tram stops are separate service points.
