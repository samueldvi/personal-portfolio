(() => {
  const input = document.getElementById('writingSearch');
  const status = document.getElementById('writingSearchStatus');
  if (!input || !status) return;
  const cards = [...document.querySelectorAll('[data-article-card]')];
  const script = document.currentScript;
  const noResults = script?.dataset.noResults || '';
  const resultsLabel = script?.dataset.results || '';
  input.addEventListener('input', () => {
    const query = input.value.trim().toLocaleLowerCase();
    let visible = 0;
    for (const card of cards) {
      const match = (card.dataset.search || '').toLocaleLowerCase().includes(query);
      card.hidden = !match;
      if (match) visible += 1;
    }
    status.textContent = visible ? `${visible} ${resultsLabel}` : noResults;
  });
})();
