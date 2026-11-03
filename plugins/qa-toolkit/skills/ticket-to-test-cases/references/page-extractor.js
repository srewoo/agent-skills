// Page extractor for ticket-to-test-cases. Evaluate this function in the page under test and save the
// returned object as page.json. It reads forms (fields, labels, required, maxLength, dropdown options), visible buttons,
// navigation links and same-origin links. It never clicks, types or submits anything.
//
// Browser automation tool: pass the function below as the script to evaluate in the page.
// No automation: open DevTools → Console, paste
//   copy(JSON.stringify((<the function below>)()))
// press Enter, then paste the clipboard into page.json.
() => {
  const sel = (el) => {
    if (el.id) return '#' + el.id;
    const tid = el.getAttribute && (el.getAttribute('data-testid') || el.getAttribute('data-test-id') || el.getAttribute('data-test'));
    if (tid) return '[data-testid="' + tid + '"]';
    const cls = (typeof el.className === 'string' ? el.className : '').split(' ').filter(Boolean).slice(0, 2);
    return el.tagName.toLowerCase() + (cls.length ? '.' + cls.join('.') : '');
  };
  const txt = (el) => (el.textContent || '').replace(/\s+/g, ' ').trim();
  const visible = (el) => { const r = el.getBoundingClientRect(); return r.width > 0 || r.height > 0 || el.getClientRects().length > 0; };
  const label = (f) => {
    if (f.id) { const l = document.querySelector('label[for="' + CSS.escape(f.id) + '"]'); if (l) return txt(l); }
    const p = f.closest('label'); if (p) return txt(p).slice(0, 80);
    return f.getAttribute('aria-label') || f.placeholder || '';
  };
  const features = [];
  document.querySelectorAll('form, [role="form"]').forEach((form, i) => {
    const fields = [...form.querySelectorAll('input, select, textarea')].filter(f => f.type !== 'hidden').map(f => ({
      name: f.name || f.id || label(f) || f.type, id: f.id || undefined, label: label(f) || undefined, type: f.tagName === 'INPUT' ? (f.type || 'text') : f.tagName.toLowerCase(),
      required: f.required || f.getAttribute('aria-required') === 'true' || undefined, placeholder: f.placeholder || undefined,
      maxLength: f.maxLength > 0 ? f.maxLength : undefined, pattern: f.pattern || undefined, selector: sel(f),
      options: f.tagName === 'SELECT' ? [...f.options].map(o => txt(o)).filter(Boolean).slice(0, 40) : undefined
    }));
    if (!fields.length) return;
    const submit = form.querySelector('button[type="submit"], input[type="submit"], button:not([type])');
    features.push({ type: 'form', name: form.name || form.id || form.getAttribute('aria-label') || ('Form ' + (i + 1)), action: form.action || '', method: form.method || 'POST',
      fields, fieldCount: fields.length, submitText: submit ? (txt(submit) || submit.value || 'Submit') : 'Submit', selector: sel(form) });
  });
  const seen = new Set();
  document.querySelectorAll('button, [role="button"], a.btn, a.button, input[type="button"], input[type="submit"]').forEach(b => {
    const t = (txt(b) || b.getAttribute('aria-label') || b.title || b.value || '').slice(0, 80);
    if (!t || seen.has(t.toLowerCase()) || !visible(b)) return;
    seen.add(t.toLowerCase());
    features.push({ type: 'button', text: t, disabled: !!b.disabled, selector: sel(b), href: b.href || undefined });
  });
  const nav = [];
  document.querySelectorAll('nav a[href], [role="navigation"] a[href], header a[href], aside a[href]').forEach(a => {
    const t = txt(a).slice(0, 60); if (!t || !a.href || a.href.startsWith('javascript:')) return;
    if (!seen.has('nav:' + t.toLowerCase())) { seen.add('nav:' + t.toLowerCase()); nav.push({ type: 'link', text: t, href: a.href, selector: sel(a) }); }
  });
  features.push(...nav.slice(0, 60));
  const links = [...new Set([...document.querySelectorAll('a[href]')].map(a => a.href).filter(h => h.startsWith(location.origin) && !h.includes('#')))].slice(0, 150);
  return { url: location.href, title: document.title, features, links, forms: features.filter(f => f.type === 'form').length, buttons: features.filter(f => f.type === 'button').length };
}
