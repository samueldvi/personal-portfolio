# Portfolio — Samuel Okotako

Portfolio statico bilingue (italiano/inglese) per presentare percorso, esperienza e progetti in Data Engineering, AI Engineering e Data Governance. Usa HTML, CSS e JavaScript vanilla; non richiede dipendenze o build.

## Esecuzione locale

Dalla cartella `personal-portfolio/`:

```sh
python3 -m http.server 8000
```

Apri `http://localhost:8000/` nel browser. In alternativa, apri direttamente `index.html`; il sito non usa chiamate API. Per verificare il fallback senza JavaScript, disabilita JavaScript nel browser: il contenuto italiano e la navigazione restano disponibili.

## Struttura

- `index.html`: contenuti italiani, markup semantico e sei aree: Home, Esperienza, Progetti, Formazione, Chi sono, Contatti.
- `style.css`: dark theme, layout responsive e focus visibile.
- `script.js`: traduzioni inglesi, selezione lingua, menu mobile e anno nel footer.
- `samuel-profile.jpg`: risorsa preesistente, attualmente non usata nella pagina.

La versione italiana in HTML è la base accessibile anche senza JavaScript. Le traduzioni inglesi sono nella mappa `translations.en` in `script.js`, associate agli attributi `data-i18n`. Quando si aggiunge un elemento traducibile, aggiungere anche la corrispondente chiave inglese. La scelta della lingua viene salvata in `localStorage` quando disponibile.

## Contenuti da completare prima della pubblicazione

- Verificare descrizione, tecnologie, soluzione e risultati pubblicabili dei progetti Data Governance & Masking, dbt + DuckDB e Big Data NoSQL con Databricks. Non aggiungere codice o materiale interno Spindox.
- Verificare componenti, misure e documentazione del radar Arduino.
- Collegare i repository GitHub dei progetti solo dopo averne verificato esistenza e pertinenza. Attualmente non sono presenti link di progetto inventati.
- Inserire nell'area espandibile l'elenco ufficiale dei 28 moduli ITS e i relativi voti, senza ore o CFU; usare “Idoneo” per moduli senza voto numerico. Non caricare il documento ITS integrale.
- Attivare un servizio di invio sicuro prima di rendere operativo il futuro modulo di contatto. Per ora è disponibile il link email.
- Confermare che email, GitHub e LinkedIn siano i recapiti pubblici desiderati.

## Hosting

Il sito può essere pubblicato come asset statico su Cloudflare Pages. La directory di output è la radice del repository; non è necessario un comando di build. Nessun deploy è stato effettuato.
