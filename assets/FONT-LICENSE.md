# Space Grotesk

`SpaceGrotesk-500.woff2` and `SpaceGrotesk-700.woff2` are subsets of Space Grotesk,
cut down to only the characters the header uses (66 glyphs, ~4.5 KB each).

Space Grotesk is by Florian Karsten, released under the SIL Open Font License 1.1,
which permits embedding. Full license: https://openfontlicense.org

Source: https://fonts.google.com/specimen/Space+Grotesk

The subsets are inlined into the header SVGs as base64 because SVGs loaded through
`<img>` run in secure animated processing mode, which blocks external references —
a webfont fetched over the network would silently fall back to a system font.
