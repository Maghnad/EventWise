import { dirname } from "path";
import { fileURLToPath } from "url";
import { FlatCompat } from "@eslint/eslintrc";
import tseslint from "typescript-eslint";
import jsxA11y from "eslint-plugin-jsx-a11y";

const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);

const compat = new FlatCompat({ baseDirectory: __dirname });

export default tseslint.config(
  /* ── Next.js built-in rules ──────────────────────── */
  ...compat.extends("next/core-web-vitals"),

  /* ── TypeScript-ESLint recommended ───────────────── */
  ...tseslint.configs.recommended,

  /* ── Accessibility (jsx-a11y) rules ──────────────── */
  {
    rules: {
      ...jsxA11y.configs.recommended.rules,
      "@typescript-eslint/no-unused-vars": [
        "warn",
        { argsIgnorePattern: "^_", varsIgnorePattern: "^_" },
      ],
      "@typescript-eslint/consistent-type-imports": "warn",
    },
  },

  /* ── Ignore patterns ─────────────────────────────── */
  {
    ignores: [".next/", "node_modules/", "out/"],
  },
);
