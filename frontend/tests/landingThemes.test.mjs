import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import test from "node:test";

const read = (path) => readFileSync(new URL(path, import.meta.url), "utf8");
const landing = read("../src/views/LandingView.vue");
const tokens = read("../src/assets/styles/tokens.css");

const themes = [
  ["weiguang-original", "#FBF6EC", "#000000"],
  ["mars-rose", "#01847F", "#F9D2E4"],
  ["ivory-cinnabar", "#FFFFF0", "#C01E25"],
  ["lemon-sea", "#F0FF0A", "#1E9BFF"],
  ["cherry-clearwater", "#F78A88", "#3F389F"],
  ["amber-kingfisher", "#F9B800", "#153C46"],
  ["cloud-cyan", "#F8FFFF", "#00B7C7"],
  ["ice-wine", "#88E7D2", "#A82F4F"],
  ["barbie-moss", "#F1BBC9", "#4D613C"],
  ["blaze-neon", "#E61A23", "#0A090C"],
  ["mint-brick", "#BBF0EA", "#8D4726"],
];

test("landing exposes every referenced palette through global CSS tokens", () => {
  for (const [id, first, second] of themes) {
    assert.match(landing, new RegExp(`id: \\"${id}\\"`));
    assert.ok(landing.includes(first) && landing.includes(second));
    if (id !== "weiguang-original") assert.match(tokens, new RegExp(`data-theme=\\"${id}\\"`));
  }
  assert.match(landing, /const defaultTheme = "weiguang-original"/);
  assert.match(landing, /document\.documentElement\.dataset\.theme/);
  assert.match(landing, /aria-haspopup="listbox"/);
  assert.match(landing, /aria-label="全局配色"/);
  assert.match(landing, /class="theme-picker__menu"/);
  assert.match(tokens + read("../src/assets/styles/landing.css"), /top:\s*calc\(100% \+ 8px\)/);
  assert.doesNotMatch(landing, /<select/);
  assert.doesNotMatch(landing, /localStorage/);
});
