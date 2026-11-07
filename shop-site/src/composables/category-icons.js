import {
  mdiFormatPaint,
  mdiHammerWrench,
  mdiHomeRoof,
  mdiPackageVariantClosed,
  mdiPineTree,
  mdiPipe,
  mdiWall,
} from '@quasar/extras/mdi-v7'

// Categories have no icon field in the database, so the icon is picked by
// keywords in the slug. Unknown categories get a neutral package icon.
const RULES = [
  [/brick|block|cement|mix|drywall|concrete|building|wall/, mdiWall],
  [/lumber|timber|wood|plywood|osb|panel|board/, mdiPineTree],
  [/roof|insulat/, mdiHomeRoof],
  [/plumb|pipe|fitting|water|sewer/, mdiPipe],
  [/paint|finish|tile|primer|plaster/, mdiFormatPaint],
  [/tool|fasten|screw|bolt|hardware/, mdiHammerWrench],
]

export function categoryIcon(slug = '') {
  for (const [re, icon] of RULES) if (re.test(slug)) return icon
  return mdiPackageVariantClosed
}
