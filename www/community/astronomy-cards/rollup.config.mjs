import resolve from "@rollup/plugin-node-resolve";
import typescript from "@rollup/plugin-typescript";
import { terser } from "rollup-plugin-terser";

export default {
  input: "index.ts",
  output: {
    // MUST NOT be "astronomy-cards.js". That is the shipped bundle: ~2800
    // hand-maintained lines registering twelve cards, tracked by the release
    // script. This config builds three TypeScript sources, so pointing the
    // output there means `npm run build` silently replaces the product with a
    // minified quarter of itself -- and the next release then aborts, because
    // terser leaves none of the version strings the bumper looks for.
    //
    // This also matches the "main" field package.json already declared, which
    // the previous value contradicted.
    // tests/test_version_literals.py enforces the general rule: no build
    // output may collide with a file the release script maintains.
    file: "dist/astronomy-cards.js",
    format: "es",
    sourcemap: false,
  },
  plugins: [
    resolve(),
    typescript(),
    terser(),
  ],
};
