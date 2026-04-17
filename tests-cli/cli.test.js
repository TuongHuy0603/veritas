/**
 * Node test suite for cli/index.js.
 *
 * Zero dependencies — uses built-in node:test (requires Node 18+).
 * Runs the CLI as a child process in temp directories; sets HOME/USERPROFILE
 * so ~-expanded targets land inside the test sandbox, not the real home.
 *
 * Invoke: `node --test tests-cli/`.
 */

"use strict";

const { test } = require("node:test");
const assert = require("node:assert/strict");
const { execFileSync } = require("node:child_process");
const fs = require("node:fs");
const os = require("node:os");
const path = require("node:path");

const REPO_ROOT = path.resolve(__dirname, "..");
const CLI = path.join(REPO_ROOT, "cli", "index.js");
const COMMAND_BASENAMES = [
  "plan",
  "design",
  "execute",
  "verify",
  "gate",
  "ground",
  "handoff",
  "resume",
];

function runCli(args, { cwd, sandboxHome }) {
  const env = { ...process.env, HOME: sandboxHome, USERPROFILE: sandboxHome };
  // Fresh PATH / hostnames — do not inherit shell junk that could leak out.
  return execFileSync(process.execPath, [CLI, ...args], {
    cwd,
    env,
    encoding: "utf-8",
  });
}

function makeSandbox(prefix) {
  const dir = fs.mkdtempSync(path.join(os.tmpdir(), prefix));
  const home = path.join(dir, "home");
  const project = path.join(dir, "project");
  fs.mkdirSync(home, { recursive: true });
  fs.mkdirSync(project, { recursive: true });
  return { dir, home, project };
}

test("list command prints all 13 platforms", () => {
  const sb = makeSandbox("veritas-list-");
  try {
    const out = runCli(["list"], { cwd: sb.project, sandboxHome: sb.home });
    for (const key of [
      "claude",
      "cursor",
      "windsurf",
      "copilot",
      "codex",
      "gemini",
      "continue",
      "roocode",
      "kilocode",
      "opencode",
      "trae",
      "warp",
      "kiro",
    ]) {
      assert.ok(out.includes(key), `platform ${key} missing from list output`);
    }
  } finally {
    fs.rmSync(sb.dir, { recursive: true, force: true });
  }
});

test("init --ai claude installs skill and all commands to sandboxed home", () => {
  const sb = makeSandbox("veritas-claude-");
  try {
    runCli(["init", "--ai", "claude"], { cwd: sb.project, sandboxHome: sb.home });
    const skillDir = path.join(sb.home, ".claude", "skills", "veritas");
    const commandsDir = path.join(sb.home, ".claude", "commands");
    assert.ok(fs.existsSync(path.join(skillDir, "SKILL.md")));
    assert.ok(fs.existsSync(path.join(skillDir, "modules", "verify-claim.md")));
    assert.ok(fs.existsSync(path.join(skillDir, "personas", "verifier.md")));
    assert.ok(fs.existsSync(path.join(skillDir, "pillars", "plan.md")));
    for (const base of COMMAND_BASENAMES) {
      assert.ok(
        fs.existsSync(path.join(commandsDir, `${base}.md`)),
        `${base}.md missing in commands dir`
      );
    }
  } finally {
    fs.rmSync(sb.dir, { recursive: true, force: true });
  }
});

test("init --ai cursor flattens skill and renames commands to veritas-*.mdc", () => {
  const sb = makeSandbox("veritas-cursor-");
  try {
    runCli(["init", "--ai", "cursor"], { cwd: sb.project, sandboxHome: sb.home });
    const rulesDir = path.join(sb.project, ".cursor", "rules");
    assert.ok(fs.existsSync(path.join(rulesDir, "veritas.mdc")), "veritas.mdc missing");
    // Commands should each be a prefixed .mdc at the top level.
    for (const base of COMMAND_BASENAMES) {
      assert.ok(
        fs.existsSync(path.join(rulesDir, `veritas-${base}.mdc`)),
        `veritas-${base}.mdc missing`
      );
    }
    // Modules/personas/pillars should be flattened, not nested folders.
    const entries = fs.readdirSync(rulesDir);
    assert.ok(
      entries.some((e) => e.startsWith("veritas-modules-") && e.endsWith(".mdc")),
      "expected flattened veritas-modules-*.mdc files"
    );
    assert.ok(!entries.includes("modules"), "modules/ should be flattened");
    assert.ok(!entries.includes("personas"), "personas/ should be flattened");
  } finally {
    fs.rmSync(sb.dir, { recursive: true, force: true });
  }
});

test("init --ai copilot writes .prompt.md command files", () => {
  const sb = makeSandbox("veritas-copilot-");
  try {
    runCli(["init", "--ai", "copilot"], { cwd: sb.project, sandboxHome: sb.home });
    const promptsDir = path.join(sb.project, ".github", "prompts");
    for (const base of COMMAND_BASENAMES) {
      assert.ok(
        fs.existsSync(path.join(promptsDir, `${base}.prompt.md`)),
        `${base}.prompt.md missing`
      );
    }
  } finally {
    fs.rmSync(sb.dir, { recursive: true, force: true });
  }
});

test("uninstall --ai claude removes skill dir and command files", () => {
  const sb = makeSandbox("veritas-uninstall-claude-");
  try {
    runCli(["init", "--ai", "claude"], { cwd: sb.project, sandboxHome: sb.home });
    const skillDir = path.join(sb.home, ".claude", "skills", "veritas");
    const commandsDir = path.join(sb.home, ".claude", "commands");
    assert.ok(fs.existsSync(skillDir), "skill dir should exist after init");
    runCli(["uninstall", "--ai", "claude"], { cwd: sb.project, sandboxHome: sb.home });
    assert.ok(!fs.existsSync(skillDir), "skill dir should be removed");
    for (const base of COMMAND_BASENAMES) {
      assert.ok(
        !fs.existsSync(path.join(commandsDir, `${base}.md`)),
        `${base}.md should be removed`
      );
    }
  } finally {
    fs.rmSync(sb.dir, { recursive: true, force: true });
  }
});

test("uninstall --ai cursor removes flat veritas-*.mdc files", () => {
  const sb = makeSandbox("veritas-uninstall-cursor-");
  try {
    runCli(["init", "--ai", "cursor"], { cwd: sb.project, sandboxHome: sb.home });
    const rulesDir = path.join(sb.project, ".cursor", "rules");
    // Sanity: install did create files.
    const beforeUninstall = fs
      .readdirSync(rulesDir)
      .filter((f) => f.startsWith("veritas-") && f.endsWith(".mdc"));
    assert.ok(beforeUninstall.length > 0, "expected veritas-*.mdc after init");
    runCli(["uninstall", "--ai", "cursor"], { cwd: sb.project, sandboxHome: sb.home });
    const afterUninstall = fs.existsSync(rulesDir)
      ? fs.readdirSync(rulesDir).filter((f) => f.startsWith("veritas-"))
      : [];
    assert.equal(afterUninstall.length, 0, "no veritas-* files should remain");
    assert.ok(
      !fs.existsSync(path.join(rulesDir, "veritas.mdc")),
      "veritas.mdc should be removed"
    );
  } finally {
    fs.rmSync(sb.dir, { recursive: true, force: true });
  }
});

test("init --ai <unknown> exits non-zero", () => {
  const sb = makeSandbox("veritas-unknown-");
  try {
    assert.throws(
      () =>
        runCli(["init", "--ai", "nonsense-platform"], {
          cwd: sb.project,
          sandboxHome: sb.home,
        }),
      /Unknown platform/
    );
  } finally {
    fs.rmSync(sb.dir, { recursive: true, force: true });
  }
});
