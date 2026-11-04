const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const { setupContactForm } = require('../contact-form.js');

const root = path.resolve(__dirname, '..');
const names = ['name', 'email', 'reason', 'message'];
const localeKeys = {
  sending: 'form_sending', success: 'form_success', errorRequired: 'form_error_required',
  errorEmail: 'form_error_email', errorInvalid: 'form_error_invalid', errorServerField: 'form_error_server_field',
  errorValidation: 'form_error_validation', errorServerValidation: 'form_error_server_validation',
  errorRate: 'form_error_rate', errorBlocked: 'form_error_blocked', errorHoneypot: 'form_error_honeypot', errorHttp: 'form_error_http',
  errorNetwork: 'form_error_network'
};

function fixture(lang = 'en', values = {}) {
  const copy = JSON.parse(fs.readFileSync(path.join(root, 'translations', `${lang}.json`), 'utf8')).content;
  const dataset = Object.fromEntries(Object.entries(localeKeys).map(([key, source]) => [key, copy[source]]));
  function field(name, value = '') {
    const attrs = {};
    return {
      name, value, attrs, validity: { typeMismatch: false }, focused: false,
      setAttribute(key, val) { attrs[key] = val; },
      removeAttribute(key) { delete attrs[key]; },
      focus() { this.focused = true; },
      checkValidity() {
        this.validity.typeMismatch = name === 'email' && !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(this.value);
        return !this.validity.typeMismatch && this.value.length <= (name === 'message' ? 10000 : 254);
      }
    };
  }
  const fields = Object.fromEntries(names.map((name) => [name, field(name, values[name] || '')]));
  fields._gotcha = field('_gotcha', values._gotcha || '');
  const errors = Object.fromEntries(names.map((name) => [name, { textContent: '' }]));
  const status = { textContent: '', dataset: {} };
  const button = { textContent: copy.form_button, disabled: false };
  const listeners = {};
  const attrs = {};
  const form = {
    dataset, attrs, action: 'https://formspree.io/f/xgaappab', noValidate: false,
    elements: { namedItem(name) { return fields[name] || null; } },
    querySelector(selector) {
      const match = selector.match(/^\[data-error-for="(\w+)"\]$/);
      if (match) return errors[match[1]];
      if (selector === '[data-form-status]') return status;
      if (selector === '[type="submit"]') return button;
      return null;
    },
    setAttribute(key, val) { attrs[key] = val; },
    removeAttribute(key) { delete attrs[key]; },
    addEventListener(name, handler) { listeners[name] = handler; },
    reset() { for (const field of Object.values(fields)) field.value = ''; this.wasReset = true; }
  };
  class FakeFormData {
    constructor(target) {
      assert.equal(target, form);
      this.sourceForm = target;
      this.entries = Object.fromEntries(Object.entries(fields).map(([name, field]) => [name, field.value]));
    }
  }
  const submitEvent = { preventDefault() { this.prevented = true; }, prevented: false };
  return { form, fields, errors, status, button, listeners, submitEvent, FakeFormData, copy };
}

for (const lang of ['it', 'en', 'fr']) {
  test(`${lang}: required, email and reason validation prevent requests`, async () => {
    const f = fixture(lang, { name: '  ', email: 'invalid', reason: '', message: 'Hello' });
    let calls = 0;
    const controller = setupContactForm(f.form, async () => { calls += 1; }, f.FakeFormData);
    assert.equal(f.form.noValidate, false);
    await controller.handleSubmit(f.submitEvent);
    assert.equal(calls, 0);
    assert.equal(f.submitEvent.prevented, true);
    assert.equal(f.errors.name.textContent, f.copy.form_error_required);
    assert.equal(f.errors.email.textContent, f.copy.form_error_email);
    assert.equal(f.errors.reason.textContent, f.copy.form_error_required);
    assert.equal(f.status.textContent, f.copy.form_error_validation);
    assert.equal(f.fields.name.focused, true);
  });
}

test('successful HTTP response resets the form only after it resolves; in-flight submit is ignored', async () => {
  const f = fixture('en', { name: 'Samuel', email: 'samuel@example.com', reason: 'project', message: 'Hello' });
  let resolveRequest;
  let calls = 0;
  let request;
  const controller = setupContactForm(f.form, (url, options) => {
    calls += 1;
    request = { url, options };
    return new Promise((resolve) => { resolveRequest = resolve; });
  }, f.FakeFormData);
  const first = controller.handleSubmit(f.submitEvent);
  const duplicate = controller.handleSubmit({ preventDefault() {} });
  assert.equal(calls, 1);
  assert.equal(f.button.disabled, true);
  assert.equal(f.form.attrs['aria-busy'], 'true');
  assert.equal(f.status.textContent, f.copy.form_sending);
  assert.equal(f.form.wasReset, undefined);
  assert.equal(request.url, 'https://formspree.io/f/xgaappab');
  assert.equal(request.options.method, 'POST');
  assert.deepEqual(request.options.headers, { Accept: 'application/json' });
  assert.ok(request.options.body instanceof f.FakeFormData);
  assert.equal(request.options.body.sourceForm, f.form);
  assert.deepEqual(request.options.body.entries, { name: 'Samuel', email: 'samuel@example.com', reason: 'project', message: 'Hello', _gotcha: '' });
  resolveRequest({ ok: true, status: 200 });
  await Promise.all([first, duplicate]);
  assert.equal(f.form.wasReset, true);
  assert.equal(f.status.textContent, f.copy.form_success);
  assert.equal(f.button.disabled, false);
  assert.equal(f.button.textContent, f.copy.form_button);
  assert.equal(f.form.attrs['aria-busy'], undefined);
});

test('HTTP 422 shows localized field error and retains the message', async () => {
  const f = fixture('fr', { name: 'Ana', email: 'ana@example.com', reason: 'question', message: 'Bonjour' });
  const controller = setupContactForm(f.form, async () => ({
    ok: false, status: 422, json: async () => ({ errors: [{ field: 'email', message: 'English server text' }] })
  }), f.FakeFormData);
  await controller.handleSubmit(f.submitEvent);
  assert.equal(f.errors.email.textContent, f.copy.form_error_server_field);
  assert.equal(f.fields.email.attrs['aria-invalid'], 'true');
  assert.equal(f.status.textContent, f.copy.form_error_server_validation);
  assert.equal(f.form.wasReset, undefined);
  assert.equal(f.fields.message.value, 'Bonjour');
  assert.equal(f.button.disabled, false);
});

test('HTTP 400 with unreadable JSON retains input and reports a validation response', async () => {
  const f = fixture('it', { name: 'Ana', email: 'ana@example.com', reason: 'project', message: 'Messaggio' });
  const controller = setupContactForm(f.form, async () => ({
    ok: false, status: 400, json: async () => { throw new SyntaxError('invalid JSON'); }
  }), f.FakeFormData);
  await controller.handleSubmit(f.submitEvent);
  assert.equal(f.status.textContent, f.copy.form_error_server_validation);
  assert.equal(f.form.wasReset, undefined);
  assert.equal(f.fields.message.value, 'Messaggio');
  assert.equal(f.button.disabled, false);
});

test('a non-OK response never shows success, even with HTTP 200', async () => {
  const f = fixture('en', { name: 'Ana', email: 'ana@example.com', reason: 'other', message: 'Hello' });
  const controller = setupContactForm(f.form, async () => ({ ok: false, status: 200 }), f.FakeFormData);
  await controller.handleSubmit(f.submitEvent);
  assert.equal(f.status.textContent, f.copy.form_error_http);
  assert.equal(f.form.wasReset, undefined);
  assert.equal(f.fields.message.value, 'Hello');
});

for (const [statusCode, key] of [[429, 'form_error_rate'], [403, 'form_error_blocked'], [503, 'form_error_http']]) {
  test(`HTTP ${statusCode} keeps input and reports localized failure`, async () => {
    const f = fixture('it', { name: 'Ana', email: 'ana@example.com', reason: 'other', message: 'Messaggio' });
    const controller = setupContactForm(f.form, async () => ({ ok: false, status: statusCode }), f.FakeFormData);
    await controller.handleSubmit(f.submitEvent);
    assert.equal(f.status.textContent, f.copy[key]);
    assert.equal(f.form.wasReset, undefined);
    assert.equal(f.button.disabled, false);
  });
}

test('network error and a filled honeypot never show success', async () => {
  const f = fixture('en', { name: 'Ana', email: 'ana@example.com', reason: 'other', message: 'Hello' });
  let calls = 0;
  const controller = setupContactForm(f.form, async () => { calls += 1; throw new Error('offline'); }, f.FakeFormData);
  await controller.handleSubmit(f.submitEvent);
  assert.equal(f.status.textContent, f.copy.form_error_network);
  assert.equal(f.form.wasReset, undefined);
  f.fields._gotcha.value = 'bot';
  await controller.handleSubmit({ preventDefault() {} });
  assert.equal(calls, 1);
  assert.equal(f.status.textContent, f.copy.form_error_honeypot);
});

for (const lang of ['it', 'en', 'fr']) {
  test(`${lang}: generated HTML has POST, exact endpoint, named fields and one mailto link`, () => {
    const html = fs.readFileSync(path.join(root, 'public', lang, 'contact', 'index.html'), 'utf8');
    const formTag = html.match(/<form\b[^>]*id="contactForm"[^>]*>/s)?.[0];
    assert.ok(formTag);
    assert.match(formTag, /method="POST"/);
    assert.match(formTag, /action="https:\/\/formspree\.io\/f\/xgaappab"/);
    const email = 'samuel.okotako.work@gmail.com';
    assert.equal((html.match(/href="mailto:[^"]+"/g) || []).length, 1);
    assert.ok(html.includes(`<a class="contact-email" href="mailto:${email}">${email}</a>`));
    for (const name of [...names, '_gotcha']) assert.match(html, new RegExp(`name="${name}"`));
  });
}

test('unsupported Fetch or FormData leaves native POST and HTML validation intact', () => {
  const f = fixture('en', { name: 'Ana', email: 'ana@example.com', reason: 'other', message: 'Hello' });
  assert.equal(setupContactForm(f.form, undefined, f.FakeFormData), null);
  assert.equal(f.form.noValidate, false);
  assert.equal(f.listeners.submit, undefined);
  assert.equal(setupContactForm(f.form, async () => ({}), undefined), null);
  assert.equal(f.form.noValidate, false);
});

test('FormData construction failure does not cancel the native POST', async () => {
  const f = fixture('en', { name: 'Ana', email: 'ana@example.com', reason: 'other', message: 'Hello' });
  let calls = 0;
  class BrokenFormData { constructor() { throw new Error('FormData unavailable'); } }
  const controller = setupContactForm(f.form, async () => { calls += 1; }, BrokenFormData);
  await controller.handleSubmit(f.submitEvent);
  assert.equal(f.submitEvent.prevented, false);
  assert.equal(f.form.noValidate, false);
  assert.equal(calls, 0);
  assert.equal(f.status.textContent, '');
});


test('browser-restored honeypot value is cleared on initialization', () => {
  const f = fixture('it', { _gotcha: 'autofilled' });
  setupContactForm(f.form, async () => ({ ok: true, status: 200 }), f.FakeFormData);
  assert.equal(f.fields._gotcha.value, '');
});


test('native invalid event shows localized email error without an AJAX request', () => {
  const f = fixture('it', { email: 'wrong' });
  let calls = 0;
  setupContactForm(f.form, async () => { calls += 1; }, f.FakeFormData);
  f.fields.email.checkValidity();
  f.listeners.invalid({ target: f.fields.email });
  assert.equal(f.errors.email.textContent, f.copy.form_error_email);
  assert.equal(f.status.textContent, f.copy.form_error_validation);
  assert.equal(f.form.noValidate, false);
  assert.equal(calls, 0);
});

test('redirected HTTP 200 is not shown as successful submission', async () => {
  const f = fixture('en', { name: 'Ana', email: 'ana@example.com', reason: 'other', message: 'Hello' });
  const controller = setupContactForm(f.form, async () => ({ ok: true, status: 200, redirected: true }), f.FakeFormData);
  await controller.handleSubmit(f.submitEvent);
  assert.equal(f.status.textContent, f.copy.form_error_http);
  assert.equal(f.form.wasReset, undefined);
});
