# Dizionari i18n

`it.json`, `en.json` e `fr.json` sono le uniche sorgenti dei testi localizzati usati dai template in `build_pages.py`. Ogni file ha `content` (pagine principali, etichette e formazione), `extra` (raccolte future, 404, categorie editoriali e pagina di scelta lingua) e `cases` (testi dei case study per ID progetto). Le chiavi devono essere identiche nelle tre lingue; `site_content.py` controlla la parità e la struttura prima del build.

Per cambiare un testo, modifica il valore nel dizionario della lingua e rigenera con `python3 build_pages.py`. Per aggiungere una nuova stringa, crea la stessa chiave in tutti e tre i file, poi usala nel template condiviso. Dati e stato dei progetti vivono in `content/projects.json`; i testi dei case study sono in `cases` nei dizionari. I 28 moduli ufficiali sono in `content/its_modules.json`. I template HTML sono unici per tutte le lingue. Non modificare l'HTML in `public/`: viene rigenerato.

Il testo della pagina radice usa l'inglese come fallback leggibile senza JavaScript. JavaScript suggerisce la lingua già scelta o quella del browser e non effettua redirect. Le pagine `/it/`, `/en/` e `/fr/` hanno HTML localizzato completo e sono accessibili direttamente.
