# Samuel Okotako — portfolio personale

Sito personale di Samuel Okotako. Presenta progetti documentati di Data Engineering, Data Management e Data Governance, esperienza e formazione, e un percorso creativo distinto. Machine Learning è descritto come area di formazione; i progetti non verificati restano fuori dal sito.

**Sito pubblico:** [samuelokotako.com](https://samuelokotako.com)

## Tecnologie e funzionalità

Python (sola libreria standard) genera HTML statico da template condivisi, registri `content/` e dizionari IT/EN/FR. L'interfaccia usa CSS e JavaScript vanilla, font locali e immagini responsive. Cloudflare Pages pubblica la cartella `public/`; Formspree gestisce il modulo di contatto.

- Pagine e case study completi in italiano, inglese e francese, con selezione manuale della lingua.
- Tema Auto/Light/Dark, navigazione accessibile, pagina 404 localizzata e layout responsive.
- Tre CV Data Engineer approvati, uno per lingua, disponibili sotto `/cv/`.
- Canonical, hreflang, sitemap e Open Graph in produzione; preview e build locali `noindex`.
- Scritti, galleria, Life & Moments e iniziative sono predisposti nei registri e appaiono nella navigazione solo quando esistono contenuti pubblicabili.

## Architettura

| Percorso | Funzione |
| --- | --- |
| `build_pages.py`, `site_content.py`, `site_config.py` | Template, validazione delle traduzioni e modalità SEO |
| `translations/it.json`, `en.json`, `fr.json` | Copy localizzato e case study |
| `content/` | Registri di progetti, media, documenti e contenuti editoriali; [convenzioni](content/README.md) |
| `style.css`, `script.js`, `contact-form.js` | Design system, interazioni e invio del modulo |
| `assets/` | Font, immagini e tre PDF approvati |
| `public/` | Output generato e distribuito; non modificare manualmente |
| `docs/RELEASE.md` | [Controlli di rilascio e produzione](docs/RELEASE.md) |

Gli stessi componenti producono `/it/`, `/en/` e `/fr/`, inclusi `/about/`, `/projects/`, `/experience/`, `/contact/` e tre case study per lingua. `content/projects.json` contiene anche bozze escluse dall'output. Il PoC di Data Governance usa dati sintetici ed è separato dal tirocinio Spindox. Le evidenze e le lacune dei progetti sono annotate in [content/CASE_STUDY_AUDIT.md](content/CASE_STUDY_AUDIT.md).

## Avvio locale

```sh
python3 -B build_pages.py
python3 -B check_site.py
python3 -m http.server 8000 --directory public
```

Apri `http://localhost:8000/`. La pagina iniziale propone la lingua salvata o quella del browser senza forzare un redirect. Modifica dizionari, registri o template sorgente e rigenera `public/`; non editare le pagine generate.

## Test automatici

```sh
python3 -B build_pages.py
python3 -B check_site.py
python3 -B tools/test_build_modes.py
python3 -B tools/check_public_safety.py
python3 -B tools/test_public_safety.py
node --test tests/*.test.cjs
git diff --check
```

La CI su pull request verso `main` ripete build e test, controlla il drift dell'output e scansiona la cronologia con Gitleaks. Non esegue il deploy. Il controllo automatico non sostituisce la revisione di contenuti, diritti e accessibilità. La procedura completa è in [docs/RELEASE.md](docs/RELEASE.md).

## Pubblicazione e SEO

Il dominio canonico è `https://samuelokotako.com`. La produzione Cloudflare Pages usa `main` e distribuisce solo `public/`. `site_config.py` abilita canonical, hreflang, sitemap e indicizzazione soltanto con `SITE_URL` canonico, `CF_PAGES=1` e `CF_PAGES_BRANCH=main`; build locali e preview restano `noindex`. `_redirects` contiene due regole 301 esatte dai vecchi URL `/assets/cv/` ai PDF sotto `/cv/`. Le 404 localizzate non usano rewrite catch-all. Configurazione, verifiche HTTP e passaggi di rilascio sono in [docs/RELEASE.md](docs/RELEASE.md).

## Contenuti, privacy e limiti

Il repository GitHub è pubblico e deve contenere solo codice, documentazione e materiali intenzionalmente pubblicabili. File riservati e report di sicurezza dettagliati restano fuori da Git; `noindex` e `.gitignore` non rendono sicuro un file già tracciato.

Per aggiungere progetti, articoli, media e traduzioni segui [content/README.md](content/README.md). Il generatore copia nell'output soltanto gli asset referenziati da contenuti pubblicati. Le immagini del ritratto e del teatro hanno autorizzazione e credito dell'autore; foto di gruppo o aziendali restano escluse senza consenso. I font Newsreader e Manrope sono distribuiti localmente con licenza SIL OFL 1.1 in `assets/fonts/`.

Il form usa POST verso Formspree con `FormData`, validazione e honeypot; senza JavaScript mantiene l'invio HTML. I test verificano il comportamento del codice, **non** la consegna delle email. Restano da controllare con un solo invio reale dashboard, destinazione, protezione antispam e recapito. Il contenuto dei messaggi non viene salvato dal sito in `localStorage` o analytics. Le istruzioni operative sono in [docs/RELEASE.md](docs/RELEASE.md).

Restano in bozza Bank Loan Approval Prediction e il dettaglio del radar Arduino finché le prove richieste non sono disponibili. Il case study NoSQL descrive i notebook esportati e il contributo personale dichiarato, ma non presenta come verificati esecuzioni, dashboard finale o risultati quantitativi. I link ai repository dei case study non sono pubblicati finché non è conclusa la verifica della pubblicabilità. I PDF hanno link HTML accessibili; la mancanza di tag strutturali nei PDF è un limite del documento.
