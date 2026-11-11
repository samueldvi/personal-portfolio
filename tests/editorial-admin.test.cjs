// Browser-controller tests with a synthetic REST/Auth/Storage fixture.
// They do not establish that Supabase RLS or Storage policies work in a live project.
const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');

const source = fs.readFileSync(path.join(__dirname, '..', 'editorial', 'admin', 'admin.js'), 'utf8');

function fixture({adminAllowed = true, uploadStatus = 200, malformedArticles = false} = {}) {
  let nextId = 1;
  const id = () => `fixture-${nextId++}`;
  const db = {articles: [], translations: [], categories: [], tags: [], links: [], revisions: [], social: [], media: [], uploads: []};
  const calls = [];
  function element(initial = {}) {
    const listeners = {};
    return {
      value: '', hidden: false, disabled: false, textContent: '', ...initial, listeners,
      addEventListener(name, callback) { listeners[name] = callback; }
    };
  }
  const names = ['slug', 'category', 'tags', 'language', 'title', 'summary', 'body', 'seo_title', 'seo_description', 'linkedin', 'cover'];
  const fields = Object.fromEntries(names.map(name => [name, element()]));
  fields.language.value = 'en';
  let coverValue = '';
  fields.cover.files = [];
  Object.defineProperty(fields.cover, 'value', {
    get() { return coverValue; },
    set(value) { coverValue = value; if (!value) this.files = []; }
  });
  const form = element({elements: fields, reportValidity() { return true; }});
  const login = element({elements: {email: element({value: 'editor@example.test'}), password: element({value: 'synthetic-password'})}});
  const articleList = element({options: [], replaceChildren(option) { this.options = [option]; this.value = option.value; }, add(option) { this.options.push(option); }});
  const els = {
    articleForm: form, loginForm: login, articleList, status: element(),
    loginPanel: element({hidden: true}), editorPanel: element({hidden: true}),
    logout: element(), publish: element(), withdraw: element(), preview: element(),
    previewTitle: element(), previewSummary: element(), previewBody: element(),
    previewPanel: element({hidden: true, scrollIntoView() {}})
  };
  const buttons = [els.logout, els.publish, els.withdraw, els.preview, element(), element()];
  const document = {
    getElementById(name) { return els[name]; },
    querySelectorAll(selector) { assert.equal(selector, 'button'); return buttons; }
  };
  const response = (body, status = 200) => ({ok: status >= 200 && status < 300, status, async json() { return body; }});
  const body = (options) => options.body ? JSON.parse(options.body) : null;
  const join = (article) => ({
    ...article,
    editorial_categories: db.categories.find(row => row.id === article.category_id) || null,
    editorial_article_tags: db.links.filter(row => row.article_id === article.id).map(row => ({editorial_tags: db.tags.find(tag => tag.id === row.tag_id)})),
    editorial_translations: db.translations.filter(row => row.article_id === article.id).map(row => ({...row, editorial_social_drafts: db.social.filter(social => social.translation_id === row.id)}))
  });
  async function fetch(url, options = {}) {
    calls.push({url, options});
    if (url === './config.json') return response({supabase_url: 'https://fixture.supabase.co', supabase_publishable_key: 'sb_publishable_fixture'});
    const parsed = new URL(url);
    const route = parsed.pathname;
    const method = options.method || 'GET';
    if (route === '/auth/v1/token') return response({access_token: 'synthetic-user-jwt'});
    if (route === '/auth/v1/user') return response({id: 'synthetic-admin-id'});
    if (route === '/rest/v1/rpc/editorial_can_manage') return response(adminAllowed);
    if (route.startsWith('/storage/v1/object/editorial-private/')) {
      db.uploads.push({url, options});
      if (uploadStatus !== 200) return response({message: 'Storage unavailable'}, uploadStatus);
      return response({Key: route});
    }
    if (!route.startsWith('/rest/v1/')) return response({message: 'Unknown route'}, 404);
    const table = route.slice('/rest/v1/'.length);
    const payload = method === 'POST' || method === 'PATCH' ? body(options) : null;
    if (table === 'editorial_articles') {
      if (method === 'GET') return response(malformedArticles ? {unexpected: true} : db.articles.map(join));
      if (method === 'POST') { const row = {id: id(), ...payload}; db.articles.push(row); return response([row], 201); }
      if (method === 'PATCH') { const row = db.articles.find(article => article.id === parsed.searchParams.get('id').slice(3)); Object.assign(row, payload); return response([row]); }
    }
    if (table === 'editorial_categories' || table === 'editorial_tags') {
      const rows = table === 'editorial_categories' ? db.categories : db.tags;
      if (method === 'GET') return response(rows.filter(row => row.slug === parsed.searchParams.get('slug').slice(3)));
      if (method === 'POST') { const row = {id: id(), ...payload}; rows.push(row); return response([row], 201); }
    }
    if (table === 'editorial_article_tags') {
      const articleId = parsed.searchParams.get('article_id')?.slice(3);
      if (method === 'GET') return response(db.links.filter(row => row.article_id === articleId));
      if (method === 'POST') { if (db.links.some(row => row.article_id === payload.article_id && row.tag_id === payload.tag_id)) return response({message: 'duplicate key'}, 409); db.links.push(payload); return response([payload], 201); }
      if (method === 'DELETE') { const tagId = parsed.searchParams.get('tag_id')?.slice(3); db.links = db.links.filter(row => row.article_id !== articleId || row.tag_id !== tagId); return response(null, 204); }
    }
    if (table === 'editorial_translations') {
      if (method === 'POST') {
        let row = db.translations.find(item => item.article_id === payload.article_id && item.language === payload.language);
        if (!row) { row = {id: id(), ...payload}; db.translations.push(row); }
        else Object.assign(row, payload);
        return response([row], 201);
      }
      if (method === 'PATCH') {
        const row = db.translations.find(item => item.id === parsed.searchParams.get('id').slice(3));
        if (payload.status === 'published' && row.cover_media_id && db.media.find(media => media.id === row.cover_media_id)?.rights_status !== 'approved') return response({message: 'Cover media rights must be approved before publication'}, 400);
        Object.assign(row, payload);
        return response([row]);
      }
    }
    if (table === 'editorial_revisions') {
      if (method === 'GET') return response(db.revisions.filter(row => row.translation_id === parsed.searchParams.get('translation_id').slice(3)).sort((a, b) => b.revision_number - a.revision_number).slice(0, 1));
      if (method === 'POST') { db.revisions.push(payload); return response([payload], 201); }
    }
    if (table === 'editorial_social_drafts' && method === 'POST') {
      let row = db.social.find(item => item.translation_id === payload.translation_id && item.platform === payload.platform);
      if (!row) { row = {id: id(), ...payload}; db.social.push(row); } else Object.assign(row, payload);
      return response([row], 201);
    }
    if (table === 'editorial_media' && method === 'POST') { const row = {id: id(), ...payload}; db.media.push(row); return response([row], 201); }
    return response({message: `Unmocked ${method} ${table}`}, 501);
  }
  const context = {document, window: {createImageBitmap: async () => ({width: 640, height: 480, close() {}})}, createImageBitmap: async () => ({width: 640, height: 480, close() {}}), fetch, URL, Option: class { constructor(text, value) { this.text = text; this.value = value; } }, crypto: {randomUUID: () => 'synthetic-uuid'}, console};
  vm.runInNewContext(source, context, {filename: 'editorial/admin/admin.js'});
  async function until(predicate) {
    for (let attempt = 0; attempt < 200; attempt += 1) {
      if (predicate()) return;
      await new Promise(resolve => setImmediate(resolve));
    }
    throw new Error(`Timed out waiting for admin UI: ${els.status.textContent}`);
  }
  const event = () => ({prevented: false, preventDefault() { this.prevented = true; }});
  async function signIn() {
    await until(() => !els.loginPanel.hidden);
    const submitted = event();
    els.loginForm.listeners.submit(submitted);
    await until(() => els.status.textContent.includes('Signed in.') || els.status.textContent.includes('not authorized') || els.status.textContent.includes('invalid response'));
    assert.equal(submitted.prevented, true);
  }
  async function save() {
    const submitted = event();
    els.status.textContent = '';
    els.articleForm.listeners.submit(submitted);
    await until(() => els.status.textContent.includes('Draft saved') || els.status.textContent.includes('Request failed') || els.status.textContent.includes('Withdraw all') || els.status.textContent.includes('Choose a'));
    assert.equal(submitted.prevented, true);
  }
  return {db, calls, els, fields, until, signIn, save};
}

test('mocked non-admin sign-in leaves editor hidden and makes no write request', async () => {
  const f = fixture({adminAllowed: false});
  await f.signIn();
  assert.equal(f.els.editorPanel.hidden, true);
  assert.equal(f.els.loginPanel.hidden, false);
  assert.equal(f.db.articles.length, 0);
  assert.equal(f.calls.filter(call => ['POST', 'PATCH', 'DELETE'].includes(call.options.method) && !call.url.includes('/auth/v1/token') && !call.url.includes('/rpc/')).length, 0);
});

test('empty project is identified and malformed article responses do not open the editor', async () => {
  const empty = fixture();
  await empty.signIn();
  assert.match(empty.els.status.textContent, /No articles in this project yet/);
  assert.equal(empty.els.articleList.options.length, 1);
  const malformed = fixture({malformedArticles: true});
  await malformed.signIn();
  assert.match(malformed.els.status.textContent, /invalid response/);
  assert.equal(malformed.els.editorPanel.hidden, true);
});

test('mocked admin can save, preview and publish English without publishing Italian', async () => {
  const f = fixture();
  await f.signIn();
  f.fields.slug.value = 'synthetic-data-pipeline';
  f.fields.category.value = 'Data Engineering';
  f.fields.tags.value = 'Python, python, SQL';
  f.fields.title.value = 'Synthetic pipeline';
  f.fields.summary.value = 'A synthetic test summary';
  f.fields.body.value = '# Data flow\n<script>not executed</script>';
  f.fields.linkedin.value = 'A synthetic LinkedIn draft';
  await f.save();
  assert.equal(f.els.status.textContent, 'Draft saved. It is not published on the website.');
  assert.equal(f.db.articles.length, 1);
  assert.equal(f.db.translations.length, 1);
  assert.equal(f.db.revisions.length, 1);
  assert.equal(f.db.links.length, 2);
  assert.equal(f.db.social[0].copy, 'A synthetic LinkedIn draft');
  f.fields.linkedin.value = '';
  await f.save();
  assert.equal(f.db.social[0].copy, '');
  f.els.preview.listeners.click();
  assert.equal(f.els.previewBody.textContent, f.fields.body.value);
  assert.equal(f.els.previewPanel.hidden, false);
  f.els.publish.listeners.click();
  await f.until(() => f.els.status.textContent.startsWith('Database status updated: publish.'));
  assert.equal(f.db.translations[0].status, 'published');
  assert.equal(f.db.translations.filter(row => row.language === 'it').length, 0);
  assert.equal(f.fields.category.disabled, true);
  f.fields.language.value = 'it';
  f.fields.language.listeners.change();
  assert.equal(f.fields.title.value, '');
  assert.equal(f.fields.category.disabled, true);
  f.fields.category.value = 'Different category';
  f.fields.title.value = 'Solo bozza';
  f.fields.summary.value = 'Test sintetico';
  f.fields.body.value = 'Contenuto sintetico';
  await f.save();
  assert.match(f.els.status.textContent, /Withdraw all published languages/);
  assert.equal(f.db.translations.length, 1);
  f.fields.category.value = 'Data Engineering';
  await f.save();
  assert.equal(f.db.translations.find(row => row.language === 'it').status, 'draft');
  assert.equal(f.db.translations.find(row => row.language === 'en').status, 'published');
  f.fields.language.value = 'en';
  f.fields.language.listeners.change();
  f.els.withdraw.listeners.click();
  await f.until(() => f.els.status.textContent.startsWith('Database status updated: withdraw.'));
  assert.equal(f.db.translations.find(row => row.language === 'en').status, 'withdrawn');
});

test('mocked private upload stays pending and publication is rejected', async () => {
  const f = fixture();
  await f.signIn();
  f.fields.slug.value = 'synthetic-cover';
  f.fields.title.value = 'Synthetic cover';
  f.fields.summary.value = 'Test summary';
  f.fields.body.value = 'Test body';
  f.fields.cover.files = [{name: 'synthetic.webp', type: 'image/webp', size: 1234}];
  await f.save();
  assert.equal(f.db.uploads.length, 1);
  assert.equal(f.db.media[0].rights_status, 'pending');
  assert.equal(f.db.media[0].visibility, 'private');
  assert.ok(f.db.translations[0].cover_media_id);
  f.els.publish.listeners.click();
  await f.until(() => f.els.status.textContent.includes('Cover media rights must be approved'));
  assert.equal(f.db.translations[0].status, 'draft');
});

test('invalid cover is rejected before creating an article or uploading media', async () => {
  const f = fixture();
  await f.signIn();
  f.fields.slug.value = 'invalid-cover';
  f.fields.title.value = 'Invalid cover';
  f.fields.summary.value = 'Test summary';
  f.fields.body.value = 'Test body';
  f.fields.cover.files = [{name: 'untrusted.svg', type: 'image/svg+xml', size: 1234}];
  await f.save();
  assert.match(f.els.status.textContent, /Choose a JPEG/);
  assert.equal(f.db.articles.length, 0);
  assert.equal(f.db.uploads.length, 0);
});

test('storage failure reports that the synthetic draft was saved and keeps it selected', async () => {
  const f = fixture({uploadStatus: 503});
  await f.signIn();
  f.fields.slug.value = 'synthetic-storage-failure';
  f.fields.title.value = 'Storage failure';
  f.fields.summary.value = 'Test summary';
  f.fields.body.value = 'Test body';
  f.fields.cover.files = [{name: 'synthetic.webp', type: 'image/webp', size: 1234}];
  await f.save();
  assert.match(f.els.status.textContent, /Draft saved, but cover upload failed/);
  assert.equal(f.db.articles.length, 1);
  assert.equal(f.db.translations.length, 1);
  assert.equal(f.db.media.length, 0);
  assert.equal(f.els.articleList.value, f.db.articles[0].id);
});
