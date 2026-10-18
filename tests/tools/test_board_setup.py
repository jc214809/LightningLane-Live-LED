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
    out = board.ok(BOARD_NAME="Disneypi", APP="lll", LED_ROWS=64, EXTRA_ARGS="--led-brightness=85")
    service = unit(out, "LightningLane-Live-LED.service")
    checkout = board.home / "LightningLane-Live-LED"
    assert f"WorkingDirectory={checkout}" in service
    assert f"ExecStart={checkout}/venv/bin/python3 {checkout}/disney.py $ARGS" in service
    assert 'Environment="ARGS=--led-brightness=85"' in service
    assert "--led-rows" not in service  # boards.json has the board's settings
    assert "ExecStartPre" not in service  # the old script's, under [Unit], where systemd ignores it
    assert "boards.json has Disneypi" in out
    assert f"git clone --branch develop-beta https://github.com/jc214809/LightningLane-Live-LED.git {checkout}" in out
    assert f"(cd {checkout} && bash LLL-install.sh)" in out  # a fresh board gets the full install
    for other in ("peloton-led.service", "mlb-led-scoreboard.service"):
        assert f"systemctl disable --now {other}" in out
    assert out.index("systemctl enable LightningLane-Live-LED.service") < out.index(
        "systemctl restart LightningLane-Live-LED.service")


def test_lll_on_a_board_it_has_set_up_updates_and_skips_apt_and_the_driver_build(board):
    checkout = board.checkout("LightningLane-Live-LED", {
        "venv/bin/python3": "", "submodules/matrix/Makefile": "", "config.json": "{}",
        "boards.json": json.dumps({"MickeyPi": {"led_rows": 64}})})
    (checkout / "venv/bin/python3").chmod(0o755)
    out = board.ok(BOARD_NAME="MickeyPi", APP="lll", LLL_BRANCH="develop-sound")
    assert f"git -C {checkout} checkout develop-sound" in out
    assert f"git -C {checkout} pull --ff-only" in out
    assert f"(cd {checkout} && bash LLL-install.sh -p -m)" in out
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


def test_lll_on_a_board_missing_from_boards_json_gets_the_panel_in_config_json(board):
    board.checkout("LightningLane-Live-LED", {"boards.json": json.dumps({"Disneypi": {}})})
    out = board.ok(BOARD_NAME="NewPi", APP="lll", LED_ROWS=64, LED_SLOWDOWN_GPIO=4)
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
    out = board.ok(BOARD_NAME="ZeroPi", APP="peloton", PELOTON_AUTO_TOKEN="yes")
    drop_in = unit(out, "peloton-led.service.d/board.conf")
    assert drop_in.splitlines() == [
        "[Service]", "ExecStart=",
        f"ExecStart={PELOTON_EXEC} --led-gpio-mapping=adafruit-hat-pwm --led-rows=32 --led-cols=64 --led-slowdown-gpio=2"]
    installer = f"(cd {checkout} && bash peloton-install.sh --auto-token)"
    assert out.index("peloton-led.service.d/board.conf") < out.index(installer)
    assert "systemctl disable --now LightningLane-Live-LED.service" in out


def test_mlb_runs_upstream_with_the_panel_flags_and_answers_its_one_question(board):
    out = board.ok(BOARD_NAME="ZeroPi", APP="mlb", EXTRA_ARGS="--led-brightness=80")
    checkout = board.home / "mlb-led-scoreboard"
    assert f"git clone --branch master https://github.com/MLB-LED-Scoreboard/mlb-led-scoreboard.git {checkout}" in out
    assert f"(cd {checkout} && printf 'y\\n' | bash install.sh )" in out
    assert (f"ExecStart={checkout}/venv/bin/python3 {checkout}/main.py --led-gpio-mapping=adafruit-hat-pwm "
            "--led-rows=32 --led-cols=64 --led-slowdown-gpio=2 --led-brightness=80") in unit(out, "mlb-led-scoreboard.service")


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


@pytest.mark.parametrize("answers, message", [
    ("COLOR=red\n", "unknown key COLOR"),
    ("APP=nba\n", "APP=nba isn't one of: lll peloton mlb"),
    ("LED_ROWS=16\n", "LED_ROWS=16 isn't one of: 32 64"),
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


def test_old_service_files_are_retired_to_a_backup_so_the_board_follows_boards_json(board):
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
    assert "Retiring" not in out and "mv " not in out
    assert "systemctl disable LightningLane-Live-LED.service" not in out
    assert "unchanged: " in out


def test_config_json_matrix_settings_that_override_boards_json_are_pointed_out_not_removed(board):
    board.checkout("LightningLane-Live-LED", {
        "boards.json": json.dumps({"PlutoPi": {"led_rows": 32}}),
        "config.json": json.dumps({"matrix": {"led_brightness": 85, "led_rows": None}})})
    out = board.ok(BOARD_NAME="PlutoPi", APP="lll")
    assert "config.json's matrix section overrides boards.json with led_brightness=85 (left as is)" in out
    assert "set in" not in out
