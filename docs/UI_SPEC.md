# A.R.I.A. UI Spec 

Companion to `MASTER_SPEC.md` §4 (`shared-ui/`). Visual reference: the published "A.R.I.A. Interface Concept" mockup. This doc is the build source of truth; the mockup is the feel.

## 1. Design principles

1. **Voice is the UI; the screen is a status display.** If the user must read the screen to use A.R.I.A., the design failed. Every screen answers one question at a glance: *what is A.R.I.A. doing right now?*
2. **One centerpiece.** The Orb (animated canvas) carries all state — color + motion, legible across the room. Nothing else on screen is allowed to glow.
3. **Never block.** Transcript and cards scroll; nothing is ever modal except tool confirmation (which must be, for safety).
4. **Cards, not paragraphs.** Tool results render as glanceable cards with one big fact (temp, time, count), never raw JSON or long text.
5. **Dark cockpit, only.** Dark theme exclusively — this UI lives on desks and phones at all hours, and a second theme is work with zero payoff. Not built, not planned.

## 2. Design tokens (`shared-ui/src/styles/tokens.css`)

```css
:root {
  /* surfaces */
  --ground:   #060A11;   /* app background */
  --panel:    #0C1320;   /* cards, frames */
  --panel-2:  #101A2B;   /* nested surfaces, inputs */
  --line:     rgba(140, 180, 240, 0.14);

  /* text */
  --text:     #E6EEF9;
  --dim:      #8FA3C0;

  /* state accents — also the Orb's colors */
  --idle:      #7E93B4;
  --listening: #3AE0FF;   /* primary accent everywhere */
  --thinking:  #A78BFA;
  --speaking:  #3FDFA8;   /* doubles as success */
  --warning:   #FFC46B;   /* errors, confirmations */

  /* type */
  --font-display: "Chakra Petch", "IBM Plex Sans", sans-serif;
  --font-body:    "IBM Plex Sans", system-ui, sans-serif;
  --font-mono:    "JetBrains Mono", monospace;

  /* space: 4px grid */
  --r-sm: 10px; --r-md: 16px; --r-lg: 24px;
  --dur-1: 120ms; --dur-2: 200ms; --dur-3: 350ms;
}
```

Type scale (do not deviate): 32/28 display · 20 status label · 15 body · 13 secondary · 11 mono uppercase labels (letter-spacing 0.08em).

## 3. Components

| Component | States | Notes |
|---|---|---|
| `StatusOrb` | `idle · listening · thinking · speaking` | Canvas **dot-blob**: ~500 dots on a golden-angle (sunflower) spiral forming a filled organic blob; the edge undulates, the core stays calm. Idle: slow breathing drift, slate. Listening: beat-driven undulation tracking live mic amplitude, cyan. Thinking: dots swirl in a slow vortex (inner rings orbit slower), violet. Speaking: ripples travel outward through the field, mint. Full-screen click does nothing — it's a display, not a button. |
| `StatusLabel` | same 4 | Chakra Petch 20px, tinted to state color. Doubles as the wake hint when idle ("Say 'Hey Aria'"). `aria-live="polite"`. |
| `TopBar` | — | 48px, translucent. Left: connection dot + session tag (mono). Right: mute toggle, settings. Nothing else — ever. |
| `TranscriptThread` | streaming | Max-width 720px, newest at bottom, auto-scroll (pauses on user scroll-up). User lines right-aligned dim; A.R.I.A. lines plain text; tool cards inline between. Streaming text renders character-delta, no cursor decoration. |
| `ToolCard` | `result · confirm · error` | `result`: icon, one big fact, 2–3 meta rows. `confirm`: amber title, plain-language action ("Create page 'Q3 notes' in Notion?"), Approve/Cancel — the only blocking UI in the product. `error`: amber, says what failed + one recovery action ("Retry"). |
| `MicButton` | `idle · recording` | Mobile only (hidden ≥900px). 88px circle, bottom-center thumb zone, **hold to talk** (PTT). Recording = cyan fill + haptic tick. |
| `BriefingCard` | — | 07:00 proactive card: weather line, next event, tasks due, Play button. Dismissable. |
| `SettingsSheet` | — | Right slide-over. Sections: Connection (wake sensitivity, follow-up window), Memories (list, forget), Keys status (which providers connected — never shows key values), About (version, session/cost stats). |

## 4. Screen layouts UI

Desktop home (Electron, 1000px+):

```
┌─────────────────────────────────────────────────┐
│ ● connected · desktop              [mute] [⚙]   │
│                                                 │
│                     ╭───╮                       │
│                   ╱  ◉  ╲     Orb 320px         │
│                   ╲     ╱     centered, 38vh    │
│                     ╰───╯                       │
│                  Listening…                     │
│            "Hey Aria" — I'm awake             │
│                                                 │
│   ┌───────────────────────────────────────┐     │
│   │ You · 14:32   What's the weather?    │      │
│   │ A.R.I.A. · 14:32  [☀ 29° Mumbai card]  │      │
│   │                 It's 29° and hazy…   │      │
│   └───────────────────────────────────────┘     │
└─────────────────────────────────────────────────┘
```

Mobile (Capacitor, ≤900px): Orb 180px at top, compact transcript cards in the middle, `MicButton` fixed bottom-center. Top bar shrinks to dot + "A.R.I.A." + gear.

## 5. Motion

- UI transitions: 120ms (hover/focus), 200ms (cards in), 350ms (sheets). Ease `cubic-bezier(.2,.8,.2,1)`.
- Orb: continuous 60fps canvas — the only always-running animation in the product.
- Cards enter once: 12px rise + fade. No loops, no shimmer, no pulse on anything but the Orb.
- `prefers-reduced-motion`: Orb renders a single static frame per state; card enters become instant.

## 6. Accessibility

- StatusLabel is `aria-live="polite"` — screen readers hear state changes.
- Mic state is always visible in the TopBar or Orb (never a hidden permission).
- Text contrast ≥ 4.5:1 (`--dim` on `--ground` passes); state colors are additive cues, never the only signal — the Orb's motion differs per state too.
- Confirm card is focus-trapped; Approve is never the default-focused button (Cancel is).

## 7. Explicitly not building

Themes/light mode · dashboards or analytics views · avatars/personas · onboarding wizard (README covers setup) · notification center (briefings are cards) · any UI library (no MUI/shadcn — tokens.css + plain CSS is the whole system).

## 8. File mapping (`shared-ui/src/`)

```
styles/tokens.css        ← §2, verbatim
styles/app.css           ← layout + components, one file
components/StatusOrb.tsx ← canvas orb, one file
components/StatusLabel.tsx · TopBar.tsx · TranscriptThread.tsx
components/ToolCard.tsx  ← result | confirm | error variants
components/MicButton.tsx · BriefingCard.tsx · SettingsSheet.tsx
lib/ws.ts                ← typed events (MASTER_SPEC §2)
```
