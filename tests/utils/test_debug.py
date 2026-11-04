import os
import stat
import subprocess
import sys
import tempfile


def test_import_survives_unwritable_log_dir():
    """Regression test: installing this package somewhere the process can't
    write (e.g. a read-only site-packages for a consuming plugin) must not
    crash on `import utils.debug` — file logging should fall back or be
    disabled instead."""
    with tempfile.TemporaryDirectory() as tmp:
        unwritable = os.path.join(tmp, "unwritable-logs")
        os.makedirs(unwritable)
        os.chmod(unwritable, stat.S_IREAD | stat.S_IEXEC)
        try:
            env = dict(os.environ, LLL_LOG_DIR=unwritable)
            result = subprocess.run(
                [sys.executable, "-c", "import utils.debug; utils.debug.info('ok')"],
                env=env,
                capture_output=True,
                text=True,
                timeout=10,
            )
        finally:
            os.chmod(unwritable, stat.S_IRWXU)

        assert result.returncode == 0, result.stderr
