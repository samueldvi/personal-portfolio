(() => {
  'use strict';
  const $ = (id) => document.getElementById(id);
  const form = $('articleForm');
  const login = $('loginForm');
  const status = $('status');
  const fields = form.elements;
  const state = {config: null, token: null, articles: [], articleId: null, translation: null};
  let busy = false;
  const say = (message) => { status.textContent = message; };
  const slugify = (value) => value.trim().toLowerCase().normalize('NFKD').replace(/[\u0300-\u036f]/g, '').replace(/[^a-z0-9]+/g, '-').replace(/^-|-$/g, '');
  const endpoint = (path) => new URL(path, state.config.url + '/').toString();

  async function request(path, options = {}) {
    const headers = {'apikey': state.config.key, 'authorization': `Bearer ${state.token}`, 'accept': 'application/json', ...options.headers};
    const response = await fetch(endpoint(path), {...options, headers});
    if (!response.ok) {
      let detail = '';
      try { detail = (await response.json()).message || ''; } catch (_) { /* no JSON body */ }
      throw new Error(`Request failed (${response.status})${detail ? ': ' + detail : ''}`);
    }
    if (response.status === 204) return null;
    return response.json();
  }
  const rest = (path, options) => request('rest/v1/' + path, options);
  const jsonHeaders = {'content-type': 'application/json', 'prefer': 'return=representation'};

  async function refresh() {
    const articles = await rest('editorial_articles?select=id,slug,category_id,editorial_categories(label),editorial_article_tags(editorial_tags(label)),editorial_translations(id,language,title,summary,body_markdown,seo_title,seo_description,status,published_at,cover_media_id,editorial_social_drafts(platform,copy))&order=created_at.desc');
    state.articles = Array.isArray(articles) ? articles : [];
    const select = $('articleList');
    select.replaceChildren(new Option('New article', ''));
    for (const article of state.articles) select.add(new Option(article.slug, article.id));
  }

  function loadSelected() {
    const article = state.articles.find((row) => row.id === $('articleList').value);
    state.articleId = article?.id || null;
    fields.slug.value = article?.slug || '';
    fields.slug.readOnly = Boolean(article);
    fields.category.value = article?.editorial_categories?.label || '';
    fields.tags.value = article?.editorial_article_tags?.map((row) => row.editorial_tags?.label).filter(Boolean).join(', ') || '';
    showTranslation();
  }
  function showTranslation() {
    const article = state.articles.find((row) => row.id === state.articleId);
    const sharedLocked = Boolean(article?.editorial_translations?.some((row) => row.status === 'published'));
    fields.category.disabled = sharedLocked;
    fields.tags.disabled = sharedLocked;
    const translation = article?.editorial_translations?.find((row) => row.language === fields.language.value);
    state.translation = translation || null;
    for (const key of ['title', 'summary', 'body_markdown', 'seo_title', 'seo_description']) {
      fields[key === 'body_markdown' ? 'body' : key].value = translation?.[key] || '';
    }
    fields.linkedin.value = translation?.editorial_social_drafts?.find((row) => row.platform === 'linkedin')?.copy || '';
    fields.cover.value = '';
    say(translation ? `${fields.language.value.toUpperCase()} — ${translation.status}` : 'New language draft.');
  }

  async function ensureCategory(label) {
    if (!label.trim()) return null;
    const slug = slugify(label);
    if (!slug) throw new Error('Category needs letters or digits.');
    const rows = await rest(`editorial_categories?slug=eq.${encodeURIComponent(slug)}&select=id`);
    if (rows.length) return rows[0].id;
    const created = await rest('editorial_categories', {method: 'POST', headers: jsonHeaders, body: JSON.stringify({slug, label: label.trim()})});
    return created[0].id;
  }
  async function saveTags(articleId, input) {
    const labels = input.split(',').map((value) => value.trim()).filter(Boolean);
    const desired = [];
    const seenSlugs = new Set();
    for (const label of labels) {
      const slug = slugify(label);
      if (!slug) throw new Error('Every tag needs letters or digits.');
      if (seenSlugs.has(slug)) continue;
      seenSlugs.add(slug);
      let rows = await rest(`editorial_tags?slug=eq.${encodeURIComponent(slug)}&select=id`);
      if (!rows.length) rows = await rest('editorial_tags', {method: 'POST', headers: jsonHeaders, body: JSON.stringify({slug, label})});
      desired.push(rows[0].id);
    }
    const existing = await rest(`editorial_article_tags?article_id=eq.${articleId}&select=tag_id`);
    for (const row of existing) {
      if (!desired.includes(row.tag_id)) await rest(`editorial_article_tags?article_id=eq.${articleId}&tag_id=eq.${row.tag_id}`, {method: 'DELETE'});
    }
    for (const tag_id of desired) {
      if (!existing.some((row) => row.tag_id === tag_id)) await rest('editorial_article_tags', {method: 'POST', headers: jsonHeaders, body: JSON.stringify({article_id: articleId, tag_id})});
    }
  }
  async function saveDraft() {
    if (!form.reportValidity()) return null;
    if (state.translation?.status === 'published') throw new Error('Withdraw this language before editing its published version.');
    const cover = fields.cover.files[0];
    const coverDimensions = cover ? await inspectCover(cover) : null;
    const slug = fields.slug.value.trim();
    if (!/^[a-z0-9]+(-[a-z0-9]+)*$/.test(slug)) throw new Error('Use a lowercase URL slug.');
    const article = state.articles.find((row) => row.id === state.articleId);
    const sharedLocked = Boolean(article?.editorial_translations?.some((row) => row.status === 'published'));
    if (sharedLocked) {
      const currentTags = article.editorial_article_tags.map((row) => row.editorial_tags?.label).filter(Boolean).sort().join(', ');
      const editedTags = fields.tags.value.split(',').map((value) => value.trim()).filter(Boolean).sort().join(', ');
      if (fields.category.value.trim() !== (article.editorial_categories?.label || '') || editedTags !== currentTags) {
        throw new Error('Withdraw all published languages before changing the category or tags.');
      }
    }
    const category_id = sharedLocked ? article.category_id : await ensureCategory(fields.category.value);
    if (!state.articleId) {
      const created = await rest('editorial_articles', {method: 'POST', headers: jsonHeaders, body: JSON.stringify({slug, category_id})});
      state.articleId = created[0].id;
    } else if (!sharedLocked) {
      await rest(`editorial_articles?id=eq.${state.articleId}`, {method: 'PATCH', headers: jsonHeaders, body: JSON.stringify({category_id})});
    }
    if (!sharedLocked) await saveTags(state.articleId, fields.tags.value);
    const hadLinkedIn = Boolean(state.translation?.editorial_social_drafts?.some((row) => row.platform === 'linkedin'));
    const data = {article_id: state.articleId, language: fields.language.value, title: fields.title.value.trim(), summary: fields.summary.value.trim(), body_markdown: fields.body.value, seo_title: fields.seo_title.value.trim() || null, seo_description: fields.seo_description.value.trim() || null, status: 'draft'};
    const rows = await rest('editorial_translations?on_conflict=article_id,language', {method: 'POST', headers: {...jsonHeaders, 'prefer': 'resolution=merge-duplicates,return=representation'}, body: JSON.stringify(data)});
    state.translation = rows[0];
    const revisions = await rest(`editorial_revisions?translation_id=eq.${state.translation.id}&select=revision_number&order=revision_number.desc&limit=1`);
    await rest('editorial_revisions', {method: 'POST', headers: jsonHeaders, body: JSON.stringify({translation_id: state.translation.id, revision_number: (revisions[0]?.revision_number || 0) + 1, snapshot: data, editor_id: state.userId})});
    if (fields.linkedin.value.trim() || hadLinkedIn) await rest('editorial_social_drafts?on_conflict=translation_id,platform', {method: 'POST', headers: {...jsonHeaders, 'prefer': 'resolution=merge-duplicates,return=representation'}, body: JSON.stringify({translation_id: state.translation.id, platform: 'linkedin', copy: fields.linkedin.value.trim()})});
    let coverError = null;
    if (cover) {
      try { await uploadPrivateCover(cover, coverDimensions); }
      catch (error) { coverError = error; }
    }
    await refresh();
    $('articleList').value = state.articleId;
    loadSelected();
    if (coverError) throw new Error(`Draft saved, but cover upload failed: ${coverError.message || 'try again.'}`);
    say('Draft saved. It is not published on the website.');
    return state.translation;
  }
  async function inspectCover(file) {
    if (!['image/jpeg', 'image/png', 'image/webp', 'image/avif'].includes(file.type) || file.size > 5 * 1024 * 1024) throw new Error('Choose a JPEG, PNG, WebP or AVIF image under 5 MB.');
    if (!('createImageBitmap' in window)) throw new Error('This browser cannot inspect image dimensions.');
    const bitmap = await createImageBitmap(file);
    const width = bitmap.width, height = bitmap.height;
    bitmap.close();
    if (width < 1 || height < 1) throw new Error('Choose an image with valid dimensions.');
    return {width, height};
  }
  async function uploadPrivateCover(file, {width, height}) {
    if (!state.translation) throw new Error('Save a draft before uploading a cover.');
    const key = `${crypto.randomUUID()}-${file.name.replace(/[^a-zA-Z0-9.-]/g, '_')}`;
    await request(`storage/v1/object/editorial-private/${encodeURIComponent(key)}`, {method: 'POST', headers: {'content-type': file.type, 'x-upsert': 'false'}, body: file});
    const rows = await rest('editorial_media', {method: 'POST', headers: jsonHeaders, body: JSON.stringify({storage_key: key, mime_type: file.type, width, height, rights_status: 'pending', visibility: 'private'})});
    await rest(`editorial_translations?id=eq.${state.translation.id}`, {method: 'PATCH', headers: jsonHeaders, body: JSON.stringify({cover_media_id: rows[0].id})});
    say('Cover uploaded to private storage. Rights review is still required.');
  }
  async function changeStatus(action) {
    if (action === 'publish' && state.translation?.status !== 'published' && !await saveDraft()) return;
    if (!state.articleId || !state.translation) throw new Error('Save this language as a draft first.');
    if (action === 'publish' && state.translation.status === 'published') throw new Error('This language is already published. Withdraw it before editing.');
    if (action === 'publish' && (!fields.title.value.trim() || !fields.summary.value.trim() || !fields.body.value.trim())) throw new Error('Title, summary and body are required to publish.');
    const update = action === 'publish' ? {status: 'published', published_at: new Date().toISOString()} : {status: 'withdrawn'};
    await rest(`editorial_translations?id=eq.${state.translation.id}`, {method: 'PATCH', headers: jsonHeaders, body: JSON.stringify(update)});
    await refresh();
    $('articleList').value = state.articleId;
    loadSelected();
    say(`Database status updated: ${action}. The public static site changes only after a reviewed export and build.`);
  }
  async function run(task) {
    if (busy) return;
    busy = true;
    for (const button of document.querySelectorAll('button')) button.disabled = true;
    try { await task(); } catch (error) { say(error.message || 'Operation failed.'); }
    finally { busy = false; for (const button of document.querySelectorAll('button')) button.disabled = false; }
  }

  login.addEventListener('submit', (event) => {
    event.preventDefault();
    run(async () => {
      const email = login.elements.email.value.trim();
      const password = login.elements.password.value;
      const response = await fetch(endpoint('auth/v1/token?grant_type=password'), {method: 'POST', headers: {'apikey': state.config.key, 'content-type': 'application/json'}, body: JSON.stringify({email, password})});
      login.elements.password.value = '';
      if (!response.ok) throw new Error('Sign in failed.');
      const auth = await response.json();
      state.token = auth.access_token;
      const user = await request('auth/v1/user');
      state.userId = user.id;
      const allowed = await rest('rpc/editorial_can_manage', {method: 'POST', headers: {'content-type': 'application/json'}, body: '{}'});
      if (allowed !== true) { state.token = null; throw new Error('This account is not authorized for editorial access.'); }
      await refresh();
      $('loginPanel').hidden = true;
      $('editorPanel').hidden = false;
      say('Signed in. Drafts remain private until you publish and run a reviewed site build.');
    });
  });
  $('logout').addEventListener('click', () => { state.token = null; state.userId = null; state.articleId = null; state.translation = null; $('editorPanel').hidden = true; $('loginPanel').hidden = false; say('Signed out.'); });
  $('articleList').addEventListener('change', loadSelected);
  fields.language.addEventListener('change', showTranslation);
  form.addEventListener('submit', (event) => { event.preventDefault(); run(saveDraft); });
  $('publish').addEventListener('click', () => run(() => changeStatus('publish')));
  $('withdraw').addEventListener('click', () => run(() => changeStatus('withdraw')));
  $('preview').addEventListener('click', () => {
    $('previewTitle').textContent = fields.title.value;
    $('previewSummary').textContent = fields.summary.value;
    $('previewBody').textContent = fields.body.value;
    $('previewPanel').hidden = false;
    $('previewPanel').scrollIntoView({block: 'nearest'});
  });
  fetch('./config.json', {cache: 'no-store'}).then(async (response) => {
    if (!response.ok) throw new Error('Editorial configuration is not installed.');
    const config = await response.json();
    const url = new URL(config.supabase_url);
    if (url.protocol !== 'https:' || url.username || url.password || url.pathname !== '/' || url.search || url.hash || !config.supabase_publishable_key?.startsWith('sb_publishable_')) throw new Error('Editorial configuration needs an HTTPS origin and a publishable key.');
    state.config = {url: url.origin, key: config.supabase_publishable_key};
    $('loginPanel').hidden = false;
    say('Sign in with the authorized editorial account.');
  }).catch((error) => say(error.message));
})();
