import { spawn } from "node:child_process";
import path from "node:path";

const root = path.resolve(import.meta.dirname, "..");
const shouldOpenBrowser = process.argv.includes("--open");
const frontendUrl = "http://localhost:5173";

function launchBrowser(url) {
    const platform = process.platform;
    const child =
        platform === "win32"
            ? spawn("cmd", ["/c", "start", "", url], {
                  stdio: "ignore",
                  detached: true,
              })
            : spawn(platform === "darwin" ? "open" : "xdg-open", [url], {
                  stdio: "ignore",
                  detached: true,
              });
    child.unref();
}

const targets = [
    {
        name: "web",
        cwd: path.join(root, "apps/web"),
        args: ["run", "dev"],
        openWhenReady: true,
    },
    { name: "api", cwd: path.join(root, "apps/backend"), args: ["run", "dev"] },
];

let browserOpened = false;

const children = targets.map(({ name, cwd, args, openWhenReady }) => {
    const child = spawn("bun", args, {
        cwd,
        stdio: ["inherit", "pipe", "pipe"],
    });
    const prefix = (data) => {
        for (const line of String(data).split("\n")) {
            if (!line.length) continue;
            process.stdout.write(`[${name}] ${line}\n`);
            if (
                shouldOpenBrowser &&
                !browserOpened &&
                openWhenReady &&
                /ready in|Local:/i.test(line)
            ) {
                browserOpened = true;
                launchBrowser(frontendUrl);
            }
        }
    };
    child.stdout.on("data", prefix);
    child.stderr.on("data", prefix);
    child.on("exit", (code) => {
        console.log(`[${name}] exited with code ${code ?? 0}`);
        for (const other of children) {
            if (other !== child && !other.killed) other.kill();
        }
        process.exit(code ?? 0);
    });
    return child;
});

for (const signal of ["SIGINT", "SIGTERM"]) {
    process.on(signal, () => {
        for (const child of children) child.kill(signal);
    });
}
