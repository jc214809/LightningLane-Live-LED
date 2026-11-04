import pytest

from tools import check_release_tag
from tools.check_release_tag import main, script_version, tag_problem


def test_a_matching_tag_passes():
    assert tag_problem("v2.0.0", "2.0.0") is None


@pytest.mark.parametrize("tag", ["2.0.0", "v2.0", "v2.0.0-beta", "release-2.0.0", "v2.0.0 "])
def test_anything_but_vmajor_minor_patch_is_refused(tag):
    assert "isn't a release tag" in tag_problem(tag, "2.0.0")


def test_a_tag_for_another_version_is_refused():
    assert "doesn't match version.py's 2.0.0" in tag_problem("v2.0.1", "2.0.0")


def test_reads_the_version_as_text(tmp_path):
    version = tmp_path / "version.py"
    version.write_text('SCRIPT_NAME = "x"\nSCRIPT_VERSION = "3.1.4"\n')
    assert script_version(str(version)) == "3.1.4"


def test_a_version_file_without_one_is_an_error(tmp_path):
    version = tmp_path / "version.py"
    version.write_text('SCRIPT_NAME = "x"\n')
    with pytest.raises(ValueError):
        script_version(str(version))


def test_the_real_version_file_has_a_release_version():
    assert tag_problem(f"v{script_version()}", script_version()) is None


def test_main_exit_codes(monkeypatch, caplog):
    monkeypatch.setattr(check_release_tag, "script_version", lambda: "2.0.0")
    assert main(["v2.0.0"]) == 0
    assert main(["v1.9.9"]) == 1
    assert "doesn't match" in caplog.text
    assert main([]) == 2
