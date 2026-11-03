# Samuel Okotako — sito personale

Sito statico in italiano, inglese e francese, pensato per crescere con progetti tecnici, scritti, media e nuove iniziative. HTML, CSS e JavaScript vanilla sono sufficienti per l'interfaccia attuale. Python (libreria standard) genera i file statici da template condivisi e dizionari IT/EN/FR separati; nessun CMS, database o framework frontend è richiesto.

## Struttura

| Percorso | Ruolo |
| --- | --- |
| `translations/it.json`, `en.json`, `fr.json` | Dizionari indipendenti per testi, etichette e contenuti editoriali |
| `site_content.py` | Caricamento e controllo di coerenza dei dizionari |
| `content/projects.json` | Progetti tecnici, stato dei case study e dati delle schede |
| `content/its_modules.json` | 28 denominazioni e voti ITS verificati sul certificato ufficiale |
| `content/CASE_STUDY_AUDIT.md` | Inventario delle prove e delle lacune prima della pubblicazione |
| `content/articles.json` | Registro articoli, al momento vuoto |
| `content/galleries.json` | Registro lavori fotografici e media, al momento vuoto |
| `content/moments.json` | Momenti personali e culturali, separati dalla galleria creativa e al momento vuoti |
| `content/documents.json` | Registro di CV e documenti pubblici, al momento vuoto |
| `content/initiatives.json` | Registro separato di iniziative professionali e imprenditoriali, al momento vuoto |
| `content/README.md` | Convenzioni per aggiungere contenuti e gestire spostamenti |
| `tools/prepare_moment_image.py` | Preparazione locale di varianti WebP senza metadati |
| `build_pages.py` | Generatore e validazione dei contenuti pubblicati |
| `site_config.py` | Configurazione centralizzata `SITE_URL` |
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

Imposta la **directory di output** di Cloudflare Pages a `public`; non serve un comando di build se i file generati sono nel repository. Pubblicare la radice del repository esporrebbe registri, script sorgente e possibili bozze: non farlo.

`SITE_URL` resta vuoto finché non esiste l'URL pubblico definitivo. In questa fase tutte le pagine hanno `noindex`, `public/robots.txt` blocca la scansione, e non vengono generati canonical, hreflang o sitemap fittizi. Dopo l'assegnazione dell'URL Cloudflare, imposta `SITE_URL` all'origin HTTPS reale e rigenera. Il generatore produrrà canonical assoluti autoreferenziali, hreflang reciproci, Open Graph URL, dati strutturati essenziali e una sitemap con i soli percorsi pubblicati, comprese le pagine di dettaglio dei progetti pubblicati, eventuali articoli e le raccolte di media e iniziative quando disponibili. Verifica i risultati sul dominio reale prima dell'indicizzazione.

La pagina `public/404.html` è il fallback generale. Le pagine `public/it/404.html`, `public/en/404.html` e `public/fr/404.html` consentono a Cloudflare Pages di servire la variante più vicina al percorso richiesto. Non c'è un `_redirects`: nessun percorso HTTP pubblicato è stato identificato come migrazione esatta. I vecchi fragment della homepage (`/#projects`, ecc.) non possono essere intercettati dal server; la pagina di scelta lingua suggerisce il nuovo percorso senza redirect automatico. Non aggiungere regole catch-all o rewrite 200 per gli errori.

Dopo un futuro deployment, verifica con `curl -I` lo status di un URL inesistente alla radice e sotto ciascuna lingua, poi controlla il corpo con `curl -L`: devono rispondere `404`, mostrare la 404 corretta e restare `noindex`. Una visita diretta a `/404.html` può essere servita come file ordinario; il controllo del codice 404 va fatto su un URL realmente inesistente.

## Design, performance e privacy

Il tema Auto segue `prefers-color-scheme`; Light/Dark sono selezionabili e persistono in `localStorage`. Lo stesso componente di tema, la navigazione e il template 404 sono usati nelle tre lingue. Le pagine restano leggibili senza JavaScript. Filtri e menu mobile sono miglioramenti progressivi, mentre le schede e la formazione espandibile usano HTML nativo.
Le griglie principali usano `auto-fit`/`minmax()` con larghezze minime legate al contenuto: quando spazio o testo ingrandito lo richiedono, le colonne tornano a una. Il menu mobile si apre nel flusso della pagina e la navigazione resta visibile se `script.js` non si carica. La tabella dei moduli ITS mantiene uno scorrimento interno. Verifica i nuovi contenuti a 320, 375, 390, 768, 1024 e 1440 px, anche con testo al 200%.

Il generatore riserva dimensioni alle immagini, usa lazy loading per quelle non prioritarie e `preload="none"` per i video. La raccolta Life & Moments richiede varianti WebP responsive; `tools/prepare_moment_image.py` le prepara senza metadati incorporati e senza aggiungere la foto al registro pubblicato. Il lightbox usa un dialog nativo, con Esc, pulsante di chiusura e ritorno del focus; il file grande resta raggiungibile come link senza JavaScript. Gli embed esterni sono caricati solo su richiesta. Non pubblicare media senza diritti verificati né documenti aziendali, dataset, recapiti privati o PDF integrali con dati sensibili.

## Contenuti da completare

- Prove di implementazione, dashboard finale e contributo personale del progetto NoSQL ITS.
- Componenti, misure e documentazione del radar Arduino, collegato a I.T. Archimede.
- Revisione finale della pubblicabilità dei repository GitHub dei case study; un controllo preliminare di segreti e file tracciati del PoC è documentato in `content/CASE_STUDY_AUDIT.md`. I link non sono mostrati finché non risultano pubblici e autorizzati.
- Conferma prima di associare al tirocinio Spindox risultati o informazioni ulteriori rispetto al contesto già pubblicato. Il PoC sintetico è descritto separatamente.
- Verifica dei recapiti pubblici e dell'URL definitivo Cloudflare.

## Modulo di contatto Formspree

Il modulo nelle tre lingue invia i campi nome, email, motivo e messaggio all’endpoint pubblico `https://formspree.io/f/xgaappab`. Con JavaScript usa `fetch` e `Accept: application/json`; senza JavaScript resta un form HTML POST con validazione nativa. Il messaggio di successo appare soltanto dopo una risposta HTTP positiva di Formspree: non prova che una notifica email sia stata consegnata. Il pulsante resta disabilitato durante la richiesta; errori di rete, validazione, limiti 429 e altre risposte negative hanno messaggi localizzati. Il campo `_gotcha` è un honeypot supportato da Formspree. Il contenuto del messaggio non viene registrato nel browser, in `localStorage` o in analytics dal sito.

L’avviso nel modulo informa che i dati sono inviati a Formspree e conservati nel suo account per gestire la richiesta e rispondere, con link alla sua informativa. Prima della pubblicazione controllare nel dashboard Formspree che l’endpoint appartenga al proprio account, che il destinatario delle notifiche sia verificato, che la protezione antispam/Formshield sia attiva e che non siano configurate integrazioni non dichiarate. Dopo aver assegnato `SITE_URL`, impostare “Restrict to domain” sul dominio effettivo. Eseguire poi un invio reale e verificare nel dashboard Formspree e nella casella di destinazione; soltanto allora si potrà confermare la consegna email. La configurazione di eventuale reCAPTCHA va verificata sul form pubblicato, compreso il percorso AJAX.

Per un test reale, apri la pagina da un server locale o dal dominio pubblicato e prepara un unico messaggio di prova senza dati sensibili. Nelle DevTools attiva la conservazione del log di rete, poi controlla la richiesta a Formspree: metodo POST, endpoint, header `Accept`, stato HTTP, eventuali redirect e riga Console. Non condividere il testo del messaggio nella diagnostica. Se `fetch` fallisce per rete/CORS, il browser potrebbe non poter leggere una risposta a un invio già accettato: verifica il dashboard Formspree prima di ripetere l’operazione. Nel dashboard controlla anche spam, restrizione del dominio, CAPTCHA e destinatario delle notifiche. Un preflight riuscito non prova l’esito del successivo POST. Il link `mailto:` dipende da un client email configurato sul dispositivo.

Test locali del controller, senza contattare Formspree:

```sh
node --test tests/contact-form.test.cjs
python3 -B build_pages.py
python3 -B check_site.py
```
