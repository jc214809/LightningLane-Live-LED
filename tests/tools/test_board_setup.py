"""board-setup.sh, run with --dry-run against a fake board: a folder standing in for / (via
BOARD_SETUP_ROOT), a home folder, and stand-ins for hostname and getent."""
import json
import re
import os
import shutil
import subprocess

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
SCRIPT = os.path.join(ROOT, "board-setup.sh")

pytestmark = pytest.mark.skipif(shutil.which("bash") is None, reason="board-setup.sh is a bash script")

PELOTON_EXEC = "/opt/peloton-led/venv/bin/python /opt/peloton-led/peloton_led.py --led-gpio-mapping adafruit-hat"


class Board:
    def __init__(self, tmp_path):
        self.root = tmp_path / "root"
        self.home = tmp_path / "home"
        self.bin = tmp_path / "bin"
        self.answers = tmp_path / "answers.txt"
        for folder in (self.root / "boot/firmware", self.root / "etc", self.root / "proc/asound", self.home, self.bin):
            folder.mkdir(parents=True)
        self.boot("cmdline.txt", "console=tty1 root=PARTUUID=abc rootwait\n")
        self.boot("config.txt", "[all]\ndtparam=audio=on\n")
        (self.root / "etc/hosts").write_text("127.0.0.1\tlocalhost\n127.0.1.1\traspberrypi\n")
        self.command("hostname", "echo raspberrypi")
        self.command("getent", "exit 2")  # no passwd entry: the home folder is $HOME
        self.command("tailscale", "exit 1")  # never this machine's own: only asked once installed, and logged out

    def boot(self, name, text):
        (self.root / "boot/firmware" / name).write_text(text)

    def command(self, name, body):
        path = self.bin / name
        path.write_text(f"#!/bin/sh\n{body}\n")
        path.chmod(0o755)

    def checkout(self, name, files=None):
        """A checkout of an app in the home folder, as an earlier run leaves it."""
        repo = self.home / name
        (repo / ".git").mkdir(parents=True)
        for rel, text in (files or {}).items():
            (repo / rel).parent.mkdir(parents=True, exist_ok=True)
            (repo / rel).write_text(text)
        return repo

    def run(self, stdin="", *flags, **answers):
        return self.run_file("".join(f"{key}={value}\n" for key, value in answers.items()), stdin, *flags)

    def run_file(self, text, stdin="", *flags, dry_run=True):
        """The script with an answers file of this text."""
        self.answers.write_text(text)
        env = dict(os.environ, HOME=str(self.home), BOARD_SETUP_ROOT=str(self.root),
                   PATH=f"{self.bin}{os.pathsep}{os.environ['PATH']}")
        env.pop("SUDO_USER", None)
        args = ["--dry-run"] if dry_run else []
        return subprocess.run(["bash", SCRIPT, *args, "--answers", str(self.answers), *flags],
                              input=stdin, capture_output=True, text=True, env=env, timeout=30)

    def ok(self, stdin="", *flags, **answers):
        result = self.run(stdin, *flags, **answers)
        assert result.returncode == 0, result.stderr
        return result.stdout


@pytest.fixture
def board(tmp_path):
    return Board(tmp_path)


def unit(out, name):
    """The unit file a dry run would write, from its printed copy."""
    head = f"/etc/systemd/system/{name} (mode 644):\n"
    assert head in out, out
    lines = []
    for line in out.split(head, 1)[1].splitlines():
        if not line.startswith("    "):
            break
        lines.append(line[4:])
    return "\n".join(lines)


def test_lll_runs_from_its_checkout_with_no_panel_flags_and_stops_the_other_apps(board):
    out = board.ok(BOARD_NAME="Disneypi", APP="lll", PANEL_OPTIONS="yes", LED_ROWS=64, EXTRA_ARGS="--led-brightness=85")
    service = unit(out, "LightningLane-Live-LED.service")
    checkout = board.home / "LightningLane-Live-LED"
    assert f"WorkingDirectory={checkout}" in service
    assert f"ExecStart={checkout}/venv/bin/python3 {checkout}/disney.py $ARGS" in service
    assert 'Environment="ARGS=--led-brightness=85"' in service
    assert "--led-rows" not in service  # config.json has the board's settings
    assert "ExecStartPre" not in service  # the old script's, under [Unit], where systemd ignores it
    assert 'matrix={"led_rows": 64, "led_cols": 64' in out
    assert f"git clone --branch develop-beta https://github.com/jc214809/LightningLane-Live-LED.git {checkout}" in out
    assert f"(cd {checkout} && bash LLL-install.sh -w)" in out  # the full install, less the Wi-Fi setup (done here)
    for other in ("peloton-led.service", "mlb-led-scoreboard.service"):
        assert f"systemctl disable --now {other}" in out
    assert out.index("systemctl enable LightningLane-Live-LED.service") < out.index(
        "systemctl restart LightningLane-Live-LED.service")


def test_lll_gets_its_settings_page_as_its_own_service_from_the_checkout(board):
    checkout = board.checkout("LightningLane-Live-LED", {"venv/bin/python3": ""})
    (checkout / "venv/bin/python3").chmod(0o755)
    out = board.ok(BOARD_NAME="Disneypi", APP="lll")
    service = unit(out, "lll-settings.service")
    assert f"WorkingDirectory={checkout}" in service
    assert f"ExecStart={checkout}/venv/bin/python3 -m settings_page.server" in service
    assert "Restart=always" in service
    assert "http://Disneypi.local:8080" in out
    steps = ["systemctl enable lll-settings.service", "systemctl restart lll-settings.service",
             "systemctl restart LightningLane-Live-LED.service"]
    at = [out.index(step) for step in steps]
    assert at == sorted(at)
    assert "disable --now lll-settings.service" not in out


def written(out, path):
    """A file other than a unit that a dry run would write, from its printed copy."""
    head = f"{path} (mode 755):\n"
    assert head in out, out
    lines = []
    for line in out.split(head, 1)[1].splitlines():
        if not line.startswith("    "):
            break
        lines.append(line[4:])
    return "\n".join(lines)


def test_lll_gets_the_updaters_boot_recovery_and_lll_rollback(board):
    checkout = board.checkout("LightningLane-Live-LED", {"venv/bin/python3": "", "self_update/__init__.py": ""})
    (checkout / "venv/bin/python3").chmod(0o755)
    out = board.ok(BOARD_NAME="Disneypi", APP="lll")
    recover = unit(out, "lll-update-recover.service")
    assert "Type=oneshot" in recover and "TimeoutStartSec=infinity" in recover and "Restart=" not in recover
    assert f"WorkingDirectory={checkout}" in recover
    assert f"ExecStart={checkout}/venv/bin/python3 -m self_update recover" in recover
    assert "Before=" not in recover, "rolling back restarts the app: ordered before it, that would deadlock"
    assert "+ systemctl enable lll-update-recover.service" in out
    assert "restart lll-update-recover" not in out and "start lll-update-recover" not in out
    command = written(out, f"{board.root}/usr/local/bin/lll-rollback")
    assert command.startswith("#!/bin/sh\n")
    assert f'cd "{checkout}" && exec "{checkout}/venv/bin/python3" -m self_update rollback "$@"' in command


def test_a_version_without_the_updater_gets_no_recovery(board):
    board.checkout("LightningLane-Live-LED")
    out = board.ok(BOARD_NAME="Disneypi", APP="lll")
    assert "lll-update-recover" not in out and "lll-rollback" not in out


def test_lll_rollback_runs_the_rollback_with_its_arguments(board, tmp_path):
    board.checkout("LightningLane-Live-LED", {"self_update/__init__.py": ""})
    out = board.ok(BOARD_NAME="Disneypi", APP="lll")
    script = tmp_path / "lll-rollback"
    script.write_text(written(out, f"{board.root}/usr/local/bin/lll-rollback")
                      .replace("/usr/bin/python3", "echo"))  # no venv in the fake checkout: the system python
    result = subprocess.run(["sh", str(script), "--extra"], capture_output=True, text=True)
    assert result.stdout == "-m self_update rollback --extra\n", result.stderr


@pytest.mark.parametrize("app", ["peloton", "mlb"])
def test_another_app_stops_lights_settings_page_if_it_has_one(board, app):
    board.checkout("Peloton-LED", {"packaging/systemd/peloton-led.service": f"[Service]\nExecStart={PELOTON_EXEC}\n"})
    assert "lll-settings.service" not in board.ok(BOARD_NAME="ZeroPi", APP=app)
    (board.root / "etc/systemd/system").mkdir(parents=True, exist_ok=True)
    (board.root / "etc/systemd/system/lll-settings.service").write_text("[Service]\n")
    (board.root / "etc/systemd/system/lll-update-recover.service").write_text("[Service]\n")
    out = board.ok(BOARD_NAME="ZeroPi", APP=app)
    assert "+ systemctl disable --now lll-settings.service" in out
    assert "+ systemctl disable --now lll-update-recover.service" in out


def test_lll_on_a_board_it_has_set_up_updates_and_skips_apt_and_the_driver_build(board):
    checkout = board.checkout("LightningLane-Live-LED", {
        "venv/bin/python3": "", "submodules/matrix/Makefile": "", "config.json": "{}"})
    (checkout / "venv/bin/python3").chmod(0o755)
    out = board.ok(BOARD_NAME="MickeyPi", APP="lll", LLL_BRANCH="develop-sound")
    assert f"git -C {checkout} checkout develop-sound" in out
    assert f"git -C {checkout} pull --ff-only" in out
    assert f"(cd {checkout} && bash LLL-install.sh -p -m -w)" in out
    assert "config.json-example" not in out  # keeps the board's config.json
    assert "set in" not in out


def test_branch_defaults_to_develop_beta_and_branch_picks_another(board):
    checkout = board.home / "LightningLane-Live-LED"
    out = board.ok(BOARD_NAME="Disneypi", APP="lll")
    assert "(branch develop-beta)" in out and "git clone --branch develop-beta" in out
    out = board.ok("", "--branch", "develop-sound", BOARD_NAME="Disneypi", APP="lll")
    assert "(branch develop-sound)" in out
    assert f"git clone --branch develop-sound https://github.com/jc214809/LightningLane-Live-LED.git {checkout}" in out


@pytest.mark.parametrize("branch", ["--upload-pack=x", "two words", ""])
def test_a_branch_that_isnt_a_plain_name_is_refused(board, branch):
    result = board.run("", "--branch", branch, BOARD_NAME="Disneypi", APP="lll")
    assert result.returncode != 0
    assert "apt-get" not in result.stdout


def test_lll_panel_answers_go_in_config_json(board):
    out = board.ok(BOARD_NAME="NewPi", APP="lll", PANEL_OPTIONS="yes", LED_ROWS=64, LED_SLOWDOWN_GPIO=4)
    assert "config.json-example" in out and "chmod 600" in out
    assert ('matrix={"led_rows": 64, "led_cols": 64, "led_gpio_mapping": "adafruit-hat-pwm", '
            '"led_slowdown_gpio": 4}') in out


def test_the_speaker_is_named_by_its_card_so_renumbering_cant_move_it(board):
    (board.root / "proc/asound/cards").write_text(
        " 0 [vc4hdmi        ]: vc4-hdmi - vc4-hdmi\n"
        "                      vc4-hdmi\n"
        " 1 [UACDemoV10     ]: USB-Audio - UACDemoV1.0\n"
        "                      Jieli Technology UACDemoV1.0 at usb-3f980000.usb-1, full speed\n")
    out = board.ok(BOARD_NAME="Disneypi", APP="lll", SPEAKER="yes")
    assert "sound.device=plughw:CARD=UACDemoV10,DEV=0" in out


def test_no_usb_speaker_says_so_and_sets_nothing(board):
    result = board.run(BOARD_NAME="Disneypi", APP="lll", SPEAKER="yes")
    assert result.returncode == 0
    assert "no USB sound card found" in result.stderr
    assert "sound.device" not in result.stdout


def test_peloton_gets_this_boards_flags_through_a_drop_in_before_its_installer_starts_it(board):
    checkout = board.checkout("Peloton-LED", {
        "packaging/systemd/peloton-led.service": f"[Service]\nUser=peloton-led\nExecStart={PELOTON_EXEC}\n"})
    out = board.ok(BOARD_NAME="ZeroPi", APP="peloton", PANEL_OPTIONS="yes", PELOTON_AUTO_TOKEN="yes")
    drop_in = unit(out, "peloton-led.service.d/board.conf")
    assert drop_in.splitlines() == [
        "[Service]", "ExecStart=",
        f"ExecStart={PELOTON_EXEC} --led-gpio-mapping=adafruit-hat-pwm --led-rows=32 --led-cols=64 --led-slowdown-gpio=2"]
    installer = f"(cd {checkout} && bash peloton-install.sh --auto-token)"
    assert out.index("peloton-led.service.d/board.conf") < out.index(installer)
    assert "systemctl disable --now LightningLane-Live-LED.service" in out


def test_mlb_runs_upstream_with_the_panel_flags_and_answers_its_one_question(board):
    out = board.ok(BOARD_NAME="ZeroPi", APP="mlb", PANEL_OPTIONS="yes", EXTRA_ARGS="--led-brightness=80")
    checkout = board.home / "mlb-led-scoreboard"
    assert f"git clone --branch master https://github.com/MLB-LED-Scoreboard/mlb-led-scoreboard.git {checkout}" in out
    assert f"(cd {checkout} && printf 'y\\n' | bash install.sh )" in out
    assert (f"ExecStart={checkout}/venv/bin/python3 {checkout}/main.py --led-gpio-mapping=adafruit-hat-pwm "
            "--led-rows=32 --led-cols=64 --led-slowdown-gpio=2 --led-brightness=80") in unit(out, "mlb-led-scoreboard.service")


def test_panel_options_are_left_to_each_apps_config_unless_asked_for(board):
    board.checkout("Peloton-LED", {
        "packaging/systemd/peloton-led.service": f"[Service]\nExecStart={PELOTON_EXEC}\n"})
    out = board.ok(BOARD_NAME="NewPi", APP="lll", LED_ROWS=64, EXTRA_ARGS="--led-brightness=85")
    assert "left to the app's own config" in out
    assert "panel options: the Pi model's; set the size and rotation at http://NewPi.local:8080" in out
    assert "matrix=" not in out and "--led-rows" not in out and "ARGS=--led-brightness" not in out
    out = board.ok(BOARD_NAME="ZeroPi", APP="peloton")
    assert "board.conf" not in out
    out = board.ok(BOARD_NAME="ZeroPi", APP="mlb")
    assert "--led-" not in unit(out, "mlb-led-scoreboard.service")
    assert f"main.py\n" in unit(out, "mlb-led-scoreboard.service") + "\n"


def test_a_new_hostname_is_set_and_written_to_hosts(board):
    out = board.ok(BOARD_NAME="TinyPi", APP="lll")
    assert "hostnamectl set-hostname TinyPi" in out
    assert "127.0.1.1\\tTinyPi" in out or "127.0.1.1\tTinyPi" in out


def test_the_same_hostname_is_left_alone(board):
    assert "hostnamectl" not in board.ok(BOARD_NAME="raspberrypi", APP="lll")


def test_the_power_button_adds_both_overlays_under_all_with_a_backup(board):
    out = board.ok(BOARD_NAME="Disneypi", APP="lll", POWER_BUTTON="yes")
    assert "config.txt.board-setup.bak" in out
    assert ("[all]\n    dtoverlay=gpio-shutdown\n"
            "    dtoverlay=gpio-led,gpio=25,label=power,trigger=default-on\n") in out


def test_the_old_scripts_shutdown_overlay_counts_and_only_the_light_is_added(board):
    board.boot("config.txt", "dtoverlay=gpio-shutdown,gpio_pin=3,active_low=1,gpio_pull=up\n")
    out = board.ok(BOARD_NAME="Disneypi", APP="lll", POWER_BUTTON="yes")
    assert "dtoverlay=gpio-led,gpio=25" in out
    assert "    dtoverlay=gpio-shutdown\n" not in out


def test_a_power_button_already_set_up_changes_nothing_and_i2c_is_flagged(board):
    board.boot("config.txt", "dtparam=i2c_arm=on\n[all]\ndtoverlay=gpio-shutdown\n"
                             "dtoverlay=gpio-led,gpio=25,label=power,trigger=default-on\n")
    result = board.run(BOARD_NAME="Disneypi", APP="lll", POWER_BUTTON="yes")
    assert "already in" in result.stdout and "board-setup.bak" not in result.stdout
    assert "the button won't work" in result.stderr


def test_matrix_tuning_is_added_once(board):
    out = board.ok(BOARD_NAME="Disneypi", APP="lll")
    assert "blacklist snd_bcm2835" in out and "isolcpus=3" in out and "sudo reboot" in out

    (board.root / "etc/modprobe.d").mkdir()
    (board.root / "etc/modprobe.d/blacklist-rgbmatrix.conf").write_text("blacklist snd_bcm2835\n")
    board.boot("cmdline.txt", "console=tty1 root=PARTUUID=abc rootwait isolcpus=3\n")
    out = board.ok(BOARD_NAME="Disneypi", APP="lll")
    assert "snd_bcm2835" not in out and "isolcpus" not in out and "sudo reboot" not in out


def test_the_second_wifi_is_a_keyfile_so_the_password_is_never_on_a_command_line(board):
    out = board.ok("hunter2 pw\n", BOARD_NAME="Disneypi", APP="lll", WIFI2="yes", WIFI2_SSID="Joel iPhone",
                   WIFI2_HIDDEN="yes")
    assert "hunter2" not in out
    assert "system-connections/Joel iPhone.nmconnection (mode 600)" in out
    for line in ("ssid=Joel iPhone", "hidden=true", "key-mgmt=wpa-psk", "psk=********", "autoconnect-priority=-10"):
        assert f"    {line}\n" in out
    assert "nmcli connection reload" in out


def test_a_blank_password_keeps_the_saved_network(board):
    saved = board.root / "etc/NetworkManager/system-connections/iPhone.nmconnection"
    saved.parent.mkdir(parents=True)
    saved.write_text("[connection]\nid=iPhone\n")
    out = board.ok("\n", BOARD_NAME="Disneypi", APP="lll", WIFI2="yes")
    assert "keeping the saved network" in out and "nmcli" not in out


def comitup_installed(board):
    comitup = board.root / "usr/sbin/comitup"
    comitup.parent.mkdir(parents=True)
    comitup.write_text("")
    comitup.chmod(0o755)


def written(out, path):
    """The file a dry run would write at path (under the fake root), from its printed copy."""
    head = f"+ write {path} ("
    assert head in out, out
    lines = []
    for line in out.split(head, 1)[1].splitlines()[1:]:
        if not line.startswith("    ") or line.startswith("    + write "):
            break
        lines.append(line[4:])
    return "\n".join(lines)


@pytest.mark.parametrize("app", ["lll", "peloton", "mlb"])
def test_every_board_gets_the_wifi_setup_hotspot_set_up_before_comitup_starts(board, app):
    out = board.ok(BOARD_NAME="ZeroPi", APP=app)
    assert "Wi-Fi setup   an open ZeroPi-setup hotspot" in out
    conf = written(out, f"{board.root}/etc/comitup.conf")
    assert "ap_name: <hostname>-setup" in conf.splitlines()
    assert "external_callback: /usr/local/bin/comitup-callback" in conf.splitlines()
    assert "ap_password" not in conf.replace("(no ap_password)", "")  # open, as asked
    callback = written(out, f"{board.root}/usr/local/bin/comitup-callback")
    assert callback.startswith("#!/bin/sh\n")
    assert ("printf '%s %s\\n' \"$1\" \"$(hostname)-setup\" > /run/comitup-state.new && "
            "mv /run/comitup-state.new /run/comitup-state") in callback
    assert "/usr/local/bin/comitup-callback (mode 755)" in out
    source = "https://davesteele.github.io/comitup/deb/davesteele-comitup-apt-source_1.3_all.deb"
    steps = [f"+ curl -fsSL -o /tmp/davesteele-comitup-apt-source.deb {source}",
             "+ dpkg -i /tmp/davesteele-comitup-apt-source.deb",
             "+ apt-get install -y -o Dpkg::Options::=--force-confold comitup"]
    at = [out.index(step) for step in steps]
    assert at == sorted(at)
    assert out.index("/etc/comitup.conf (mode 644)") < at[0], "settings first, so comitup starts with them"
    assert "systemctl restart comitup" not in out
    wait = written(out, f"{board.root}/etc/systemd/system/comitup.service.d/wait-for-wifi.conf")
    for line in ("[Unit]", "Wants=sys-subsystem-net-devices-wlan0.device",
                 "After=sys-subsystem-net-devices-wlan0.device", "[Service]", "ExecStartPre=/bin/sleep 10"):
        assert line in wait.splitlines()
    assert out.index("wait-for-wifi.conf (mode 644)") < at[0], "in place before comitup's first start"


WIFI_SETUP_FILES = ("etc/comitup.conf", "usr/local/bin/comitup-callback",
                    "etc/systemd/system/comitup.service.d/wait-for-wifi.conf")


def wifi_section(out):
    """The Wi-Fi setup step's output, up to the next step."""
    rest = out.split("Wi-Fi setup hotspot (comitup)", 1)[1]
    return rest.split("\n→ ", 1)[0]


def keep_wifi_setup_files(board, out, paths=WIFI_SETUP_FILES):
    """Put the files a run wrote in place, as the real run would have."""
    for path in paths:
        target = board.root / path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(written(out, f"{board.root}/{path}") + "\n")


def test_the_wifi_setup_callback_writes_the_state_the_app_reads(board, tmp_path):
    from utils.wifi_setup import hotspot_name
    out = board.ok(BOARD_NAME="ZeroPi", APP="lll")
    state = tmp_path / "comitup-state"
    script = tmp_path / "callback"
    script.write_text(written(out, f"{board.root}/usr/local/bin/comitup-callback").replace("/run/comitup-state", str(state)))
    script.chmod(0o755)
    board.command("hostname", "echo ZeroPi")
    env = dict(os.environ, PATH=f"{board.bin}{os.pathsep}{os.environ['PATH']}")
    subprocess.run([str(script), "HOTSPOT"], check=True, env=env)
    assert hotspot_name(str(state)) == "ZeroPi-setup"
    subprocess.run([str(script), "CONNECTED"], check=True, env=env)
    assert hotspot_name(str(state)) is None


def test_wifi_setup_already_in_place_is_left_alone(board):
    out = board.ok(BOARD_NAME="raspberrypi", APP="lll")
    keep_wifi_setup_files(board, out)
    comitup_installed(board)
    out = board.ok(BOARD_NAME="raspberrypi", APP="lll")
    assert "already set up" in out
    assert "comitup.conf (mode" not in out and "dpkg" not in out and "systemctl restart comitup" not in out
    assert "wait-for-wifi.conf (mode" not in out and "daemon-reload" not in wifi_section(out)


def test_changed_wifi_setup_settings_or_a_new_hostname_restart_comitup(board):
    comitup_installed(board)
    out = board.ok(BOARD_NAME="raspberrypi", APP="lll")
    assert "+ systemctl restart comitup\n" in out and "dpkg" not in out
    keep_wifi_setup_files(board, out)
    out = board.ok(BOARD_NAME="ZeroPi", APP="lll")  # renamed: the hotspot is named after the board
    assert "+ systemctl restart comitup\n" in out


def test_a_board_set_up_before_the_wifi_wait_gets_it_without_a_comitup_restart(board):
    out = board.ok(BOARD_NAME="raspberrypi", APP="lll")
    keep_wifi_setup_files(board, out, WIFI_SETUP_FILES[:2])  # comitup.conf and the callback only
    comitup_installed(board)
    out = board.ok(BOARD_NAME="raspberrypi", APP="lll")
    assert "wait-for-wifi.conf (mode 644)" in out
    assert "+ systemctl daemon-reload\n" in wifi_section(out)
    assert "systemctl restart comitup" not in out and "already set up" not in out and "dpkg" not in out


def test_a_saved_wifi_with_no_mode_gets_one_so_comitup_doesnt_hotspot_over_it(board):
    folder = board.root / "etc/NetworkManager/system-connections"
    folder.mkdir(parents=True)
    (folder / "preconfigured.nmconnection").write_text(
        "[connection]\nid=preconfigured\ntype=wifi\n\n[wifi]\nssid=Home\n\n[ipv4]\nmethod=auto\n")
    (folder / "phone.nmconnection").write_text(
        "[connection]\nid=phone\ntype=wifi\n\n[wifi]\nmode=infrastructure\nssid=iPhone\n")
    (folder / "wired.nmconnection").write_text("[connection]\nid=wired\ntype=ethernet\n")
    out = board.ok(BOARD_NAME="Disneypi", APP="lll")
    assert "+ nmcli connection modify preconfigured 802-11-wireless.mode infrastructure\n" in out
    assert "modify phone" not in out and "modify wired" not in out
    assert out.index("modify preconfigured") < out.index("apt-get install -y -o Dpkg::Options::=--force-confold comitup")


def test_a_hostname_too_long_for_a_hotspot_name_is_refused(board):
    result = board.run(BOARD_NAME="a" * 27, APP="lll")
    assert result.returncode != 0
    assert "would be over Wi-Fi's 32 letters" in result.stderr
    assert board.ok(BOARD_NAME="a" * 26, APP="lll")


def test_wifi_setup_only_asks_nothing_and_does_only_that(board):
    board.command("hostname", "echo MickeyPi")
    result = board.run_file("", "", "--wifi-setup-only")
    assert result.returncode == 0, result.stderr
    out = result.stdout
    assert "Wi-Fi setup hotspot (comitup): an open MickeyPi-setup" in out
    assert "dpkg -i" in out
    assert "Board setup" not in out and "git clone" not in out and "LightningLane-Live-LED.service" not in out
    # LLL-install.sh runs it from the app's folder: the settings page comes with setup mode
    service = unit(out, "lll-settings.service")
    assert f"WorkingDirectory={ROOT}" in service and " -m settings_page.server" in service
    assert "systemctl restart lll-settings.service" in out
    # and the updater's backstops, since this version has it
    assert f" -m self_update recover" in unit(out, "lll-update-recover.service")
    assert "lll-rollback (mode 755)" in out


def test_wifi_setup_only_needs_the_pi_and_sudo(board):
    result = board.run_file("", "", "--wifi-setup-only", dry_run=False)
    assert result.returncode != 0
    assert "run this on the Pi" in result.stderr or "sudo" in result.stderr


def tailscale_installed(board, running=False):
    tailscale = board.root / "usr/bin/tailscale"
    tailscale.parent.mkdir(parents=True, exist_ok=True)
    tailscale.write_text("")
    tailscale.chmod(0o755)
    state = "Running" if running else "NeedsLogin"
    board.command("tailscale", f"""[ "$1 $2" = "status --json" ] && echo '{{\n  "BackendState": "{state}",'""")


FAKE_TAILSCALE_KEY = "tskey-" + "auth-example-notreal"  # plain words: secret scanners flag random-looking keys


TAILSCALE_STEPS = ["+ curl -fsSL -o /tmp/tailscale-install.sh https://tailscale.com/install.sh",
                   "+ sh /tmp/tailscale-install.sh", "+ rm -f /tmp/tailscale-install.sh"]


@pytest.mark.parametrize("app, unit_name", [("lll", "LightningLane-Live-LED.service"),
                                            ("peloton", "peloton-led.service"), ("mlb", "mlb-led-scoreboard.service")])
def test_every_board_installs_tailscale_and_joins_from_a_link_last(board, app, unit_name):
    out = board.ok(BOARD_NAME="TinyPi", APP=app)
    assert "Tailscale     joins from a link it prints at the end, Tailscale SSH on" in out
    at = [out.index(step) for step in [*TAILSCALE_STEPS, "+ tailscale up --ssh --timeout=10m\n"]]
    assert at == sorted(at)
    assert out.index(f"systemctl restart {unit_name}") < at[0], "the app runs while the login link waits"
    assert "open the link it prints to add TinyPi" in out
    assert "auth-key" not in out


def test_a_tailscale_auth_key_joins_from_a_file_and_is_never_shown(board):
    key = FAKE_TAILSCALE_KEY
    out = board.ok(BOARD_NAME="TinyPi", APP="lll", TAILSCALE_AUTHKEY=key)
    assert key not in out
    assert "Tailscale     joins with the auth key" in out
    key_file = f"{board.root}/run/board-setup-tailscale.key"
    assert f"+ write {key_file} (mode 600):\n    ********\n" in out
    steps = [key_file, "+ tailscale up --ssh --timeout=10m --auth-key=file:/run/board-setup-tailscale.key\n",
             f"+ rm -f {key_file}\n"]
    at = [out.index(step) for step in steps]
    assert at == sorted(at)
    assert "open the link" not in out


def test_a_bad_tailscale_auth_key_is_refused_without_showing_it(board):
    result = board.run(BOARD_NAME="TinyPi", APP="lll", TAILSCALE_AUTHKEY="hunter2-not-a-key")
    assert result.returncode != 0
    assert "isn't a Tailscale auth key" in result.stderr
    assert "hunter2" not in result.stderr + result.stdout and "apt-get" not in result.stdout


def test_a_board_already_on_the_tailnet_just_gets_tailscale_ssh(board):
    tailscale_installed(board, running=True)
    out = board.ok(BOARD_NAME="Disneypi", APP="lll", TAILSCALE_AUTHKEY=FAKE_TAILSCALE_KEY)
    assert "Tailscale     already on the tailnet (Tailscale SSH on)" in out
    assert "+ tailscale set --ssh\n" in out
    assert "tailscale-install.sh" not in out and "tailscale up" not in out and "tailscale.key" not in out


def test_tailscale_installed_but_logged_out_joins_without_reinstalling(board):
    tailscale_installed(board)
    out = board.ok(BOARD_NAME="TinyPi", APP="lll")
    assert "tailscale-install.sh" not in out
    assert "+ tailscale up --ssh --timeout=10m\n" in out


def test_tailscale_no_leaves_it_out(board):
    out = board.ok(BOARD_NAME="TinyPi", APP="lll", TAILSCALE="no")
    assert "Tailscale     no" in out
    assert "+ tailscale" not in out and "tailscale-install.sh" not in out


def test_wifi_setup_only_installs_tailscale_but_cant_join(board):
    out = board.ok("", "--wifi-setup-only")
    at = [out.index(step) for step in TAILSCALE_STEPS]
    assert at == sorted(at)
    assert "tailscale up" not in out.replace("sudo tailscale up --ssh (it prints", "")
    assert "not on the tailnet yet: sudo tailscale up --ssh" in out


def test_wifi_setup_only_leaves_a_board_on_the_tailnet_alone(board):
    tailscale_installed(board, running=True)
    out = board.ok("", "--wifi-setup-only")
    assert "already on the tailnet" in out
    assert "tailscale-install.sh" not in out and "+ tailscale" not in out


@pytest.mark.parametrize("answers, message", [
    ("COLOR=red\n", "unknown key COLOR"),
    ("APP=nba\n", "APP=nba isn't one of: lll peloton mlb"),
    ("PANEL_OPTIONS=yes\nLED_ROWS=16\n", "LED_ROWS=16 isn't one of: 32 64"),
    ("BOARD_NAME=my_pi\n", "not a usable hostname"),
    ("just words\n", "not KEY=value"),
])
def test_bad_answers_stop_it_before_anything_runs(board, answers, message):
    result = board.run_file(answers)
    assert result.returncode != 0
    assert message in result.stderr
    assert "apt-get" not in result.stdout


def test_answers_take_quotes_comments_and_blank_lines(board):
    result = board.run_file('# ZeroPi\n\nAPP="mlb"\nBOARD_NAME=\'ZeroPi\'\n')
    assert result.returncode == 0, result.stderr
    assert "App           mlb" in result.stdout and "Hostname      ZeroPi" in result.stdout


def test_without_dry_run_it_needs_the_pi_and_sudo(board):
    result = board.run_file("APP=lll\n", "", "--yes", dry_run=False)
    assert result.returncode != 0
    assert "run this on the Pi" in result.stderr or "sudo" in result.stderr
    assert result.stdout == ""


def test_old_service_files_are_retired_to_a_backup_so_the_board_follows_its_config(board):
    """A hand-made board's own units (PlutoPi has both, with its flags in them) are moved, never deleted."""
    flags = 'Environment="ARGS=--led-rows=32 --led-pixel-mapper=Rotate:180 --led-brightness=85"'
    for folder in ("lib/systemd/system", "etc/systemd/system/LightningLane-Live-LED.service.d"):
        (board.root / folder).mkdir(parents=True)
    (board.root / "lib/systemd/system/LightningLane-Live-LED.service").write_text(f"[Service]\n{flags}\n")
    (board.root / "etc/systemd/system/LightningLane-Live-LED.service").write_text(f"[Service]\n{flags}\nExecStart=/old\n")
    (board.root / "etc/systemd/system/LightningLane-Live-LED.service.d/flags.conf").write_text(
        "[Service]\nEnvironment=\"ARGS=--led-slowdown-gpio=3\"\n")
    out = board.ok(BOARD_NAME="PlutoPi", APP="lll")
    backup = f"{board.root}/var/backups/board-setup/"
    for old, saved in (("lib/systemd/system/LightningLane-Live-LED.service", "LightningLane-Live-LED.service.lib"),
                       ("etc/systemd/system/LightningLane-Live-LED.service", "LightningLane-Live-LED.service"),
                       ("etc/systemd/system/LightningLane-Live-LED.service.d", "LightningLane-Live-LED.service.d")):
        assert f"Retiring the old {board.root}/{old}" in out
        assert re.search(rf"\+ mv {re.escape(f'{board.root}/{old}')} {re.escape(backup)}\d{{8}}-\d{{6}}/{re.escape(saved)}\n", out)
    assert f"it ran with: {flags}" in out and 'it ran with: Environment="ARGS=--led-slowdown-gpio=3"' in out
    assert "--led-rows" not in unit(out, "LightningLane-Live-LED.service")
    assert out.index("Retiring") < out.index("/etc/systemd/system/LightningLane-Live-LED.service (mode 644)")
    # its old boot link goes first (once), and ours is enabled at the end
    assert out.count("+ systemctl disable LightningLane-Live-LED.service\n") == 1
    assert out.index("systemctl disable LightningLane-Live-LED.service") < out.index("+ mv ")
    assert out.rindex("systemctl enable LightningLane-Live-LED.service") > out.index("+ mv ")


def test_our_own_service_file_unchanged_on_a_rerun_is_left_alone(board):
    ours = unit(board.ok(BOARD_NAME="Disneypi", APP="lll"), "LightningLane-Live-LED.service")
    (board.root / "etc/systemd/system").mkdir(parents=True)
    (board.root / "etc/systemd/system/LightningLane-Live-LED.service").write_text(ours + "\n")
    out = board.ok(BOARD_NAME="Disneypi", APP="lll")
    assert "Retiring" not in out and "+ mv " not in out
    assert "systemctl disable LightningLane-Live-LED.service" not in out
    assert "unchanged: " in out


def test_a_boards_own_config_json_matrix_is_left_alone(board):
    board.checkout("LightningLane-Live-LED", {
        "config.json": json.dumps({"matrix": {"led_brightness": 85, "led_rows": None}})})
    out = board.ok(BOARD_NAME="PlutoPi", APP="lll")
    assert "set in" not in out


