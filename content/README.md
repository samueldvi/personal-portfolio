# Convenzioni editoriali

I file in questa cartella sono **sorgenti**, non file da pubblicare direttamente. `python3 build_pages.py` genera `public/`, che è l'unica cartella da distribuire su Cloudflare Pages. Non modificare manualmente l'HTML in `public/`: la rigenerazione lo sostituisce.

## Progetti tecnici

Aggiungi un oggetto a `projects.json` con:

- `id`: slug stabile (`a-z`, numeri e trattini); diventa l'anchor `#project-id` nelle tre pagine `/it/projects/`, `/en/projects/`, `/fr/projects/`.
- `category`: categoria tecnica; aggiungi l'etichetta corrispondente nei `filters` di `translations/it.json`, `en.json` e `fr.json`.
- `number`: progressivo editoriale.
- `status`: `draft` mantiene il record fuori da pagine, filtri e sitemap; `published` rende visibile la scheda. I record esistenti senza `status` sono considerati pubblicati.
- `translations.it`, `.en`, `.fr`: `name`, `type`, `teaser`, `context`, `problem`, `approach`, `outcome`, `tech`.

Poi esegui `python3 build_pages.py`. Solo un record con `status: "published"` appare nella pagina Progetti senza modificare le pagine HTML. Per un case study completo, imposta `"detail": "published"` nel record e aggiungi `cases.[id]` in ciascuno dei tre dizionari `translations/it.json`, `en.json`, `fr.json`. Ogni caso richiede `context`, `problem`, `goal`, `responsibility`, `technologies`, `architecture`, `decisions` (coppie `heading`/`text`), `checks`, `results` (coppie `label`/`detail`), `limits`, `diagram_title`, `diagram_note` e `diagram_steps`; `results_heading` permette di distinguere risultati misurati e materiali di un progetto. Un solo template genera `/[lingua]/projects/[id]/`, canonical e voci sitemap. Usa `"detail": "draft"` quando la scheda può essere pubblica ma mancano prove per una pagina di dettaglio. Usa anche `"status": "draft"` per tenere fuori dall’intero sito una scheda ancora da verificare; il record e le traduzioni restano nell’inventario sorgente. Inserisci `github` nel record soltanto dopo aver confermato che il repository è pubblico e pubblicabile: il template mostra il link solo se presente, senza testi segnaposto. Non cambiare un `id` pubblicato: se serve cambiare URL o anchor, documenta la migrazione e aggiungi un 301 solo per un percorso HTTP realmente esistente. I fragment `#...` non sono visibili al server e non possono essere migrati con `_redirects`.

### Visualizzazioni e prove

Ogni progetto pubblico richiede un record in `project_visuals.json`. Il registro separa il tipo di visualizzazione (`flow`, `screenshot`, `concept`), gli identificativi delle fasi e il livello di evidenza dalla presentazione. Le etichette delle fasi sono in `cases.[id].diagram_steps` per IT/EN/FR e devono avere lo stesso ordine e la stessa lunghezza del registro. Disegna soltanto fasi documentate nel codice o negli artefatti: il diagramma NoSQL descrive definizioni esportate, non una run completata. Per una scheda senza case study, usa un visual `concept` e una didascalia che ne dichiari il carattere illustrativo.

Uno `screenshot` richiede `src` PNG di fallback, `webp_srcset`, dimensioni effettive, `alt` nelle tre lingue, `license_file` e `rights` con licenza, base e credito. Ottimizza WebP senza metadati incorporati, conserva il file di licenza e verifica che la schermata non mostri credenziali, dati personali o materiali aziendali. `build_pages.py` copia in `public/` solo gli asset referenziati dai record pubblicati. Le immagini fuori dalla viewport usano `loading="lazy"`; non inserire screenshot costruiti con dati inventati.

## Articoli

`articles.json` è vuoto finché non esistono contenuti completi. Per pubblicare un articolo aggiungi, per esempio, questo schema (i valori sono illustrativi e non sono un articolo reale):

```json
{
  "status": "published",
  "slug": "titolo-stabile",
  "date": "2026-11-02",
  "languages": ["en"],
  "categories": ["Data Engineering"],
  "tags": ["Python"],
  "author": "Samuel Okotako",
  "image": null,
  "translations": {"en": {"title": "Title", "description": "Description"}}
}
```

Crea il corpo per ogni lingua elencata, per esempio `content/articles/titolo-stabile/en.html`. Usa solo `p`, `h2`–`h4`, liste, `strong`, `em`, `code`, `pre`, `blockquote`, `br` e link HTTPS/locali/mailto; gli attributi sono ammessi soltanto per `href` dei link. Il generatore rifiuta altri tag e attributi. Gli archivi `/it/writing/`, `/en/writing/`, `/fr/writing/` sono sempre disponibili; le pagine di dettaglio sono generate solo per le lingue pubblicate. Il selettore lingua apre l'archivio quando la traduzione dell'articolo manca. Le bozze (`"status": "draft"`) e i contenuti non pubblici non sono generati né copiati in `public/`. In produzione ogni archivio dispone di un feed RSS; gli articoli possono avere `tags` per ricerca e collegamenti correlati.

Per un'immagine dell'articolo, sostituisci `null` con `{"src":"/assets/articolo.webp","width":1200,"height":800,"alt":{"it":"...","en":"...","fr":"..."}}`. Puoi aggiungere `srcset`. Metti l'asset originale in `assets/`; il generatore copia solo quelli referenziati da contenuti pubblicati. Specifica dimensioni reali per evitare spostamenti del layout. Per ora le immagini nel corpo HTML sono escluse: usa il campo `image` con dimensioni, alt localizzato e approvazione dei diritti. Un componente per media incorporati richiederà una policy di sicurezza separata.

## Galleria e media

`galleries.json` è vuoto finché non esiste un lavoro pubblicabile. Un elemento richiede `status`, `slug`, `category` (per esempio `modelling`, `creative` o `collaboration`), `author`, `kind`, `media`, `rights` e traduzioni IT/EN/FR di `title`, `description`, `alt`.

Per pubblicare, `rights` deve contenere almeno `{"status":"approved","basis":"owned or written permission","credit":"Nome da mostrare"}`. Conserva la prova dell'autorizzazione fuori dal repository se contiene dati privati. Non segnare `approved` senza aver verificato diritti di immagine, persone ritratte, musica e altri materiali.

- Immagine: `"kind":"image"`, `media.src` locale in `/assets/`, `width`, `height`; `srcset` opzionale. L'HTML usa `loading="lazy"` e `decoding="async"`.
- Video: `"kind":"video"`, `media.src` e `poster` locali in `/assets/`, `width`, `height`. L'HTML usa controlli e `preload="none"`; non usa autoplay.
- Embed: `"kind":"embed"`, `media.url` HTTPS, `poster` locale in `/assets/`, `width`, `height`. Il player esterno viene caricato solo dopo un clic; senza JavaScript resta un link diretto.

La galleria `/[lingua]/gallery/` e il relativo link di navigazione vengono generati solo quando esiste almeno un elemento `published` con diritti approvati. Fotografie di modelling, video e collaborazioni restano in questa raccolta, separate dai progetti tecnici e dagli articoli.

## Life & Moments

`moments.json` è una raccolta editoriale distinta dai progetti tecnici, dalla formazione e dalla galleria di lavori creativi. La pagina `/[lingua]/moments/` e il link “Life & Moments” appaiono solo quando almeno una fotografia è esplicitamente `published` e supera i controlli.

Per ogni foto servono `slug`, `category`, `context` (`personal`, `group`, `company`), `rights` (`status: "approved"`, `basis`, `credit`), `media` e `translations.it/en/fr` con `title`, `caption` breve e `alt` descrittivo. Evita date, luoghi, opere o eventi se non confermati. Le categorie ammesse sono `technology-events`, `culture-theatre`, `modelling-creative`, `education-moments`, con etichette nei dizionari IT/EN/FR. I lavori creativi completi restano nella galleria separata; qui trovano spazio solo momenti personali approvati. `media` contiene `small`, `small_width`, `medium`, `medium_width`, `large`, `width`, `height`: i tre file devono essere WebP locali sotto `/assets/`; `width` e `height` sono le dimensioni del file grande. La griglia usa le due varianti minori, il lightbox usa quella grande.

Prepara i file, dopo aver scelto e verificato una fotografia, con `python3 tools/prepare_moment_image.py /percorso/dell/originale.heic slug-stabile`. Su macOS servono `sips` e `cwebp`; per HEIC serve anche `heif-convert`. Il comando mostra i metadati da copiare nel registro e non modifica l'originale. `cwebp` elimina i metadati incorporati. Controlla ritaglio, orientamento e qualità visiva prima di usare i file. Non salvare originali privati in `assets/`: solo le varianti approvate. Gli asset non entrano in `public/` finché il record non è pubblicato.

La pubblicazione richiede `approval.owner: true` dopo conferma esplicita. Per `group` e `company` serve anche `approval.people: true` dopo aver verificato il consenso delle persone riconoscibili. Per `company` serve inoltre `approval.organization: true` dopo aver verificato il permesso per ambienti, marchi e materiale aziendale. Un valore nel file non sostituisce la conferma reale: registralo soltanto dopo la verifica. Le foto in revisione restano fuori da `moments.json` oppure hanno `status: "draft"`; non sono generate né copiate.

## Documenti e nuove iniziative

Curriculum e documenti pubblici si aggiungono in `documents.json`. Per i documenti diversi dai CV, ogni record `published` richiede `slug`, `file` locale in `/assets/` (per esempio `/assets/docs/documento.pdf`), `updated` in formato `YYYY-MM-DD` e `translations.it/en/fr` con `title` e `description`. Il generatore copia il file e mostra un blocco Documenti pubblici nella pagina About solo quando esiste almeno un record pubblicato. Verifica privacy, aggiornamento e diritti; non inserire PDF integrali con dati sensibili. Nuove iniziative professionali o imprenditoriali vanno in `initiatives.json`, separate da articoli, galleria e progetti tecnici. Ogni record `published` richiede `slug` stabile, `category` e `translations.it/en/fr` con `title` e `summary`. Per esempio: `{"status":"published","slug":"nome-iniziativa","category":"Impresa","translations":{"it":{"title":"Titolo","summary":"Sintesi"},"en":{"title":"Title","summary":"Summary"},"fr":{"title":"Titre","summary":"Résumé"}}}`. L’elenco `/[lingua]/initiatives/` appare nella navigazione e nella sitemap solo quando esiste almeno un record pubblicato. `draft` resta fuori dall’output. Valuta una pagina di dettaglio quando esiste materiale sufficiente.

Per i CV servono tre record con `kind: "cv"`, `language` pari a `it`, `en` e `fr`, `file` pubblico sotto `/cv/`, `source` sotto `/assets/cv/`, SHA-256 del PDF approvato e `approval: {"owner": true, "privacy_reviewed": true}`. Il generatore mostra il link localizzato soltanto con l’intera terna approvata e rifiuta PDF mancanti, non validi o diversi dai checksum. La homepage è l’unico accesso nell’interfaccia ai CV; gli altri documenti pubblici, quando presenti, appaiono nella sezione About. I file approvati in `cv/final/website-ready/` sono copiati senza modificarli. La verifica automatica non sostituisce la lettura integrale, la verifica di accessibilità e l’autorizzazione personale. Non aggiungere bozze o documenti privati in `assets/`: il repository Git può essere pubblico anche se il file non è copiato in `public/`.

## Link e contenuti spostati

Mantieni stabili slug e URL. Quando una pagina HTTP pubblicata cambia percorso, crea una regola esatta 301 in `_redirects` nel formato `/vecchio-percorso/ /nuovo-percorso/ 301`, annotando la ragione nel README. Evita wildcard e controlla che la destinazione non ritorni al percorso sorgente. Per contenuti rimossi senza sostituto pertinente, conserva una risposta 404 (o valuta 410 in futuro), senza inviare l'utente alla home con HTTP 200.

**Nota privacy:** il repository GitHub può essere pubblico anche quando `public/` non contiene una bozza. Non salvare in `content/`, `assets/` o altrove nel repository bozze riservate, liberatorie, documenti interni o dati personali non destinati alla pubblicazione.

## Piano ITS verificato

`its_modules.json` conserva esclusivamente il numero progressivo, la denominazione e il voto dei 28 moduli, trascritti dal certificato ufficiale e confrontati con la pagina originale. Le denominazioni, inclusa l'ortografia del documento, e la dicitura `IDONEO` rimangono esatte in tutte le lingue. Non aggiungere ore, CFU, numero di protocollo o copia del certificato all'output pubblico. Prima di correggere un dato, confrontalo con un documento ufficiale aggiornato.
