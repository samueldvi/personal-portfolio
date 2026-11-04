# Bank Loan Approval Prediction — scheda in bozza

**Stato:** non pubblicare la scheda o una pagina di dettaglio. Il progetto è stato descritto dall’autore come lavoro di Machine Learning svolto durante la formazione su dati relativi a clienti bancari per prevedere l’esito di richieste di prestito. Non è stato identificato un artefatto locale riconducibile con certezza al progetto. Non assumere che i dati siano reali, sintetici, pubblici o aziendali.

## Materiali da recuperare e verifiche

1. **Dataset:** fonte, versione/data, licenza, permessi di utilizzo, dizionario delle variabili, dimensioni, natura dei dati e presenza di identificatori o dati personali. Non copiare record di clienti nel sito o nel repository.
2. **Target e domanda:** definizione precisa dell’esito da prevedere, unità di analisi, momento in cui le variabili sono disponibili e possibili leakage rispetto alla decisione di prestito.
3. **Preprocessing:** gestione dei mancanti, encoding, scaling, outlier e sbilanciamento delle classi; verificare che le trasformazioni siano apprese solo sul training set.
4. **Algoritmi e baseline:** notebook/codice, librerie e versioni, modelli confrontati, iperparametri e criteri di scelta. Non inferire algoritmi dal titolo.
5. **Validazione:** split train/validation/test, eventuale cross-validation o separazione temporale, riproducibilità del seed e prevenzione del leakage.
6. **Metriche:** matrice di confusione, precision, recall, F1, ROC/PR, calibrazione e analisi degli errori se realmente calcolate; documentare soglia e prevalenza della classe. Non pubblicare numeri senza output riproducibili.
7. **Contributo personale:** verificare ruolo, notebook, commit o relazione finale; distinguere attività individuali e di gruppo.
8. **Pubblicabilità:** controllare licenza di dataset e codice, informazioni personali, segreti, risultati di training e autorizzazioni di eventuali coautori.

## Sezioni da predisporre per un futuro case study

- **Explainability:** metodo usato, spiegazioni globali/locali, stabilità e limiti delle spiegazioni; evitare di chiamare causale una correlazione.
- **Bias:** rappresentatività del dataset, variabili proxy, errori e calibrazione per sottogruppi quando valutabili in modo appropriato; documentare ciò che non è misurabile.
- **Privacy:** minimizzazione e protezione dei dati, controllo degli output e dei notebook, nessuna pubblicazione di record individuali.
- **Limiti per il credito:** errori del modello, cambiamenti nella popolazione e nei dati, revisione umana e governance. Un prototipo formativo non costituisce prova di idoneità a decisioni creditizie reali.

La scheda pubblica e la categoria di filtro restano nascoste fino alla verifica delle fonti e a una scelta editoriale esplicita.
