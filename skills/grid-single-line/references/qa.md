# Controllo qualità

1. Fonti: ogni valore specifico ha riscontro o marcatura esplicita; non confondere un esempio del cliente con il modello acquistato.
2. QET: validazione XML, UUID, terminali e riferimenti; controllare terminali reali e rotazioni. Verifica aperta se QET non è disponibile.
3. Grafo: nessun collegamento duplicato/involontario, apparecchi attesi connessi, confini e domini coerenti; per A/B verificare cosa resta connesso rimuovendo logicamente il DG e i dispositivi dei rami. Distinguere porte funzionali da apparecchi fisici.
4. Preservazione: quando si modifica l'esistente confrontare componenti e netlist prima/dopo. Dichiarare ogni modifica intenzionale; verificare polarità DC e indipendenza ausiliari.
5. Geometria: percorsi ortogonali, endpoint coincidenti, testi senza sovrapposizioni, incroci di potenza controllati, etichette lontane dai segni; la sola assenza di incroci non dimostra correttezza del circuito.
6. Rendering: vedere tutte le pagine e ingrandire magnetotermico/RCBO, dorsale, station, cartigli. Verificare riquadri, quadratino pieno, Id, orientamento TR e simboli, tratteggi reali, tagli ai bordi, titoli e numerazione.
7. Resa nativa: l'anteprima MCP è approssimativa; il successo di `open_project` non prova una verifica visiva. Scrivere separatamente XML verificato / PDF verificato / QET nativo verificato / verifica progettista.
8. Emissione: indice coerente, generali prima dei dettagli, nessuna pagina legenda non richiesta, dati cliente corretti, niente dati di altre commesse accidentalmente rimasti nel nuovo progetto.

Difetti riscontrati e correzioni da conservare:

- SVG polilinea riempita non affidabile in MuPDF: usare un vero `polygon` chiuso per il quadratino automatico.
- MuPDF può perdere `stroke-dasharray`: convertire i tratteggi in segmenti espliciti (`svg_primitives.explicit_dashes`).
- Non basare la verifica solo sul renderer: confrontare definizione QET, riferimento fornito e PDF.
- Un prefisso testuale generico (`GS.BA`) può confondere nodi ausiliari e batteria (`GS.BAT`): usare ID espliciti e domini, contare i due collegamenti DC.
- Non fissare il foglio a un rapporto inadatto e poi ridurre tutto, creando margini laterali enormi.

`gridline check` copre solo scheletro e riferimenti elementari. Le altre verifiche devono essere effettuate e registrate: nessun comando qui certifica selettività, taratura, dimensionamento o norme CEI/IEC applicabili.
