# Palermo in 30 secondi

La storia di Palermo dai Fenici a oggi, in stile ritagli di carta animati. Il video è in 16:9, 1080p, 30 fps.

- **Video finale:** `out/palermo-storia.mp4`
- **Musica:** una tarantella in 6/8 (mandolino, fisarmonica, tamburello) generata da `song.js`. Ogni epoca ha anche un suo colore sonoro: tabla per gli Arabi, campane per Normanni e Vespri, tamburo militare per Garibaldi.
- **Voce:** piper con la voce italiana "Paola" (`voices/it_IT-paola-medium.onnx`, non inclusa nel repository).
- **Sottotitoli:** su una striscia di carta strappata; la parola pronunciata si evidenzia nel colore dell'epoca.

## Rigenerare

```bash
pip install piper-tts
mkdir -p voices && cd voices
curl -LO https://huggingface.co/rhasspy/piper-voices/resolve/main/it/it_IT/paola/medium/it_IT-paola-medium.onnx
curl -LO https://huggingface.co/rhasspy/piper-voices/resolve/main/it/it_IT/paola/medium/it_IT-paola-medium.onnx.json
cd ..
npm run build   # musica + voce, video, mux, controlli
```

La timeline è tutta in `score.js` (testi, anni, tempi). Le scene si disegnano in `film.js`.
