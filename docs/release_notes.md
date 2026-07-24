# Influx Time Series Editor Release Notes

[![Up](img/goup.gif)](./index.md)

## V1.1.0

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
