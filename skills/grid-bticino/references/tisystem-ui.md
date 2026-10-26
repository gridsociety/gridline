# TiSystem web: riscontri operativi qualificati

Applicazione usata su macOS con browser autenticato: https://tisystem.bticino.it/.
Non esiste un API pubblico TiSystem implementato da questo backend.

- I menu dipendenti possono caricarsi e ripristinare valori dopo una prima
  lettura DOM. Attendere la stabilizzazione e rileggere sorgente/taglia/posa.
  Selezionare prima il tipo di trasformatore e poi la potenza finale.
- Per quattro derivazioni sotto un generale: selezionare il generale, inserire
  la prima in serie; inserire le successive in parallelo alla prima. Verificare
  il collegamento effettivo nel disegno, non soltanto il numero di elementi.
- La scelta manuale delle sezioni può attivare da sola il blocco sezione:
  rileggere la casella prima di cambiarla.
- Le finestre di ricerca prodotto sono annidate. Agire sull'ultimo dialogo,
  aspettare i risultati e verificare codice/articolo prima della conferma.
- Le note del circuito nel caso provato hanno limite di 35 caratteri. Non
  forzare valori oltre i limiti HTML: può bloccare il salvataggio e i tab.
- Stampa tecnica: solo quadro corrente, legende e unifilare; copertina nativa e
  carpenteria disattivate quando il fascicolo usa la copertina Documentor.
- Esportare separatamente report dettagliato, CSV e progetto `.ti8` dopo calcolo,
  verifica e salvataggio. Non correggere PDF/CSV per far passare i controlli.
- Se l'interfaccia cambia, osservare la nuova pagina e aggiornare la procedura;
  coordinate e ID effimeri di una sessione non sono selettori riutilizzabili.
