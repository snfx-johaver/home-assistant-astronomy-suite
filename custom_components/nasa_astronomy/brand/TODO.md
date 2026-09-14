# Brand assets: outstanding work

`icon.png` (256x256) is the canonical brand icon for this integration.

There is currently no `logo.png` here. The file that used to occupy this path
was a byte-for-byte copy of `icon.png` — a square icon mislabeled as a logo,
not a wide lockup. Home Assistant's brand convention expects `logo.png` to be
a wide horizontal wordmark/lockup, which does not exist for this project yet.

Shipping the mislabeled copy was worse than shipping nothing: it silently
passed as "having a logo" while being wrong in shape. It was removed rather
than replaced with another placeholder.

**Needed from Joris:** real wide-format logo art (mark + "Astronomy Space
Suite" wordmark) before `logo.png` is reintroduced here. Until then, this
integration ships an icon but no logo, which HACS/Home Assistant treat as
optional.

There are also no `@2x` variants (`icon@2x.png`, `logo@2x.png`). The previous
ones falsely claimed 512x512 while actually containing 256x256 pixel data --
a HiDPI consumer scaling that into a 512 slot got a blurrier result than
just using the 1x file. Removed for the same reason: wrong is worse than
absent. Add real 512x512 exports here if/when they exist.
