# Rilascio del portfolio

Obiettivo del rilascio: `main` come branch di produzione Cloudflare Pages. Prima del passaggio la produzione risultava associata a `feature/portfolio-v2`; verificare il valore effettivo nella dashboard dopo il merge. Il cambio di branch Git non aggiorna automaticamente la configurazione Pages.

## Verifiche prima della pull request

```sh
python3 -B build_pages.py
python3 -B check_site.py
python3 -B tools/test_build_modes.py
python3 -B tools/check_public_safety.py
node --test tests/*.test.cjs
git diff --check
```

Confermare che `git status --short` mostri solo i file voluti. Riesaminare a mano media, documenti e contenuti nuovi: la scansione automatica rileva solo alcuni formati privati e credenziali riconoscibili. I due CV Data Engineer IT/EN sono gli unici PDF approvati nel registro e nell’output; non aggiungere le altre varianti, sorgenti LaTeX o report QA. Bank Loan Approval Prediction resta in bozza finché dataset, metodologia, metriche e rischi non sono documentati.

## CI e protezione di `main`

Il workflow `.github/workflows/portfolio-quality.yml` si attiva su pull request verso `main`, senza deploy. I job sono `Build, tests and publication checks` e `Gitleaks history scan`. Il primo rigenera `public/` in modalità produzione autorizzata per `main` e richiede che corrisponda ai file committati. Il secondo controlla la cronologia Git; su un account personale Gitleaks Action non richiede licenza separata, ma la prima esecuzione va comunque verificata. Dopo una prima esecuzione riuscita, configurare su GitHub una regola di protezione per `main` che richieda pull request, revisione e i due status check. Verificare che il nome dei check sia univoco prima di renderli obbligatori. Non configurare credenziali Cloudflare in questo workflow.

## Modalità SEO

| Modalità | Variabili rilevanti | Output |
| --- | --- | --- |
| Locale | Nessun opt-in | `noindex`, `Disallow: /`, senza canonical/hreflang/sitemap |
| Preview Pages | `CF_PAGES_BRANCH` diverso da `PORTFOLIO_PRODUCTION_BRANCH` | Come locale; verificare anche `X-Robots-Tag: noindex` della preview |
| Produzione autorizzata | `SITE_URL=https://samuelokotako.com`, `PORTFOLIO_INDEXING=enabled`, `CF_PAGES=1`, `CF_PAGES_BRANCH=PORTFOLIO_PRODUCTION_BRANCH` | Canonical, hreflang, sitemap e `Allow: /` |

Cloudflare inietta `CF_PAGES` e `CF_PAGES_BRANCH` durante il build Pages. Configurare `PORTFOLIO_PRODUCTION_BRANCH` con il branch **effettivamente** designato come produzione. Attualmente è `feature/portfolio-v2`; dopo il passaggio autorizzato a `main` aggiornare la variabile. `SITE_URL` da solo non abilita l'indicizzazione. Le tre modalità sono testate in directory temporanee da `tools/test_build_modes.py`.

Prima del rilascio SEO verificare nella dashboard Pages che il build command sia `python3 -B build_pages.py` e la output directory `public`. Se Pages pubblica solo i file `public/` già committati senza eseguire Python, le variabili d'ambiente non hanno alcun effetto sui meta tag. Applicare la configurazione solo dopo approvazione; quindi controllare l'HTML **servito** su `https://samuelokotako.com` e una preview, non solo l'output locale.

## Controlli sul dominio dopo un deployment autorizzato

- `curl -I https://samuelokotako.com/it/` e pagine campione: 200, canonical autoreferenziale, IT/EN/FR reciproci, Open Graph e Twitter card con immagine raggiungibile.
- `curl -I https://samuelokotako.com/robots.txt` e `sitemap.xml`: contenuti corretti e solo URL pubblicati. Sulla preview: header `X-Robots-Tag: noindex` e nessuna sitemap indicizzabile.
- URL inesistenti alla radice e sotto `/it/`, `/en/`, `/fr/`: HTTP 404 reale, contenuto localizzato e `noindex`. Controllare anche asset CSS/JS/font. Non usare redirect catch-all o rewrite 200.
- `https://www.samuelokotako.com/`: un redirect verso l'apice, senza loop, mantenendo il percorso. Verificare slash finali e URL senza slash.
- Test reale Formspree con un solo messaggio non sensibile, dopo autorizzazione, verificando la dashboard e la casella di destinazione. I test locali non provano la consegna.
- Lighthouse e Core Web Vitals sul dominio finale; misurare INP con dati di interazione adatti, non dedurlo da un test senza traffico reale.
- Controllare pagina, temi, lingua, menu, filtri, contrasto, tastiera, zoom 200% e 320–1440 px su dispositivi e browser reali.

Dopo il rilascio, documentare commit, pull request, merge, branch di produzione Pages e verifiche HTTP nel rapporto finale. Non segnare un controllo come superato senza una prova sul dominio.
