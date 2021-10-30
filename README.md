# NysseAsemanaytto

A configurable copy of Nysse's busstop display.

You need to create a `config.json` file from the included `config.example.json` template. <br />
Config parameters are documented below:
- `stopcode`: a number (i.e. 3522). If stopcode includes any leading zeros, strip them (i.e. 0825 => 825).
- `departure_count`: a number that determines how many departures to show.
- `poll_rate`: how often to refresh the departure data. (Waits the specified amount of seconds between polls. You should avoid doing more than 10 requests before to reduce load on Digitransit's servers)
- `endpoint`: The Digitransit API:s endpoint you want to send requests to. Can be targeted to a server hosted locally.
- `window_size`: The size of the process window
- `fullscreen`: Pretty self-explanatory
- `framerate`: Limit the window refresh rate. -1 if unlocked.
