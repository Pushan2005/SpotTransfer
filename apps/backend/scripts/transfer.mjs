import { spawn, spawnSync } from "node:child_process";
import { existsSync } from "node:fs";
import path from "node:path";

const root = path.resolve(import.meta.dirname, "..");
const isWin = process.platform === "win32";

const venvDir = path.join(root, ".venv");
const venvPython = path.join(
    venvDir,
    isWin ? "Scripts\\python.exe" : "bin/python",
);

function findSystemPython() {
    for (const cmd of isWin ? ["python", "py"] : ["python3", "python"]) {
        const result = spawnSync(cmd, ["--version"]);
        if (result.status === 0) return cmd;
    }
    throw new Error(
        "No Python interpreter found on PATH (tried python3/python/py).",
    );
}

function run(cmd, args) {
    const result = spawnSync(cmd, args, { cwd: root, stdio: "inherit" });
    if (result.status !== 0) process.exit(result.status ?? 1);
}

if (!existsSync(venvPython)) {
    console.log("Creating virtualenv...");
    run(findSystemPython(), ["-m", "venv", ".venv"]);
    console.log("Installing requirements...");
    run(venvPython, ["-m", "pip", "install", "-r", "requirements.txt"]);
}

const child = spawn(venvPython, ["selfhost.py", ...process.argv.slice(2)], {
    cwd: root,
    stdio: "inherit",
});
child.on("exit", (code) => process.exit(code ?? 0));
