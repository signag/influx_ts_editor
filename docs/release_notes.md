# Influx Time Series Editor Release Notes

[![Up](img/goup.gif)](./index.md)

## V1.2.0

### New Features

- Supports [deletion of data points](./usage.md#deleting-data-points)
- Supports [insertion of new data points](./usage.md#inserting-data-points)

## V1.1.1

### Changes

- Extended the time range for query of field keys from the InfluxDB schema from -30d (default) to -370d.
<br>This will retrieve all field keys for a measurement which have been used within the last year.

## V1.1.0

### New Features

- Range selection by [mouse click-dragging](./usage.md#selecting-range-with-mouse).
- Minimum time range window is now 1 m (1 minute)

### Changes

- The graphical representation of results now shows time series points on a real time axis instead as equally-spaced points. So, the distance of points on the x-axis correctly represents their time difference.

## V1.0.1

### Bugfixes

- Fixed typing of field values for modified values.
<br>Previously, an error occured during update when values did not have the correct type.
<br>Now, the type of the field value is determined from the original time series. Updated values are casted to this type before update.

### Changes

- The default port was changed from 5000 to 8087 which is next to the default port uset by InfluxDB

## V1.0.0

Initial Commit
