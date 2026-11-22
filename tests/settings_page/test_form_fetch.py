"""The settings pages' form helper (settings_page/form_fetch.js), run under Node with a faked browser: a form's submit is
sent with fetch (Safari warns about an insecure form posted over plain http, and doesn't about fetch), and what the board
answers is shown the way a plain form post would show it. Without the script the forms post themselves (the page tests
check every form is still a plain method=post form). Also checked: each page carries the helper."""

import json
import re
import shutil
import subprocess

import pytest

from settings_page import page, surprises_page
from settings_page.page_script import FORM_FETCH

NODE = shutil.which("node")
needs_node = pytest.mark.skipif(NODE is None, reason="the helper runs under Node")

# A faked browser: the helper registers its submit listeners on `document`; the test body then drives them.
PRELUDE = """
const listeners = [], calls = [];
globalThis.document = {addEventListener: (type, fn, capture) => listeners.push([type, fn, !!capture]),
                       open: () => calls.push(['open']), write: html => calls.push(['write', html]),
                       close: () => calls.push(['close'])};
globalThis.location = {pathname: '/', search: '', reload: () => calls.push(['reload']),
                       assign: url => calls.push(['assign', url])};
globalThis.history = {replaceState: (a, b, url) => calls.push(['replaceState', url])};
globalThis.window = globalThis;
globalThis.alert =text => calls.push(['alert', text]);
globalThis.FormData = function (form) { return form.fields; };
const env = () => ({location, history, document, fetch: globalThis.fetch});
const fire = async (form, submitter, refused) => {
  const e = {target: form, submitter, defaultPrevented: !!refused, preventDefault() { calls.push(['preventDefault']); }};
  for (const [type, fn, capture] of listeners) if (type === 'submit' && capture) fn(e);
  for (const [type, fn, capture] of listeners) if (type === 'submit' && !capture) await fn(e);
};
"""


def run(body):
    # The block makes the helper's consts local, as on a page; the test body sits inside it, with them.
    script = (
        PRELUDE + "{\n" + FORM_FETCH + "\n(async () => {\n" + body + "\nconsole.log(JSON.stringify(calls));\n})();\n}"
    )
    out = subprocess.run([NODE, "-e", script], capture_output=True, text=True, timeout=30)
    assert out.returncode == 0, out.stderr
    return json.loads(out.stdout)


FORM = """{method: 'post', fields: [['pin', '1234']], getAttribute: () => '/pin', closest: () => null,
           dataset: {}, querySelectorAll: () => []}"""


@needs_node
def test_a_form_is_sent_with_fetch_with_its_fields_and_the_session_cookie():
    calls = run(f"""
        globalThis.fetch = async (url, init) => {{
          calls.push(['fetch', url, init.method, init.credentials, String(init.body)]);
          return {{redirected: true, url: 'http://board/?x'}};
        }};
        await fire({FORM}, {{name: 'go', value: 'yes'}});""")
    assert calls[0] == ["preventDefault"]
    assert calls[1] == ["fetch", "/pin", "POST", "same-origin", "pin=1234&go=yes"]


@needs_node
def test_a_redirect_is_followed_to_the_page_it_names_keeping_the_updates_anchor():
    calls = run("""
        globalThis.fetch = async () => ({redirected: true, url: 'http://board/?update=started'});
        await sendForm('/update/start', new URLSearchParams(), '#updates', env());""")
    assert calls == [["assign", "http://board/?update=started#updates"]]


@needs_node
def test_a_redirect_to_the_page_already_open_reloads_it():
    calls = run("""
        globalThis.fetch = async () => ({redirected: true, url: 'http://board/'});
        await sendForm('/update/check', new URLSearchParams(), '#updates', env());""")
    assert calls == [["replaceState", "http://board/#updates"], ["reload"]]


@needs_node
def test_a_page_answered_without_a_redirect_replaces_the_document():
    calls = run("""
        globalThis.fetch = async () => ({redirected: false, text: async () => '<p>Not saved</p>'});
        await sendForm('/save', new URLSearchParams(), '', env());""")
    assert calls == [["open"], ["write", "<p>Not saved</p>"], ["close"]]


@needs_node
def test_a_refused_confirm_sends_nothing():
    calls = run(f"""
        globalThis.fetch = async () => {{ calls.push(['fetch']); }};
        await fire({FORM}, null, true);""")
    assert calls == []


@needs_node
def test_a_board_that_cannot_be_reached_puts_the_buttons_back_and_says_so():
    calls = run("""
        globalThis.fetch = async () => { throw new TypeError('offline'); };
        const button = {disabled: false, innerHTML: 'Save'};
        const form = {method: 'post', fields: [], getAttribute: () => '/save', closest: () => null,
                      dataset: {submitting: '1'}, querySelectorAll: () => [button]};
        const e = {target: form, defaultPrevented: false, preventDefault() {}};
        for (const [t, fn, capture] of listeners) if (t === 'submit' && capture) fn(e);
        button.disabled = true; button.innerHTML = 'Saving';
        for (const [t, fn, capture] of listeners) if (t === 'submit' && !capture) await fn(e);
        calls.push(['button', button.disabled, button.innerHTML, form.dataset.submitting]);""")
    assert calls[0][0] == "alert" and "didn't reach the board" in calls[0][1]
    assert calls[1] == ["button", False, "Save", None]


def test_every_page_with_a_form_carries_the_helper():
    assert FORM_FETCH in page.SCRIPT and FORM_FETCH in surprises_page.SCRIPT and FORM_FETCH in page.FORM_SCRIPT
    assert "send.submit()" not in surprises_page.SCRIPT, "the import's hidden form would get Safari's prompt"
    html = page.pin_page(board="b")
    assert page.FORM_SCRIPT in html


def test_the_forms_still_post_themselves_without_the_script():
    html = page.pin_page(board="b", phone=True)
    assert re.findall(r'<form method="post" action="(/[a-z/]+)"', html) == ["/pin/show", "/pin/send", "/pin"]
