const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');

const source = fs.readFileSync(path.join(__dirname, '..', 'writing-search.js'), 'utf8');

function setup(label, noResults) {
  let onInput;
  const input = {value: '', addEventListener(type, listener) {
    assert.equal(type, 'input');
    onInput = listener;
  }};
  const status = {textContent: ''};
  const cards = [
    {dataset: {search: 'Data Engineering · Python'}, hidden: false},
    {dataset: {search: 'Gouvernance des données · SQL'}, hidden: false},
  ];
  const document = {
    getElementById(id) { return {writingSearch: input, writingSearchStatus: status}[id]; },
    querySelectorAll(selector) {
      assert.equal(selector, '[data-article-card]');
      return cards;
    },
    currentScript: {dataset: {results: label, noResults}},
  };
  vm.runInNewContext(source, {document});
  return {input, status, cards, search(value) { input.value = value; onInput(); }};
}

test('writing search matches metadata without hiding unrelated results on clear', () => {
  const page = setup('results', 'No articles found');
  page.search('  PYTHON  ');
  assert.deepEqual(page.cards.map(card => card.hidden), [false, true]);
  assert.equal(page.status.textContent, '1 results');
  page.search('');
  assert.deepEqual(page.cards.map(card => card.hidden), [false, false]);
  assert.equal(page.status.textContent, '2 results');
});

test('writing search reports no matches with the localized label', () => {
  const page = setup('résultats', 'Aucun article trouvé');
  page.search('unmatched');
  assert.deepEqual(page.cards.map(card => card.hidden), [true, true]);
  assert.equal(page.status.textContent, 'Aucun article trouvé');
});
