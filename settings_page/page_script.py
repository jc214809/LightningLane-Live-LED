"""The main settings page's script: trip rows, the park picker, the previews, the Updates card's polling. The page works without it."""

import os

with open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "form_fetch.js"), encoding="utf-8") as _f:
    FORM_FETCH = _f.read()

# The sign-in page has no other script.
FORM_SCRIPT = "{\n" + FORM_FETCH + "}\n"

# In a block, so a page the board answers with (document.write) can run the script again: its consts aren't globals.
SCRIPT = (
    "{\n"
    + FORM_FETCH
    + """
const form = document.getElementById('settings');
const status = document.getElementById('save-status');
form.addEventListener('input', () => {
  form.dataset.dirty = '1';
  status.classList.add('dirty');
  status.querySelector('span:last-child').textContent = 'Unsaved changes';
});
form.addEventListener('submit', e => {
  // Not disabled: a disabled button's restart=0/1 wouldn't be sent. A second press is dropped instead.
  if (form.dataset.submitting) return e.preventDefault();
  form.dataset.submitting = '1';
  const button = e.submitter || document.getElementById('save');
  document.querySelectorAll('.save-buttons button').forEach(b => b.setAttribute('aria-disabled', 'true'));
  button.querySelector('span').textContent = 'Saving\\u2026';
});
window.addEventListener('beforeunload', e => {
  if (form.dataset.dirty && !form.dataset.submitting) e.preventDefault();
});
let nextTrip = document.querySelectorAll('#trip-list .trip').length;
document.getElementById('add-trip').addEventListener('click', () => {
  const trips = document.getElementById('trip-list');
  const n = nextTrip++;  // removed trips stay in the page, hidden, so counting them could repeat a number
  const row = document.getElementById('trip-row').content.cloneNode(true);
  row.querySelectorAll('[name]').forEach(el => { el.name = el.name.replace('_N', '_' + n); el.id = el.name; });
  row.querySelectorAll('label[for]').forEach(el => { el.htmlFor = el.htmlFor.replace('_N', '_' + n); });
  trips.appendChild(row);
  trips.querySelector('.trip:last-child input[type=text]').focus();
});
const parkList = document.getElementById('park-chips');
const parkAdd = document.getElementById('park_add');
const parkError = document.getElementById('park-error');
// Lower-case name to the name as listed; empty when the list hasn't loaded, and then names go as typed.
const parkNames = new Map([...document.querySelectorAll('#park-names option')].map(o => [o.value.toLowerCase(), o.value]));
const changed = () => form.dispatchEvent(new Event('input'));
const parkProblem = text => { parkError.textContent = text; parkError.hidden = !text; };
// The landmark the board plays before a park, by the loose name match the board uses.
const parkScenes = JSON.parse(document.getElementById('park-scenes')?.textContent || '{}');
function addPark() {
  const typed = parkAdd.value.trim().replace(/\\s+/g, ' ');
  if (!typed) return;
  const name = parkNames.size ? parkNames.get(typed.toLowerCase()) : typed;
  if (!name) return parkProblem(`"${typed}" isn't a ThemeParks.wiki park: pick one from the list.`);
  const chosen = [...parkList.querySelectorAll('input[name=park]')].map(i => i.value.toLowerCase());
  if (chosen.includes(name.toLowerCase())) return parkProblem(`${name} is already on the board.`);
  const chip = document.getElementById('park-chip').content.cloneNode(true);
  chip.querySelector('input[name=park]').value = name;
  chip.querySelector('input[name=park_remove]').value = name;
  chip.querySelector('.park-name').textContent = name;
  const scene = Object.entries(parkScenes).find(([key]) => name.toLowerCase().includes(key));
  if (scene) {
    const img = chip.querySelector('.park-landmark');
    img.src = scene[1];
    img.hidden = false;
    chip.querySelector('.noland').hidden = true;
  }
  chip.querySelectorAll('[aria-label]').forEach(el => { el.setAttribute('aria-label', el.getAttribute('aria-label') + ' ' + name); });
  parkList.appendChild(chip);
  parkAdd.value = '';
  parkProblem('');
  changed();
}
parkAdd.addEventListener('keydown', e => { if (e.key === 'Enter') { e.preventDefault(); addPark(); } });
// Picking a suggestion adds it straight away; typing waits for Enter or Add, as a typed name can be
// the start of a longer one.
parkAdd.addEventListener('input', e => {
  parkProblem('');
  if (e.inputType === 'insertReplacementText' || e.inputType === undefined) addPark();
});
document.getElementById('park-add-btn').addEventListener('click', addPark);
parkList.addEventListener('change', e => {  // with the script, a removed park leaves the page, so it can be added back
  if (e.target.name === 'park_remove' && e.target.checked) { e.target.closest('.park-chip').remove(); parkAdd.focus(); }
});
parkList.addEventListener('click', e => {
  const move = e.target.closest('.chip-btn');
  if (!move) return;
  const chip = move.closest('.park-chip');
  if (chip.previousElementSibling) { parkList.insertBefore(chip, chip.previousElementSibling); changed(); }
  (chip.querySelector('.chip-btn:not([hidden])') || move).focus();
});
document.querySelectorAll('.js-only').forEach(el => { el.hidden = false; });
const device = document.getElementById('sound_device');
const custom = document.getElementById('custom-device');
const showCustom = () => { custom.hidden = device.value !== 'custom'; };
device.addEventListener('change', showCustom);
showCustom();
// Volume: the slider and the box follow each other; the buttons ask the board without leaving the page.
const volume = document.getElementById('sound_volume');
const volumeSlider = document.getElementById('volume_slider');
const volumeStatus = document.getElementById('volume-status');
volumeSlider.addEventListener('input', () => { volume.value = volumeSlider.value; });
volume.addEventListener('input', () => { if (volume.value !== '') volumeSlider.value = volume.value; });
document.querySelectorAll('button[name=volume_action]').forEach(button => button.addEventListener('click', async e => {
  // The rest of the form goes along (for the speaker picked) but stays unsaved.
  const data = new URLSearchParams(new FormData(form));
  data.set('volume_action', button.value);
  button.disabled = true;
  delete volumeStatus.dataset.ok;
  volumeStatus.textContent = button.value === 'test' ? 'Playing\u2026' : 'Setting\u2026';
  try {
    const reply = await fetch('/volume', {method: 'POST', body: data, headers: {Accept: 'application/json'}});
    const result = await reply.json();  // a signed-out page gets HTML back, and lands in catch
    volumeStatus.textContent = result.message;
    volumeStatus.dataset.ok = result.ok;
  } catch {
    volumeStatus.textContent = "That didn't reach the board: reload the page and try again.";
    volumeStatus.dataset.ok = false;
  } finally {
    button.disabled = false;
  }
}));
const scheduleOn = document.getElementById('brightness_schedule');
const showSchedule = () => { document.getElementById('schedule').hidden = !scheduleOn.checked; };
scheduleOn.addEventListener('change', showSchedule);
showSchedule();
// A blank panel setting says the Pi model's default (page.py's panel texts, per model): follow
// a new pick of model.
const piModel = document.getElementById('pi_model');
const panelData = JSON.parse(document.getElementById('panel-blanks')?.textContent || '{}');
piModel?.addEventListener('change', () => {
  const blanks = panelData.blanks[piModel.value === 'auto' ? panelData.auto : piModel.value] || {};
  document.querySelectorAll('[data-key]').forEach(el => {
    const text = blanks[el.dataset.key] || 'Default';
    if (el.tagName === 'SELECT') el.options[0].textContent = text; else el.placeholder = text;
  });
});
// Updates: the buttons say they're working (a check can take a while), Roll back asks first, and
// while an update runs the page follows it, reloading once it's done. The settings page restarts
// during an update, so a failed ask just tries again.
// On the document, not each form: the page's own check puts in an Update now form later.
document.addEventListener('submit', e => {
  const f = e.target;
  if (!f.matches('form[data-busy]')) return;
  if (f.dataset.confirm && !confirm(f.dataset.confirm)) return e.preventDefault();
  const button = f.querySelector('button[type=submit]');
  button.disabled = true;
  button.querySelector('span').textContent = f.dataset.busy;
});
const updateRunning = document.getElementById('update-running');
if (updateRunning) {
  const follow = async () => {
    try {
      const reply = await fetch('/update/status', {headers: {Accept: 'application/json'}});
      const now = await reply.json();
      if (!now.running) return location.replace('/?t=' + Date.now() + '#updates');
      document.getElementById('update-phase').textContent = now.phase;
      const steps = document.getElementById('update-steps');
      if (steps) {
        steps.hidden = now.step === null;
        steps.querySelectorAll('li').forEach((li, i) => {
          li.className = i < now.step ? 'done' : i === now.step ? 'now' : '';
          if (i === now.step) li.setAttribute('aria-current', 'step'); else li.removeAttribute('aria-current');
        });
      }
    } catch {}
    setTimeout(follow, 5000);
  };
  setTimeout(follow, 5000);
}
// No check yet: check the installed channel now (the board keeps it ten minutes), without
// reloading the page over unsaved settings.
const autoCheck = document.querySelector('#update-check[data-auto]');
if (autoCheck) (async () => {
  try {
    const reply = await fetch('/update/check', {method: 'POST', body: new URLSearchParams({channel: autoCheck.dataset.auto}),
                                                headers: {Accept: 'application/json'}});
    autoCheck.outerHTML = (await reply.json()).html;  // a signed-out page gets HTML back, and lands in catch
  } catch {
    autoCheck.querySelector('div').textContent = "Couldn't check: press Check to try again.";
  }
})();
// The castle previews: dimmed to the brightness the Display card sets, turned the way Rotation turns it.
const level = id => { const v = parseInt(document.getElementById(id)?.value, 10); return isNaN(v) ? null : v; };
const dim = (id, percent) => { const img = document.getElementById(id); if (img) img.style.filter = `brightness(${0.25 + 0.75 * percent / 100})`; };
function brightnessPreviews() {
  if (!document.getElementById('pv-all')) return;
  const scheduleOn = document.getElementById('brightness_schedule').checked;
  const day = level('bright_day') ?? 80, night = level('bright_night') ?? 15, all = level('matrix_led_brightness');
  document.getElementById('pv-all-box').hidden = scheduleOn;
  document.getElementById('pv-day-box').hidden = !scheduleOn;
  document.getElementById('pv-night-box').hidden = !scheduleOn;
  dim('pv-all', all ?? 100);
  dim('pv-day', day);
  dim('pv-night', night);
  document.getElementById('pv-all-l').textContent = all ? `All day, ${all}%` : "All day, the Pi model's default";
  document.getElementById('pv-day-l').textContent = `Day, ${day}%`;
  document.getElementById('pv-night-l').textContent = `Night, ${night}%`;
}
['bright_day', 'bright_night', 'matrix_led_brightness', 'brightness_schedule'].forEach(id =>
  document.getElementById(id)?.addEventListener('input', brightnessPreviews));
brightnessPreviews();
const rotation = document.getElementById('matrix_led_pixel_mapper');
const turns = {'Rotate:90': 'rotate(90deg) scale(.5)', 'Rotate:180': 'rotate(180deg)', 'Rotate:270': 'rotate(270deg) scale(.5)',
               'Mirror:H': 'scaleX(-1)', 'Mirror:V': 'scaleY(-1)'};
function rotationPreview() {
  const img = document.getElementById('pv-rot');
  if (!img || !rotation) return;
  img.style.transform = turns[rotation.value] || '';
  const text = rotation.options[rotation.selectedIndex].text.split(' (')[0];
  document.getElementById('pv-rot-l').textContent = rotation.value ? `Drawn ${text.toLowerCase()}` : 'Drawn as is';
}
rotation?.addEventListener('change', rotationPreview);
rotationPreview();
const links = [...document.querySelectorAll('.toc a')];
const spy = new IntersectionObserver(entries => entries.forEach(e => {
  if (e.isIntersecting) links.forEach(a => a.classList.toggle('on', a.hash === '#' + e.target.id));
}), {rootMargin: '-80px 0px -65% 0px'});
document.querySelectorAll('main .card[id]').forEach(s => spy.observe(s));
}
"""  # noqa: E501  (served as written: a browser script, not Python)
)
