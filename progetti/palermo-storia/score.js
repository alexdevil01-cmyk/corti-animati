// PALERMO IN 30 SECONDI: the score is the single source of truth for music AND picture.
// A Sicilian tarantella in 6/8 (A minor): 1 bar = 1 s, every era of the city = 3 bars, cut on the downbeat.
(function () {
  const node = typeof require !== 'undefined';
  const U = node ? require('./engine/util') : globalThis.U;
  const MU = node ? require('./engine/music') : globalThis.MUSIC;
  const { m, makeClock, makeChords } = MU;

  const FPS = 30;
  const FORMAT = U.pickFormat('16:9');
  const [W, H] = U.formatSize(FORMAT);
  const SAFE = U.safeArea(W, H);
  const WIDE = W / H > 1.2;
  // 6/8 felt in 2: one beat = a dotted quarter (0.5 s), one bar = 1 s, one eighth = 1/6 s
  const clock = makeClock({ bpm: 120, offset: 0.5, beatsPerBar: 2 });
  const { T, BEAT } = clock;
  const E8 = BEAT / 3; // one eighth note
  const T8 = (bar, step) => T(bar) + step * E8;
  const DURATION = 30;

  // ---------- the story: 7 eras, 3 bars each ----------
  const ERAS = [
    { key: 'fenici', year: '734 a.C.', title: 'I Fenici', lines: ['Fondano Ziz, "il fiore":', 'un porto tra due fiumi.'], bg: '#2F6F8F', accent: '#7A3A7E' },
    { key: 'romani', year: '254 a.C.', title: 'I Romani', lines: ['Conquistano Panormus,', '"tutto porto".'], bg: '#9A4E36', accent: '#E8B04B' },
    { key: 'arabi', year: '831', title: 'Gli Arabi', lines: ['Nasce Balarm: giardini,', 'agrumi, cupole e mercati.'], bg: '#2E7A5E', accent: '#D9573F' },
    { key: 'normanni', year: '1072', title: 'I Normanni', lines: ['Con Ruggero II è capitale', 'di un regno: mosaici d\'oro.'], bg: '#2B3A73', accent: '#F2B84B' },
    { key: 'vespri', year: '1282', title: 'Vespri e Spagnoli', lines: ['La rivolta dei Vespri,', 'poi secoli di Barocco.'], bg: '#7A2E3E', accent: '#F2B84B' },
    { key: 'garibaldi', year: '1860', title: 'Garibaldi', lines: ['I Mille entrano in città:', 'Palermo diventa Italia.'], bg: '#3E6B3A', accent: '#C8322B' },
    { key: 'oggi', year: 'OGGI', title: 'Palermo oggi', lines: ['Teatro Massimo, mercati, arancine:', 'arabo-normanna e UNESCO.'], bg: '#C46A2E', accent: '#F6E3B0' },
  ].map((e, i) => ({ ...e, i, bar: 2 + i * 3, t0: T(2 + i * 3), t1: T(5 + i * 3) }));

  const ev = {
    title: T(0), // the title card lands on the first downbeat
    sub: T8(0, 3),
    lettersAt: T(23), // P-A-L-E-R-M-O stamped on eighth notes
    breath: T(23) - E8, // one eighth of silence before the letters
    final: T(27), // the A major chord: sunburst + confetti (after the last spoken word)
  };
  const LETTERS = 'PALERMO'.split('').map((ch, i) => ({ ch, i, t: ev.lettersAt + i * E8, midi: m(['A4', 'B4', 'C5', 'D5', 'E5', 'G#5', 'A5'][i]) }));
  const endSub = { t: T8(24, 0), text: 'oltre 2.700 anni di storia' };

  // ---------- the voiceover (piper, Italian voice "Paola"): one line per era, just after each stamp ----------
  const VO_AT = 0.18; // the stamp thud hits first, then the voice speaks (never a hit on a word)
  const vo = [
    { at: ev.title + 0.3, text: 'Palermo, in trenta secondi.' },
    ...['La fondano i Fenici: Ziz, il fiore.', 'Poi Roma: Panormus, tutto porto.', 'Gli Arabi: giardini, agrumi e cupole.',
      'I Normanni: un regno e mosaici d\'oro.', 'I Vespri, poi il Barocco spagnolo.', 'Garibaldi e i Mille: arriva l\'Italia.',
      'Oggi: arte, mercati e arancine.'].map((text, i) => ({ at: T(2 + i * 3) + VO_AT, text })),
    { at: ev.lettersAt + 7 * E8 + 0.05, text: 'Palermo: oltre duemilasettecento anni di storia.', display: 'Palermo: oltre 2.700 anni di storia.' },
  ];

  const S = { intro: [0, T(2)] };
  ERAS.forEach((e) => { S[e.key] = [e.t0, e.t1]; });
  S.finale = [T(23), DURATION];

  // ---------- harmony (one chord per bar) ----------
  const prog = ['Am', 'E', /* fenici */ 'Am', 'Am', 'E', /* romani */ 'Am', 'Dm', 'E', /* arabi */ 'Dm', 'Am', 'E', /* normanni */ 'F', 'C', 'E',
    /* vespri */ 'Dm', 'Am', 'E', /* garibaldi */ 'Am', 'Dm', 'E', /* oggi */ 'F', 'G', 'E', /* finale */ 'Am', 'Dm', 'Dm', 'E', 'A', 'A'];
  const { chords, chordAt } = makeChords(clock, {
    Am: { notes: ['A3', 'C4', 'E4'], bass: 'A1' },
    Dm: { notes: ['A3', 'D4', 'F4'], bass: 'D2' },
    E: { notes: ['G#3', 'B3', 'E4'], bass: 'E2' },
    F: { notes: ['A3', 'C4', 'F4'], bass: 'F1' },
    C: { notes: ['G3', 'C4', 'E4'], bass: 'C2' },
    G: { notes: ['G3', 'B3', 'D4'], bass: 'G1' },
    A: { notes: ['A3', 'C#4', 'E4'], bass: 'A1' },
  }, prog.map((c, b) => [b, 0, 2, c]));

  // ---------- mandolin tune: 6 eighths per bar, [note, step, dur] ----------
  const LICK = {
    Am: [['A4', 0, 1], ['C5', 1, 1], ['E5', 2, 1], ['A5', 3, 2], ['E5', 5, 1]],
    Am2: [['E5', 0, 2], ['D5', 2, 1], ['C5', 3, 1], ['B4', 4, 1], ['C5', 5, 1]],
    Dm: [['D5', 0, 1], ['F5', 1, 1], ['A5', 2, 1], ['F5', 3, 2], ['D5', 5, 1]],
    E: [['B4', 0, 1], ['E5', 1, 1], ['G#5', 2, 1], ['B5', 3, 1], ['G#5', 4, 1], ['E5', 5, 1]],
    F: [['C5', 0, 1], ['F5', 1, 1], ['A5', 2, 1], ['C6', 3, 2], ['A5', 5, 1]],
    C: [['C5', 0, 1], ['E5', 1, 1], ['G5', 2, 1], ['C6', 3, 2], ['G5', 5, 1]],
    G: [['B4', 0, 1], ['D5', 1, 1], ['G5', 2, 1], ['B5', 3, 2], ['D5', 5, 1]],
  };
  const melody = [];
  prog.forEach((c, b) => {
    if (b === 23 || b >= 27) return; // the letters bar and the final chord carry their own notes
    const lick = c === 'Am' && b % 2 === 1 ? LICK.Am2 : LICK[c];
    for (const [n, s, d] of lick) melody.push({ t: T8(b, s), dur: d * E8, midi: m(n), bar: b });
  });
  melody.push({ t: ev.final, dur: 2.5, midi: m('A5'), bar: 27 }, { t: ev.final, dur: 2.5, midi: m('C#6'), bar: 27 });

  // ---------- named moments: every cut is a hit (stamp + thud) ----------
  const markers = { title: { t: ev.title, sync: 'av' } };
  ERAS.forEach((e) => { markers[e.key] = { t: e.t0, sync: 'av' }; });
  markers.palermo = { t: ev.lettersAt, sync: 'av' };
  markers.final = { t: ev.final, sync: 'av' };


  const SCORE = { FPS, FORMAT, W, H, SAFE, WIDE, DURATION, clock, T, T8, BEAT, E8, S, m, chords, chordAt, prog, ERAS, ev, LETTERS, endSub, melody, markers, vo };
  if (node) module.exports = SCORE; else globalThis.SCORE = SCORE;
})();
