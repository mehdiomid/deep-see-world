# Deep See World

An educational point-and-click puzzle adventure for kids (and their grown-ups), set in the ocean.
You dive from a sunlit coral reef down to the pitch-dark Midnight Zone, solving puzzles that are
built on real ocean science. Every animal you click teaches you something, and every fact you find
goes into your **Sea Journal**.

Everything runs in the browser. No server, no downloads, no external libraries or fonts. The
art is hand-drawn SVG and the sounds are made on the fly with the Web Audio API.

## Play

Open `index.html` in a browser. That's it.

## The dive

| Zone | Depth | Puzzle | What it teaches |
|---|---|---|---|
| ☀️ Sunlit Zone: coral reef | 10 m | **Who helps whom?** Match the animal partners using their clues. | Symbiosis: clownfish and anemone, cleaner shrimp and moray eel, pistol shrimp and goby |
| 🐢 Mini-game: Turtle Lunch | reef | Help a leatherback eat jellyfish and dodge plastic bags. | Leatherbacks eat jellyfish; plastic bags look like jellyfish to them |
| 🌒 Twilight Zone | 500 m | **The daily trip.** Decide where the lanternfish go at night and by day. | Diel vertical migration, the biggest migration on Earth |
| 🌑 Midnight Zone | 2,000 m | **Talk in light.** Watch glowing animals flash, then repeat the pattern. | Bioluminescence: anglerfish, Atolla jellyfish, vampire squid |

There are 21 facts to collect. Progress is saved in the browser (localStorage).

## Files

- `index.html`: the whole game (markup, SVG art, styles, and script).
- `deep-see-world.en.js`: all English text, including every fact. Kept separate so the facts are easy
  to review and the game is easy to translate: add `deep-see-world.<lang>.js` with the same keys.
- `tests/check.py`: zero-dependency checks (see below).
- `tests/play.html`: an automated playthrough used by `check.py`.

## Testing

```sh
python3 tests/check.py
```

This checks that every message and fact exists, every fact can be earned and appears in the journal,
the SVG groups are balanced, there are no external resources, and every clickable thing has an accessible
label. If Google Chrome is installed, it also loads each room headless and runs a full playthrough
that solves every puzzle (including some deliberate wrong answers), failing on any JavaScript error.
Set `DSW_SHOTS=/some/folder` to keep screenshots of each room.

Developer shortcut: `index.html#twilight` or `index.html#midnight` jumps straight to a room.

## Accuracy

The facts are meant to be true and simple enough for a child to read aloud. When adding or changing
one, check it against a trustworthy source (for example NOAA, the Smithsonian Ocean portal, or MBARI)
and keep the wording careful: "about", "most", and "many" are often more honest than exact numbers.

## Credits

Gameplay structure inspired by [Loft Day](https://marketa.behdad.org/loft-day). All art, text, and
code here are original.
