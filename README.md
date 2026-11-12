# Corti animati con IA

Repository per creare corti animati con Claude Code, sia su questo computer sia nelle sessioni cloud.

## Skill incluse

Si trovano in `.claude/skills/` e Claude le carica da solo quando apri una sessione su questo repository.

| Skill | A cosa serve |
|---|---|
| `video-storyboard` | Crea lo storyboard di ogni scena: l'immagine (`storyboard/scene-XX.png`) e il testo da dare all'IA che genera il video (`storyboard/scene-XX.md`). Tiene uguali personaggi, vestiti, oggetti e luoghi da una scena all'altra. |
| `video-director` | Fa da regista: struttura della storia, ritmo, suono e controllo qualità. Produce il video finale in MP4. |

Fonti originali, nel caso servano aggiornamenti:
- `video-storyboard`: https://skills.sh/agentara/skills
- `video-director`: https://skills.sh/win4r/video-director

## Struttura

```
.claude/skills/   le skill
progetti/         una sottocartella per ogni corto (storia, storyboard, video)
```

## Come iniziare un corto

Apri una sessione di Claude Code su questo repository e scrivi, per esempio:

> Voglio fare un corto di 60 secondi in stile anime. Storia: ... Personaggi: ...
> Crea il progetto in `progetti/nome-del-corto`.

## Aggiornare le skill

Su un computer con Node.js:

```bash
npx skills add agentara/skills@video-storyboard -g -y
npx skills add win4r/video-director@video-director -g -y
```

Poi ricopia le cartelle aggiornate da `~/.agents/skills/` dentro `.claude/skills/`.
