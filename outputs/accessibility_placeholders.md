# Future Accessibility Metrics

This project is structured to add jobs reachable within 30 minutes by car and transit, but Phase 1 does not fake network accessibility.

## Needed For Car Accessibility

- Routable street network or travel-time API.
- Tract origin points, preferably population-weighted centroids.
- Job destination points or tract-level job allocation method.
- Departure time assumptions and congestion treatment.

## Needed For Transit Accessibility

- Static GTFS feed with stops, routes, trips, stop_times, calendar, and calendar_dates.
- Walking access assumptions to stops.
- Transfer assumptions and maximum walking distance.
- Departure time window, such as weekday 7:00-9:00 AM.
- Routing engine such as OpenTripPlanner, r5py/R5, Conveyal, or a comparable API.

## Planned Output Fields

- `jobs_reachable_30min_car`
- `jobs_reachable_30min_transit`
- `share_county_jobs_reachable_30min_car`
- `share_county_jobs_reachable_30min_transit`
