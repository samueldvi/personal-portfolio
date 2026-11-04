# Big Data NoSQL ITS — nota privata sugli artefatti recuperati

**Stato:** case study basato sull’export sorgente pubblicato solo nel sito generato locale; materiali originali non copiati nel repository. Il rapporto dettagliato è nel deliverable di revisione del 2 novembre 2026.

## Fonte e contributi

- ZIP originale letto in una directory di lavoro separata dal repository pubblico.
- Progetto di gruppo ITS. Samuel dichiara di essere stato team leader e di aver contribuito principalmente a coordinamento e ingestion.
- Il notebook Bronze porta il nome Samuel; il nome del file non prova l’autorialità delle singole celle. Silver, Gold e dashboard restano attribuiti al gruppo.
- Databricks Community Edition è l’ambiente originale; non è confermato l’accesso al workspace oggi.

## Architettura documentata

1. Quattro CSV detailed Inside Airbnb dichiarati per Amsterdam e Rio, assenti dallo ZIP.
2. Notebook Bronze: quattro tabelle Delta, con città e timestamp d’ingestion.
3. Notebook Silver: `silver_listings` con `UNION ALL` e conversioni. `silver_reviews` compare nella documentazione e in Gold, ma il relativo notebook/DDL non è nell’export.
4. Notebook Gold: definizioni di viste e query; un IPYNB conserva due configurazioni grafiche senza risultati numerici.

Questa sequenza descrive il codice disponibile e non dimostra un run end-to-end. Il case study pubblico non attribuisce conteggi o dashboard finali al progetto.

## Verifiche aperte

- Recuperare dataset/versioni, `silver_reviews`, schemi finali, output, run log e dashboard.
- Correggere il `CREATE ... TABLE ... SELECT` senza `AS`, le viste non idempotenti e le query con filtri città incoerenti prima di qualunque nuova esecuzione.
- Verificare la semantica di `RECENSIONI_MESI`: usa l’ultima recensione per annuncio, non gli eventi di recensione.
- Controllare dati personali in CSV/output e ottenere consenso dei coautori prima di pubblicare codice, documentazione, screenshot o dashboard.
- Attribuire Inside Airbnb e rispettare le sue Data Policies; non ripubblicare i dataset nel portfolio.

Nessun file dell’archivio deve essere copiato in `public/` o nel repository del portfolio in questa fase.
