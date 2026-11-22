// Every action on the settings pages is a <form> post that the script sends with fetch() instead: Safari warns "this
// form is not secure, Send Anyway" for any form posted over plain http, and fetch() doesn't get that prompt. Without the
// script the forms post themselves as before. Shared by the main, sign-in and Surprise characters pages (each page's
// script sits in a block, so a page the board redraws with document.write can run it again).
// Showing what the board answered: a redirect (every save, sign-in and sign-out) is followed to the page it names, as
// the browser would; a page (a problem, a refused save, a filled-in import) replaces this one.
const showReply = async (reply, hash, env = window) => {
  const where = env.location;
  if (reply.redirected) {
    const to = new URL(reply.url);  // fetch drops the redirect's #fragment: the form says where it lands
    to.hash = hash;
    if (to.pathname + to.search === where.pathname + where.search) {  // the same page again: assign() wouldn't reload it
      env.history.replaceState(null, '', to.href);
      where.reload();
    } else {
      where.assign(to.href);
    }
    return;
  }
  const html = await reply.text();
  env.document.open();
  env.document.write(html);
  env.document.close();
};
const sendForm = async (url, params, hash = '', env = window) => {
  const reply = await env.fetch(url, {method: 'POST', body: params, credentials: 'same-origin'});
  await showReply(reply, hash, env);
};
// The form's fields as the browser would post them, with the button that was pressed (if it has a name).
const fieldsOf = (form, submitter) => {
  const params = new URLSearchParams(new FormData(form));
  if (submitter && submitter.name) params.append(submitter.name, submitter.value);
  return params;
};
// Capture phase, so it sees the buttons before the page's own handlers say "Saving..." on them.
document.addEventListener('submit', e => {
  const form = e.target;
  form.llButtons = [...form.querySelectorAll('button[type=submit]')].map(b => [b, b.disabled, b.innerHTML]);
}, true);
// Bubble phase, after the page's own handlers: one that refused (Roll back's confirm) has called preventDefault.
document.addEventListener('submit', async e => {
  const form = e.target;
  if (e.defaultPrevented || !window.fetch || (form.method || '').toLowerCase() !== 'post') return;
  e.preventDefault();
  try {
    await sendForm(form.getAttribute('action') || location.pathname, fieldsOf(form, e.submitter),
                   form.closest('#updates') ? '#updates' : '');
  } catch (error) {  // the board couldn't be reached: put the buttons back, so the person can press again
    delete form.dataset.submitting;
    (form.llButtons || []).forEach(([button, disabled, html]) => { button.disabled = disabled; button.innerHTML = html; });
    alert("That didn't reach the board: check the connection and try again.");
  }
});
