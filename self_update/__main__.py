"""The updater's command line, run from the app's folder with its venv's Python:

    venv/bin/python3 -m self_update status                       # what's installed, the last update
    venv/bin/python3 -m self_update check [--channel beta]       # what an update would do; changes nothing
    sudo venv/bin/python3 -m self_update update [--channel beta] # update, rolling back if it fails
    sudo venv/bin/python3 -m self_update rollback                # undo the last update (sudo lll-rollback)
    sudo venv/bin/python3 -m self_update recover                 # at boot: undo an update a power cut stopped

The channel is "releases" (the default) or "beta" (develop-beta's tip, once its CI passed). A
rollback also puts back config.json as it was before the update, undoing settings saved since.
Exits 0 when it did (or would do) what was asked, or there was nothing to do; 1 otherwise.
"""
import argparse
import logging
import os
import sys

from self_update.board import Board
from self_update.update import CHANNELS, NOTHING_TO_UNDO, RELEASES, Updater
from utils import debug, heartbeat

APP_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def status(updater):
    record = updater.state.load()
    board = updater.board
    lines = [f"Installed: {updater.installed_version} at {board.head()[:7]}"
             f" ({'on ' + board.branch() if board.branch() else 'detached'})",
             f"Last update: {record['phase']}"]
    if record.get("to"):
        lines.append(f"  to {record['to'].get('ref')} ({str(record['to'].get('sha'))[:7]}),"
                     f" from {record['from'].get('version')} ({str(record['from'].get('sha'))[:7]})")
    if record.get("reason"):
        lines.append(f"  rolled back because: {record['reason']}")
    if record.get("good"):
        lines.append(f"Good commits: {', '.join(sha[:7] for sha in record['good'])}")
    beat = heartbeat.read(updater.heartbeat_path)
    lines.append(f"Heartbeat: {updater.clock() - beat['at']:.0f}s ago" if beat else "Heartbeat: none")
    return "\n".join(lines)


def main(argv=None, updater=None, euid=os.geteuid):
    parser = argparse.ArgumentParser(prog="python3 -m self_update", description="Update the board from GitHub, with rollback.")
    commands = parser.add_subparsers(dest="command", required=True)
    commands.add_parser("status", help="what's installed and how the last update went")
    for name, text in (("check", "say what an update would do, changing nothing"),
                       ("update", "update, rolling back if the new version isn't healthy (as root)")):
        command = commands.add_parser(name, help=text)
        command.add_argument("--channel", choices=CHANNELS, default=RELEASES)
    commands.add_parser("rollback", help="undo the last update, config.json included (as root)")
    commands.add_parser("recover", help="roll back an update that stopped midway, else nothing (as root; "
                                        "board-setup.sh's lll-update-recover.service runs it at boot)")
    args = parser.parse_args(argv)

    debug.logger.setLevel(logging.INFO)
    # To the journal only (systemd-run's unit, or the terminal): the app's logs/app.log rotates in
    # the app's process, and two writers rotating one file lose lines.
    if debug.file_handler is not None:
        debug.logger.removeHandler(debug.file_handler)

    updater = updater or Updater(Board(APP_DIR))
    if args.command == "status":
        print(status(updater))
        return 0
    if args.command in ("update", "rollback", "recover") and euid() != 0:
        print(f"{args.command} needs root: sudo venv/bin/python3 -m self_update {args.command}", file=sys.stderr)
        return 1
    if args.command == "rollback":
        outcome = updater.rollback()
    elif args.command == "recover":
        outcome = updater.recover()
    else:
        outcome = updater.update(args.channel, dry_run=args.command == "check")
    print(f"{outcome.result}: {outcome.message}")
    usual_boot = args.command == "recover" and outcome.result == NOTHING_TO_UNDO
    return 0 if outcome.ok or usual_boot else 1


if __name__ == "__main__":
    sys.exit(main())
