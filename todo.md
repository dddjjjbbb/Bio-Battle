# To Do

- [ ] Let's think about how we can calculate a Controversy metric.

# Done

- [x] Sometimes text is truncated, see: "Prime Minister of the United Kingdom from 1979 to...". Perhaps text below bars is better?
  - DONE: Redesigned card layout with wrapped description text at bottom

- [x] Images should all be dithered and black and white to give an old school but consistent feel.
  - DONE: Added Floyd-Steinberg dithering, images now render as halftone B&W

- [x] It isn't clear at a glance what the categories refer to, can we come up with better names?
  - DONE: Renamed categories and added actual values:
    - Letters: "15 letters"
    - Lifespan: "76 yrs old"
    - Fame: "187.5K views"
    - Legacy: "14.3K words"
    - Reach: "192 editions"

- [x] Bio text is too short (e.g., "Polish-French physicist and chemist (1867-1934)")
  - DONE: Now uses Wikipedia's `extract` field which contains full opening paragraph
  - Added `Person.bio` property that returns extract if longer than description

- [x] Add emoji flags for country of birth/nationality
  - DONE: Now uses country codes instead of emoji (PDF fonts don't support emoji)
  - Displays as "[PL/FR]" after name for "Polish-French physicist"

- [x] Dithering should be less aggressive
  - DONE: Changed from pure 1-bit B&W to 4-level posterized grayscale
  - Higher contrast but more readable than pure halftone

- [x] Text under bar chart should attempt to be of a similar length for uniformity
  - DONE: Reformatted values to consistent lengths (~10-12 chars each)
  - "15 letters", "76 yrs old", "187.5K views", "14.3K words", "192 editions"

- [x] It's not clear what the square next to the name are (score?)
  - DONE: These were emoji flags that didn't render in PDF fonts
  - Changed to readable country codes: "[DE]", "[PL/FR]", "[GB/US]"

- [x] Certain characters fail to render: "The honorific Mah_tm_"
  - DONE: Added text sanitization that converts Unicode to ASCII equivalents
  - "Mahatma" now renders correctly

- [x] Is there a way while filling the space, to get more of the person's actual face in frame
  - DONE: Changed vertical crop from top-edge to 10% offset
  - Faces are typically in upper-middle of portraits, not at very top
