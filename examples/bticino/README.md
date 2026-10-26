# Esempio sintetico — quattro partenze AUX

`request.json` e `cover.json` descrivono un caso didattico: tre batterie da
2,5 MW / 5 MWh ciascuna, station obiettivo 7,5 MW, quattro AUX e MT. Carichi AUX
30/30/30/10 kW e lunghezze 35/45/55/25 m sono ipotesi, non dati di un cliente.
Il progettista è generico e il timbro è assente.

Questo esempio mostra **gli input**, non contiene un calcolo esecutivo pronto.
Gli export TiSystem, i cataloghi OEM e i timbri non sono redistribuiti nel repo.
Non si generano simboli sintetici per sostituirli. Il collaudo end-to-end è stato
eseguito con originali locali; leggere VALIDATION.md per ambito e limiti.

Per riprodurre il flusso:

1. `gridline new /percorso/test --workflow equipment`.
2. Copiare i due JSON in `source/bticino/cases/current/`; adattare identità,
   input e ambito. Per solo BT lasciare `engineering.json` senza viste MT e
   rendere coerenti descrizione/indice del fascicolo.
3. Creare/calcolare/verificare il caso in TiSystem con le ipotesi dichiarate.
4. Acquisire quattro originali e compilare `exports.json` secondo lo schema
   incluso nel workspace, con mappa dei circuiti, pagine e hash.
5. `gridline check /percorso/test`, poi `gridline bticino-smoke /percorso/test`.
6. Controllare PDF, continuità, tabelle, dimensionamento e punti aperti.

Per MT acquisire separatamente le fonti originali: non basta copiare la tabella
numerica dell'esempio. La FSK 7860 candidata non dimostra 7,5 MW bidirezionali
nelle condizioni del datasheet citato; consumi/spunti AUX, interfaccia esterna
station e ripartizione DC richiedono conferma OEM. Il test conserva questi
limiti anziché presentare l'esempio come approvato.
