// PALERMO IN 30 SECONDI: paper cut-out history. Every frame is a pure function of t, timed from score.js.
(function () {
  const U = globalThis.U, G = globalThis.G, Ch = globalThis.Ch, S = globalThis.SCORE, Studio = globalThis.Studio, Shots = globalThis.Shots;
  const { T, BEAT, E8, ev, ERAS, clock } = S;
  const { clamp, lerp, ease } = U;
  const W = G.W, H = G.H;
  const GY = 800; // the coastline: buildings and people stand here
  const SEA = 830;
  let VO = null; // out/voice.json: word times for the subtitles

  const pop = (t, t0, d = 0.22) => (t < t0 ? 0 : ease.outBack(clamp((t - t0) / d), 2.4));
  const lum = (hex) => { const n = parseInt(hex.slice(1), 16); return (0.299 * (n >> 16) + 0.587 * ((n >> 8) & 255) + 0.114 * (n & 255)) / 255; };
  const inkOn = (hex) => (lum(hex) > 0.55 ? G.C.ink : '#FFF6E6');
  const hop = (t, amp) => amp * Math.sin(Math.PI * clock.phase(t));
  // grow a cut-out from its base point (x, y)
  function grow(ctx, x, y, k, fn) {
    if (k <= 0.001) return;
    ctx.save(); ctx.translate(x, y); ctx.scale(k, k); fn(ctx); ctx.restore();
  }
  const sh = (hex, k) => G.tint(hex, k);
  const hatch = (hex) => ({ color: 'rgba(40,25,15,0.18)', gap: 8 });

  // ---------- the shared world: paper sky, Monte Pellegrino, the coast and the sea ----------
  function world(ctx, t, bg, seed) {
    G.bg(ctx, bg);
    // a paper sun
    G.ellipse(ctx, 1760, 250, 70, 70, { fill: '#F6D27A', lw: 4, seed: seed + 1, hatch: { color: 'rgba(160,90,20,0.2)', gap: 7 } });
    // Monte Pellegrino, the mountain that watches over every era
    G.poly(ctx, [[1380, GY + 10], [1470, 610], [1560, 520], [1640, 470], [1720, 480], [1800, 540], [1880, 600], [1990, 640], [1990, GY + 10]],
      { fill: sh(bg, -0.28), lw: 4, seed: seed + 2, hatch: { color: 'rgba(0,0,0,0.16)', gap: 9, angle: 0.6 } });
    // the coast
    G.poly(ctx, [[-40, GY], [1990, GY - 6], [1990, SEA + 20], [-40, SEA + 20]], { fill: '#E6D3A8', lw: 4, seed: seed + 3, hatch: { color: 'rgba(120,80,40,0.16)', gap: 8 } });
    // the sea, in torn strips that rock on the beat
    const cols = ['#2C6A93', '#245A80', '#1D4B6C'];
    for (let i = 0; i < 3; i++) {
      const y0 = SEA + i * 85, dx = Math.sin(t * 2.2 + i) * 18;
      const pts = [[-60 + dx, y0]];
      for (let x = -60; x <= 2000; x += 120) pts.push([x + dx, y0 + Math.sin(x / 90 + t * 3 + i * 2) * 9]);
      pts.push([2000 + dx, H + 40], [-60 + dx, H + 40]);
      G.poly(ctx, pts, { fill: cols[i], lw: 4, seed: seed + 10 + i });
    }
  }

  // ---------- the era card: the year stamps on the downbeat, the title slides in after it ----------
  function eraCard(ctx, t, e) {
    const k = t < e.t0 ? 0 : lerp(2.4, 1, ease.outBack(clamp((t - e.t0) / 0.14), 2));
    ctx.save(); ctx.translate(410, 250); ctx.rotate(-0.05); ctx.scale(k, k);
    G.tornPaper(ctx, -270, -100, 540, 200, { fill: '#F6F0E2', seed: 30 + e.i, tear: 6 });
    G.tape(ctx, -220, -110, 110, 34, -0.3, 40 + e.i);
    G.text(ctx, e.year, 0, 44, { size: e.year.length > 6 ? 104 : 130, fam: 'Bungee', weight: 400, color: G.C.ink, align: 'center' });
    ctx.restore();
    const p = ease.outCubic(clamp((t - e.t0 - 2 * E8) / 0.3));
    if (p > 0) {
      ctx.save(); ctx.translate(lerp(-500, 420, p), 440); ctx.rotate(0.025);
      G.tornPaper(ctx, -300, -70, 600, 135, { fill: e.accent, seed: 50 + e.i, tear: 5 });
      G.text(ctx, e.title, 0, 26, { size: e.title.length > 12 ? 62 : 78, fam: 'Permanent Marker', weight: 400, color: inkOn(e.accent), align: 'center' });
      ctx.restore();
    }
  }

  // ---------- a paper timeline at the top: 7 pins, the current one big ----------
  function timeline(ctx, t, cur) {
    const x0 = 940, x1 = 1640, y = 92;
    G.line(ctx, [[x0 - 30, y], [x1 + 30, y]], { color: 'rgba(255,246,230,0.75)', lw: 5, seed: 3 });
    ERAS.forEach((e, i) => {
      const x = lerp(x0, x1, i / (ERAS.length - 1));
      const on = i === cur, past = i < cur;
      const r = on ? 18 + 6 * Math.exp(-(t - e.t0) * 6) : 10;
      G.ellipse(ctx, x, y, r, r, { fill: on ? e.accent : past ? '#FFF6E6' : 'rgba(255,246,230,0.25)', lw: 3, seed: 70 + i });
    });
  }

  // ---------- the seven scenes ----------
  const SCENES = {
    fenici(ctx, t, e) {
      // Ziz, "the flower"
      grow(ctx, 860, GY + 4, pop(t, e.t0 + 5 * E8), (c) => {
        G.line(c, [[0, 0], [6, -60], [0, -110]], { color: '#3E7A3A', lw: 7, seed: 5 });
        for (let i = 0; i < 6; i++) { const a = (i / 6) * Math.PI * 2 + t; G.ellipse(c, Math.cos(a) * 30, -130 + Math.sin(a) * 30, 22, 22, { fill: '#E8718D', lw: 3, seed: 80 + i }); }
        G.ellipse(c, 0, -130, 18, 18, { fill: '#F2B84B', lw: 3, seed: 90 });
      });
      // a Phoenician ship with a purple sail sails into the port
      const u = clamp((t - e.t0) / (e.t1 - e.t0));
      const x = lerp(1560, 1230, ease.outCubic(u)), y = SEA + 30 + Math.sin(t * 3) * 8;
      grow(ctx, x, y, pop(t, e.t0 + E8), (c) => {
        c.rotate(Math.sin(t * 2.5) * 0.03);
        for (let i = 0; i < 5; i++) G.line(c, [[-130 + i * 60, 10], [-170 + i * 60, 90]], { color: '#5A3A22', lw: 6, seed: 100 + i });
        G.line(c, [[0, -30], [0, -380]], { color: '#5A3A22', lw: 9, seed: 110 });
        const sk = 0.6 + 0.4 * pop(t, e.t0 + 3 * E8);
        G.poly(c, [[-160, -370], [160, -370], [170 * sk + 0, -120], [-170 * sk, -120]], { fill: e.accent, lw: 4, seed: 111, hatch: { color: 'rgba(0,0,0,0.18)', gap: 9 } });
        for (let i = 0; i < 3; i++) G.line(c, [[-160 + i * 4, -300 + i * 70], [160 - i * 4, -300 + i * 70]], { color: '#F2D9A8', lw: 6, seed: 112 + i });
        G.poly(c, [[-250, -40], [250, -40], [200, 40], [-200, 40]], { fill: '#8A5A3A', lw: 5, seed: 115, hatch: hatch() });
        G.poly(c, [[250, -40], [300, -130], [325, -120], [270, -40]], { fill: '#8A5A3A', lw: 4, seed: 116 });
        G.poly(c, [[-250, -40], [-300, -120], [-275, -125], [-230, -40]], { fill: '#8A5A3A', lw: 4, seed: 117 });
        G.ellipse(c, 205, -10, 16, 12, { fill: '#FFF6E6', lw: 3, seed: 118 }); G.ellipse(c, 208, -10, 6, 6, { fill: G.C.ink, lw: 1, seed: 119 });
      });
    },
    romani(ctx, t, e) {
      const cx = 1180;
      grow(ctx, cx, GY + 4, pop(t, e.t0 + E8), (c) => {
        G.rrect(c, -330, -50, 660, 50, 6, { fill: '#E9DFC8', lw: 4, seed: 120, hatch: hatch() });
        G.rrect(c, -300, -90, 600, 44, 6, { fill: '#F1E8D4', lw: 4, seed: 121 });
      });
      for (let i = 0; i < 6; i++) {
        grow(ctx, cx - 250 + i * 100, GY - 86, pop(t, e.t0 + 2 * E8 + i * 0.05), (c) => {
          G.rrect(c, -22, -270, 44, 270, 6, { fill: '#F4EDE0', lw: 4, seed: 130 + i, hatch: { color: 'rgba(80,60,40,0.18)', gap: 10, angle: 1.57 } });
          G.rrect(c, -32, -290, 64, 24, 5, { fill: '#E9DFC8', lw: 3, seed: 140 + i });
        });
      }
      grow(ctx, cx, GY - 376, pop(t, e.t0 + 4 * E8), (c) => {
        G.rrect(c, -320, -50, 640, 50, 6, { fill: '#E9DFC8', lw: 4, seed: 150 });
        G.poly(c, [[-340, -50], [0, -190], [340, -50]], { fill: '#F4EDE0', lw: 4, seed: 151, hatch: hatch() });
        G.text(c, 'SPQR', 0, -78, { size: 52, fam: 'Bungee', weight: 400, color: e.bg, align: 'center' });
      });
      // a cypress
      grow(ctx, 1640, GY + 4, pop(t, e.t0 + 5 * E8), (c) => {
        G.line(c, [[0, 0], [0, -60]], { color: '#5A3A22', lw: 10, seed: 160 });
        G.ellipse(c, 0, -230, 60, 190, { fill: '#2F5E3A', lw: 4, seed: 161, hatch: { color: 'rgba(0,0,0,0.2)', gap: 8 } });
      });
    },
    arabi(ctx, t, e) {
      const cx = 1200;
      // an orange tree: agrumi
      grow(ctx, 820, GY + 4, pop(t, e.t0 + 4 * E8), (c) => {
        G.line(c, [[0, 0], [4, -120]], { color: '#6A4426', lw: 14, seed: 170 });
        G.ellipse(c, 0, -200, 120, 100, { fill: '#3E8A4A', lw: 4, seed: 171, hatch: { color: 'rgba(0,0,0,0.16)', gap: 8 } });
        for (let i = 0; i < 9; i++) G.ellipse(c, Math.cos(i * 2.4) * 80, -200 + Math.sin(i * 1.7) * 60, 15, 15, { fill: '#F08A24', lw: 3, seed: 172 + i });
      });
      grow(ctx, cx, GY + 4, pop(t, e.t0 + E8), (c) => {
        G.rrect(c, -250, -280, 500, 280, 4, { fill: '#E8CFA0', lw: 5, seed: 180, hatch: hatch() });
        for (let i = 0; i < 3; i++) {
          const x = -150 + i * 150;
          G.poly(c, [[x - 34, -10], [x - 34, -120], [x, -165], [x + 34, -120], [x + 34, -10]], { fill: '#5A3A2A', lw: 4, seed: 181 + i });
        }
        G.rrect(c, -240, -300, 480, 26, 4, { fill: '#D9BC88', lw: 4, seed: 185 });
      });
      // three red domes, like San Giovanni degli Eremiti
      [[-150, 0.85], [0, 1.15], [150, 0.85]].forEach(([dx, s], i) => {
        grow(ctx, cx + dx, GY - 296, pop(t, e.t0 + (2 + i) * E8), (c) => {
          G.rrect(c, -62 * s, -30 * s, 124 * s, 30 * s, 3, { fill: '#E8CFA0', lw: 4, seed: 190 + i });
          G.poly(c, [[-70 * s, -28 * s], [-62 * s, -90 * s], [-30 * s, -128 * s], [0, -138 * s], [30 * s, -128 * s], [62 * s, -90 * s], [70 * s, -28 * s]],
            { fill: e.accent, lw: 4, seed: 193 + i, hatch: { color: 'rgba(80,10,0,0.25)', gap: 8 } });
        });
      });
      // a palm tree
      grow(ctx, 1600, GY + 4, pop(t, e.t0 + 5 * E8), (c) => {
        G.line(c, [[0, 0], [10, -120], [30, -250], [50, -360]], { color: '#7A5230', lw: 22, seed: 200 });
        for (let i = 0; i < 6; i++) {
          const a = -Math.PI / 2 + (i - 2.5) * 0.55 + Math.sin(t * 2 + i) * 0.05;
          c.save(); c.translate(50, -360); c.rotate(a);
          G.ellipse(c, 85, 0, 95, 22, { fill: '#2F7A3A', lw: 3, seed: 201 + i }); c.restore();
        }
      });
    },
    normanni(ctx, t, e) {
      const cx = 1200;
      grow(ctx, cx, GY + 4, pop(t, e.t0 + E8), (c) => {
        const arch = [[-280, 0], [-280, -380]];
        for (let i = 0; i <= 16; i++) { const a = Math.PI + (i / 16) * Math.PI; arch.push([Math.cos(a) * 280, -380 + Math.sin(a) * 200]); }
        arch.push([280, 0]);
        G.poly(c, arch, { fill: '#2B3A73', lw: 6, seed: 210 });
        const inner = arch.map(([x, y]) => [x * 0.86, y * 0.93]);
        G.poly(c, inner, { fill: '#E2B33F', lw: 4, seed: 211 });
        // golden mosaic tiles light up row by row, on the eighths
        const rows = Math.floor(clamp((t - e.t0 - 2 * E8) / (6 * E8)) * 14);
        for (let r = 0; r < rows; r++) for (let q = 0; q < 11; q++) {
          const x = -215 + q * 39, y = -40 - r * 38;
          if (y < -370 && Math.abs(x) > 230 - (y + 370) * -0.6) continue;
          c.fillStyle = ['#F2C94C', '#E0A72E', '#F6DE8A', '#C98F22'][Math.floor(G.rnd(r, q, 3) * 4)];
          c.fillRect(x, y, 33, 32);
        }
      });
      // the crown of Ruggero II
      grow(ctx, cx, GY - 270, pop(t, e.t0 + 4 * E8), (c) => {
        c.translate(0, hop(t, -10));
        G.poly(c, [[-110, 0], [-125, -120], [-60, -60], [0, -150], [60, -60], [125, -120], [110, 0]], { fill: '#F2B84B', lw: 5, seed: 220, hatch: { color: 'rgba(120,60,0,0.25)', gap: 8 } });
        [[-60, -30, '#C8322B'], [0, -40, '#2E7A9E'], [60, -30, '#3E8A4A']].forEach(([x, y, col], i) => G.ellipse(c, x, y, 14, 14, { fill: col, lw: 3, seed: 221 + i }));
      });
      for (let i = 0; i < 4; i++) {
        const a = t - (e.t0 + (5 + i * 0.5) * E8);
        if (a > 0) G.star(ctx, cx + [-380, 380, -330, 340][i], GY - [520, 480, 220, 260][i], 26 * ease.outBack(clamp(a / 0.25), 3), { fill: '#FFF1D2', rot: t + i, seed: 230 + i });
      }
    },
    vespri(ctx, t, e) {
      // the bell tower: the bell of the Vespers swings on every beat
      grow(ctx, 960, GY + 4, pop(t, e.t0 + E8), (c) => {
        G.rrect(c, -90, -520, 180, 520, 4, { fill: '#D9B98A', lw: 5, seed: 240, hatch: hatch() });
        G.poly(c, [[-110, -520], [0, -640], [110, -520]], { fill: '#9A4E36', lw: 5, seed: 241 });
        G.poly(c, [[-55, -330], [-55, -440], [0, -480], [55, -440], [55, -330]], { fill: '#3A2A2A', lw: 4, seed: 242 });
        c.save(); c.translate(0, -460); c.rotate(Math.sin(Math.PI * clock.beatPos(t)) * 0.5);
        G.poly(c, [[-34, 90], [-26, 30], [-14, 10], [14, 10], [26, 30], [34, 90]], { fill: '#F2B84B', lw: 4, seed: 243 });
        c.restore();
      });
      // a Baroque facade with niches and statues (in the spirit of the Quattro Canti)
      grow(ctx, 1380, GY + 4, pop(t, e.t0 + 2 * E8), (c) => {
        G.rrect(c, -260, -520, 520, 520, 4, { fill: '#E8C48A', lw: 5, seed: 250, hatch: hatch() });
        for (let r = 0; r < 3; r++) {
          const y = -r * 170;
          G.rrect(c, -275, y - 20, 550, 22, 4, { fill: '#D2A86A', lw: 4, seed: 251 + r });
          for (let q = 0; q < 2; q++) {
            const x = q ? 130 : -130;
            G.poly(c, [[x - 45, y - 30], [x - 45, y - 120], [x, y - 150], [x + 45, y - 120], [x + 45, y - 30]], { fill: '#8A5A3A', lw: 3, seed: 254 + r * 2 + q });
            if (t > e.t0 + (3 + r) * E8) { G.ellipse(c, x, y - 108, 13, 13, { fill: '#F4EDE0', lw: 3, seed: 260 + r * 2 + q }); G.rrect(c, x - 18, y - 95, 36, 62, 10, { fill: '#F4EDE0', lw: 3, seed: 266 + r * 2 + q }); }
          }
          for (const x of [-230, -10, 10, 230]) G.line(c, [[x, y - 30], [x, y - 160]], { color: '#B88A50', lw: 7, seed: 270 + r + x });
        }
        G.poly(c, [[-200, -520], [-120, -600], [0, -630], [120, -600], [200, -520]], { fill: '#E8C48A', lw: 5, seed: 280 });
      });
    },
    garibaldi(ctx, t, e) {
      // the Mille, in red shirts, behind
      for (let i = 0; i < 7; i++) {
        grow(ctx, 860 + i * 120, GY - 10, pop(t, e.t0 + (3 + i * 0.3) * E8) * 0.8, (c) => {
          c.translate(0, hop(t + i * 0.13, -8));
          G.rrect(c, -34, -150, 68, 120, 22, { fill: '#B8302A', lw: 4, seed: 290 + i });
          G.ellipse(c, 0, -180, 28, 30, { fill: '#E3B48A', lw: 3, seed: 300 + i });
        });
      }
      // the flag of united Italy, waving
      grow(ctx, 1500, GY + 4, pop(t, e.t0 + 4 * E8), (c) => {
        G.line(c, [[0, 0], [0, -520]], { color: '#5A3A22', lw: 10, seed: 310 });
        ['#2E8B4A', '#F6F0E2', '#C8322B'].forEach((col, i) => {
          const pts = [];
          const xa = i * 70, xb = (i + 1) * 70;
          for (let k = 0; k <= 4; k++) { const x = lerp(xa, xb, k / 4); pts.push([x, -510 + Math.sin(x / 40 - t * 6) * 12 * (x / 210)]); }
          for (let k = 4; k >= 0; k--) { const x = lerp(xa, xb, k / 4); pts.push([x, -370 + Math.sin(x / 40 - t * 6) * 12 * (x / 210)]); }
          G.poly(c, pts, { fill: col, lw: 4, seed: 311 + i });
        });
      });
      // Garibaldi: red shirt, beard, cheering on the beat
      const k = pop(t, e.t0 + E8);
      if (k > 0) Ch.person(ctx, { x: 1260, y: GY + 6 - hop(t, 18), pose: 'stand', s: 1.05 * k, gesture: 'cheer', eyes: 'happy', mouth: 'grin', brows: 'up',
        style: { skin: '#E8B98E', hair: '#A0693A', hairStyle: 'short', facialHair: 'beard', outfit: 'shirt', shirt: '#C8322B', collar: '#F6F0E2', bottoms: 'pants', shorts: '#3A3F5A', build: 'regular', sleeves: 'long' } });
    },
    oggi(ctx, t, e) {
      const cx = 1150;
      // Teatro Massimo: the dome rises, then the portico
      grow(ctx, cx, GY - 330, pop(t, e.t0 + 2 * E8), (c) => {
        const dome = [];
        for (let i = 0; i <= 16; i++) { const a = Math.PI + (i / 16) * Math.PI; dome.push([Math.cos(a) * 260, Math.sin(a) * 210]); }
        G.poly(c, dome, { fill: '#7E8E7A', lw: 5, seed: 320, hatch: { color: 'rgba(0,0,0,0.2)', gap: 9 } });
        for (let i = 1; i < 6; i++) { const x = -260 + i * 86.6; G.line(c, [[x, 0], [x * 0.35, -195]], { color: '#5E6E5A', lw: 4, seed: 321 + i }); }
        G.rrect(c, -40, -270, 80, 70, 8, { fill: '#7E8E7A', lw: 4, seed: 327 });
      });
      grow(ctx, cx, GY + 4, pop(t, e.t0 + E8), (c) => {
        G.rrect(c, -360, -340, 720, 340, 4, { fill: '#EADBC0', lw: 5, seed: 330, hatch: hatch() });
        G.rrect(c, -380, -40, 760, 40, 4, { fill: '#D8C6A2', lw: 4, seed: 331 });
        for (let i = 0; i < 6; i++) G.rrect(c, -250 + i * 100 - 18, -300, 36, 260, 5, { fill: '#F6F0E2', lw: 3, seed: 332 + i });
        G.poly(c, [[-300, -300], [0, -420], [300, -300]], { fill: '#EADBC0', lw: 5, seed: 340 });
      });
      // an arancina, hopping on the beat
      grow(ctx, 1640, GY + 6 - hop(t, 50), pop(t, e.t0 + 4 * E8), (c) => {
        const sq = Math.max(0, 1 - clock.phase(t) * 5);
        c.scale(1 + 0.12 * sq, 1 - 0.12 * sq);
        G.poly(c, [[-80, -10], [-95, -70], [-70, -140], [0, -210], [70, -140], [95, -70], [80, -10], [0, 4]], { fill: '#E39A2F', lw: 5, seed: 350, hatch: { color: 'rgba(120,50,0,0.3)', gap: 6 } });
        G.text(c, '^  ^', 0, -86, { size: 46, fam: 'Gochi Hand', weight: 400, color: G.C.ink, align: 'center', boil: 0.3 });
        G.line(c, [[-22, -66], [0, -50], [22, -66]], { color: G.C.ink, lw: 5, seed: 351 });
        G.ellipse(c, -50, -70, 12, 8, { fill: 'rgba(232,113,141,0.6)', lw: 0, seed: 352 }); G.ellipse(c, 50, -70, 12, 8, { fill: 'rgba(232,113,141,0.6)', lw: 0, seed: 353 });
      });
    },
  };

  function eraShot(e) {
    return (ctx, t) => {
      world(ctx, t, e.bg, 10 + e.i * 50);
      timeline(ctx, t, e.i);
      SCENES[e.key](ctx, t, e);
      eraCard(ctx, t, e);
    };
  }

  // ---------- the title: the card drops onto the first downbeat ----------
  function titleShot(ctx, t) {
    world(ctx, t, '#2F6F8F', 5);
    const u = clamp((t - (ev.title - 0.45)) / 0.45);
    const y = t < ev.title ? lerp(-300, 400, ease.inQuad(u)) : 400;
    const sq = t >= ev.title ? Math.exp(-(t - ev.title) * 9) * Math.cos((t - ev.title) * 30) : 0;
    ctx.save(); ctx.translate(W / 2 - 180, y); ctx.rotate(-0.04); ctx.scale(1 + 0.08 * sq, 1 - 0.1 * sq);
    G.tornPaper(ctx, -520, -150, 1040, 270, { fill: '#F6F0E2', seed: 3, tear: 7 });
    G.tape(ctx, -470, -165, 140, 40, -0.25, 4); G.tape(ctx, 340, -165, 140, 40, 0.25, 5);
    G.text(ctx, 'PALERMO', 0, 62, { size: 180, fam: 'Bungee', weight: 400, color: '#C8322B', align: 'center' });
    ctx.restore();
    const p = pop(t, ev.sub);
    if (p > 0) {
      ctx.save(); ctx.translate(W / 2 - 180, 640); ctx.rotate(0.03); ctx.scale(p, p);
      G.tornPaper(ctx, -330, -60, 660, 110, { fill: '#F2B84B', seed: 6, tear: 5 });
      G.text(ctx, 'dai Fenici a oggi', 0, 24, { size: 66, fam: 'Permanent Marker', weight: 400, color: G.C.ink, align: 'center' });
      ctx.restore();
    }
  }

  // ---------- the finale: P-A-L-E-R-M-O stamped on eighth notes, the sunburst on the A major chord ----------
  function finaleShot(ctx, t) {
    G.bg(ctx, '#27305C');
    if (t >= ev.final) {
      ctx.save(); ctx.translate(W / 2, 430); ctx.rotate((t - ev.final) * 0.35);
      for (let i = 0; i < 24; i++) {
        ctx.fillStyle = i % 2 ? '#F2B84B' : '#E0703E';
        const a0 = (i / 24) * Math.PI * 2, a1 = ((i + 1) / 24) * Math.PI * 2;
        ctx.beginPath(); ctx.moveTo(0, 0); ctx.lineTo(Math.cos(a0) * 2400, Math.sin(a0) * 2400); ctx.lineTo(Math.cos(a1) * 2400, Math.sin(a1) * 2400); ctx.fill();
      }
      ctx.restore();
    }
    const cols = ['#C8322B', '#F2B84B', '#2E7A5E', '#E8718D', '#2F6F8F', '#E0703E', '#7A3A7E'];
    const cw = 205, x0 = W / 2 - (cw * 7) / 2 + cw / 2;
    for (const L of S.LETTERS) {
      if (t < L.t) continue;
      const k = lerp(2.6, 1, ease.outBack(clamp((t - L.t) / 0.13), 2));
      const rot = (G.rnd(L.i, 9) - 0.5) * 0.3;
      const bob = t >= ev.final ? hop(t + L.i * 0.07, -14) : 0;
      ctx.save(); ctx.translate(x0 + L.i * cw, 430 + bob); ctx.rotate(rot); ctx.scale(k, k);
      G.tornPaper(ctx, -92, -115, 184, 230, { fill: cols[L.i], seed: 400 + L.i, tear: 5 });
      G.text(ctx, L.ch, 0, 64, { size: 180, fam: 'Bungee', weight: 400, color: inkOn(cols[L.i]), align: 'center' });
      ctx.restore();
    }
    const p = 0; // the spoken line's subtitle says it (no duplicate card)
    if (p > 0) {
      ctx.save(); ctx.translate(W / 2, 690); ctx.rotate(-0.02); ctx.scale(p, p);
      G.tornPaper(ctx, -440, -62, 880, 115, { fill: '#F6F0E2', seed: 420, tear: 5 });
      G.text(ctx, S.endSub.text, 0, 24, { size: 64, fam: 'Permanent Marker', weight: 400, color: G.C.ink, align: 'center' });
      ctx.restore();
    }
    if (t >= ev.final) G.confetti(ctx, t, ev.final, { n: 160, seed: 7, spawn: 2 });
  }

  // ---------- subtitles: a torn paper strip, the spoken word in the era's colour ----------
  function subtitles(ctx, t) {
    if (!VO || !VO.lines) return;
    const i = VO.lines.findIndex((l) => t >= l.t - 0.08 && t < l.end + 0.3);
    if (i < 0) return;
    const l = VO.lines[i];
    const disp = (S.vo[i] && S.vo[i].display) || null;
    let words = (l.words && l.words.length ? l.words : l.text.split(' ').map((w) => ({ w, t: l.t, end: l.end })));
    if (disp) words = words.map((w) => ({ ...w, w: w.w.replace(/duemilasettecento/i, '2.700') }));
    const era = ERAS.find((e) => t >= e.t0 && t < e.t1);
    const hi = era ? (lum(era.accent) > 0.6 ? sh(era.accent, -0.55) : era.accent) : '#C8322B';
    const size = 54, fam = 'Patrick Hand', sp = G.measure(ctx, ' ', size, fam, 400);
    const ws = words.map((w) => G.measure(ctx, w.w, size, fam, 400));
    const total = ws.reduce((a, b) => a + b, 0) + sp * (ws.length - 1);
    const k = pop(t, l.t - 0.08, 0.2);
    const out = clamp((l.end + 0.3 - t) / 0.15);
    ctx.save(); ctx.globalAlpha *= out;
    ctx.translate(W / 2, 985); ctx.rotate(-0.012 + (i % 2) * 0.02); ctx.scale(k, k);
    G.tornPaper(ctx, -total / 2 - 46, -52, total + 92, 96, { fill: '#F6F0E2', seed: 500 + i, tear: 4 });
    G.tape(ctx, -total / 2 - 70, -50, 90, 28, -0.4, 510 + i);
    let x = -total / 2;
    words.forEach((w, j) => {
      const on = t >= w.t && t < w.end;
      G.text(ctx, w.w, x, 18, { size, fam, weight: 400, color: on ? hi : G.C.ink, boil: 0.4 });
      if (on) G.line(ctx, [[x, 30], [x + ws[j], 30]], { color: hi, lw: 5, seed: 520 + j });
      x += ws[j] + sp;
    });
    ctx.restore();
  }

  const shots = [{ at: 0, draw: titleShot, cam: Shots.push(1.0, 1.04) }];
  for (const e of ERAS) shots.push({ at: e.t0, draw: eraShot(e), cam: Shots.push(1.0, 1.035) });
  shots.push({ at: T(23), draw: finaleShot, cam: Shots.combine(Shots.push(1.0, 1.05), Shots.shake(16, ev.final, 6)) });
  const film = Shots.film(shots, { end: S.DURATION });

  Studio.film({
    async init() { VO = await Studio.loadJSON('out/voice.json'); },
    draw(ctx, t) {
      if (t < 0.15) return;
      film(ctx, t);
      subtitles(ctx, t);
      const flash = t >= ev.final ? 0.8 * Math.exp(-(t - ev.final) * 12) : 0;
      if (flash > 0.01) { ctx.fillStyle = `rgba(255,250,235,${flash})`; ctx.fillRect(0, 0, W, H); }
    },
    post: { paper: 0.55, vignette: 0.3, grain: 0.06 },
    fadeOut: 1.2,
  });
})();
