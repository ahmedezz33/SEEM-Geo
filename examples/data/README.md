# Example data folder

This folder is for your field data files:

- `example_stations.csv` — **FICTITIOUS** station coordinates for demonstration
  (UTM Zone 30N, mid-Mediterranean — clearly a placeholder, not a real site).
  Replace with your own borehole coordinate CSV.

- `ERT/` — place your ERT shot files here (CSV, one per station)
- `MASW/` — place your MASW shot gathers here

To generate test data for the full pipeline:
```
seem-geo gen-data --out examples/data/
```

**No real client, project, or location data is included in this repository.**
