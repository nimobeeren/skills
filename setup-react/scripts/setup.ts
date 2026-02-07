import { execSync } from "node:child_process";
import { readFileSync, rmSync, unlinkSync, writeFileSync } from "node:fs";

function run(cmd: string) {
  console.log(`\n$ ${cmd}`);
  execSync(cmd, { stdio: "inherit" });
}

function stripJsonComments(text: string): string {
  let result = "";
  let i = 0;
  let inString = false;

  while (i < text.length) {
    if (inString) {
      if (text[i] === "\\") {
        result += text.slice(i, i + 2);
        i += 2;
      } else if (text[i] === '"') {
        result += '"';
        inString = false;
        i++;
      } else {
        result += text[i];
        i++;
      }
    } else if (text[i] === '"') {
      result += '"';
      inString = true;
      i++;
    } else if (text.startsWith("//", i)) {
      const newline = text.indexOf("\n", i);
      i = newline === -1 ? text.length : newline;
    } else if (text.startsWith("/*", i)) {
      const end = text.indexOf("*/", i + 2);
      i = end === -1 ? text.length : end + 2;
    } else {
      result += text[i];
      i++;
    }
  }

  return result;
}

function readJson(filePath: string) {
  return JSON.parse(stripJsonComments(readFileSync(filePath, "utf-8")));
}

function writeJson(filePath: string, data: unknown) {
  writeFileSync(filePath, JSON.stringify(data, null, 2) + "\n");
}

// 1. Set up Git repo
run("git init");

// 2. Scaffold Vite React + TypeScript project
run("pnpm create vite@latest . --template react-ts");
run("pnpm install");

// 3. Add Tailwind CSS
run("pnpm add tailwindcss @tailwindcss/vite");
writeFileSync("src/index.css", '@import "tailwindcss";\n');

// 4. Configure path aliases in tsconfig files
for (const file of ["tsconfig.json", "tsconfig.app.json"]) {
  const config = readJson(file);
  config.compilerOptions ??= {};
  config.compilerOptions.baseUrl = ".";
  config.compilerOptions.paths = { "@/*": ["./src/*"] };
  writeJson(file, config);
}

// 5. Update vite.config.ts with path alias and Tailwind plugin
run("pnpm add -D @types/node");
writeFileSync(
  "vite.config.ts",
  `import path from "path"
import tailwindcss from "@tailwindcss/vite"
import react from "@vitejs/plugin-react"
import { defineConfig } from "vite"

export default defineConfig({
  plugins: [react(), tailwindcss()],
  resolve: {
    alias: {
      "@": path.resolve(__dirname, "./src"),
    },
  },
})
`,
);

// 6. Initialize shadcn/ui and add a Button component
run("pnpm dlx shadcn@latest init --defaults");
run("pnpm dlx shadcn@latest add button");

// 7. Remove Vite boilerplate and replace with a minimal shadcn example (kebab-case)
unlinkSync("src/App.css");
unlinkSync("src/App.tsx");
rmSync("src/assets", { recursive: true });

writeFileSync(
  "src/app.tsx",
  `import { Button } from "@/components/ui/button"

function App() {
  return (
    <div className="flex min-h-svh items-center justify-center">
      <Button>Click me</Button>
    </div>
  )
}

export default App
`,
);

writeFileSync(
  "src/main.tsx",
  `import { StrictMode } from "react"
import { createRoot } from "react-dom/client"
import "./index.css"
import App from "./app"

createRoot(document.getElementById("root")!).render(
  <StrictMode>
    <App />
  </StrictMode>,
)
`,
);

// 8. Replace Vite README with a minimal one
const { name } = readJson("package.json");
writeFileSync(
  "README.md",
  `# ${name}

## Getting Started

### Prerequisites

- Node.js >= 23
- pnpm

### Installation

\`\`\`sh
pnpm install
\`\`\`

### Development

\`\`\`sh
pnpm dev
\`\`\`

### Build

\`\`\`sh
pnpm build
\`\`\`
`,
);

// 9. Set up Prettier with pre-commit hook
run("pnpm add -D prettier lint-staged husky");
run("pnpm exec husky init");
writeFileSync(".husky/pre-commit", "pnpm exec lint-staged\n");

const pkg = readJson("package.json");
pkg["lint-staged"] = { "*": "prettier --write --ignore-unknown" };
writeJson("package.json", pkg);
