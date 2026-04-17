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
const REPO_ROOT = path.resolve(__dirname, "..");
const SKILL_ROOT = path.join(REPO_ROOT, "src", "veritas");
const COMMANDS_ROOT = path.join(REPO_ROOT, "commands");

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

function copyFile(from, to) {
  fs.mkdirSync(path.dirname(to), { recursive: true });
  fs.copyFileSync(from, to);
}

function removeTree(dir) {
  if (!fs.existsSync(dir)) return;
  fs.rmSync(dir, { recursive: true, force: true });
}

function installSkill(skillDir, layout) {
  copyTree(SKILL_ROOT, skillDir);
  if (layout === "cursor-mdc") {
    // Cursor expects flat .mdc files in .cursor/rules/, not a nested folder.
    const entry = path.join(skillDir, "SKILL.md");
    if (fs.existsSync(entry)) {
      fs.renameSync(entry, path.join(path.dirname(skillDir), "veritas.mdc"));
    }
    // Move modules/personas into flat rule files too.
    const subDirs = ["modules", "personas", "pillars"];
    for (const sd of subDirs) {
      const src = path.join(skillDir, sd);
      if (!fs.existsSync(src)) continue;
      for (const file of fs.readdirSync(src)) {
        if (!file.endsWith(".md")) continue;
        const flatName = `veritas-${sd}-${file.replace(/\.md$/, ".mdc")}`;
        fs.renameSync(path.join(src, file), path.join(path.dirname(skillDir), flatName));
      }
    }
    removeTree(skillDir);
  } else if (layout === "rules-folder") {
    const entry = path.join(skillDir, "SKILL.md");
    const target = path.join(skillDir, "veritas.mdc");
    if (fs.existsSync(entry) && !fs.existsSync(target)) {
      fs.renameSync(entry, target);
    }
  }
}

function installCommands(commandsDir, layout) {
  if (!fs.existsSync(COMMANDS_ROOT)) return;
  fs.mkdirSync(commandsDir, { recursive: true });
  for (const file of fs.readdirSync(COMMANDS_ROOT)) {
    if (!file.endsWith(".md")) continue;
    const src = path.join(COMMANDS_ROOT, file);
    let name = file;
    if (layout === "prompt-files") {
      name = file.replace(/\.md$/, ".prompt.md");
    } else if (layout === "cursor-mdc") {
      // Cursor slash commands live as flat .mdc files in .cursor/rules/.
      // Prefix with "veritas-" so they don't collide with other rules.
      name = "veritas-" + file.replace(/\.md$/, ".mdc");
    }
    copyFile(src, path.join(commandsDir, name));
  }
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
  console.log("Supported platforms:\n");
  for (const [key, cfg] of Object.entries(ADAPTERS)) {
    console.log(`  ${key.padEnd(12)} ${cfg.label}`);
    console.log(`      skill    -> ${cfg.skill_target}`);
    console.log(`      commands -> ${cfg.commands_target}`);
    if (cfg.notes) console.log(`      note: ${cfg.notes}`);
    console.log("");
  }
}

function cmdInit(platform) {
  const cfg = ADAPTERS[platform];
  if (!cfg) {
    console.error(`Unknown platform: ${platform}. Run 'veritas-cli list' to see options.`);
    process.exit(2);
  }
  const skillTarget = expand(cfg.skill_target);
  const commandsTarget = expand(cfg.commands_target);
  console.log(`Installing Veritas for ${cfg.label}`);
  console.log(`  skill    source: ${SKILL_ROOT}`);
  console.log(`           target: ${skillTarget}`);
  console.log(`  commands source: ${COMMANDS_ROOT}`);
  console.log(`           target: ${commandsTarget}`);
  installSkill(skillTarget, cfg.layout);
  installCommands(commandsTarget, cfg.layout);
  console.log("\nDone. Veritas auto-activates based on SKILL.md triggers; slash commands are explicit.");
  if (cfg.notes) console.log(`Note: ${cfg.notes}`);
}

function cmdUninstall(platform) {
  const cfg = ADAPTERS[platform];
  if (!cfg) {
    console.error(`Unknown platform: ${platform}.`);
    process.exit(2);
  }
  const skillTarget = expand(cfg.skill_target);
  const commandsTarget = expand(cfg.commands_target);
  let removed = false;
  if (fs.existsSync(skillTarget)) {
    removeTree(skillTarget);
    console.log(`Removed ${skillTarget}`);
    removed = true;
  }
  // Only remove individual command files, never the platform's entire commands dir.
  if (fs.existsSync(commandsTarget) && fs.existsSync(COMMANDS_ROOT)) {
    for (const file of fs.readdirSync(COMMANDS_ROOT)) {
      if (!file.endsWith(".md")) continue;
      const base = file.replace(/\.md$/, "");
      const candidates = [
        file,
        `${base}.prompt.md`,
        `${base}.mdc`,
        `veritas-${base}.mdc`,
      ];
      for (const candidate of candidates) {
        const p = path.join(commandsTarget, candidate);
        if (fs.existsSync(p)) {
          fs.unlinkSync(p);
          console.log(`Removed ${p}`);
          removed = true;
        }
      }
    }
    // Cursor flat-skill files live in the same dir as commands:
    //   veritas.mdc                          (SKILL entrypoint)
    //   veritas-<type>-<name>.mdc            (flattened modules/personas/pillars)
    //   veritas-<command>.mdc                (slash commands)
    for (const file of fs.readdirSync(commandsTarget)) {
      if (
        (file === "veritas.mdc") ||
        (file.startsWith("veritas-") && file.endsWith(".mdc"))
      ) {
        const p = path.join(commandsTarget, file);
        fs.unlinkSync(p);
        console.log(`Removed ${p}`);
        removed = true;
      }
    }
  }
  if (!removed) console.log("Nothing to remove.");
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
        "  init --ai <platform>       install skill + slash commands",
        "  uninstall --ai <platform>  remove skill + slash commands",
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
