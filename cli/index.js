#!/usr/bin/env node
/**
 * veritas-cli — install the Veritas skill into an AI coding platform.
 *
 * Usage:
 *   npx veritas-cli init --ai <platform>
 *   npx veritas-cli list
 *   npx veritas-cli uninstall --ai <platform>
 *
 * Platforms: see `npx veritas-cli list`.
 */

"use strict";

const fs = require("fs");
const os = require("os");
const path = require("path");

const ADAPTERS = require("./adapters.json");
const SKILL_ROOT = path.resolve(__dirname, "..", "src", "veritas");

function expand(target) {
  if (target.startsWith("~")) {
    return path.join(os.homedir(), target.slice(1).replace(/^[\\/]/, ""));
  }
  return path.resolve(process.cwd(), target);
}

function copyTree(from, to) {
  fs.mkdirSync(to, { recursive: true });
  for (const entry of fs.readdirSync(from, { withFileTypes: true })) {
    const src = path.join(from, entry.name);
    const dst = path.join(to, entry.name);
    if (entry.isDirectory()) {
      copyTree(src, dst);
    } else if (entry.isFile()) {
      fs.copyFileSync(src, dst);
    }
  }
}

function renameEntrypoint(dir, layout) {
  if (layout !== "rules-folder") return;
  const from = path.join(dir, "SKILL.md");
  const to = path.join(dir, "veritas.mdc");
  if (fs.existsSync(from) && !fs.existsSync(to)) {
    fs.renameSync(from, to);
  }
}

function removeTree(dir) {
  if (!fs.existsSync(dir)) return;
  fs.rmSync(dir, { recursive: true, force: true });
}

function parseArgs(argv) {
  const args = { _: [] };
  for (let i = 0; i < argv.length; i++) {
    const a = argv[i];
    if (a.startsWith("--")) {
      const key = a.slice(2);
      const next = argv[i + 1];
      if (!next || next.startsWith("--")) {
        args[key] = true;
      } else {
        args[key] = next;
        i++;
      }
    } else {
      args._.push(a);
    }
  }
  return args;
}

function cmdList() {
  console.log("Supported platforms:");
  for (const [key, cfg] of Object.entries(ADAPTERS)) {
    console.log(`  ${key.padEnd(12)} ${cfg.label.padEnd(22)} -> ${cfg.target}`);
    if (cfg.notes) console.log(`               ${cfg.notes}`);
  }
}

function cmdInit(platform) {
  const cfg = ADAPTERS[platform];
  if (!cfg) {
    console.error(`Unknown platform: ${platform}. Run 'veritas-cli list' to see options.`);
    process.exit(2);
  }
  const target = expand(cfg.target);
  console.log(`Installing Veritas for ${cfg.label}`);
  console.log(`  source: ${SKILL_ROOT}`);
  console.log(`  target: ${target}`);
  copyTree(SKILL_ROOT, target);
  renameEntrypoint(target, cfg.layout);
  console.log("Done. Veritas will auto-activate based on the triggers in SKILL.md.");
  if (cfg.notes) console.log(`Note: ${cfg.notes}`);
}

function cmdUninstall(platform) {
  const cfg = ADAPTERS[platform];
  if (!cfg) {
    console.error(`Unknown platform: ${platform}.`);
    process.exit(2);
  }
  const target = expand(cfg.target);
  if (!fs.existsSync(target)) {
    console.log(`Nothing to remove at ${target}.`);
    return;
  }
  removeTree(target);
  console.log(`Removed ${target}.`);
}

function main() {
  const argv = process.argv.slice(2);
  const args = parseArgs(argv);
  const cmd = args._[0];

  if (!cmd || cmd === "help" || args.help) {
    console.log(
      [
        "veritas-cli — install the Veritas skill.",
        "",
        "Commands:",
        "  init --ai <platform>       install into the given platform",
        "  uninstall --ai <platform>  remove from the given platform",
        "  list                       show supported platforms",
      ].join("\n")
    );
    return;
  }

  if (cmd === "list") return cmdList();
  if (cmd === "init") return cmdInit(args.ai);
  if (cmd === "uninstall") return cmdUninstall(args.ai);

  console.error(`Unknown command: ${cmd}`);
  process.exit(2);
}

main();
