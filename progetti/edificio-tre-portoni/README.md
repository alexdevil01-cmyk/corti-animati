# Edificio a tre portoni: blueprint

Blueprint ricavato dallo schizzo a mano. Serve come riferimento per modellare l'edificio in 3D con l'IA generativa.

## File

| File | Contenuto |
|---|---|
| `blueprint_edificio_tre_portoni.pdf` | Le 5 tavole in un unico PDF A3 |
| `tavole/tav01_prospetto_sezione-C.png` | Prospetto su strada e sezione trasversale C-C |
| `tavole/tav02_piante_PT_P1.png` | Piante del piano terra e del primo piano |
| `tavole/tav03_piante_P2_P3.png` | Piante del secondo e del terzo piano |
| `tavole/tav04_copertura_sezioni-A-B.png` | Copertura e sezioni longitudinali A-A e B-B |
| `tavole/tav05_assonometrie_dettagli.png` | Assonometrie, dettagli delle aperture, schema della scala imperiale, note |
| `tavole/_iso_esterno.png`, `tavole/_iso_spaccato.png` | Assonometrie singole, da usare come immagini di riferimento |
| `modello/edificio.obj` + `.mtl` | Modello a blocchi (Y in alto, 1 unità = 1 u), importabile in Blender o altri programmi |
| `modello/edificio.json` | Stessa geometria in formato dati |
| `src/` | Script che generano tutto. Le misure si cambiano in `geometria.py` |

Per rigenerare tutto:

```bash
cd src
python3 esporta_modello.py && python3 tavole.py
node render.js <cartella con node_modules/three> all
```

## Scheda tecnica (unità di griglia u, consigliato 1 u ≈ 1 m)

- **Tipo**: edificio in linea, collegato a destra e a sinistra con edifici uguali. I muri laterali sono in comune e senza aperture.
- **Ingombro**: 12 u di fronte × 10 u di profondità × 15,5 u di altezza (parapetto compreso).
- **Struttura**: muri perimetrali da 0,5 u. Due muri portanti interni da 0,3 u, perpendicolari alla facciata, dividono l'edificio in 3 campate: sinistra 3,35 u, centrale 3,7 u, destra 3,35 u. Solai da 0,3 u.
- **Quote dei pavimenti**:

  | Livello | Quota | Altezza del piano |
  |---|---|---|
  | Piano terra | 0 | 4,5 u |
  | Primo piano | +4,5 | 3,6 u |
  | Secondo piano | +8,1 | 3,6 u |
  | Terzo piano | +11,7 | 2,8 u |
  | Terrazza | +14,5 | parapetto alto 1 u |

- **Piano terra**: tre portoni ad arco mistilineo "a spalle", larghi 2 u e alti 3,6 u.
  - Il portone centrale si apre e dà sull'androne. I portoni laterali sono chiusi.
  - A sinistra c'è una bottega o magazzino. A destra c'è il vano scala.
  - In fondo all'androne c'è un arco.
- **Rampa dal piano terra al primo piano**: rampa dritta lunga 7,5 u e larga 1,3 u, con 26 alzate. Corre lungo il muro in comune di destra e sale verso il retro.
- **Primo piano**:
  - Nella campata centrale parte la **scala imperiale**. Una rampa centrale larga 1,5 u, con 10 alzate, porta a un pianerottolo intermedio a +6,3, appoggiato al muro del retro. Da lì la scala si divide in due bracci larghi 1 u, con 10 alzate ciascuno, che tornano verso il fronte e arrivano al secondo piano.
  - Nella campata destra c'è un ballatoio con ringhiera affacciato sul vuoto della rampa.
- **Rampa dal secondo al terzo piano**: rampa dritta con 20 alzate, nella campata destra, sopra la prima rampa.
- **Terzo piano**: una scala alla marinara porta alla **botola** (0,8 × 0,8 u) nell'angolo in fondo a destra, che dà sul tetto piano.
- **Facciata**:
  - Primo e secondo piano: finestre da 1,1 × 2 u con persiane lunghe chiuse (tipo A).
  - Terzo piano, campate centrale e destra: finestre ad arco da 1 × 1,6 u con persiane piccole aperte (tipo B).
  - Terzo piano, campata sinistra: persiana lunga da 0,9 × 1,6 u (tipo C).
  - Marcapiani a ogni piano e cornicione sotto il parapetto.
- **Porte interne**: aperture ad arco a tutto sesto, larghe 1 u.

## Prompt di base per l'IA 3D (in inglese)

> Narrow 4-storey Italian historic townhouse, part of a continuous row of identical buildings (blind party walls on both sides), 12 m wide × 10 m deep × 15.5 m tall, flat accessible roof with 1 m parapet and a small roof hatch.
> Ground floor 4.5 m high with three equal mixtilinear "shouldered" arched wooden portals (2 m wide, 3.6 m high); only the central one is open, leading into an entrance hall, the side ones closed.
> First and second floors 3.6 m high, each with three tall windows with closed full-length louvered shutters.
> Third floor 2.8 m high with two small round-arched windows with small open louvered shutters, plus one shuttered window on the left.
> Stone string courses at every floor and a cornice.
> Interior split into three bays by two load-bearing walls. A straight single-flight stair runs along the right party wall from the ground to the first floor. From the first to the second floor there is an imperial staircase: one central flight up to a mid landing against the back wall, splitting into two side flights returning towards the front. Round-arched internal doorways. A ladder leads to the roof hatch.

## Interpretazioni da verificare

1. **Rampa dal secondo al terzo piano**: lo schizzo non la disegna. L'ho messa sopra la prima rampa, nella campata destra.
2. **Prospetto posteriore**: nello schizzo non si vede. L'ho lasciato cieco, salvo l'arco in fondo all'androne.
3. **Finestra a sinistra del terzo piano**: l'ho fatta con persiana lunga, come indica la freccia "persiane lunghe" dello schizzo.
