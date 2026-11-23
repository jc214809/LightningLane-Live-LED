# Sounds

WAV clips the board plays through its speaker while the castle fireworks run. This folder is committed, but only this README is: Disney's audio isn't ours to publish, so the WAVs are gitignored and every board needs its own copy. Without them the board runs normally, just silently, and shows a red music-note badge (bottom-left) while sound is turned on.

## Getting sound working

1. **Hardware.** A Pi needs a USB sound card and a powered speaker (the Pi's own audio is turned off: it shares hardware with the LED matrix). Parts and hook-up: [docs/hardware/SOUND.md](../docs/hardware/SOUND.md). An emulator run on a Mac uses the Mac's speakers.
2. **Get the audio** for each show you want to hear (the files below). For Happily Ever After, the synced shows are timed to ["Happily Ever After Full Show Audio" on SoundCloud](https://soundcloud.com/my-happy-place-380915582/happily-ever-after-full-show-audio); convert it as it is, with no trimming. If the link dies, any copy of the same recording will do: `align_audio.py` (below) tells you whether it matches.
3. **Convert it to WAV.** The Pi plays through `aplay`, which can't read MP3 or M4A. With [ffmpeg](https://ffmpeg.org/):

   ```sh
   ffmpeg -i "Happily Ever After Full Show Audio.mp3" -ac 2 -ar 44100 -sample_fmt s16 happily-ever-after.wav
   ```

4. **Copy it into this folder** on each board, under `~/LightningLane-Live-LED/sounds/`. From a Mac, with the board on Tailscale or the home network:

   ```sh
   scp happily-ever-after.wav <user>@<hostname>.local:LightningLane-Live-LED/sounds/
   ```

   Updates leave the folder alone, so this is once per board.
5. **Turn sound on** in the settings page's Sound card (or `"sound": {"enabled": true}` in `config.json`; every key is in the main README's Sound section). The card's **Play test sound** plays a few seconds of `fireworks.wav`, or a chime if there isn't one.
6. **Hear a show now:** add `"force": true` to its entry in `config.json`'s `shows` and restart the service (main README, Sound section).

## The files

For each show the board plays the first of these that exists:

| File | Plays for |
|---|---|
| `happily-ever-after.wav` | Happily Ever After, the nightly show. **Must be the "Happily Ever After Full Show Audio" recording**: the synced versions (`"v1"`, `"v2"`) time every burst to it, and run 1102s of it. Another recording plays, but the fireworks drift off the music. |
| `disneys-not-so-spooky-spectacular.wav` | The Halloween party's show |
| `minnies-wonderful-christmastime-fireworks.wav` | The Christmas party's show |
| `fireworks.wav` | Any show without its own file, the default five-minute castle fireworks, and the settings page's test sound |

A file's name is the show's name in lower case with dashes, no apostrophes (`utils/sound.py:clip_name`). A clip stops when the board's fireworks end: five minutes in, or at the end of a synced show.

To check a Happily Ever After file is the right recording, `python3 docs/shows/happily-ever-after/align_audio.py` lines it up against the show video (needs `yt-dlp`, `ffmpeg` and numpy): strong matches on one straight line mean it's the same track.

## Troubleshooting

- **Music note with an X (bottom-left):** sound is on, but a show has no file here. Check the name against the table.
- **Speaker with an X:** no player (`aplay`) or no sound card for `sound.device`; `aplay -l` lists the cards.
- **White flash or the board slows during the show:** a USB speaker near full volume under-volts the Pi. Keep `volume` at 80 or less.
- **Silent at night:** `quiet_hours` in `config.json`.
