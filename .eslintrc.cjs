module.exports = {
  root: true,
  env: {
    browser: true,
    es2022: true,
    worker: true
  },
  parserOptions: {
    ecmaVersion: "latest",
    sourceType: "module"
  },
  extends: ["eslint:recommended", "plugin:import/recommended"],
  plugins: ["import"],
  rules: {
    "no-unused-vars": ["error", { "argsIgnorePattern": "^_", "varsIgnorePattern": "^_" }],
    "no-undef": "error",
    "no-console": ["warn", { "allow": ["warn", "error"] }],
    "import/no-unresolved": "off"
  },
  overrides: [
    {
      files: ["sw.js"],
      env: {
        serviceworker: true
      },
      globals: {
        self: "readonly",
        caches: "readonly",
        registration: "readonly"
      }
    },
    {
      files: ["tests/**/*.js"],
      env: {
        node: true,
        es2022: true
      }
    }
  ],
  ignorePatterns: [
    "node_modules/",
    "dist/",
    "**/*.min.js"
  ]
};
