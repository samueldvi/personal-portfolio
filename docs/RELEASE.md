# Rilascio del portfolio

La produzione Cloudflare Pages del portfolio usa `main` e il dominio `https://samuelokotako.com`. Questa procedura si applica alle modifiche successive: una pull request verificata precede ogni merge e il deployment è un passaggio separato. Controllare sempre la configurazione Pages e l’HTML effettivamente servito; il branch Git da solo non aggiorna le impostazioni Cloudflare.

## Verifiche prima della pull request

```sh
python3 -B build_pages.py
python3 -B check_site.py
python3 -B tools/test_build_modes.py
python3 -B tools/check_public_safety.py
node --test tests/*.test.cjs
git diff --check
```

Confermare che `git status --short` mostri solo i file voluti. Riesaminare a mano media, documenti e contenuti nuovi: la scansione automatica rileva solo alcuni formati privati e credenziali riconoscibili. I tre CV Data Engineer IT/EN/FR provenienti da `cv/final/website-ready/` sono gli unici PDF approvati nel registro e nell’output, sotto `/cv/`; verificare le lingue, i checksum e i link localizzati prima del merge. Non aggiungere altre varianti, sorgenti LaTeX o report QA. Bank Loan Approval Prediction resta in bozza finché dataset, metodologia, metriche e rischi non sono documentati.

## CI e protezione di `main`

Il workflow `.github/workflows/portfolio-quality.yml` si attiva su pull request verso `main`, senza deploy. I job sono `Build, tests and publication checks` e `Gitleaks history scan`. Il primo rigenera `public/` in modalità produzione autorizzata per `main` e richiede che corrisponda ai file committati. Il secondo controlla la cronologia Git; verificarne sempre l’esito nella pull request. Configurare su GitHub una regola di protezione per `main` che richieda pull request, revisione e i due status check; la CI è già stata eseguita su pull request precedenti. Verificare che il nome dei check sia univoco prima di renderli obbligatori. Non configurare credenziali Cloudflare in questo workflow.

## Modalità SEO

| Modalità | Condizione | Output |
| --- | --- | --- |
| Locale | `CF_PAGES` assente | `noindex`, `Disallow: /`, senza canonical/hreflang/sitemap |
| Preview Pages | `CF_PAGES_BRANCH` diverso da `main` | Come locale; verificare anche `X-Robots-Tag: noindex` della preview |
| Produzione autorizzata | `SITE_URL=https://samuelokotako.com`, `CF_PAGES=1`, `CF_PAGES_BRANCH=main` | Canonical, hreflang, sitemap e `Allow: /` |

Cloudflare inietta `CF_PAGES` e `CF_PAGES_BRANCH` durante il build Pages. Il generatore approva esplicitamente `main` come unico branch indicizzabile; variabili legacy `PORTFOLIO_PRODUCTION_BRANCH` e `PORTFOLIO_INDEXING` non controllano più questa scelta. Un `SITE_URL` vuoto usa il dominio canonico noto; un URL temporaneo mantiene `noindex`. `SITE_URL` da solo non abilita l'indicizzazione. Le modalità sono testate in directory temporanee da `tools/test_build_modes.py`.

La configurazione Pages attuale usa `python3 build_pages.py && python3 check_site.py` come build command e `public` come output directory. Le variabili automatiche `CF_PAGES` e `CF_PAGES_BRANCH` distinguono produzione e preview. Dopo ogni modifica alla configurazione, verificare nella dashboard che questi valori siano ancora corretti; controllare l'HTML **servito** sul dominio e su una preview.

## Controlli sul dominio dopo un deployment autorizzato

- `curl -I https://samuelokotako.com/it/` e pagine campione: 200, canonical autoreferenziale, IT/EN/FR reciproci, Open Graph e Twitter card con immagine raggiungibile.
- `curl -I https://samuelokotako.com/robots.txt` e `sitemap.xml`: contenuti corretti e solo URL pubblicati. Sulla preview: header `X-Robots-Tag: noindex` e nessuna sitemap indicizzabile.
- URL inesistenti alla radice e sotto `/it/`, `/en/`, `/fr/`: HTTP 404 reale, contenuto localizzato e `noindex`. Controllare anche asset CSS/JS/font. Non usare redirect catch-all o rewrite 200.
- `https://www.samuelokotako.com/`: un redirect verso l'apice, senza loop, mantenendo il percorso. Verificare slash finali e URL senza slash.
- Test reale Formspree con un solo messaggio non sensibile, dopo autorizzazione, verificando la dashboard e la casella di destinazione. I test locali non provano la consegna.
- Lighthouse e Core Web Vitals sul dominio finale; misurare INP con dati di interazione adatti, non dedurlo da un test senza traffico reale.
- Controllare pagina, temi, lingua, menu, filtri, contrasto, tastiera, zoom 200% e 320–1440 px su dispositivi e browser reali.

Dopo il rilascio, documentare commit, pull request, merge, branch di produzione Pages e verifiche HTTP nel rapporto finale. Non segnare un controllo come superato senza una prova sul dominio.

## Modulo di contatto: verifica reale

L'endpoint HTML e Fetch è `https://formspree.io/f/xgaappab`; entrambi usano POST. Il controller invia `FormData` con `Accept: application/json`, mantiene la validazione HTML5, disabilita il pulsante durante l'invio e mostra il successo solo dopo una risposta HTTP positiva non reindirizzata. `_gotcha` è l'honeypot. Il sito non memorizza il messaggio nel browser né lo invia ad analytics.

Un test locale conferma la logica del form, non il recapito. Per una verifica reale, aprire `/it/contact/`, `/en/contact/` o `/fr/contact/` dal dominio o da un server locale e inviare **un solo** messaggio di prova non sensibile. Nelle DevTools, conservare il log di rete e annotare metodo, endpoint, stato HTTP, redirect ed eventuali errori Console, senza copiare il messaggio. Nel dashboard Formspree verificare che l'endpoint appartenga all'account corretto, la destinazione sia confermata, le impostazioni di restrizione dominio e antispam siano coerenti con il sito, e che il messaggio appaia. Controllare anche la casella di destinazione prima di dichiarare la consegna email. In caso di errore di rete o CORS, controllare il dashboard prima di ripetere l'invio: il browser potrebbe non poter leggere una risposta a un POST già accettato. Il link `mailto:` richiede un client di posta configurato sul dispositivo.
