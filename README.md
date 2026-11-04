# Samuel Okotako — sito personale

Sito statico in italiano, inglese e francese, pensato per crescere con progetti tecnici, scritti, media e nuove iniziative. HTML, CSS e JavaScript vanilla sono sufficienti per l'interfaccia attuale. Python (libreria standard) genera i file statici da template condivisi e dizionari IT/EN/FR separati; nessun CMS, database o framework frontend è richiesto.

## Struttura

| Percorso | Ruolo |
| --- | --- |
| `translations/it.json`, `en.json`, `fr.json` | Dizionari indipendenti per testi, etichette e contenuti editoriali |
| `site_content.py` | Caricamento e controllo di coerenza dei dizionari |
| `content/projects.json` | Progetti tecnici, stato dei case study e dati delle schede |
| `content/home_media.json` | Ritratto e fotografia personale autorizzati; slot per eventuali anteprime reali dei progetti |
| `content/its_modules.json` | 28 denominazioni e voti ITS verificati sul certificato ufficiale |
| `content/CASE_STUDY_AUDIT.md` | Inventario delle prove e delle lacune prima della pubblicazione |
| `content/articles.json` | Registro articoli, al momento vuoto |
| `content/galleries.json` | Registro lavori fotografici e media, al momento vuoto |
| `content/moments.json` | Momenti personali e culturali, separati dalla galleria creativa e al momento vuoti |
| `content/documents.json` | Registro dei tre CV Data Engineer approvati e degli eventuali documenti pubblici |
| `content/initiatives.json` | Registro separato di iniziative professionali e imprenditoriali, al momento vuoto |
| `content/README.md` | Convenzioni per aggiungere contenuti e gestire spostamenti |
| `tools/prepare_moment_image.py` | Preparazione locale di varianti WebP senza metadati |
| `build_pages.py` | Generatore e validazione dei contenuti pubblicati |
| `site_config.py` | Configurazione SEO con consenso esplicito all'indicizzazione |
| `style.css`, `script.js`, `contact-form.js` | Design system, interazioni condivise e invio del modulo |
| `tests/contact-form.test.cjs` | Test del modulo con risposte Formspree simulate |
| `assets/` | Sorgenti media approvati, quando disponibili |
| `public/` | **Output generato da distribuire**; non modificare a mano |

`public/` contiene la homepage di scelta lingua, cinque percorsi principali per lingua (`/`, `/about/`, `/projects/`, `/experience/`, `/contact/`), tre case study per lingua (`/projects/governance/`, `/projects/dbt/`, `/projects/nosql/`) e le pagine 404. Le raccolte `/writing/`, `/gallery/`, `/moments/` (“Life & Moments”) e `/initiatives/` sono previste nel generatore, ma non vengono create né mostrate nella navigazione finché non esiste almeno un contenuto pubblicato e completo. Esperienza e formazione condividono il percorso `/experience/`, con anchor stabile `#education`.

## Avvio locale

```sh
python3 build_pages.py
python3 check_site.py
cd public
python3 -m http.server 8000
```

Apri `http://localhost:8000/`. Le versioni localizzate sono a `/it/`, `/en/` e `/fr/`. Ogni pagina contiene HTML completo nella propria lingua. La pagina iniziale suggerisce la lingua salvata o quella del browser; non reindirizza automaticamente. La scelta manuale IT/EN/FR viene memorizzata localmente e le pagine localizzate non cambiano lingua da sole. Per modificare testi, aggiorna il dizionario in `translations/`; per progetti, documenti o media aggiorna il relativo registro in `content/`. Torna alla radice del repository ed esegui `python3 build_pages.py`. Una modifica a un componente in `build_pages.py`, `style.css`, `script.js` o `contact-form.js` si riflette su tutte le lingue alla rigenerazione: non si modificano le copie HTML in `public/`. Il generatore sostituisce interamente `public/` solo se trova il proprio file marker. I media e i documenti non referenziati da contenuti pubblicati non sono copiati nell'output. Il repository stesso può essere pubblico: non inserirvi bozze o autorizzazioni riservate. I tre originali fotografici appena analizzati sono ignorati da Git e rimangono locali; non vengono copiati in `public/`.

## Cloudflare Pages e indicizzazione

Il dominio canonico è `https://samuelokotako.com`. `site_config.py` usa questo valore come `SITE_URL` predefinito anche se la variabile d’ambiente esiste ma è vuota e abilita l’indicizzazione **solo** quando Cloudflare Pages genera il sito dal branch `main` (`CF_PAGES=1`, `CF_PAGES_BRANCH=main`). Build locali e branch preview restano `noindex`, anche se `SITE_URL` è valorizzato. `tools/test_build_modes.py` verifica le quattro modalità, compresa una configurazione Cloudflare precedente rimasta nell’ambiente. Il branch `main` è la condizione esplicita di pubblicazione approvata per questo rilascio.

Cloudflare Pages deve pubblicare **solo** la directory `public`. Il repository include anche l'output statico di produzione, rigenerato e controllato dalla CI della pull request: se il comando di build Pages è vuoto, può servirlo direttamente. Se Pages esegue `python3 -B build_pages.py`, usa le variabili `CF_PAGES` e `CF_PAGES_BRANCH` iniettate dalla piattaforma; quando la produzione passa a `main`, la build genera canonical, hreflang, sitemap e `robots.txt` indexable. Le preview su altri branch restano `noindex`; Cloudflare aggiunge inoltre l'header `X-Robots-Tag: noindex` alle preview.

La produzione era associata a `feature/portfolio-v2` prima del rilascio. Dopo il merge, verificare nella dashboard **Workers & Pages → progetto → Settings → Builds & deployments → Production deployments** che la produzione usi `main`, con repository GitHub corretto, output `public` e build command coerente. Nessuna modifica al branch Git cambia da sola queste impostazioni. Controllare l'HTML realmente servito, `robots.txt`, sitemap, canonical e hreflang sul dominio.

La pagina `public/404.html` è il fallback generale. Le pagine `public/it/404.html`, `public/en/404.html` e `public/fr/404.html` consentono a Cloudflare Pages di servire la variante più vicina al percorso richiesto. Non c'è un `_redirects`: nessun percorso HTTP pubblicato è stato identificato come migrazione esatta. I vecchi fragment della homepage (`/#projects`, ecc.) non possono essere intercettati dal server; la pagina di scelta lingua suggerisce il nuovo percorso senza redirect automatico. Non aggiungere regole catch-all o rewrite 200 per gli errori.

Dopo un futuro deployment, verifica con `curl -I` lo status di un URL inesistente alla radice e sotto ciascuna lingua, poi controlla il corpo con `curl -L`: devono rispondere `404`, mostrare la 404 corretta e restare `noindex`. Una visita diretta a `/404.html` può essere servita come file ordinario; il controllo del codice 404 va fatto su un URL realmente inesistente.

## Curriculum e controlli di rilascio

Il registro `content/documents.json` pubblica esclusivamente i tre CV Data Engineer definitivi in italiano, inglese e francese. I PDF approvati provengono da `cv/final/website-ready/`, sono copiati senza modificarli in `assets/cv/` e vengono distribuiti in `public/cv/`; il registro ne fissa gli SHA-256. La homepage mostra un solo link primario, sempre nella lingua della pagina: IT → PDF italiano, EN → PDF inglese, FR → PDF francese. I due vecchi percorsi `/assets/cv/` hanno redirect 301 esatti verso `/cv/`. Gli altri sei CV specializzati, i sorgenti LaTeX, i report QA e gli archivi rimangono fuori dal repository. I link includono `download` e il tipo PDF. L'assenza di tag strutturali nei PDF resta un limite di accessibilità del documento, distinto dall'accessibilità del collegamento HTML.

La CI in `.github/workflows/portfolio-quality.yml` si attiva su pull request verso `main`: rigenera l'output pubblico di produzione, verifica il sito e i test JavaScript, rileva drift dei file generati, controlla artefatti privati evidenti e usa Gitleaks sulla cronologia Git. Non effettua deploy. La revisione umana di contenuti e diritti resta necessaria. Per proteggere `main`, richiedere pull request e i controlli obbligatori dopo la prima esecuzione riuscita. La procedura è in `docs/RELEASE.md`.

## Design, performance e privacy

Il tema Auto segue `prefers-color-scheme`; Light/Dark sono selezionabili e persistono in `localStorage`. Lo stesso componente di tema, la navigazione e il template 404 sono usati nelle tre lingue. Le pagine restano leggibili senza JavaScript. Filtri e menu mobile sono miglioramenti progressivi, mentre le schede e la formazione espandibile usano HTML nativo.
Le griglie principali usano `auto-fit`/`minmax()` con larghezze minime legate al contenuto: quando spazio o testo ingrandito lo richiedono, le colonne tornano a una. Il menu mobile si apre nel flusso della pagina e la navigazione resta visibile se `script.js` non si carica. La tabella dei moduli ITS mantiene uno scorrimento interno. Verifica i nuovi contenuti a 320, 375, 390, 768, 1024 e 1440 px, anche con testo al 200%.

La homepage usa il template condiviso per IT/EN/FR: introduzione, progetti documentati, ambiti, quattro tappe di esperienza e formazione, un momento personale e invito al contatto con modulo ed email diretta. Il ritratto nell'hero e in About deriva da `samuel-profile.jpg`: Samuel ha confermato il diritto di pubblicarlo e il credito “Samuel Okotako” il 3 novembre 2026. Le varianti WebP da 320 e 426 px e il fallback JPEG sono in `assets/portrait/`; il ritratto nell'hero e in About è prioritario. La fotografia al Teatro Massimo Bellini deriva da `IMG_5358.HEIC`: Samuel ha confermato il diritto di pubblicarla e il medesimo credito il 3 novembre 2026. Le varianti WebP da 480 e 960 px e il JPEG di fallback sono in `assets/moments/`, senza data, GPS o dati del dispositivo incorporati; sono caricate in lazy loading. La fotografia `IMG_5750.JPG`, con altre persone e marchi visibili, resta esclusa. Le anteprime astratte dei progetti sono composizioni CSS decorative, non screenshot di risultati. Il motion è breve e si applica solo alle sezioni fuori dalla prima schermata; con `prefers-reduced-motion: reduce` o senza JavaScript i contenuti restano subito visibili.

Per sostituire una composizione con un'immagine reale, aggiungi a `content/home_media.json` lo slot `portrait`, `creative` o `projects.<id>` con `status: "approved"`, `src` di fallback in `/assets/`, `width`, `height`, `alt` nelle tre lingue e `rights` contenente `status: "approved"`, `basis` e `credit`. Lo slot `creative` richiede anche una breve `caption` localizzata. Puoi aggiungere `avif_srcset`, `webp_srcset` e `srcset` con descrittori di larghezza. Il generatore emette `<picture>` con `sizes`, dimensioni esplicite e fallback; carica il ritratto con priorità e le immagini sotto la prima schermata in lazy loading. Gli asset vengono copiati in `public/` solo se referenziati da slot approvati. Ottimizza i file e verifica l'autorizzazione prima di compilare lo slot; non usare foto di gruppo, materiale aziendale o screenshot non verificati.

La direzione Editorial Tech Luxury usa Ivory, Forest, Sage, Champagne e Ink come token CSS. Newsreader 400 (headline) e Manrope variabile (testo e interfaccia) sono WOFF2 locali in `assets/fonts/`; i rispettivi file `OFL-*.txt` sono conservati accanto ai font e copiati in `public/assets/fonts/`. Le fonti sono Google Fonts/Newsreader e Google Fonts/Manrope, con licenza SIL OFL 1.1. I fallback restano Georgia e i font di sistema; non ci sono richieste a Google Fonts durante la visita.

Il generatore riserva dimensioni alle immagini, usa lazy loading per quelle non prioritarie e `preload="none"` per i video. La raccolta Life & Moments richiede varianti WebP responsive; `tools/prepare_moment_image.py` le prepara senza metadati incorporati e senza aggiungere la foto al registro pubblicato. Il lightbox usa un dialog nativo, con Esc, pulsante di chiusura e ritorno del focus; il file grande resta raggiungibile come link senza JavaScript. Gli embed esterni sono caricati solo su richiesta. Non pubblicare media senza diritti verificati né documenti aziendali, dataset, recapiti privati o PDF integrali con dati sensibili.

## Contenuti da completare

- Prove di implementazione, dashboard finale e contributo personale del progetto NoSQL ITS.
- Componenti, misure e documentazione del radar Arduino, collegato a I.T. Archimede.
- Revisione finale della pubblicabilità dei repository GitHub dei case study; un controllo preliminare di segreti e file tracciati del PoC è documentato in `content/CASE_STUDY_AUDIT.md`. I link non sono mostrati finché non risultano pubblici e autorizzati.
- Conferma prima di associare al tirocinio Spindox risultati o informazioni ulteriori rispetto al contesto già pubblicato. Il PoC sintetico è descritto separatamente.
- Verifica finale dei recapiti pubblici e degli URL canonici sul dominio effettivo.

## Modulo di contatto Formspree

Il modulo nelle tre lingue invia i campi nome, email, motivo e messaggio all’endpoint pubblico `https://formspree.io/f/xgaappab`. Con JavaScript usa `fetch` e `Accept: application/json`; senza JavaScript resta un form HTML POST con validazione nativa. Il messaggio di successo appare soltanto dopo una risposta HTTP positiva di Formspree: non prova che una notifica email sia stata consegnata. Il pulsante resta disabilitato durante la richiesta; errori di rete, validazione, limiti 429 e altre risposte negative hanno messaggi localizzati. Il campo `_gotcha` è un honeypot supportato da Formspree. Il contenuto del messaggio non viene registrato nel browser, in `localStorage` o in analytics dal sito.

L’avviso nel modulo informa che i dati sono inviati a Formspree e conservati nel suo account per gestire la richiesta e rispondere, con link alla sua informativa. Prima della pubblicazione controllare nel dashboard Formspree che l’endpoint appartenga al proprio account, che il destinatario delle notifiche sia verificato, che la protezione antispam/Formshield sia attiva e che non siano configurate integrazioni non dichiarate. Impostare “Restrict to domain” sul dominio effettivo quando si autorizza il rilascio. Eseguire poi un invio reale e verificare nel dashboard Formspree e nella casella di destinazione; soltanto allora si potrà confermare la consegna email. La configurazione di eventuale reCAPTCHA va verificata sul form pubblicato, compreso il percorso AJAX.

Per un test reale, apri la pagina da un server locale o dal dominio pubblicato e prepara un unico messaggio di prova senza dati sensibili. Nelle DevTools attiva la conservazione del log di rete, poi controlla la richiesta a Formspree: metodo POST, endpoint, header `Accept`, stato HTTP, eventuali redirect e riga Console. Non condividere il testo del messaggio nella diagnostica. Se `fetch` fallisce per rete/CORS, il browser potrebbe non poter leggere una risposta a un invio già accettato: verifica il dashboard Formspree prima di ripetere l’operazione. Nel dashboard controlla anche spam, restrizione del dominio, CAPTCHA e destinatario delle notifiche. Un preflight riuscito non prova l’esito del successivo POST. Il link `mailto:` dipende da un client email configurato sul dispositivo.

Test locali del controller, senza contattare Formspree:

```sh
node --test tests/contact-form.test.cjs
python3 -B build_pages.py
python3 -B check_site.py
```
