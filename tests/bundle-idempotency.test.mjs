/**
 * A card bundle must survive being evaluated twice.
 *
 * Run with: node --test "tests/*.test.mjs"
 *
 * Why this is a real requirement and not defensive programming
 * -----------------------------------------------------------
 * Lovelace fetches one resource per registered URL, and every registered URL
 * for this integration resolves into the same `/local/community/astronomy-cards/`
 * directory. Two entries that name the same file -- a resource a user added by
 * hand next to the one `__init__.py` registers (README "Troubleshooting" tells
 * them to go and check that list, so people do add them), a YAML dashboard that
 * declares its own `resources:`, or a stale entry left behind by a URL rewrite
 * -- are two fetches evaluated against one shared `customElements` registry.
 *
 * `customElements.define` throws `NotSupportedError` on a name already in the
 * registry. In an unguarded bundle the throw aborts the rest of the module, and
 * the registration block is ordered defines-then-`customCards`, so the cost is
 * not the one duplicate card: it is every card in the bundle plus every one of
 * its picker entries. The dashboard shows "Custom element doesn't exist" for
 * all of them.
 *
 * What is asserted, and what is deliberately not
 * ---------------------------------------------
 * This asserts the *property* -- evaluating twice is harmless -- not any
 * particular mechanism for reaching it. `astronomy-cards.js` has always had
 * that property (`defineElement` wraps `customElements.get`,
 * `registerCustomCard` wraps `customCards.some`); `deepsky-cards.js`, same
 * directory and same release, had ten raw `customElements.define` calls and an
 * unguarded `push`. A guard in one sibling and not the other is not a style
 * difference, and the test is written so that a third bundle added later is
 * held to whichever of the two got it right.
 *
 * Bundles are enumerated from `BUNDLES`, not listed here, because the failure
 * being guarded against is precisely a bundle nobody remembered.
 */

import test from "node:test";
import assert from "node:assert/strict";

import { BUNDLES, makeSandbox, evaluateBundleInto } from "./harness.mjs";

const BUNDLE_ENTRIES = Object.entries(BUNDLES);

/** Card types currently advertised to the Lovelace card picker. */
function cardTypes(sandbox) {
  return (sandbox.window.customCards || []).map((card) => card.type);
}

function duplicates(values) {
  const seen = new Set();
  const dupes = new Set();
  for (const value of values) {
    if (seen.has(value)) dupes.add(value);
    seen.add(value);
  }
  return [...dupes];
}

test("every card bundle is discovered", () => {
  // Non-vacuity for the whole file: the loops below must not pass over an
  // empty list. Two bundles ship from two directories each.
  assert.ok(
    BUNDLE_ENTRIES.length >= 4,
    `expected at least 4 bundle copies, got ${BUNDLE_ENTRIES.length}`,
  );
});

for (const [name, file] of BUNDLE_ENTRIES) {
  test(`${name}: a single evaluation registers cards`, () => {
    // Non-vacuity per bundle. Without this, a bundle that registered nothing
    // at all would satisfy every assertion below by having nothing to lose.
    // This passes before and after the fix -- it is the control that shows the
    // suite is discriminating rather than uniformly red.
    const sandbox = makeSandbox();
    evaluateBundleInto(sandbox, file);

    assert.ok(
      sandbox.customElements._names().length > 0,
      `${name} registered no custom elements at all`,
    );
    assert.ok(
      cardTypes(sandbox).length > 0,
      `${name} advertised no cards to the picker`,
    );
  });

  test(`${name}: evaluating it twice keeps every card`, () => {
    const sandbox = makeSandbox();
    evaluateBundleInto(sandbox, file);

    const elementsAfterFirst = sandbox.customElements._names();
    const cardsAfterFirst = cardTypes(sandbox);

    // The whole test: a second evaluation against the same registry.
    assert.doesNotThrow(
      () => evaluateBundleInto(sandbox, file),
      `${name} threw when evaluated a second time`,
    );

    assert.deepEqual(
      sandbox.customElements._names().sort(),
      elementsAfterFirst.slice().sort(),
      `${name} lost or gained custom elements on the second evaluation`,
    );
    assert.deepEqual(
      cardTypes(sandbox).sort(),
      cardsAfterFirst.slice().sort(),
      `${name} changed its picker entries on the second evaluation`,
    );
  });

  test(`${name}: a double evaluation does not duplicate picker entries`, () => {
    // Distinct from the test above: surviving the second evaluation is not
    // enough if it leaves the card picker showing each card twice. This is the
    // `customCards.some` half of the guard, which a bundle can miss while
    // having the `customElements.get` half.
    const sandbox = makeSandbox();
    evaluateBundleInto(sandbox, file);
    try {
      evaluateBundleInto(sandbox, file);
    } catch {
      // The throw is reported by the test above; this one is about the picker.
      return;
    }

    assert.deepEqual(
      duplicates(cardTypes(sandbox)),
      [],
      `${name} advertised duplicate cards to the picker`,
    );
  });
}

test("the two copies of each bundle behave identically", () => {
  // The bundles ship from two directories and must stay byte-identical, so a
  // guard added to one copy and not the other is a real failure mode. Compare
  // observable registration rather than bytes -- test_cards_resource_version.py
  // already pins the byte equality, and this is the behavioural counterpart.
  const observed = new Map();
  for (const [name, file] of BUNDLE_ENTRIES) {
    const sandbox = makeSandbox();
    evaluateBundleInto(sandbox, file);
    const bundle = name.replace(/Www$/, "");
    const fingerprint = JSON.stringify({
      elements: sandbox.customElements._names().sort(),
      cards: cardTypes(sandbox).sort(),
    });
    if (!observed.has(bundle)) observed.set(bundle, new Map());
    observed.get(bundle).set(name, fingerprint);
  }

  for (const [bundle, copies] of observed) {
    const distinct = new Set(copies.values());
    assert.equal(
      distinct.size,
      1,
      `${bundle} copies register different things: ${[...copies.keys()].join(", ")}`,
    );
  }
});
