"""The Sound card: the fireworks music's speaker, volume and quiet hours."""

from settings_page.markup import _attr, _field, _input, _options, _section, _switch, icon, sub_dict
from utils.config import DEFAULT_VOLUME


def _speaker_control(device, sound_cards):
    """The speaker dropdown, with a box for an ALSA device that isn't one of the board's cards."""
    custom = bool(device) and device not in sound_cards
    custom_input = _input(
        "sound_device_custom", device if custom else "", extra=' class="mono" placeholder="plughw:CARD=Device,DEV=0"'
    )
    return (
        _options(
            "sound_device",
            [("", "The board's default")] + [(c, c) for c in sound_cards] + [("custom", "Other device…")],
            "custom" if custom else device,
        )
        + f'<div class="below" id="custom-device"><label class="mini" for="sound_device_custom">ALSA device'
        f"</label>{custom_input}</div>"
    )


def _volume_control(volume):
    return (
        '<div class="volume">'
        f'<input type="range" id="volume_slider" class="js-only" min="0" max="100" '
        f'value="{_attr(volume if volume != "" else DEFAULT_VOLUME)}" aria-label="Volume slider" hidden>'
        + _input(
            "sound_volume", volume, "number", f' min="0" max="100" inputmode="numeric" placeholder="{DEFAULT_VOLUME}"'
        )
        # Plain buttons, not submits: Enter in any field must still mean Save.
        + '</div><div class="below buttons js-only" hidden>'
        f'<button type="button" class="secondary" name="volume_action" value="set">{icon("check")}Set volume</button>'
        f'<button type="button" class="secondary" name="volume_action" value="test">{icon("sound")}Play test sound'
        "</button></div>"
        '<p class="hint volume-status" id="volume-status" role="status" aria-live="polite"></p>'
    )


def _quiet_hours_control(quiet):
    inputs = (
        _input("quiet_start", quiet.get("start", ""), "time", ' aria-label="Quiet from"')
        + "<span>to</span>"
        + _input("quiet_end", quiet.get("end", ""), "time", ' aria-label="Quiet until"')
    )
    return f'<div class="pair">{inputs}</div>'


def sound_card(config, sound_cards):
    """sound_cards: ALSA device names for the dropdown."""
    sound = sub_dict(config, "sound")
    return _section(
        "sound",
        "Sound",
        "The fireworks music, from a speaker on the board.",
        (
            _switch(
                "sound_enabled",
                "Play the fireworks music",
                sound.get("enabled", False),
                "Needs a speaker, and the music in the sounds folder.",
            )
            + _field("sound_device", "Speaker", _speaker_control(sound.get("device") or "", sound_cards))
            + _field(
                "sound_volume",
                "Volume",
                _volume_control(sound.get("volume", "")),
                f"0 to 100, set before each show. Blank is {DEFAULT_VOLUME}: louder can draw more power than "
                "the Pi can spare and slow the show down. Set volume saves just this, with no restart; "
                "Play test sound plays a few seconds at it without saving.",
            )
            + _field(
                "quiet_start",
                "Quiet hours",
                _quiet_hours_control(sub_dict(sound, "quiet_hours")),
                "No music between these times. Leave both blank for none.",
            )
        ),
        "sound",
    )
