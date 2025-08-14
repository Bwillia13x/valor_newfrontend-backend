import { defineConfig } from "vitest/config";

export default defineConfig({
  test: {
    environment: "jsdom",
    include: ["tests/test_collaboration_engine.js"],
    coverage: {
      provider: "v8",
      reporter: ["text", "lcov"],
      statements: 0.7,
      branches: 0.7,
      functions: 0.7,
      lines: 0.7,
      exclude: ["**/node_modules/**", "**/tests/**"]
    }
  }
});
