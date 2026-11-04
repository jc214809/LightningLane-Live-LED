#!/usr/bin/env bash
# Sets up a Raspberry Pi LED board for one app: LightningLane-Live-LED, Peloton-LED or
# MLB-LED-Scoreboard. Asks everything up front, shows a summary, then does it all; safe to re-run
# (to update, or to switch apps). Each app's own installer does the app; this script does the board
# around it: hostname, a second Wi-Fi network, the Wi-Fi setup hotspot, the power button, matrix
# tuning and the service.
#
#   sudo bash board-setup.sh                      # asks
#   sudo bash board-setup.sh --answers board.txt  # KEY=value lines skip those questions
#   bash board-setup.sh --dry-run ...             # prints what it would do, changes nothing
#   sudo bash board-setup.sh --wifi-setup-only    # just the Wi-Fi setup hotspot and settings page (LLL-install.sh's)
set -Eeuo pipefail

ROOT="${BOARD_SETUP_ROOT:-}"   # tests: a folder standing in for / (system files are read from it)
SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"

LLL_REPO=https://github.com/jc214809/LightningLane-Live-LED.git
PELOTON_REPO=https://github.com/jc214809/Peloton-LED.git
MLB_REPO=https://github.com/MLB-LED-Scoreboard/mlb-led-scoreboard.git
LLL_UNIT=LightningLane-Live-LED.service
PELOTON_UNIT=peloton-led.service
MLB_UNIT=mlb-led-scoreboard.service
SETTINGS_UNIT=lll-settings.service  # LightningLane-Live-LED's settings page (settings_page/server.py)
UNIT_DIR="$ROOT/etc/systemd/system"
# comitup: with no known Wi-Fi in range, it opens a hotspot whose page puts the board on a network.
COMITUP_SOURCE_DEB=https://davesteele.github.io/comitup/deb/davesteele-comitup-apt-source_1.3_all.deb
COMITUP_CALLBACK=/usr/local/bin/comitup-callback
COMITUP_STATE=/run/comitup-state   # utils/wifi_setup.py reads it
HOTSPOT_SUFFIX=-setup              # the hotspot is "<hostname>-setup"

ANSWER_KEYS="BOARD_NAME APP PANEL_OPTIONS LED_ROWS LED_COLS LED_GPIO_MAPPING LED_SLOWDOWN_GPIO EXTRA_ARGS LLL_BRANCH
PELOTON_AUTO_TOKEN WIFI2 WIFI2_IFACE WIFI2_NAME WIFI2_SSID WIFI2_HIDDEN POWER_BUTTON SPEAKER"
ANSWERED=" "
DRY_RUN=false
ASSUME_YES=false
NEEDS_REBOOT=false
WROTE=false  # set by write_file when it changes (or, in a dry run, would change) a file
RENAMED=false

usage() {
    cat <<'USAGE'
Usage: sudo bash board-setup.sh [--answers FILE] [--branch NAME] [--yes] [--dry-run] [--wifi-setup-only] [-h]

  --answers FILE  KEY=value lines (# comments) answering questions ahead, e.g. APP=lll.
                  Keys: BOARD_NAME APP PANEL_OPTIONS LED_ROWS LED_COLS LED_GPIO_MAPPING LED_SLOWDOWN_GPIO
                  EXTRA_ARGS LLL_BRANCH PELOTON_AUTO_TOKEN WIFI2 WIFI2_IFACE WIFI2_NAME
                  WIFI2_SSID WIFI2_HIDDEN POWER_BUTTON SPEAKER. The Wi-Fi password is never in it: it's
                  asked (or, with stdin not a terminal, read from its first line), and a blank
                  one keeps the saved network.
  --branch NAME   LightningLane-Live-LED's branch (default develop-beta), like LLL_BRANCH=NAME.
  --yes           Don't ask: unanswered questions take their defaults, and no confirmation.
  --dry-run       Print the commands and files it would write; change nothing.
  --wifi-setup-only
                  Only install or update the Wi-Fi setup hotspot (comitup), with no questions,
                  and, run from LightningLane-Live-LED's folder, its settings page.
USAGE
}

die() { echo "board-setup: $*" >&2; exit 1; }
say() { printf '\n→ %s\n' "$*"; }

# ─── Doing things (or, with --dry-run, printing them) ─────────────────────
run() {
    if [[ "$DRY_RUN" == true ]]; then printf '+ %s\n' "$*"; else "$@"; fi
}

in_dir() {  # in_dir DIR COMMAND...: run COMMAND from DIR
    local dir=$1; shift
    if [[ "$DRY_RUN" == true ]]; then printf '+ (cd %s && %s)\n' "$dir" "$*"; else (cd "$dir" && "$@"); fi
}

as_user() { run runuser -u "$BOARD_USER" -- "$@"; }

write_file() {  # write_file PATH MODE < content; SHOWN replaces the content in --dry-run output
    local path=$1 mode=$2 content
    content="$(cat)"
    if [[ -f "$path" ]] && [[ "$(cat "$path")" == "$content" ]]; then
        echo "  unchanged: $path"
        return
    fi
    if [[ "$DRY_RUN" == true ]]; then
        printf '+ write %s (mode %s):\n%s\n' "$path" "$mode" "${SHOWN:-$content}" | sed 's/^/    /'
        WROTE=true
        return
    fi
    mkdir -p "$(dirname "$path")"
    local tmp
    tmp="$(mktemp)"
    printf '%s\n' "$content" > "$tmp"
    install -m "$mode" "$tmp" "$path"
    rm -f "$tmp"
    echo "  wrote $path"
    WROTE=true
}

# ─── Answers ──────────────────────────────────────────────────────────────
read_answers() {
    local file=$1 line key value
    [[ -f "$file" ]] || die "no answers file at $file"
    while IFS= read -r line || [[ -n "$line" ]]; do
        line="${line%$'\r'}"
        [[ "$line" =~ ^[[:space:]]*(#|$) ]] && continue
        [[ "$line" == *=* ]] || die "$file: not KEY=value: $line"
        key="${line%%=*}"; key="${key//[[:space:]]/}"
        value="${line#*=}"
        value="${value#\"}"; value="${value%\"}"; value="${value#\'}"; value="${value%\'}"
        [[ " $(echo $ANSWER_KEYS) " == *" $key "* ]] || die "$file: unknown key $key (keys: $(echo $ANSWER_KEYS))"
        printf -v "$key" '%s' "$value"
        ANSWERED="$ANSWERED$key "
    done < "$file"
}

ask() {  # ask VAR QUESTION DEFAULT [CHOICE...]: answers file, else prompt, else the default
    local var=$1 question=$2 default=$3 value
    shift 3
    while true; do
        if [[ "$ANSWERED" == *" $var "* ]]; then
            value="${!var}"
        elif [[ "$ASSUME_YES" == false && -t 0 ]]; then
            read -r -p "$question [$default]: " value || true
            value="${value:-$default}"
        else
            value="$default"
        fi
        if [[ $# -eq 0 ]] || [[ " $* " == *" $value "* ]]; then
            printf -v "$var" '%s' "$value"
            return
        fi
        echo "  $question: choose one of: $*" >&2
        [[ "$ANSWERED" != *" $var "* && "$ASSUME_YES" == false && -t 0 ]] || die "$var=$value isn't one of: $*"
    done
}

collect_answers() {
    ask BOARD_NAME "Hostname (the board's name on the network, and its settings page's)" "$(hostname -s 2>/dev/null || hostname)"
    [[ "$BOARD_NAME" =~ ^[A-Za-z0-9]([A-Za-z0-9-]{0,61}[A-Za-z0-9])?$ ]] || die "not a usable hostname: $BOARD_NAME"
    hotspot_name_fits "$BOARD_NAME" || die "$BOARD_NAME is too long: its Wi-Fi setup hotspot, $BOARD_NAME$HOTSPOT_SUFFIX, would be over Wi-Fi's 32 letters"
    ask APP "App to run (lll = LightningLane-Live-LED, peloton = Peloton-LED, mlb = MLB-LED-Scoreboard)" lll lll peloton mlb
    # Each app can keep these in its own config (LLL: config.json's matrix, from its settings page),
    # so by default they aren't asked and no flags go in the service.
    ask PANEL_OPTIONS "Set the panel options (size, GPIO mapping, slowdown, extra flags) in the service? (yes/no; no leaves them to the app's own config)" no yes no
    if [[ "$PANEL_OPTIONS" == yes ]]; then
        ask LED_ROWS "Panel rows" 32 32 64
        ask LED_COLS "Panel columns" 64 64
        ask LED_GPIO_MAPPING "GPIO mapping (adafruit-hat-pwm needs the Bonnet's GPIO 4-18 jumper soldered)" adafruit-hat-pwm adafruit-hat-pwm adafruit-hat regular
        ask LED_SLOWDOWN_GPIO "GPIO slowdown (2 on a Pi Zero, 4 on a Pi 4)" 2 0 1 2 3 4
        ask EXTRA_ARGS "Extra app flags, like --led-brightness=85 (none)" ""
    else
        EXTRA_ARGS=""
    fi
    case "$APP" in
        lll) ask LLL_BRANCH "LightningLane-Live-LED branch" develop-beta
             [[ "$LLL_BRANCH" =~ ^[A-Za-z0-9._/-]+$ && "$LLL_BRANCH" != -* ]] || die "not a branch name: $LLL_BRANCH"
             ask SPEAKER "USB speaker plugged in? (yes/no)" no yes no ;;
        peloton) ask PELOTON_AUTO_TOKEN "Renew the Peloton login automatically? (yes/no; installs Chromium)" no yes no ;;
    esac
    ask WIFI2 "Add a second Wi-Fi network, like a phone hotspot? (yes/no)" no yes no
    if [[ "$WIFI2" == yes ]]; then
        ask WIFI2_IFACE "  Wi-Fi interface" wlan0
        ask WIFI2_SSID "  Network name (SSID)" iPhone
        ask WIFI2_NAME "  Connection name" "$WIFI2_SSID"
        ask WIFI2_HIDDEN "  Hidden network? (yes/no)" no yes no
        [[ "$WIFI2_NAME" =~ ^[A-Za-z0-9._\ -]+$ ]] || die "connection name may use letters, digits, spaces and . _ -"
        [[ "$WIFI2_SSID" != *$'\n'* && "$WIFI2_SSID" != *';'* ]] || die "the SSID can't contain ; or a newline"
        WIFI2_PSK=""
        if [[ -t 0 ]]; then
            read -r -s -p "  Password (blank keeps the saved one): " WIFI2_PSK || true
            echo
        elif [[ "$ASSUME_YES" == false ]]; then
            read -r WIFI2_PSK || true  # unattended: the first line of stdin
        fi
    fi
    ask POWER_BUTTON "Power button on GPIO 3 with its light on GPIO 25 (docs/hardware/POWER.md)? (yes/no)" no yes no
}

panel_summary() {
    if [[ "$PANEL_OPTIONS" == yes ]]; then
        echo "  Panel         ${LED_COLS}x$LED_ROWS, $LED_GPIO_MAPPING, slowdown $LED_SLOWDOWN_GPIO"
        echo "  Extra flags   ${EXTRA_ARGS:-none}"
    else
        echo "  Panel         left to the app's own config"
    fi
}

show_summary() {
    cat <<EOF

Board setup
  Hostname      $BOARD_NAME (now $(hostname -s 2>/dev/null || hostname))
  User          $BOARD_USER ($BOARD_HOME)
  App           $APP${LLL_BRANCH:+ (branch $LLL_BRANCH)}
$(panel_summary)
  Second Wi-Fi  $WIFI2${WIFI2_SSID:+ ($WIFI2_SSID on $WIFI2_IFACE)}
  Wi-Fi setup   an open $BOARD_NAME$HOTSPOT_SUFFIX hotspot when no known Wi-Fi is in range
  Power button  $POWER_BUTTON
EOF
    [[ "$APP" == lll ]] && echo "  Speaker       $SPEAKER"
    [[ "$APP" == peloton ]] && echo "  Auto token    $PELOTON_AUTO_TOKEN"
    if [[ "$DRY_RUN" == false && "$ASSUME_YES" == false ]]; then
        local answer
        read -r -p $'\nGo ahead? [Y/n] ' answer || true
        [[ "$answer" =~ ^[Nn] ]] && die "stopped; nothing changed"
    fi
    return 0
}

# ─── Board steps ──────────────────────────────────────────────────────────
boot_file() {  # boot_file NAME: Bookworm keeps it in /boot/firmware, older releases in /boot
    if [[ -f "$ROOT/boot/firmware/$1" ]]; then echo "$ROOT/boot/firmware/$1"; else echo "$ROOT/boot/$1"; fi
}

set_hostname() {
    local current
    current="$(hostname -s 2>/dev/null || hostname)"
    [[ "$current" == "$BOARD_NAME" ]] && { echo "  hostname already $BOARD_NAME"; return; }
    say "Renaming the board $current → $BOARD_NAME"
    RENAMED=true  # the Wi-Fi setup hotspot is named after it
    run hostnamectl set-hostname "$BOARD_NAME"
    if grep -q '^127\.0\.1\.1' "$ROOT/etc/hosts" 2>/dev/null; then
        run sed -i "s/^127\.0\.1\.1.*/127.0.1.1\t$BOARD_NAME/" "$ROOT/etc/hosts"
    else
        run sed -i "\$a 127.0.1.1\t$BOARD_NAME" "$ROOT/etc/hosts"
    fi
}

setup_wifi() {
    [[ "$WIFI2" == yes ]] || return 0
    local file="$ROOT/etc/NetworkManager/system-connections/$WIFI2_NAME.nmconnection"
    say "Second Wi-Fi network: $WIFI2_SSID"
    if [[ -z "$WIFI2_PSK" ]]; then
        [[ -f "$file" ]] || { [[ "$DRY_RUN" == true ]] && { echo "  (would ask for the password)"; return; }; die "no password given for $WIFI2_SSID"; }
        echo "  keeping the saved network $file"
        return
    fi
    local hidden=false
    [[ "$WIFI2_HIDDEN" == yes ]] && hidden=true
    # A keyfile, so the password is never on a command line (where ps and the shell history see it).
    # The lower autoconnect-priority makes it the fallback when the main network is in range too.
    local body
    body="[connection]
id=$WIFI2_NAME
type=wifi
interface-name=$WIFI2_IFACE
autoconnect=true
autoconnect-priority=-10

[wifi]
mode=infrastructure
ssid=$WIFI2_SSID
hidden=$hidden

[wifi-security]
key-mgmt=wpa-psk
psk=%PSK%

[ipv4]
method=auto

[ipv6]
method=auto"
    SHOWN="${body/\%PSK\%/********}" write_file "$file" 600 <<<"${body/\%PSK\%/$WIFI2_PSK}"
    run systemctl enable --now NetworkManager
    run nmcli connection reload
}

hotspot_name_fits() { (( ${#1} + ${#HOTSPOT_SUFFIX} <= 32 )); }

comitup_conf() {
    cat <<EOF
# Written by board-setup.sh (re-running it rewrites this); man comitup-conf has the other keys.
# With no known Wi-Fi in range, comitup opens this hotspot; joining it brings up a page that puts
# the board on a network. It's open (no ap_password): while it's up, anyone nearby can join it
# and see the Wi-Fi password typed into that page.
ap_name: <hostname>$HOTSPOT_SUFFIX
external_callback: $COMITUP_CALLBACK
EOF
}

comitup_callback() {
    cat <<EOF
#!/bin/sh
# Written by board-setup.sh. comitup runs this as its owner (root) on each change of state:
# HOTSPOT, CONNECTING or CONNECTED. LightningLane-Live-LED reads the state and the hotspot's name
# from $COMITUP_STATE (utils/wifi_setup.py) for its Wi-Fi setup screen.
printf '%s %s\n' "\$1" "\$(hostname)$HOTSPOT_SUFFIX" > $COMITUP_STATE.new && mv $COMITUP_STATE.new $COMITUP_STATE
EOF
}

name_wifi_modes() {
    # comitup only tries saved networks whose mode says infrastructure (comitup/nm.py). A keyfile
    # that leaves the mode to NetworkManager's default (as hand-made ones can) has none, and with
    # only that network saved, comitup would put the hotspot up in its place, cutting the board off.
    local file id
    for file in "$ROOT/etc/NetworkManager/system-connections/"*.nmconnection; do
        [[ -f "$file" ]] || continue
        grep -Eq '^type=(wifi|802-11-wireless)$' "$file" || continue
        sed -n '/^\[wifi\]/,/^\[/p' "$file" | grep -q '^mode=' && continue
        id="$(sed -n 's/^id=//p' "$file" | head -n 1)"
        [[ -n "$id" ]] || continue
        echo "  $id has no Wi-Fi mode: setting it to infrastructure so comitup tries it"
        run nmcli connection modify "$id" 802-11-wireless.mode infrastructure
    done
}

setup_wifi_hotspot() {
    say "Wi-Fi setup hotspot (comitup): an open $BOARD_NAME$HOTSPOT_SUFFIX when no known Wi-Fi is in range"
    # comitup runs on NetworkManager, Raspberry Pi OS's own since Bookworm. An older board on
    # dhcpcd is left alone: moving it over from here could take it off the network.
    if [[ "$DRY_RUN" == false ]] && ! systemctl is-active --quiet NetworkManager; then
        echo "  NetworkManager isn't running (an older Raspberry Pi OS?): skipping the Wi-Fi setup hotspot" >&2
        return 0
    fi
    hotspot_name_fits "$BOARD_NAME" || { echo "  $BOARD_NAME is too long for a hotspot name: skipping" >&2; return 0; }
    name_wifi_modes
    # The settings and callback go first, so comitup starts with them (and --force-confold has
    # dpkg keep this comitup.conf over the package's).
    local changed=false
    WROTE=false
    write_file "$ROOT/etc/comitup.conf" 644 <<<"$(comitup_conf)"
    write_file "$ROOT$COMITUP_CALLBACK" 755 <<<"$(comitup_callback)"
    [[ "$WROTE" == true || "$RENAMED" == true ]] && changed=true
    if [[ ! -x "$ROOT/usr/sbin/comitup" ]]; then
        # From its own repository: Bookworm's comitup needs a newer python3-networkmanager than Debian's.
        run curl -fsSL -o /tmp/davesteele-comitup-apt-source.deb "$COMITUP_SOURCE_DEB"
        run dpkg -i /tmp/davesteele-comitup-apt-source.deb
        run rm -f /tmp/davesteele-comitup-apt-source.deb
        run apt-get update
        # It starts at once and stays on the network the board is on: saved networks in range are
        # always tried before the hotspot.
        run apt-get install -y -o Dpkg::Options::=--force-confold comitup
        echo "  installed; apt upgrade keeps it current"
    elif [[ "$changed" == true ]]; then
        run systemctl restart comitup  # for the new settings or name; it stays on the network it's on
    else
        echo "  already set up"
    fi
}

tune_matrix() {
    # What rpi-rgb-led-matrix wants for a steady picture; LLL's and MLB's installers do the same,
    # but not on every run (LLL's -m skips it) and Peloton-LED's not at all.
    local blacklist="$ROOT/etc/modprobe.d/blacklist-rgbmatrix.conf" cmdline
    if [[ ! -f "$blacklist" ]]; then
        say "Turning off the onboard sound (it clashes with the matrix's hardware pulse)"
        write_file "$blacklist" 644 <<<"blacklist snd_bcm2835"
        NEEDS_REBOOT=true
    fi
    cmdline="$(boot_file cmdline.txt)"
    if [[ -f "$cmdline" ]] && ! grep -qw 'isolcpus=3' "$cmdline"; then
        say "Keeping CPU 3 for the matrix (isolcpus=3 in $cmdline)"
        run sed -i '1 s/$/ isolcpus=3/' "$cmdline"
        NEEDS_REBOOT=true
    fi
}

setup_power_button() {
    [[ "$POWER_BUTTON" == yes ]] || return 0
    local config add=""
    config="$(boot_file config.txt)"
    [[ -f "$config" ]] || { echo "  no $config; skipping the power button" >&2; return; }
    say "Power button (docs/hardware/POWER.md)"
    # The old BoardSetup.sh added "dtoverlay=gpio-shutdown,gpio_pin=3,..." (the defaults): that counts.
    grep -q '^dtoverlay=gpio-shutdown' "$config" || add="${add}dtoverlay=gpio-shutdown"$'\n'
    grep -q '^dtoverlay=gpio-led' "$config" || add="${add}dtoverlay=gpio-led,gpio=25,label=power,trigger=default-on"$'\n'
    if grep -q '^dtparam=i2c_arm=on' "$config"; then
        echo "  warning: $config turns on I2C (dtparam=i2c_arm=on), which takes GPIO 3: the button won't work until it's removed" >&2
    fi
    if [[ -z "$add" ]]; then
        echo "  already in $config"
        return
    fi
    [[ -f "$config.board-setup.bak" ]] || run cp "$config" "$config.board-setup.bak"
    if [[ "$DRY_RUN" == true ]]; then
        printf '+ append to %s:\n[all]\n%s' "$config" "$add" | sed 's/^/    /'
    else
        printf '\n[all]\n%s' "$add" >> "$config"
    fi
    echo "  Pi 4: also check 'rpi-eeprom-config' shows WAKE_ON_GPIO=1 (or nothing), or the button can't wake it"
    NEEDS_REBOOT=true
}

# ─── Apps ─────────────────────────────────────────────────────────────────
checkout() {  # checkout URL DIR BRANCH: clone or update as the board's user
    local url=$1 dir=$2 branch=$3
    if [[ -d "$dir/.git" ]]; then
        give_back "$dir"  # an earlier sudo install may have left root-owned files in .git
        as_user git -C "$dir" fetch origin
        as_user git -C "$dir" checkout "$branch"
        as_user git -C "$dir" pull --ff-only
    else
        as_user git clone --branch "$branch" "$url" "$dir"
    fi
    as_user mkdir -p "$dir/logs"  # both older installers tee into logs/, which a fresh clone lacks
}

give_back() {
    # The installers run git and pip under sudo, leaving root-owned files the user's own
    # `git pull` then can't replace. The services run as root either way.
    run chown -R "$BOARD_USER:$(id -gn "$BOARD_USER")" "$1"
}

matrix_flags() {  # empty when the panel options are left to the app's config
    [[ "$PANEL_OPTIONS" == yes ]] || return 0
    echo "--led-gpio-mapping=$LED_GPIO_MAPPING --led-rows=$LED_ROWS --led-cols=$LED_COLS --led-slowdown-gpio=$LED_SLOWDOWN_GPIO${EXTRA_ARGS:+ $EXTRA_ARGS}"
}

app_unit() {  # app_unit DESCRIPTION DIR EXEC [ENV]: a unit for an app that runs from its checkout as root
    cat <<EOF
[Unit]
Description=$1
Wants=network-online.target
After=network-online.target time-sync.target

[Service]
WorkingDirectory=$2${4:+
Environment=$4}
ExecStart=$3
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
EOF
}

usb_speaker() {  # the first USB sound card's ALSA name, by name so it survives renumbering
    [[ -f "$ROOT/proc/asound/cards" ]] || return 0  # no sound card at all
    sed -n 's/^ *[0-9][0-9]* \[\([^] ]*\) *\]: USB-Audio.*/\1/p' "$ROOT/proc/asound/cards" | head -n 1
}

lll_config() {
    # config.json from the example if missing, plus the panel answers in its "matrix" section (the
    # Pi's model gives the rest) and the speaker. Only the keys it sets change.
    local dir=$1 matrix="" device=""
    if [[ "$PANEL_OPTIONS" == yes ]]; then
        matrix="{\"led_rows\": $LED_ROWS, \"led_cols\": $LED_COLS, \"led_gpio_mapping\": \"$LED_GPIO_MAPPING\", \"led_slowdown_gpio\": $LED_SLOWDOWN_GPIO}"
        echo "  panel settings: in config.json's matrix section"
    else
        echo "  panel options: the Pi model's; set the size and rotation at http://$BOARD_NAME.local:8080"
    fi
    if [[ "$SPEAKER" == yes ]]; then
        device="$(usb_speaker)"
        if [[ -n "$device" ]]; then
            device="plughw:CARD=$device,DEV=0"
            echo "  speaker: $device"
        else
            echo "  no USB sound card found (plug it in and re-run, or see docs/hardware/SOUND.md)" >&2
        fi
    fi
    if [[ ! -f "$dir/config.json" ]]; then
        as_user cp "$dir/config.json-example" "$dir/config.json"
        run chmod 600 "$dir/config.json"
        echo "  made config.json from the example: add your API keys and trip dates to it"
    fi
    [[ -n "$matrix" || -n "$device" ]] || return 0
    if [[ "$DRY_RUN" == true ]]; then
        echo "+ set in $dir/config.json:${matrix:+ matrix=$matrix}${device:+ sound.device=$device}"
        return
    fi
    python3 - "$dir/config.json" "$matrix" "$device" <<'PY'
import json, sys
path, matrix, device = sys.argv[1:]
with open(path, encoding="utf-8") as f:
    config = json.load(f)
if matrix:
    config.setdefault("matrix", {}).update(json.loads(matrix))
if device:
    if "sound" in config:
        config["sound"]["device"] = device
    else:
        print(f"  this branch has no sound settings; when it does, set sound.device to {device}")
with open(path, "w", encoding="utf-8") as f:
    json.dump(config, f, indent=2)
    f.write("\n")
PY
}

install_lll() {
    local dir="$BOARD_HOME/LightningLane-Live-LED" flags=()
    say "LightningLane-Live-LED ($LLL_BRANCH) in $dir"
    checkout "$LLL_REPO" "$dir" "$LLL_BRANCH"
    # A board that has it already skips apt (-p) and the slow matrix-driver build (-m).
    [[ -x "$dir/venv/bin/python3" && -d "$dir/submodules/matrix" ]] && flags=(-p -m)
    # -w: the Wi-Fi setup hotspot is this script's own step, for every app
    in_dir "$dir" bash LLL-install.sh ${flags[@]+"${flags[@]}"} -w
    give_back "$dir"
    lll_config "$dir"
    # No panel flags: the Pi's model and config.json's matrix give them.
    local unit
    unit="$(app_unit "LightningLane-Live-LED" "$dir" "$dir/venv/bin/python3 $dir/disney.py \$ARGS" "\"ARGS=$EXTRA_ARGS\"")"
    retire_old_units "$LLL_UNIT" "$unit"
    write_file "$UNIT_DIR/$LLL_UNIT" 644 <<<"$unit"
    setup_settings_page "$dir"
}

setup_settings_page() {  # setup_settings_page DIR: LightningLane-Live-LED's settings page, its own service
    # Its own service, so a config.json that stops the app can still be fixed from it. Root, as the
    # app: it writes config.json and restarts the app.
    local dir=$1 python=$1/venv/bin/python3
    say "Settings page: config.json from a browser at http://$BOARD_NAME.local:8080 (or 10.41.0.1:8080 on the setup hotspot)"
    [[ -x "$python" ]] || python=/usr/bin/python3
    write_file "$UNIT_DIR/$SETTINGS_UNIT" 644 <<<"$(app_unit "LightningLane-Live-LED settings page" "$dir" "$python -m settings_page.server")"
    run systemctl daemon-reload
    run systemctl enable "$SETTINGS_UNIT"
    run systemctl restart "$SETTINGS_UNIT"  # for an update's new code
}

retire_old_units() {  # retire_old_units UNIT CONTENT: move older copies of UNIT out of systemd's way
    # Boards set up by hand have their own service file, often with the panel flags in it, in /lib
    # or /etc (and sometimes overrides in UNIT.d/). Any of them would keep a board on its old flags
    # instead of its config.json, so each goes to a dated backup folder, never deleted, with the
    # flags it ran with printed so they can be checked on the settings page. Ours, unchanged, stays.
    local unit=$1 content=$2 backup old disabled=false
    backup="$ROOT/var/backups/board-setup/$(date +%Y%m%d-%H%M%S)"
    for old in "$ROOT/lib/systemd/system/$unit" "$UNIT_DIR/$unit" "$UNIT_DIR/$unit.d"; do
        [[ -e "$old" ]] || continue
        if [[ -f "$old" && "$old" == "$UNIT_DIR/$unit" && "$(cat "$old")" == "$content" ]]; then
            continue
        fi
        if [[ "$disabled" == false ]]; then
            # its boot link points at the old file; drop it (the app keeps running) so enabling ours
            # later doesn't trip over a link to a file that's gone
            run systemctl disable "$unit" || true
            disabled=true
        fi
        say "Retiring the old $old (moved to $backup, not deleted)"
        grep -h -r -E '^(Environment|ExecStart)=' "$old" | sed 's/^/  it ran with: /' || true
        run mkdir -p "$backup"
        run mv "$old" "$backup/$(basename "$old")$([[ "$old" == "$ROOT/lib/"* ]] && echo .lib)"
    done
}

install_peloton() {
    local dir="$BOARD_HOME/Peloton-LED" exec_start flags=()
    say "Peloton-LED in $dir (installed to /opt/peloton-led by its own installer)"
    checkout "$PELOTON_REPO" "$dir" main
    # Its unit runs a 64x64 panel on adafruit-hat; a drop-in adds this board's flags (the last
    # one of a flag wins), written first so its installer starts the service with them.
    if [[ "$PANEL_OPTIONS" == yes ]]; then
        exec_start="$(sed -n 's/^ExecStart=//p' "$dir/packaging/systemd/$PELOTON_UNIT" 2>/dev/null || true)"
        exec_start="${exec_start:-<ExecStart from $dir/packaging/systemd/$PELOTON_UNIT>}"
        printf '[Service]\nExecStart=\nExecStart=%s %s\n' "$exec_start" "$(matrix_flags)" \
            | write_file "$UNIT_DIR/$PELOTON_UNIT.d/board.conf" 644
    fi
    [[ "$PELOTON_AUTO_TOKEN" == yes ]] && flags=(--auto-token)
    in_dir "$dir" bash peloton-install.sh ${flags[@]+"${flags[@]}"}
}

install_mlb() {
    local dir="$BOARD_HOME/mlb-led-scoreboard" flags=()
    say "MLB-LED-Scoreboard in $dir"
    checkout "$MLB_REPO" "$dir" master
    [[ -x "$dir/venv/bin/python3" ]] && flags=(-p)
    # Its one question (bring config.json up to date with new options) gets a yes. printf, not
    # `yes |`: yes dies of SIGPIPE when the installer exits, which pipefail counts as a failure.
    if [[ "$DRY_RUN" == true ]]; then
        echo "+ (cd $dir && printf 'y\n' | bash install.sh ${flags[*]+${flags[*]}})"
    else
        (cd "$dir" && printf 'y\n' | bash install.sh ${flags[@]+"${flags[@]}"})
    fi
    give_back "$dir"
    app_unit "MLB LED Scoreboard" "$dir" "$dir/venv/bin/python3 $dir/main.py$(flags=$(matrix_flags); echo "${flags:+ $flags}")" \
        | write_file "$UNIT_DIR/$MLB_UNIT" 644
}

start_service() {
    local unit=$1 other
    say "Running $unit at boot"
    run systemctl daemon-reload
    # Only one app can drive the matrix.
    for other in "$LLL_UNIT" "$PELOTON_UNIT" "$MLB_UNIT"; do
        [[ "$other" == "$unit" ]] && continue
        if [[ "$DRY_RUN" == true ]] || systemctl list-unit-files "$other" 2>/dev/null | grep -q "^$other"; then
            run systemctl disable --now "$other"
        fi
    done
    # LightningLane-Live-LED's settings page goes with it.
    if [[ "$unit" != "$LLL_UNIT" && -f "$UNIT_DIR/$SETTINGS_UNIT" ]]; then
        run systemctl disable --now "$SETTINGS_UNIT"
    fi
    run systemctl enable "$unit"
    run systemctl restart "$unit"
}

main() {
    PANEL_OPTIONS=no LED_ROWS=32 LED_COLS=64 LED_GPIO_MAPPING=adafruit-hat-pwm LED_SLOWDOWN_GPIO=2 EXTRA_ARGS=""
    LLL_BRANCH="" SPEAKER=no PELOTON_AUTO_TOKEN=no WIFI2_SSID="" WIFI2_IFACE="" WIFI2_PSK="" WIFI_SETUP_ONLY=false
    while (($#)); do
        case "$1" in
            --answers) [[ $# -ge 2 ]] || die "--answers needs a file"; read_answers "$2"; shift 2 ;;
            --branch)
                [[ $# -ge 2 && -n "$2" ]] || die "--branch needs a branch name"
                LLL_BRANCH="$2"; ANSWERED="${ANSWERED}LLL_BRANCH "; shift 2 ;;
            --yes|-y) ASSUME_YES=true; shift ;;
            --dry-run) DRY_RUN=true; shift ;;
            --wifi-setup-only) WIFI_SETUP_ONLY=true; shift ;;
            -h|--help) usage; exit 0 ;;
            *) usage >&2; exit 2 ;;
        esac
    done

    if [[ "$WIFI_SETUP_ONLY" == true ]]; then
        # LLL-install.sh's step: no questions, and fine as root (board-setup.sh runs that as root).
        if [[ "$DRY_RUN" == false ]]; then
            [[ "$(uname -s)" == Linux ]] || die "run this on the Pi"
            [[ $EUID -eq 0 ]] || die "run it with sudo: sudo bash $0 --wifi-setup-only"
        fi
        BOARD_NAME="$(hostname -s 2>/dev/null || hostname)"
        export DEBIAN_FRONTEND=noninteractive
        setup_wifi_hotspot
        # LLL-install.sh runs this from the app's folder; the settings page is part of setup mode.
        [[ -d "$SCRIPT_DIR/settings_page" ]] && setup_settings_page "$SCRIPT_DIR"
        return
    fi
    if [[ "$DRY_RUN" == true ]]; then
        BOARD_USER="${SUDO_USER:-$(id -un)}"
    else
        [[ "$(uname -s)" == Linux ]] || die "run this on the Pi"
        [[ $EUID -eq 0 ]] || die "run it with sudo: sudo bash $0"
        [[ -n "${SUDO_USER:-}" && "$SUDO_USER" != root ]] || die "run it with sudo from your own login, not as root"
        BOARD_USER="$SUDO_USER"
    fi
    BOARD_HOME="$(getent passwd "$BOARD_USER" 2>/dev/null | cut -d: -f6 || true)"
    BOARD_HOME="${BOARD_HOME:-$HOME}"

    collect_answers
    show_summary

    export DEBIAN_FRONTEND=noninteractive
    say "Packages"
    run apt-get update
    run apt-get install -y git python3 python3-venv
    set_hostname
    setup_wifi
    setup_wifi_hotspot
    tune_matrix
    setup_power_button
    case "$APP" in
        lll) install_lll; start_service "$LLL_UNIT" ;;
        peloton) install_peloton; start_service "$PELOTON_UNIT" ;;
        mlb) install_mlb; start_service "$MLB_UNIT" ;;
    esac

    local unit
    case "$APP" in lll) unit=$LLL_UNIT ;; peloton) unit=$PELOTON_UNIT ;; mlb) unit=$MLB_UNIT ;; esac
    printf '\n✅ Done. Logs: journalctl -u %s -f\n' "$unit"
    if [[ "$NEEDS_REBOOT" == true ]]; then
        echo "   Reboot to finish (boot settings changed): sudo reboot"
    fi
}

main "$@"
