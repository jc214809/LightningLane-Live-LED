const table = document.querySelector('table.odds');
const body = table.tBodies[0];
const rows = () => Array.from(body.rows).filter(row => row.dataset.name);
const picked = row => row.nextElementSibling.querySelectorAll(
  'input[name="rides_' + row.dataset.name + '"]:checked, input[type=hidden][name="rides_' + row.dataset.name + '"]').length;
const numberOf = input => { const text = input.value || input.placeholder; return text === '' ? 0 : parseFloat(text); };
const keyOf = (row, kind, cell) => {
  if (kind === 'on') return row.querySelector('.switch').checked ? 1 : 0;
  if (kind === 'name') return row.dataset.label.toLowerCase();
  if (kind === 'rides') return row.querySelector('.add-rides') ? picked(row) : -1;
  const input = row.cells[cell].querySelector('input');
  return input ? numberOf(input) : -1;
};
table.querySelectorAll('thead th').forEach((th, cell) => {
  th.querySelector('button').addEventListener('click', () => {
    const kind = th.dataset.sort;
    const direction = th.getAttribute('aria-sort') === 'none' ? th.dataset.first
      : th.getAttribute('aria-sort') === 'ascending' ? 'descending' : 'ascending';
    table.querySelectorAll('thead th').forEach(other => other.setAttribute('aria-sort', 'none'));
    th.setAttribute('aria-sort', direction);
    const sign = direction === 'ascending' ? 1 : -1;
    rows().map(row => [row, row.nextElementSibling, keyOf(row, kind, cell)])
      .sort((a, b) => (a[2] < b[2] ? -sign : a[2] > b[2] ? sign : a[0].dataset.label.localeCompare(b[0].dataset.label)))
      .forEach(([row, panel]) => { body.appendChild(row); body.appendChild(panel); });
  });
});
const form = document.getElementById('settings');
const status = document.getElementById('share-status');
const say = (text, bad) => { status.textContent = text; status.classList.toggle('bad', !!bad); };

// Export: one click copies every setting on the page, saved or not. They're fetched ahead (on load, and a moment after
// each edit) so the click can copy at once: a browser only lets a click copy while it's still fresh.
let ready = null, version = 0, timer = null;
const refresh = () => {
  clearTimeout(timer);
  const mine = ++version;
  ready = null;
  return fetch('/surprises/export', {method: 'POST', body: new URLSearchParams(new FormData(form))})
    .then(response => response.json())
    .catch(() => ({ok: false, problems: ["Couldn't reach the board."]}))
    .then(reply => { if (mine === version) ready = reply; return reply; });
};
const stale = () => { ready = null; version++; clearTimeout(timer); timer = setTimeout(refresh, 300); };
form.addEventListener('input', stale);
form.addEventListener('change', stale);
refresh();
// The board's page is plain http, where navigator.clipboard doesn't exist: copy through a hidden textarea, which
// works there, and use the clipboard API where the browser has it.
const copyText = async text => {
  const area = document.createElement('textarea');
  area.value = text;
  area.setAttribute('readonly', '');
  area.style.cssText = 'position:fixed;top:0;left:-9999px;opacity:0';
  document.body.appendChild(area);
  area.select();
  let copied = false;
  try { copied = document.execCommand('copy'); } catch (error) { copied = false; }
  area.remove();
  if (copied) return true;
  if (navigator.clipboard && window.isSecureContext) {
    try { await navigator.clipboard.writeText(text); return true; } catch (error) { /* not allowed */ }
  }
  return false;
};
document.getElementById('export-btn').addEventListener('click', async () => {
  say('');
  const reply = ready || await refresh();
  if (!reply.ok) { say('Not copied: ' + reply.problems.join(' '), true); return; }
  say(await copyText(reply.json) ? 'Copied everything on this page. On the other board, press Import.'
                                  : "Your browser wouldn't let the page copy. Try Export again.", false);
});

// Import: takes what is on the clipboard. Where the browser lets the page read it, that is the click; on plain http
// it doesn't, so the click waits for one Ctrl+V (Cmd+V on a Mac), which a page is always allowed to see.
const importText = async text => {
  let reply;
  try {
    const response = await fetch('/surprises/import', {method: 'POST', headers: {Accept: 'application/json'},
                                                       body: new URLSearchParams({surprises_json: text})});
    reply = await response.json();
  } catch (error) { say("Couldn't reach the board to import. Try again.", true); return; }
  if (!reply.ok) { say('Nothing imported: ' + reply.problems.join(' '), true); return; }
  const send = document.createElement('form');  // the board draws the page filled from the settings
  send.method = 'post'; send.action = '/surprises/import'; send.hidden = true;
  const field = document.createElement('textarea');
  field.name = 'surprises_json'; field.value = text;
  send.appendChild(field);
  document.body.appendChild(send);
  send.submit();
};
let waiting = null;
const onPaste = event => {
  event.preventDefault();
  clearTimeout(waiting);
  say('Importing...');
  importText(event.clipboardData.getData('text'));
};
document.getElementById('import-btn').addEventListener('click', async () => {
  say('');
  if (navigator.clipboard && navigator.clipboard.readText && window.isSecureContext) {
    try { await importText(await navigator.clipboard.readText()); return; } catch (error) { /* not allowed: ask */ }
  }
  say('Press Ctrl+V (Cmd+V on a Mac) now to paste the settings. The browser does not let this page read the clipboard itself.');
  document.removeEventListener('paste', onPaste);
  document.addEventListener('paste', onPaste, {once: true});
  clearTimeout(waiting);
  waiting = setTimeout(() => { document.removeEventListener('paste', onPaste); say("Didn't get a paste. Press Import to try again."); }, 20000);
});
const percentOf = input => { const n = parseFloat(input.value || input.placeholder); return isNaN(n) ? 0 : n; };
const showTotals = () => {
  let all = 0, ticked = 0;
  rows().forEach(row => {
    const input = row.cells[2].querySelector('input');
    all += percentOf(input);
    if (row.querySelector('.switch').checked) ticked += percentOf(input);
  });
  const total = document.getElementById('total-all');
  total.textContent = parseFloat(all.toFixed(3)) + '%';
  total.classList.toggle('over', all > 100);
  document.getElementById('total-ticked').textContent = parseFloat(ticked.toFixed(3)) + '% from the ticked characters';
};
table.addEventListener('input', showTotals);
table.addEventListener('change', showTotals);
const rideList = JSON.parse(document.getElementById('ride-list').textContent);
const namesText = row => {
  const names = Array.from(row.nextElementSibling.querySelectorAll('input[type=checkbox]:checked')).map(input => input.value);
  return names.length ? names.join(', ') : 'No rides';
};
const listed = Object.entries(rideList).filter(([, rides]) => rides.length);
document.querySelectorAll('button.add-rides').forEach(button => {
  const row = button.closest('tr');
  const panel = row.nextElementSibling;
  const box = panel.querySelector('.ride-pick');
  const field = 'rides_' + row.dataset.name;
  let built = false;
  const setOpen = open => {
    panel.hidden = !open;
    button.setAttribute('aria-expanded', String(open));
    button.title = open ? 'Close' : 'Add rides';
  };
  const closeButton = () => {
    const close = document.createElement('button');
    close.type = 'button'; close.className = 'secondary close-rides'; close.textContent = 'Close';
    close.addEventListener('click', () => { setOpen(false); row.scrollIntoView({block: 'nearest'}); button.focus(); });
    return close;
  };
  panel.addEventListener('keydown', event => {
    if (event.key === 'Escape') { setOpen(false); row.scrollIntoView({block: 'nearest'}); button.focus(); }
  });
  button.addEventListener('click', () => {
    setOpen(panel.hidden);
    if (panel.hidden || built) return;
    built = true;
    if (!listed.length) {
      const note = document.createElement('p');
      note.textContent = "The ride list hasn't loaded yet. The board fetches it from ThemeParks.wiki when it's online; try again in a minute.";
      box.append(note, closeButton());
      return;
    }
    const chosen = new Set(Array.from(box.querySelectorAll('input[type=hidden][name="' + field + '"]')).map(input => input.value));
    const marker = box.querySelector('input[name="rides_set_' + row.dataset.name + '"]');
    const markerValue = marker ? marker.value : '1';  // "saved" says these rides were saved: keep saying it
    const known = new Set(listed.flatMap(([, rides]) => rides));
    const gone = Array.from(chosen).filter(ride => !known.has(ride));
    box.textContent = '';
    const set = document.createElement('input');
    set.type = 'hidden'; set.name = 'rides_set_' + row.dataset.name; set.value = markerValue;
    const search = document.createElement('input');
    search.type = 'search'; search.placeholder = 'Search rides'; search.setAttribute('aria-label', 'Search rides');
    const bar = document.createElement('div');
    bar.className = 'ride-bar';
    bar.append(search, closeButton());
    const grid = document.createElement('div');
    grid.className = 'ride-grid';
    (gone.length ? listed.concat([['No longer listed', gone]]) : listed).forEach(([park, rides]) => {
      const column = document.createElement('div');
      column.className = 'ride-park';
      const title = document.createElement('h4');
      title.textContent = park;
      column.appendChild(title);
      rides.forEach(ride => {
        const label = document.createElement('label');
        const input = document.createElement('input');
        input.type = 'checkbox'; input.name = field; input.value = ride; input.checked = chosen.has(ride);
        const text = document.createElement('span');
        text.textContent = ride;
        label.append(input, text);
        column.appendChild(label);
      });
      grid.appendChild(column);
    });
    const foot = document.createElement('div');
    foot.className = 'ride-bar ride-foot';
    foot.appendChild(closeButton());
    box.append(set, bar, grid, foot);
    search.addEventListener('keydown', event => { if (event.key === 'Enter') event.preventDefault(); });  // not a save
    const none = document.createElement('p');
    none.hidden = true;
    grid.after(none);
    search.addEventListener('input', () => {
      const needle = search.value.trim().toLowerCase();
      grid.querySelectorAll('label').forEach(label => { label.hidden = needle && !label.textContent.toLowerCase().includes(needle); });
      let shown = 0;
      grid.querySelectorAll('.ride-park').forEach(column => {
        const matches = column.querySelectorAll('label:not([hidden])').length;
        column.hidden = !matches;
        shown += matches;
      });
      none.textContent = 'No rides match "' + search.value.trim() + '".';
      none.hidden = shown > 0;
    });
    box.addEventListener('change', () => {
      const names = row.querySelector('.ride-names');
      names.textContent = namesText(row);
      names.classList.toggle('none', names.textContent === 'No rides');
    });
  });
});
