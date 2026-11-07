// Generates the illustrated placeholder photos used by the demo (mock) catalog.
// Run from shop-site/: node scripts/generate-mock-images.mjs
// Output: public/mock/products/<slug>-1.svg (product shot) and -2.svg (texture close-up).
// These are drawings, not real photos. Replace them with real photos via the admin app.
import { mkdirSync, writeFileSync } from 'node:fs'
import { dirname, join } from 'node:path'
import { fileURLToPath } from 'node:url'
import { products } from '../src/mock/catalog-data.js'

const root = join(dirname(fileURLToPath(import.meta.url)), '..')
const outDir = join(root, 'public', 'mock', 'products')
mkdirSync(outDir, { recursive: true })

const W = 800
const H = 600
const COS = Math.cos(Math.PI / 6)
const SIN = 0.5

// ---------- colour helpers ----------

function hexToRgb(hex) {
  const n = parseInt(hex.slice(1), 16)
  return [(n >> 16) & 255, (n >> 8) & 255, n & 255]
}

function shade(hex, amount) {
  const [r, g, b] = hexToRgb(hex)
  const f = (c) => {
    const v = amount >= 0 ? c + (255 - c) * amount : c * (1 + amount)
    return Math.max(0, Math.min(255, Math.round(v)))
  }
  return `#${[f(r), f(g), f(b)].map((c) => c.toString(16).padStart(2, '0')).join('')}`
}

// ---------- isometric primitives ----------

function makeIso(cx, cy, s) {
  return (x, y, z) => [cx + (x - y) * COS * s, cy + (x + y) * SIN * s - z * s]
}

function poly(points, fill, extra = '') {
  const d = points.map(([x, y]) => `${x.toFixed(1)},${y.toFixed(1)}`).join(' ')
  return `<polygon points="${d}" fill="${fill}" ${extra}/>`
}

function cuboid(iso, x, y, z, w, d, h, color, opts = {}) {
  const stroke = opts.stroke ?? 'rgba(11,17,33,0.35)'
  const sw = opts.strokeWidth ?? 1.2
  const extra = `stroke="${stroke}" stroke-width="${sw}" stroke-linejoin="round"`
  const top = [iso(x, y, z + h), iso(x + w, y, z + h), iso(x + w, y + d, z + h), iso(x, y + d, z + h)]
  const right = [iso(x + w, y, z), iso(x + w, y + d, z), iso(x + w, y + d, z + h), iso(x + w, y, z + h)]
  const left = [iso(x, y + d, z), iso(x + w, y + d, z), iso(x + w, y + d, z + h), iso(x, y + d, z + h)]
  return [
    poly(left, shade(color, -0.32), extra),
    poly(right, shade(color, -0.12), extra),
    poly(top, shade(color, 0.14), extra),
  ].join('')
}

// Draw items back-to-front so nearer boxes cover the ones behind.
function stack(iso, boxes, color, opts) {
  return boxes
    .slice()
    .sort((a, b) => a[0] + a[1] + a[2] - (b[0] + b[1] + b[2]))
    .map(([x, y, z, w, d, h, c]) => cuboid(iso, x, y, z, w, d, h, c ?? color, opts))
    .join('')
}

function cylinderV(cx, baseY, rx, ry, height, color) {
  const top = baseY - height
  return [
    `<path d="M${cx - rx},${top} L${cx - rx},${baseY} A${rx},${ry} 0 0 0 ${cx + rx},${baseY} L${cx + rx},${top} Z" fill="url(#cylV)" />`,
    `<path d="M${cx - rx},${top} L${cx - rx},${baseY} A${rx},${ry} 0 0 0 ${cx + rx},${baseY} L${cx + rx},${top} Z" fill="${color}" opacity="0.85"/>`,
    `<path d="M${cx - rx},${top} L${cx - rx},${baseY} A${rx},${ry} 0 0 0 ${cx + rx},${baseY} L${cx + rx},${top} Z" fill="url(#cylShade)"/>`,
    `<ellipse cx="${cx}" cy="${top}" rx="${rx}" ry="${ry}" fill="${shade(color, 0.22)}" stroke="rgba(11,17,33,0.3)"/>`,
  ].join('')
}

function tubeH(x1, x2, cy, r, color, inner = true) {
  const ry = r
  const rx = r * 0.42
  return [
    `<rect x="${x1}" y="${cy - r}" width="${x2 - x1}" height="${r * 2}" fill="${color}"/>`,
    `<rect x="${x1}" y="${cy - r}" width="${x2 - x1}" height="${r * 2}" fill="url(#tubeShade)"/>`,
    `<ellipse cx="${x1}" cy="${cy}" rx="${rx}" ry="${ry}" fill="${shade(color, -0.25)}"/>`,
    `<ellipse cx="${x2}" cy="${cy}" rx="${rx}" ry="${ry}" fill="${shade(color, 0.18)}" stroke="rgba(11,17,33,0.3)"/>`,
    inner ? `<ellipse cx="${x2}" cy="${cy}" rx="${rx * 0.7}" ry="${ry * 0.7}" fill="#0b1121" opacity="0.85"/>` : '',
  ].join('')
}

// ---------- material drawings (centre of the floor is 400, 430) ----------

const drawings = {
  brick(color) {
    const iso = makeIso(400, 300, 26)
    const boxes = []
    for (let z = 0; z < 5; z++) {
      for (let i = 0; i < 3; i++) {
        for (let j = 0; j < 2; j++) boxes.push([i * 2.5, j * 2.6, z * 0.75, 2.4, 1.2, 0.7])
      }
    }
    return stack(iso, boxes.map(([x, y, z, w, d, h]) => [x - 3.7, y - 2.6, z, w, d, h]), color)
  },
  block(color) {
    const iso = makeIso(400, 300, 30)
    const boxes = []
    for (let z = 0; z < 3; z++) {
      for (let i = 0; i < 2; i++) for (let j = 0; j < 2; j++) boxes.push([i * 3.05 - 3, j * 1.55 - 1.5, z * 1.55, 3, 1.5, 1.5])
    }
    return stack(iso, boxes, color, { stroke: 'rgba(11,17,33,0.22)' })
  },
  bag(color) {
    const iso = makeIso(400, 320, 30)
    const boxes = [
      [-3, -1.6, 0, 4, 2.6, 0.9],
      [-3, 1.1, 0, 4, 2.6, 0.9],
      [-2.6, -0.4, 0.92, 4, 2.6, 0.9],
    ]
    return stack(iso, boxes, color, { stroke: 'rgba(11,17,33,0.25)' })
  },
  sheet(color) {
    const iso = makeIso(400, 330, 22)
    const boxes = []
    for (let z = 0; z < 10; z++) boxes.push([-5, -3.5, z * 0.32, 10, 7, 0.3])
    return stack(iso, boxes, color, { stroke: 'rgba(11,17,33,0.28)', strokeWidth: 0.9 })
  },
  beam(color) {
    const iso = makeIso(400, 320, 24)
    const boxes = []
    for (let z = 0; z < 3; z++) for (let j = 0; j < 3; j++) boxes.push([-6, j * 1.15 - 1.7, z * 1.15, 12, 1.1, 1.1])
    return stack(iso, boxes, color, { stroke: 'rgba(11,17,33,0.3)' })
  },
  profile(color) {
    const iso = makeIso(400, 320, 24)
    const boxes = []
    for (let z = 0; z < 4; z++) for (let j = 0; j < 4; j++) boxes.push([-6.5, j * 0.75 - 1.5, z * 0.55, 13, 0.6, 0.45])
    return stack(iso, boxes, color, { stroke: 'rgba(11,17,33,0.35)' })
  },
  insulation(color) {
    const iso = makeIso(400, 320, 26)
    const boxes = []
    for (let z = 0; z < 4; z++) boxes.push([-4.5, -2.5, z * 1.02, 9, 5, 1])
    return stack(iso, boxes, color, { stroke: 'rgba(11,17,33,0.18)' })
  },
  roofing(color) {
    const iso = makeIso(400, 320, 24)
    let out = ''
    for (let z = 0; z < 6; z++) {
      const pts = []
      const y0 = -3
      for (let k = 0; k <= 12; k++) {
        const x = -5.5 + k
        pts.push(iso(x, y0, z * 0.32 + (k % 2 === 0 ? 0 : 0.28)))
      }
      for (let k = 12; k >= 0; k--) {
        const x = -5.5 + k
        pts.push(iso(x, y0 + 6, z * 0.32 + (k % 2 === 0 ? 0 : 0.28)))
      }
      out += poly(pts, shade(color, z * 0.03 - 0.1), 'stroke="rgba(11,17,33,0.35)" stroke-width="1"')
    }
    return out
  },
  roll(color) {
    return [
      tubeH(250, 520, 360, 70, color, false),
      `<ellipse cx="520" cy="360" rx="${70 * 0.42 * 0.35}" ry="${70 * 0.35}" fill="#0b1121" opacity="0.8"/>`,
      tubeH(330, 590, 260, 62, shade(color, 0.08), false),
      `<ellipse cx="590" cy="260" rx="${62 * 0.42 * 0.35}" ry="${62 * 0.35}" fill="#0b1121" opacity="0.8"/>`,
    ].join('')
  },
  pipe(color) {
    let out = ''
    for (let i = 4; i >= 0; i--) {
      const shift = (i % 2) * 34
      out += tubeH(170 + shift, 600 + shift, 430 - i * 42, 22, color)
    }
    return out
  },
  valve(color) {
    return [
      tubeH(250, 550, 360, 34, color),
      `<rect x="355" y="300" width="90" height="120" rx="18" fill="${shade(color, 0.05)}" stroke="rgba(11,17,33,0.35)"/>`,
      `<rect x="355" y="300" width="90" height="120" rx="18" fill="url(#tubeShade)"/>`,
      `<rect x="390" y="250" width="20" height="56" rx="4" fill="${shade(color, -0.2)}"/>`,
      `<rect x="300" y="226" width="200" height="34" rx="10" fill="#ff8a00"/>`,
      `<rect x="300" y="226" width="200" height="12" rx="6" fill="#ffffff" opacity="0.18"/>`,
    ].join('')
  },
  bucket(color) {
    return [
      cylinderV(330, 440, 95, 26, 190, color),
      `<rect x="250" y="320" width="160" height="70" rx="8" fill="#0b1121" opacity="0.18"/>`,
      `<path d="M240,${250} Q330,170 420,250" fill="none" stroke="#cbd5e1" stroke-width="5"/>`,
      cylinderV(500, 450, 70, 20, 130, shade(color, -0.08)),
      `<path d="M435,${320} Q500,262 565,320" fill="none" stroke="#cbd5e1" stroke-width="4"/>`,
    ].join('')
  },
  tile(color) {
    const iso = makeIso(400, 320, 24)
    const boxes = []
    for (let z = 0; z < 8; z++) boxes.push([-4.5, -4.5, z * 0.3, 9, 9, 0.26])
    return stack(iso, boxes, color, { stroke: 'rgba(11,17,33,0.25)', strokeWidth: 0.8 })
  },
  drill(color) {
    return [
      `<path d="M250,250 h230 a40,40 0 0 1 40,40 v10 a40,40 0 0 1 -40,40 h-100 l-40,110 a20,20 0 0 1 -19,13 h-46 a12,12 0 0 1 -11,-16 l40,-107 h-14 a40,40 0 0 1 -40,-40 v0 a40,40 0 0 1 40,-50 z" fill="${color}" stroke="rgba(11,17,33,0.4)" stroke-width="2"/>`,
      `<rect x="232" y="432" width="128" height="46" rx="10" fill="#1f2937" stroke="rgba(255,255,255,0.12)"/>`,
      `<rect x="520" y="280" width="60" height="30" rx="6" fill="#334155"/>`,
      `<rect x="578" y="289" width="90" height="12" rx="3" fill="#cbd5e1"/>`,
      `<rect x="260" y="262" width="150" height="14" rx="7" fill="#ffffff" opacity="0.18"/>`,
    ].join('')
  },
  grinder(color) {
    return [
      `<rect x="200" y="300" width="320" height="80" rx="40" fill="${color}" stroke="rgba(11,17,33,0.4)" stroke-width="2"/>`,
      `<rect x="215" y="312" width="200" height="14" rx="7" fill="#ffffff" opacity="0.2"/>`,
      `<rect x="500" y="290" width="70" height="100" rx="16" fill="#334155"/>`,
      `<ellipse cx="600" cy="420" rx="110" ry="30" fill="#94a3b8" stroke="#475569" stroke-width="3"/>`,
      `<ellipse cx="600" cy="420" rx="40" ry="11" fill="#334155"/>`,
      `<rect x="150" y="320" width="60" height="40" rx="12" fill="#1f2937"/>`,
    ].join('')
  },
  box(color) {
    const iso = makeIso(400, 320, 30)
    return stack(
      iso,
      [
        [-3, -2, 0, 3, 2, 2.2],
        [0.2, -2, 0, 3, 2, 2.2],
        [-1.4, 0.3, 0, 3, 2, 2.2],
      ],
      color,
      { stroke: 'rgba(11,17,33,0.3)' },
    )
  },
  pile(color) {
    return [
      `<path d="M150,450 C230,300 330,210 410,200 C500,205 590,310 660,450 Z" fill="${color}"/>`,
      `<path d="M150,450 C230,300 330,210 410,200 C380,260 360,360 380,450 Z" fill="#ffffff" opacity="0.1"/>`,
      `<path d="M410,200 C500,205 590,310 660,450 L520,450 C520,340 470,260 410,200 Z" fill="#0b1121" opacity="0.18"/>`,
    ].join('')
  },
}

// ---------- texture close-ups ----------

const textures = {
  brick: (c) => pattern(c, 'brick'),
  block: (c) => pattern(c, 'block'),
  bag: (c) => pattern(c, 'grain'),
  sheet: (c) => pattern(c, 'lines'),
  beam: (c) => pattern(c, 'wood'),
  profile: (c) => pattern(c, 'lines'),
  insulation: (c) => pattern(c, 'fibre'),
  roofing: (c) => pattern(c, 'wave'),
  roll: (c) => pattern(c, 'fibre'),
  pipe: (c) => pattern(c, 'rings'),
  valve: (c) => pattern(c, 'rings'),
  bucket: (c) => pattern(c, 'drops'),
  tile: (c) => pattern(c, 'grid'),
  drill: (c) => pattern(c, 'dots'),
  grinder: (c) => pattern(c, 'dots'),
  box: (c) => pattern(c, 'dots'),
  pile: (c) => pattern(c, 'grain'),
}

function pattern(color, kind) {
  const dark = shade(color, -0.35)
  const light = shade(color, 0.18)
  let defs = ''
  switch (kind) {
    case 'brick':
      defs = `<pattern id="p" width="120" height="60" patternUnits="userSpaceOnUse"><rect width="120" height="60" fill="${dark}"/><rect x="3" y="3" width="114" height="24" rx="2" fill="${color}"/><rect x="-57" y="33" width="114" height="24" rx="2" fill="${light}"/><rect x="63" y="33" width="114" height="24" rx="2" fill="${color}"/></pattern>`
      break
    case 'block':
      defs = `<pattern id="p" width="200" height="100" patternUnits="userSpaceOnUse"><rect width="200" height="100" fill="${dark}"/><rect x="2" y="2" width="196" height="46" fill="${color}"/><rect x="-98" y="52" width="196" height="46" fill="${light}"/><rect x="102" y="52" width="196" height="46" fill="${color}"/></pattern>`
      break
    case 'wood':
      defs = `<pattern id="p" width="800" height="40" patternUnits="userSpaceOnUse"><rect width="800" height="40" fill="${color}"/><path d="M0,10 C200,0 300,22 500,12 S700,4 800,10" stroke="${dark}" stroke-width="2" fill="none" opacity="0.6"/><path d="M0,28 C150,36 350,20 520,30 S720,36 800,28" stroke="${light}" stroke-width="2" fill="none" opacity="0.6"/></pattern>`
      break
    case 'lines':
      defs = `<pattern id="p" width="40" height="40" patternUnits="userSpaceOnUse"><rect width="40" height="40" fill="${color}"/><rect y="36" width="40" height="4" fill="${dark}" opacity="0.6"/></pattern>`
      break
    case 'fibre':
      defs = `<pattern id="p" width="60" height="60" patternUnits="userSpaceOnUse"><rect width="60" height="60" fill="${color}"/><path d="M0,15 Q15,5 30,15 T60,15 M0,45 Q15,35 30,45 T60,45" stroke="${light}" stroke-width="3" fill="none"/><path d="M0,30 Q15,20 30,30 T60,30" stroke="${dark}" stroke-width="2" fill="none" opacity="0.6"/></pattern>`
      break
    case 'wave':
      defs = `<pattern id="p" width="80" height="80" patternUnits="userSpaceOnUse"><rect width="80" height="80" fill="${color}"/><path d="M0,40 Q20,0 40,40 T80,40" stroke="${light}" stroke-width="10" fill="none"/><path d="M0,60 Q20,20 40,60 T80,60" stroke="${dark}" stroke-width="6" fill="none" opacity="0.5"/></pattern>`
      break
    case 'rings':
      defs = `<pattern id="p" width="100" height="100" patternUnits="userSpaceOnUse"><rect width="100" height="100" fill="${dark}"/><circle cx="50" cy="50" r="44" fill="${color}"/><circle cx="50" cy="50" r="30" fill="#0b1121"/><circle cx="50" cy="50" r="44" fill="none" stroke="${light}" stroke-width="3"/></pattern>`
      break
    case 'drops':
      defs = `<pattern id="p" width="80" height="80" patternUnits="userSpaceOnUse"><rect width="80" height="80" fill="${color}"/><circle cx="20" cy="20" r="10" fill="${light}"/><circle cx="60" cy="60" r="14" fill="${light}" opacity="0.7"/><circle cx="62" cy="18" r="4" fill="${dark}" opacity="0.5"/></pattern>`
      break
    case 'grid':
      defs = `<pattern id="p" width="150" height="150" patternUnits="userSpaceOnUse"><rect width="150" height="150" fill="${shade(color, -0.5)}"/><rect x="3" y="3" width="144" height="144" rx="2" fill="${color}"/><path d="M20,40 Q60,20 120,60" stroke="${light}" stroke-width="2" fill="none" opacity="0.5"/></pattern>`
      break
    case 'dots':
      defs = `<pattern id="p" width="36" height="36" patternUnits="userSpaceOnUse"><rect width="36" height="36" fill="${dark}"/><circle cx="18" cy="18" r="8" fill="${color}"/><circle cx="16" cy="16" r="3" fill="${light}"/></pattern>`
      break
    default:
      defs = `<pattern id="p" width="24" height="24" patternUnits="userSpaceOnUse"><rect width="24" height="24" fill="${color}"/><circle cx="6" cy="7" r="1.6" fill="${light}"/><circle cx="17" cy="15" r="1.3" fill="${dark}"/><circle cx="10" cy="19" r="1" fill="${light}"/></pattern>`
  }
  return { defs, body: `<rect width="${W}" height="${H}" fill="url(#p)"/>` }
}

// ---------- page wrappers ----------

const commonDefs = `
  <linearGradient id="bg" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#1b2540"/><stop offset="1" stop-color="#0f172a"/></linearGradient>
  <radialGradient id="glow" cx="0.5" cy="0.55" r="0.5"><stop offset="0" stop-color="#ff8a00" stop-opacity="0.22"/><stop offset="1" stop-color="#ff8a00" stop-opacity="0"/></radialGradient>
  <pattern id="grid" width="40" height="40" patternUnits="userSpaceOnUse"><path d="M40 0H0V40" fill="none" stroke="#ffffff" stroke-opacity="0.04"/></pattern>
  <linearGradient id="tubeShade" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#ffffff" stop-opacity="0.28"/><stop offset="0.45" stop-color="#ffffff" stop-opacity="0"/><stop offset="1" stop-color="#000000" stop-opacity="0.35"/></linearGradient>
  <linearGradient id="cylShade" x1="0" y1="0" x2="1" y2="0"><stop offset="0" stop-color="#000000" stop-opacity="0.35"/><stop offset="0.35" stop-color="#ffffff" stop-opacity="0.12"/><stop offset="1" stop-color="#000000" stop-opacity="0.4"/></linearGradient>
  <linearGradient id="cylV" x1="0" y1="0" x2="1" y2="0"><stop offset="0" stop-color="#000"/><stop offset="1" stop-color="#000"/></linearGradient>`

function shot(product) {
  const draw = drawings[product.art]
  if (!draw) throw new Error(`Unknown art "${product.art}" for ${product.slug}`)
  return `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 ${W} ${H}" role="img" aria-label="${escapeXml(product.name)} (illustration)">
<defs>${commonDefs}</defs>
<rect width="${W}" height="${H}" fill="url(#bg)"/>
<rect width="${W}" height="${H}" fill="url(#grid)"/>
<ellipse cx="400" cy="330" rx="360" ry="260" fill="url(#glow)"/>
<ellipse cx="400" cy="470" rx="270" ry="38" fill="#000000" opacity="0.35"/>
<g>${draw(product.color)}</g>
</svg>
`
}

function closeUp(product) {
  const t = textures[product.art](product.color)
  return `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 ${W} ${H}" role="img" aria-label="${escapeXml(product.name)} (texture illustration)">
<defs>${commonDefs}${t.defs}<radialGradient id="vig" cx="0.5" cy="0.5" r="0.75"><stop offset="0.55" stop-color="#0b1121" stop-opacity="0"/><stop offset="1" stop-color="#0b1121" stop-opacity="0.75"/></radialGradient></defs>
${t.body}
<rect width="${W}" height="${H}" fill="url(#vig)"/>
</svg>
`
}

function escapeXml(s) {
  return s.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;')
}

let count = 0
for (const product of products) {
  if (product.imageCount === 0) continue
  writeFileSync(join(outDir, `${product.slug}-1.svg`), shot(product))
  count++
  if (product.imageCount > 1) {
    writeFileSync(join(outDir, `${product.slug}-2.svg`), closeUp(product))
    count++
  }
}
console.info(`Wrote ${count} images to ${outDir}`)
