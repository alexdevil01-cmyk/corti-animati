// THE SONG: a little Sicilian tarantella rendered from score.js -> out/music.wav
const path = require('path');
const { SR, Bus, reverb } = require('./engine/audio/dsp');
const I = require('./engine/audio/instruments');
const MIX = require('./engine/audio/mix');
const Voice = require('./engine/audio/voice');
const MU = require('./engine/music');
const sc = require('./score');
const { T, T8, E8, DURATION, m, ev, ERAS } = sc;

const N = Math.ceil(DURATION * SR);
const bus = () => new Bus(N);
const perc = bus(), bass = bus(), acc = bus(), mando = bus(), color = bus(), fx = bus(), verb = bus();

const eraAt = (t) => ERAS.find((e) => t >= e.t0 && t < e.t1);
const silent = (t) => t >= ev.breath && t < ev.lettersAt + 7 * E8; // the breath and the letters bar

// ---------- groove: tambourine + bass + accordion oom-pa, bars 0..25 ----------
const HAT = [I.hat(false, 11), I.hat(false, 12)], SHK = [I.shaker(1, 15), I.shaker(0.5, 16)];
for (let b = 0; b < 27; b++) {
  const c = sc.chords[b];
  for (let s = 0; s < 6; s++) {
    const t = T8(b, s);
    if (silent(t)) continue;
    // tambourine: jingles on every eighth, accents on the two beats
    perc.addMono(SHK[s % 2], t, s % 3 === 0 ? 0.5 : 0.22, s % 2 ? 0.35 : -0.35);
    if (s % 3 === 0) perc.addMono(HAT[s % 2], t, 0.14, 0.25);
    // bass: root on beat 1, fifth on beat 2
    if (s === 0) bass.addMono(I.bass(c.bass + 12, E8 * 2.4, { sub: 0.7 }), t, 0.55);
    if (s === 3) bass.addMono(I.bass(c.bass + 19, E8 * 2.2, { sub: 0.6 }), t, 0.45);
    // accordion stabs on the off-eighths
    if (s === 1 || s === 2 || s === 4 || s === 5) {
      for (const n of c.notes) { const h = I.harmonium(n, E8 * 0.8, { attack: 0.01, release: 0.06, seed: b * 7 + s }); acc.addStereo(h.L, h.R, t, 0.07); }
    }
    // era colours
    const e = eraAt(t);
    if (!e) continue;
    if (e.key === 'arabi') { const st = ['dha', 'na', 'na', 'ge', 'na', 'tin'][s]; color.addMono(I.tabla(st, { seed: b * 6 + s }), t, s === 0 || s === 3 ? 0.55 : 0.3, -0.2); }
    if (e.key === 'normanni' && s === 0) { const bl = I.bell(MU.mtof(b % 2 ? m('E5') : m('A5')), 2.2); color.addMono(bl, t, 0.16, 0.3); verb.addMono(bl, t, 0.12); }
    if (e.key === 'vespri' && s === 0) { const bl = I.bell(392, 1.8, 3, 2.4); color.addMono(bl, t, 0.18, 0.4); verb.addMono(bl, t, 0.12); }
    if (e.key === 'garibaldi') { color.addMono(I.snare({ tone: 0.3, snap: 0.8, decay: 0.08 }), t, s === 0 ? 0.35 : s === 3 ? 0.25 : 0.1, 0.1); if (s === 5) color.addMono(I.snare({ decay: 0.06 }), t + E8 / 2, 0.12, 0.1); }
    if (e.key === 'oggi' && s === 3) { color.addMono(I.clap(), t, 0.4); verb.addMono(I.clap(), t, 0.15); }
    if (e.key === 'romani' && s === 0) color.addMono(I.tom(110, 0.3), t, 0.35, -0.2);
    if (e.key === 'fenici' && s === 0 && (b - e.bar) === 1) fx.addMono(I.noiseSweep(1.0, 600, 250, { q: 0.7, pink: true }), t, 0.12); // a wave
  }
}

// ---------- mandolin: plucked notes, tremolo on the long ones ----------
for (const n of sc.melody) {
  if (silent(n.t)) continue;
  const pan = 0.15;
  if (n.dur > E8 * 1.5) {
    const k = Math.round(n.dur / (E8 / 3));
    for (let j = 0; j < k; j++) { const g = I.guitar(n.midi, E8 / 2.5, { bright: 0.8, seed: j + n.midi }); mando.addMono(g, n.t + j * E8 / 3, j ? 0.22 : 0.32, pan); verb.addMono(g, n.t + j * E8 / 3, 0.06); }
  } else {
    const g = I.guitar(n.midi, n.dur * 1.2, { bright: 0.85, seed: n.midi });
    mando.addMono(g, n.t, 0.34, pan); verb.addMono(g, n.t, 0.08);
  }
}

// ---------- hits: every cut = a paper stamp (thud + fwip + crash) ----------
const CR = I.crash(18);
const hit = (t, big) => {
  fx.addMono(I.thud(90, 0.09), t, big ? 0.8 : 0.65);
  fx.addMono(I.paperFwip(0.9, Math.round(t * 10)), t - 0.05, 0.2);
  perc.addMono(CR, t, big ? 0.32 : 0.18, 0.2);
};
hit(ev.title, true);
fx.addMono(I.noiseSweep(0.45, 3000, 500, { q: 1, pink: true }), ev.title - 0.45, 0.18); // the title card falls
for (const e of ERAS) hit(e.t0, false);
fx.addMono(I.paperFwip(1.1, 7), ev.sub - 0.03, 0.2);

// ---------- P-A-L-E-R-M-O: each letter a stamp and a note ----------
for (const L of sc.LETTERS) {
  fx.addMono(I.thud(110, 0.06), L.t, 0.55);
  const g = I.guitar(L.midi, 0.35, { bright: 0.9, seed: L.i });
  mando.addMono(g, L.t, 0.4, (L.i - 3) * 0.12);
  const h = I.harmonium(L.midi - 12, 0.3, { attack: 0.005, release: 0.08, seed: L.i }); acc.addStereo(h.L, h.R, L.t, 0.12);
}
fx.addMono(I.paperFwip(1.0, 9), sc.endSub.t - 0.03, 0.18);

// ---------- the final A major chord ----------
hit(ev.final, true);
fx.addMono(I.subBoom(2.0), ev.final, 0.5);
for (const n of ['A3', 'C#4', 'E4', 'A4']) { const h = I.harmonium(m(n), 3.2, { attack: 0.01, release: 0.8, seed: 3 }); acc.addStereo(h.L, h.R, ev.final, 0.12); verb.addStereo(h.L, h.R, ev.final, 0.06); }
bass.addMono(I.bass(m('A1') + 12, 3, { sub: 1 }), ev.final, 0.55);

// ---------- the voiceover: piper + the Italian voice in voices/, the music ducks under it ----------
process.env.PIPER_MODEL = process.env.PIPER_MODEL || path.join(__dirname, 'voices', 'it_IT-paola-medium.onnx');
const vo = Voice.speak(sc.vo, { out: path.join(__dirname, 'out'), length: DURATION, engine: 'piper' });
MIX.duck([perc, bass, acc, mando, color], vo.bus, { depth: 0.5 });

// ---------- mix ----------
const stems = { perc, bass, acc, mando, color, fx, voice: vo.bus, verb: reverb(verb, { room: 0.8, damp: 0.35 }) };
const GAIN = { perc: 0.55, bass: 0.75, acc: 1.4, mando: 1.1, color: 0.9, fx: 0.9, voice: 1.0, verb: 1 };
const out = path.join(__dirname, 'out');
const mix = MIX.mixdown(stems, GAIN, { stemDir: process.env.STEMS ? out : null });
MIX.highpass(mix, 22);
MIX.gate(mix, ev.breath, ev.lettersAt - 0.004);
MIX.fadeOut(mix, DURATION - 1.4, DURATION);
const M = MIX.master(mix, parseFloat(process.env.DRIVE || '0.8'), undefined, { lufs: process.env.LUFS ? parseFloat(process.env.LUFS) : -14 });
MIX.writeWav(path.join(out, 'music.wav'), mix);
console.log(`wrote out/music.wav (${DURATION.toFixed(2)}s${M.lufs !== undefined ? `, ${M.lufs.toFixed(1)} LUFS at drive ${M.drive.toFixed(2)}` : ''})`);
