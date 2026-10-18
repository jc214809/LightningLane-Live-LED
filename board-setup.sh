#!/usr/bin/env bash
# Sets up a Raspberry Pi LED board for one app: LightningLane-Live-LED, Peloton-LED or
# MLB-LED-Scoreboard. Asks everything up front, shows a summary, then does it all; safe to re-run
# (to update, or to switch apps). Each app's own installer does the app; this script does the board
# around it: hostname, a second Wi-Fi network, the power button, matrix tuning and the service.
#
#   sudo bash board-setup.sh                      # asks
#   sudo bash board-setup.sh --answers board.txt  # KEY=value lines skip those questions
#   bash board-setup.sh --dry-run ...             # prints what it would do, changes nothing
set -Eeuo pipefail

ROOT="${BOARD_SETUP_ROOT:-}"   # tests: a folder standing in for / (system files are read from it)
SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"

LLL_REPO=https://github.com/jc214809/LightningLane-Live-LED.git
PELOTON_REPO=https://github.com/jc214809/Peloton-LED.git
MLB_REPO=https://github.com/MLB-LED-Scoreboard/mlb-led-scoreboard.git
LLL_UNIT=LightningLane-Live-LED.service
PELOTON_UNIT=peloton-led.service
MLB_UNIT=mlb-led-scoreboard.service
UNIT_DIR="$ROOT/etc/systemd/system"

ANSWER_KEYS="BOARD_NAME APP LED_ROWS LED_COLS LED_GPIO_MAPPING LED_SLOWDOWN_GPIO EXTRA_ARGS LLL_BRANCH
PELOTON_AUTO_TOKEN WIFI2 WIFI2_IFACE WIFI2_NAME WIFI2_SSID WIFI2_HIDDEN POWER_BUTTON SPEAKER"
ANSWERED=" "
DRY_RUN=false
ASSUME_YES=false
NEEDS_REBOOT=false

usage() {
    cat <<'USAGE'
Usage: sudo bash board-setup.sh [--answers FILE] [--branch NAME] [--yes] [--dry-run] [-h]

  --answers FILE  KEY=value lines (# comments) answering questions ahead, e.g. APP=lll.
                  Keys: BOARD_NAME APP LED_ROWS LED_COLS LED_GPIO_MAPPING LED_SLOWDOWN_GPIO
                  EXTRA_ARGS LLL_BRANCH PELOTON_AUTO_TOKEN WIFI2 WIFI2_IFACE WIFI2_NAME
                  WIFI2_SSID WIFI2_HIDDEN POWER_BUTTON SPEAKER. The Wi-Fi password is never in it: it's
                  asked (or, with stdin not a terminal, read from its first line), and a blank
                  one keeps the saved network.
  --branch NAME   LightningLane-Live-LED's branch (default develop-beta), like LLL_BRANCH=NAME.
  --yes           Don't ask: unanswered questions take their defaults, and no confirmation.
  --dry-run       Print the commands and files it would write; change nothing.
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
        return
    fi
    mkdir -p "$(dirname "$path")"
    local tmp
    tmp="$(mktemp)"
    printf '%s\n' "$content" > "$tmp"
    install -m "$mode" "$tmp" "$path"
    rm -f "$tmp"
    echo "  wrote $path"
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
    ask BOARD_NAME "Hostname (boards.json picks LightningLane-Live-LED's settings by it)" "$(hostname -s 2>/dev/null || hostname)"
    [[ "$BOARD_NAME" =~ ^[A-Za-z0-9]([A-Za-z0-9-]{0,61}[A-Za-z0-9])?$ ]] || die "not a usable hostname: $BOARD_NAME"
    ask APP "App to run (lll = LightningLane-Live-LED, peloton = Peloton-LED, mlb = MLB-LED-Scoreboard)" lll lll peloton mlb
    ask LED_ROWS "Panel rows" 32 32 64
    ask LED_COLS "Panel columns" 64 64
    ask LED_GPIO_MAPPING "GPIO mapping (adafruit-hat-pwm needs the Bonnet's GPIO 4-18 jumper soldered)" adafruit-hat-pwm adafruit-hat-pwm adafruit-hat regular
    ask LED_SLOWDOWN_GPIO "GPIO slowdown (2 on a Pi Zero, 4 on a Pi 4)" 2 0 1 2 3 4
    ask EXTRA_ARGS "Extra app flags, like --led-brightness=85 (none)" ""
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

show_summary() {
    cat <<EOF

Board setup
  Hostname      $BOARD_NAME (now $(hostname -s 2>/dev/null || hostname))
  User          $BOARD_USER ($BOARD_HOME)
  App           $APP${LLL_BRANCH:+ (branch $LLL_BRANCH)}
  Panel         ${LED_COLS}x$LED_ROWS, $LED_GPIO_MAPPING, slowdown $LED_SLOWDOWN_GPIO
  Extra flags   ${EXTRA_ARGS:-none}
  Second Wi-Fi  $WIFI2${WIFI2_SSID:+ ($WIFI2_SSID on $WIFI2_IFACE)}
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

matrix_flags() {
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
    # config.json from the example if missing, plus a "matrix" section when boards.json has no
    # entry for this hostname, and the speaker. Only the keys it sets change.
    local dir=$1 boards=$1/boards.json in_boards matrix="" device=""
    [[ -f "$boards" ]] || boards="$SCRIPT_DIR/boards.json"
    in_boards="$(python3 -c 'import json,sys; print(sys.argv[2] in json.load(open(sys.argv[1])))' "$boards" "$BOARD_NAME" 2>/dev/null || echo False)"
    if [[ "$in_boards" == True ]]; then
        echo "  boards.json has $BOARD_NAME; its settings come from there"
        # config.json's matrix section overrides boards.json: say so, but leave the user's config alone
        python3 - "$dir/config.json" <<'CONFIG' 2>/dev/null || true
import json, sys
try:
    matrix = json.load(open(sys.argv[1], encoding="utf-8")).get("matrix") or {}
except (OSError, ValueError):
    sys.exit()
overrides = {k: v for k, v in matrix.items() if v is not None}
if overrides:
    print("  note: config.json's matrix section overrides boards.json with "
          + ", ".join(f"{k}={v}" for k, v in overrides.items()) + " (left as is)")
CONFIG
    else
        matrix="{\"led_rows\": $LED_ROWS, \"led_cols\": $LED_COLS, \"led_gpio_mapping\": \"$LED_GPIO_MAPPING\", \"led_slowdown_gpio\": $LED_SLOWDOWN_GPIO}"
        echo "  boards.json has no $BOARD_NAME: putting the panel settings in config.json's matrix section"
        echo "  (or add a boards.json entry for it and commit it, like the other boards)"
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
    in_dir "$dir" bash LLL-install.sh ${flags[@]+"${flags[@]}"}
    give_back "$dir"
    lll_config "$dir"
    # No panel flags: boards.json (or config.json's matrix) has them.
    local unit
    unit="$(app_unit "LightningLane-Live-LED" "$dir" "$dir/venv/bin/python3 $dir/disney.py \$ARGS" "\"ARGS=$EXTRA_ARGS\"")"
    retire_old_units "$LLL_UNIT" "$unit"
    write_file "$UNIT_DIR/$LLL_UNIT" 644 <<<"$unit"
}

retire_old_units() {  # retire_old_units UNIT CONTENT: move older copies of UNIT out of systemd's way
    # Boards set up by hand have their own service file, often with the panel flags in it, in /lib
    # or /etc (and sometimes overrides in UNIT.d/). Any of them would keep a board on its old flags
    # instead of boards.json, so each goes to a dated backup folder, never deleted, with the flags
    # it ran with printed so they can be checked against boards.json. Ours, unchanged, stays.
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
    exec_start="$(sed -n 's/^ExecStart=//p' "$dir/packaging/systemd/$PELOTON_UNIT" 2>/dev/null || true)"
    exec_start="${exec_start:-<ExecStart from $dir/packaging/systemd/$PELOTON_UNIT>}"
    printf '[Service]\nExecStart=\nExecStart=%s %s\n' "$exec_start" "$(matrix_flags)" \
        | write_file "$UNIT_DIR/$PELOTON_UNIT.d/board.conf" 644
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
    app_unit "MLB LED Scoreboard" "$dir" "$dir/venv/bin/python3 $dir/main.py $(matrix_flags)" \
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
    run systemctl enable "$unit"
    run systemctl restart "$unit"
}

main() {
    LLL_BRANCH="" SPEAKER=no PELOTON_AUTO_TOKEN=no WIFI2_SSID="" WIFI2_IFACE="" WIFI2_PSK=""
    while (($#)); do
        case "$1" in
            --answers) [[ $# -ge 2 ]] || die "--answers needs a file"; read_answers "$2"; shift 2 ;;
            --branch)
                [[ $# -ge 2 && -n "$2" ]] || die "--branch needs a branch name"
                LLL_BRANCH="$2"; ANSWERED="${ANSWERED}LLL_BRANCH "; shift 2 ;;
            --yes|-y) ASSUME_YES=true; shift ;;
            --dry-run) DRY_RUN=true; shift ;;
            -h|--help) usage; exit 0 ;;
            *) usage >&2; exit 2 ;;
        esac
    done

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
