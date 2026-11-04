from self_update.release_notes import first_line, main, problem, release_notes

TEMPLATE = open(".github/pull_request_template.md", encoding="utf-8").read()


def test_the_notes_are_the_section_under_their_heading_bullets_and_comments_dropped():
    body = ("## Release notes\r\n<!-- for the owner -->\r\n- The castle sparkles at night.\r\n"
            "* Rides that are down blink slower.\r\n\r\n## Summary\r\n- Refactor the sparkle.\r\n")
    assert release_notes(body) == ["The castle sparkles at night.", "Rides that are down blink slower."]
    assert release_notes("Intro\n\n### Release Notes:\n1. One thing\n") == ["One thing"], "any level, numbered"


def test_none_is_an_empty_list_and_no_section_is_none():
    assert release_notes("## Release notes\nNone.\n## Summary\nCI only") == []
    assert release_notes("## Release notes\n- N/A\n") == []
    assert release_notes("## Summary\nStuff") is None
    assert release_notes("") is None and release_notes(None) is None
    assert release_notes(TEMPLATE) is None, "the template's comment alone isn't notes"
    assert release_notes("## Release notes\nNone of the screens change colour\n") == \
        ["None of the screens change colour"], "a sentence starting None is a note"


def test_the_first_line_skips_headings_comments_and_the_notes():
    assert first_line("Show what an update brings\n") == "Show what an update brings", "a merge before notes"
    assert first_line("## Release notes\nNone\n\n## Summary\n<!-- x -->\n- Faster CI\n") == "Faster CI"
    assert first_line("## Release notes\nNone\n") is None


def test_a_pull_request_needs_notes_unless_its_a_release():
    assert "Release notes" in problem(TEMPLATE)
    assert problem(TEMPLATE.replace("## Summary", "None\n\n## Summary")) is None
    assert problem("", head_branch="develop-beta") is None, "a release carries its PRs' notes"
    assert problem("", head_branch="feature/x")


def test_main_reads_the_description_from_the_environment():
    assert main({"PR_BODY": "## Release notes\nThe castle sparkles.", "PR_HEAD": "feature/x"}) == 0
    assert main({"PR_BODY": "## Summary\nx"}) == 1
    assert main({}) == 1
