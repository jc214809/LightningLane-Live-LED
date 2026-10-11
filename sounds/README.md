# Sounds

WAV clips the board plays through its speaker. Everything here but this file is gitignored: Disney's audio isn't ours to publish, so each board gets its own copy.

Turn sound on in `config.json` (see the README's Sound section). For the fireworks show the board plays the first of these that exists:

- `<show>.wav`, the show's name in lower case with dashes: `happily-ever-after.wav`, `disneys-not-so-spooky-spectacular.wav`
- `fireworks.wav`, for any show

The clip stops when the board's fireworks end: 5 minutes in, or at the end of a show with a score in `display/fireworks/shows/` (Happily Ever After's runs the whole 1102s, so `happily-ever-after.wav` must be the recording that score was timed to: "Happily Ever After Full Show Audio"). Use WAV: the Pi plays through `aplay`, which can't read MP3.
