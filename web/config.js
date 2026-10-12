// The narration Worker's URL, or "" for no written summary.
//
// The Pages workflow (.github/workflows/pages.yml) overwrites this file at build time from the
// repository variable NARRATOR_URL (Settings > Secrets and variables > Actions > Variables), so
// each copy of the site sets its own or leaves narration off. This committed default is what a
// local build (web/build.sh, then python3 -m http.server -d web) uses. See INSTALL.md.
export const NARRATOR_URL = "";
