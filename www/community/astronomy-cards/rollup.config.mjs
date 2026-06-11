import resolve from "@rollup/plugin-node-resolve";
import typescript from "@rollup/plugin-typescript";
import { terser } from "rollup-plugin-terser";

export default {
  input: "index.ts",
  output: {
    file: "astronomy-cards.js",
    format: "es",
    sourcemap: false,
  },
  plugins: [
    resolve(),
    typescript(),
    terser(),
  ],
};
