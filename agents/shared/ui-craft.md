## UI craft standard

This standard is built into you. Apply it to every UI change, whether or not Impeccable is installed. `DESIGN.md` and the brief win over it on any conflict. A reviewer uses it as a checklist and never fixes anything.

### 1. Commit to a direction before writing code
- If `PRODUCT.md`, `DESIGN.md` or the brief fix a direction, follow it exactly. Do not steer it toward your own taste.
- Otherwise, write the direction in one line before any code: the audience, the screen's job, and one concrete reference world (for example "Swiss transit signage", "1970s lab manual" or "quiet ledger for accountants"). Record it in `DESIGN.md`.
- The job sets the priorities. **Operate** (apps, dashboards, settings): scanability, density, consistency. **Persuade** (landing, pricing): one message and one action per viewport. **Read** (docs, articles): measure, rhythm, hierarchy. **Showcase** (portfolios, galleries): the content leads and the chrome recedes.
- Refinement keeps the existing tokens, components and copy. A redesign replaces the look but keeps the content and behavior. Never do half of each.

### 2. Tokens
- Define color, type scale, spacing, radius, shadow and motion once, in the theme file, and reference them everywhere.
- Spacing on a 4px base: 4, 8, 12, 16, 24, 32, 48, 64, 96.
- A modular type scale (ratio 1.2 to 1.333), at most two families and at most three weights in use.

### 3. Typography
- Choose typefaces that express the direction. Inter, Roboto, Arial or the system stack only when `DESIGN.md` says so, or for a dense Operate screen where a neutral sans is a deliberate choice (then use tabular numerals for figures).
- Body text at least 16px on the web, line height 1.4 to 1.6, line length 45 to 75 characters.
- Build hierarchy with size, weight and space, not color alone. Display headings get tighter line height (1.1 to 1.25) and slightly negative letter spacing.
- Use real typographic characters: curly quotes, en dashes for ranges, the ellipsis character, and a non-breaking space between a number and its unit.

### 4. Color
- One neutral ramp tinted toward the brand hue (never pure gray), one primary accent, and semantic colors for success, warning, danger and info. The accent covers about a tenth of a screen.
- Contrast at least 4.5:1 for text, and 3:1 for large text and control boundaries. On a colored background, use a tint of that hue for secondary text, never gray.
- A dark theme is designed, not inverted: raise surfaces with lighter tints rather than shadows, desaturate accents, and avoid pure #000 and #fff.

### 5. Layout and composition
- One primary action per view, and it is the most prominent element. Secondary actions look secondary.
- Group by proximity: space inside a group is smaller than space between groups.
- Align to a grid so every edge lines up with something. Vary section rhythm on purpose; not every block gets the same height and padding.
- Prefer a clear focal point and some asymmetry over a symmetric grid of equal boxes. Use cards only for separate, actionable objects.
- Design for 390px and 1440px together. Reflow the layout; do not just shrink it.

### 6. Components and states
- Every interactive element has default, hover, visible focus, active and disabled states. Every data view has empty, loading, error and success states.
- Loading uses skeletons shaped like the final content, never a blank screen. An empty state says what belongs there and offers the first action. An error says what happened and how to recover, next to its cause.
- Touch targets aim for 44px and are never below 24px.
- Forms have visible labels (never placeholder-only), validate on blur and keep the user's input after an error.

### 7. Motion
- Motion explains change: 150 to 250ms for feedback, ease-out for entering, ease-in for leaving. Animate only transform and opacity.
- No decorative loops, no bounce on everything, and respect `prefers-reduced-motion`.

### 8. Copy
- Specific, plain words. Buttons name their action ("Save invoice", not "Submit"). Sentence case for UI text.
- No lorem ipsum, no placeholder people such as "John Doe", and no filler such as "Unlock the power of", "seamless" or "revolutionize".

### 9. Refuse list
These make an interface look machine-made. Never ship them unless `DESIGN.md` or the brief asks for them:
- Purple-to-blue or rainbow gradients, gradient text in headings, and glowing orbs or blurred blobs as decoration.
- Frosted glass as the default surface.
- A centered hero (big headline, one-line subhead, two buttons) followed by three equal feature cards with icons.
- Grids of identical cards, cards inside cards, and everything wrapped in a rounded box with a drop shadow.
- The same large radius and the same shadow on every element.
- Emoji used as icons, or mixed icon sets. Use one icon set at consistent sizes.
- Pure gray neutrals, pure black text on pure white, and gray text on colored backgrounds.
- Invented metrics, testimonials, logos or user counts that the brief does not provide.
- Centered body text longer than two lines, and paragraphs in all caps.
- Unmodified framework defaults (stock Bootstrap, Tailwind or component-library styling) shipped as the final look.

### 10. Pattern scan
Run these from the project root on the UI source folders (replace `<ui>`, for example `src/`). They work in Bash and PowerShell, and `--untracked` includes files you just created. Exit code 1 with no output means no hits. Outside a git repository, use `grep -rnIE` with the same patterns.

```
# Gradients and gradient text
git grep -n -I --untracked -E "linear-gradient|radial-gradient|bg-gradient-to|bg-clip-text|background-clip: *text" -- <ui>
# Glow, blobs and frosted glass
git grep -n -I --untracked -E "backdrop-filter|backdrop-blur|blur-2xl|blur-3xl" -- <ui>
# Colors hard-coded outside the theme file (replace the theme path)
git grep -n -I --untracked -E "#[0-9a-fA-F]{3,8}\b|rgba?\(|hsla?\(" -- <ui> ':!<theme file>'
# Emoji used as icons
git grep -n -I --untracked -P "[\x{1F300}-\x{1FAFF}\x{2600}-\x{27BF}]" -- <ui>
# Placeholder and filler copy
git grep -n -I --untracked -i -E "lorem|ipsum|john doe|jane doe|unlock the power|seamless|revolutioni[sz]e|supercharge|game-?changer" -- <ui>
# Invented social proof
git grep -n -I --untracked -E "[0-9]+[kKmM]?\+ (users|customers|teams|companies|developers)" -- <ui>
# Default fonts
git grep -n -I --untracked -w -i -E "Inter|Roboto|Arial" -- <ui>
# The same big radius and shadow everywhere (many files with high counts means sameness)
git grep -c -I --untracked -E "rounded-(2xl|3xl)|shadow-(lg|xl|2xl)|border-radius: *(1[6-9]|2[0-9])px" -- <ui>
# Images without alt text
git grep -n -I --untracked -P "<img(?![^>]*\balt=)" -- <ui>
# Removed focus outlines
git grep -n -I --untracked -E "outline: *none|outline-none" -- <ui>
# Motion without a reduced-motion path: if the first finds files and the second finds none, it is a hit
git grep -l -I --untracked -E "transition|animation|animate-|@keyframes" -- <ui>
git grep -l -I --untracked -E "prefers-reduced-motion|motion-reduce|useReducedMotion" -- <ui>
```

A hit is a lead, not a verdict. Open each one: fix it, or keep it only when `DESIGN.md` or the brief asks for it and say so in your return. A removed outline is fine only with a visible `:focus-visible` replacement.

### 11. Check once, then stop
- Run the pattern scan first. Then take screenshots at 1440x900 and 390x844 with the Screenshot command in `docs/ARCHITECTURE.md`, view them, and check them against sections 1 to 9.
- Fix everything you find in one batch, check once more, and stop. Do not loop on polish.
- If screenshots are not possible, check the source against this list and say that screenshots were unavailable.

### DESIGN.md without Impeccable
When Impeccable is not loaded, write root `DESIGN.md` with these sections:
- **Direction:** one paragraph covering the audience, the job and the reference world.
- **Tokens:** a table of color, type, spacing, radius, shadow and motion.
- **Components:** each component with its states.
- **Layout rules.**
- **Do and Don't:** include the refuse-list items most relevant to this project.
