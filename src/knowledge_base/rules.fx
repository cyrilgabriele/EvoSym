world open.

?P:LongPlatform <- ?P:Platform AND ?P[platformLength -> ?L] AND ?L > 320.

// A planned demolition still describes a standing hall; a planned new hall does not.
?S[hasWaitingHall -> true] <- ?H:WaitingHall AND ?H[atStopPoint -> ?S] AND
    (?H[status -> "BESTEHEND"] OR ?H[status -> "PROJEKTIERT ABBRUCH"]).

?S:Junction <- ?S:StopPoint AND ?S[servedByLine -> ?A] AND
    ?S[servedByLine -> ?B] AND ?A != ?B.

?S[busyIn(?Year) -> true] <- ?S:StopPoint AND
    ?S[observedFrequency(?Year) -> ?V] AND ?V > 20000.

?S[servedByCategory -> ?C] <- ?E:StopEvent AND ?E[atStopPoint -> ?S] AND
    ?E[ofRun -> ?R] AND ?R:TrainRun AND ?R[category -> ?C].

?S:LongDistanceStation <- ?S:StopPoint AND ?S[servedByCategory -> ?C] AND
    (?C = "IC" OR ?C = "IR" OR ?C = "EC" OR ?C = "ICE" OR
     ?C = "TGV" OR ?C = "NJ" OR ?C = "RJ" OR ?C = "RJX").

// Directional adjacency of actual stops of the same run, never a transitive closure.
?A[nonStopTo -> ?B] <- ?E:StopEvent AND ?E[nextStop -> ?F] AND ?F:StopEvent AND
    ?E[ofRun -> ?R] AND ?F[ofRun -> ?R] AND
    ?E[atStopPoint -> ?A] AND ?F[atStopPoint -> ?B] AND ?A != ?B.

?S:Interchange <- ?S:StopPoint AND ?S[servesMode -> mode_train] AND
    ?S[servesMode -> mode_tram].
