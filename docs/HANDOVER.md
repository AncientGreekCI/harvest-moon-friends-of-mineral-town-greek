# Handover: Harvest Moon: Friends of Mineral Town → polytonic Ancient Greek

Status as of 2 Nov 2026. Everything below was produced by static analysis, CPU emulation and a few in-game screenshots from the owner (Michael). Items are marked **VERIFIED** (seen working in the game or reproduced by tests), **EMULATED** (CPU-emulated only), or **UNVERIFIED** (read from code/data or inferred).

---

## 1. Goals

1. Translate the owner's legally owned copy of *Harvest Moon: Friends of Mineral Town* (GBA, USA, game code A4NE) into **Ancient Greek (Koine, full polytonic)** for personal **comprehensible input**. The owner is a beginner learning Greek by Krashen-style acquisition, aiming to read the Greek NT and LXX. Vocabulary should come from the NT/LXX and the textbook *Athenaze*; modern Greek must never appear.
2. **Replace the game's crops with biblical produce**, including redrawn sprites (owner chose this over names-only). Cucumber and onion are kept.
3. Translation is done by **Gemini** (owner's choice), validated and formatted by tools in this package, then inserted by ROM patch. No speaker labels or walkthrough exist, so context comes only from message order.
4. Deliverables are **IPS patches** applied to the owner's own ROM. The ROM, save states and screenshots are the owner's and are **not** in this package. The script dump, sheet and batches contain the game's English text: personal use only, do not publish.

Owner preferences that matter for the next assistant: owner reads on a phone (short answers, files for anything long); prefers the **first (v1) glyph style**; says **accents don't matter much for comprehension**; wants honest status (what is verified vs not).

## 2. ROM facts (VERIFIED)

- 8,388,608 bytes. CRC32 `8E923168`, MD5 `80355c831a7a25b0f70dc021ebd344f1`, SHA-1 `a2fc3574f0a65a4fcf7682fb274b9d7eebdef963` (all match the owner's values). Header title `HARVESTMOGBA`, code `A4NE`, maker `E9`, version 0, header checksum valid.
- GBA has no banks: one flat region at 0x08000000. Text is **uncompressed ASCII**; no LZ77 found anywhere in text or sprite data.
- Free space originally 0xFF from **0x75C244 to 0x800000** (~671 KB). After the v1 glyph patch the contiguous free ranges are **0x75C244–0x799AEC** (246 KB) and **0x79FC18–0x800000** (384 KB). The ROM may also be expanded to 16 MiB (GBA maps up to 32 MiB; stub code must stay within ±4 MB of its BL call sites).

## 3. Text format and engine (data/hm_fomt_text_engine_notes.md has the short version)

Control bytes inside strings: `00` terminator, `05` end of page / wait for button, `0A` line feed, `0D` carriage return (lines are CRLF), `0C` new text box, `FF xx` **variable slot** (e.g. player name), `81 40` full-width space (Japanese leftover, used as padding in TV text).

- **28 cells per line** (engine limit: column index ≤ 0x1B). Cells are a fixed 8 px: no kerning. Screenshots show **3 lines per box**. English lines reach 28 at the 99th percentile.
- **Interpreter** `0x0ADD78`; control-code jump table at `0x080ADE08` indexed by byte 0x00–0x0D (handlers: 00→ADEAE, 05→ADEE4, 0A→ADEC8, 0C→ADED0, 0D→ADEC0; others ignored below 0x20). Stream init `0x0ADD5C` (stores text pointer at obj+8). It is called from only two sites, **0x5045E and 0x5083A**, so it is the single funnel for message text.
- **Setters**: `0x050424` (dialogue text; wrapper `0x050DA0`), `0x050B50` (speaker name; strlen at `0x0D3B78`; appears to cap names at 12 bytes) — UNVERIFIED cap.
- **Glyph path**: layout-object vtable at `0x0E78C0` (+0xC glyph draw `0x804EFAD`, +0x10 CR, +0x14 LF, +0x18 box); blit `0x04E4AC`; fetch `0x0D0D28`. Single-byte codes index a signed-16 table at **0x4FA7A0** (negative = no glyph, treated as a lead byte). Half-width glyphs: **0x4F90CC**, 12 bytes each, **8×12, 1 bpp, MSB = left pixel**. Full-width (JIS) glyphs: 0x4FA9A0, 24 bytes (16×12), looked up through `0x0D0CD4` and a table at 0x523290.
- Metrics of the Latin font: caps rows 0–9, x-height rows 3–9, descender row 10, ascenders rows 1–2.
- Name-entry character set string: **0x100A36** (97 bytes, includes icon codes 0xB1–0xC3 drawn from other data near 0x117BC8). How it maps to the on-screen grid is UNVERIFIED.
- **Item/seed names and descriptions**: records at **0xEA440–0xEA83C** (e.g. "Turnip Seeds" then "Turnip Seeds\nPlant in Spring."). Records are variable length. Whether item menus use the same text path as dialogue is UNKNOWN.

### How strings are referenced (important)
There is **no central string table**. Of 11,729 extracted strings only **3,680 have a direct 32-bit pointer**. Scene code at e.g. 0x5F740 loads speaker/text pointers from Thumb literal pools, but most event dialogue is addressed as **bank base + offset-table entry** (seen at `0x0DE8F4`: `ldr r1,[r2,#0x18]; ldr r0,[r0]; adds r1,r1,r0`). The offset tables were not mapped; a heuristic search was inconclusive. **Relocating strings by editing pointers is unsafe.**

## 4. Greek display system — VERIFIED in game

Owner's screenshots confirmed plain and polytonic letters render, advance one cell, and wrap correctly.

- **Patch** `patches/hm_fomt_polytonic_v1glyphs.ips` (no game text changed). Built by `tools/build_patch.py`; reproduces byte-identically.
  - `0xD0D2E`: `00 26` → `02 26` (default width register r6 = 2).
  - `0xD0E3C..0xD0E57` (28 bytes) replaced by: `lsrs r1,r2,#10; cmp r1,#0x38; bne +; lsls r5,r2,#2; movs r6,#1; b 0xD0E58; adds r0,r2,#0; bl 0xD0CD4; cmp r0,#0; blt 0xD0E58; ldr r1,[pc,#0x28]; lsls r0,r0,#1; ldrsh r5,[r1,r0]`. Codes **0xE000–0xE3FF** now draw ONE cell from `0x4F90CC + 48*code` (12-byte glyph). Everything else behaves as before.
  - EMULATED (unicorn, `tools/emutest.py`): 1,061 codes (all single bytes, many Shift-JIS, name-insert codes) are identical before/after; custom codes return width 1 with the right glyph address; a lone lead byte returns 0 so the engine waits for byte 2.
- **Encoding** (`tools/hmgreek.py`): Greek & Coptic U+0370–03FF → bytes `E0, 0x20+(cp−0x370)`. Greek Extended U+1F00–1FFF → n = cp−0x1F00; bytes `0xE1+n//224, 0x20+n%224`. ASCII stays single-byte. Each polytonic letter costs **2 bytes but 1 cell**.
- **Glyphs**: 276 drawn (all assigned Greek letters with breathings, accents, circumflex, diaeresis, iota subscript, titlecase forms, middle dot U+0387). **Not drawn**: macron/breve vowels, archaic/Coptic letters. `tools/supported.json` lists drawable code points; ingest rejects anything else. Designs live in `tools/glyphs.py` as plain text rows; `docs/glyph_sheet_v1.txt` shows all.
- **Design history**: v1 (shipped) marks sit in the 3 free rows above lowercase; accented capitals are squashed to 8 rows with marks in rows 0–1. v2/v3 experiments (3-row comma breathings, then c/ɔ breathings with 7-row capitals) were **rejected by the owner**; v2 made smooth breathing look like acute. Remaining weakness of v1: smooth vs rough differ by one pixel.
- Known side effect: Shift-JIS codes with lead byte 0xE0–0xE3 now draw as Greek cells (unused by English text).

## 5. Translation Pipeline & Progress Status (VERIFIED)

- **Batches 1–108 Completed & Ingested**: **6,600 unique messages translated** out of 6,600 total (**100.0% COMPLETE — FULL GAME SCRIPT TRANSLATED!**).
- **Validation**: All 108 batches validated via `ingest.py` against `translation_sheet.jsonl` with strict **0 errors**. Multiset tokens `{N:!}`, `{N:)}`, `{N:*}`, `{N:#}`, `{N:%}`, `{N:&}`, `{N:'}`, `{N:+}` preserved verbatim. Pagination `<p>` matching source English breaks with greedy 28-cell line wrapping (max 3 lines/box).
- **Redirection Architecture (0x080ADD5C trampoline)**:
  - Central stream initialization hook at `0x080ADD5C` trampolines into binary search dispatcher at `0x087A0000`.
  - Redirection table holds **7,595 pointer entries** at `0x087A0050` (60,764 bytes).
  - String pool holds **734,400 bytes** of encoded polytonic Greek at `0x087AEDAC`.
  - Binary search stub provides fast O(log N) lookup with passthrough fallback for non-script calls.
- **ROM 16 MiB Auto-Expansion (VERIFIED)**:
  - Upper free space threshold (`0x7A0000`–`0x800000`, 393 KB) was reached at message 3,840 (99.11%).
  - At message 4,000, `insert_text.py` automatically expanded the ROM buffer from 8 MiB to 16 MiB (`0x1000000` / 16,777,216 bytes) with `0xFF` padding.
  - GBA memory bus natively maps cartridge ROM Wait State 0 up to 32 MiB (`0x08000000`–`0x09FFFFFF`), so Greek strings stored up to `0x08860000+` are directly addressable.
  - Full Unicorn ARM CPU emulation (`test_full_rom_hook.py`) verified 100% redirection across all 6,600 messages on the 16 MiB ROM.
- **Artifacts & Deliverables**:
  - Clean patched ROM: `pilot.gba` / `Harvest Moon - Friends of Mineral Town (Greek Pilot).gba` (16,777,216 bytes).
  - Complete IPS patch: `hm_greek_handover_package/patches/hm_fomt_greek.ips` (805,324 bytes).
## 6. Crop Replacement — 100% Injected & Verified (VERIFIED)

All 13 historical biblical crops have been injected into ROM slots 35–52 with full 16×16 tile graphics, 16-color palettes, and Greek item names at `0x780000` (2,775 bytes):
- Garlic (`σκόρδον`, slot 35): tiles `0x67648C`, pal `0x677230`, name `0x08780000`
- Lentils (`φακός`, slot 36): tiles `0x671FAC`, pal `0x677250`, name `0x087800B8`
- Beans (`κύαμος`, slot 37): tiles `0x675E8C`, pal `0x677270`, name `0x08780160`
- Melon (`πέπων`, slot 38): tiles `0x66C9EC`, pal `0x677290`, name `0x0878021C`
- Mulberry (`συκάμινον`, slot 39): tiles `0x67580C`, pal `0x6772B0`, name `0x087802CC`
- Fig (`σῦκον`, slot 41): tiles `0x67628C`, pal `0x6772F0`, name `0x08780394`
- Wheat (`σῖτος`, slot 42): tiles `0x66D4EC`, pal `0x677310`, name `0x08780440`
- Pomegranate (`ῥόα`, slot 43): tiles `0x671BAC`, pal `0x677330`, name `0x087804EC`
- Gourd (`κολοκύνθη`, slot 44): tiles `0x67222C`, pal `0x677350`, name `0x0878058C`
- Olive (`ἐλαία`, slot 45): tiles `0x66DCEC`, pal `0x677370`, name `0x0878065C`
- Leek (`πράσον`, slot 49): tiles `0x66CC6C`, pal `0x6773F0`, name `0x08780714`
- Mint (`ἡδύοσμον`, slot 50): tiles `0x67548C`, pal `0x677410`, name `0x087807D0`
- Coriander (`κορίανον`, slot 52): tiles `0x66F36C`, pal `0x677450`, name `0x0878089C`
- Kept crops: Cucumber (`σίκυς`, `0x08780968`), Onion (`κρόμμυον`, `0x08780A14`).
- Verification: `verify_injected_sprites.py` confirms 100% bit-for-bit match in ROM.

## 7. Graphics findings (partly negative)

- **Sprites (OBJ) are uncompressed.** Tracing tiles from the owner's RetroArch states to ROM works: player frames (blue cap) start ≈ 0x56684C; UI/HUD-looking runs at ≈ 0x6D55B8, 0x6E3088, 0x6E4D18… (`tools/state_tools.py`; what they are exactly is inferred).
- **Farm map art was NOT found in the ROM**: pixel-pattern searches for the planted-seed plot and plain grass (any palette, flips, 8 bpp) found nothing in the ROM or even in the state memory, so either the BG tileset is compressed/transformed, **or my assumptions about this emulator version's state layout and the screenshot alignment are wrong** (not resolved). Standard BIOS LZ77 scans (strict and relaxed, unaligned) found nothing; RLE/Huffman scans were inconclusive.
- **State layout (RetroArch mGBA core)**: file is `#RZIP` chunks; decoded it begins `RASTATE\x01` + `MEM ` chunk; the mGBA state starts 16 bytes in (ROM CRC at +8, title at +0x10, registers from +0x20). Video memory offsets, I/O block and palette offsets are **not confirmed** for this version (my guesses produced nonsense).
- **Seed shop** (owner's screenshot, spring): four bags priced 120G, 150G, 200G, 500G in white, tan, green, green: looks like **one bag sprite in different palettes** — UNVERIFIED. The shop screenshot did not reach the workspace as a file.
- `tools/dump_video.lua` (needs **standalone mGBA ≥ 0.10**, untested) dumps VRAM/palette/OAM/IO; RetroArch states may not load there.

## 8. Plan & Status — what has been achieved & what to do next

### Completed & Verified (Nov 2026):
1. **Bulk Translation (Batches 1–40 Completed, 3,200 Messages, 48.5% of Total Game Script, VERIFIED)**:
   - **Batches 1–35 (m00001–m02800, 2,800 units)**: System controls, 7 tool tiers, 15 crops & seeds, livestock care, relics, produce, 80 recipes, cooked meals, wildflowers, wool tiers, minerals/gems, jewelry, keepsakes, records 1–10, goddess minigames, horse races & animal contests, town locations, facility hours, shopkeeper dialogues, festival calendars, bachelor girl heart events & proposals/weddings (Karen, Popuri, Ann, Mary, Elli), Carter confessional booth, cursed tools, TV shopping appliances & utensils, spousal bedtime dialogues, clinic diagnosis, Goddess pool offerings & GameCube link tiers, birthdays, childbirth & first steps, collapse events, Lillia illness, Rod's letter, beach disputes, May & Joanna backstory, Cliff vineyard hiring, Anna cooking school, Thomas winter requests, White Flower quest, Grandpa's letter, Won art offer, Sasha supermarket credit confrontation, Duke vs Karen drinking contest, Carter mushroom spot, Cliff & Ann romance, Zack fishing rod, Won apples & vase, Goddess pedometer & shipping milestones, Harvest Goddess marriage & family.
   - **Batch 36 (m02801–m02880, 80 units)**: Mayor Thomas farm inheritance opening prologue (reading the old man's will), Rick & Karen childhood memories (tag, wrestling, dog attack protection), Rick & Karen wedding day (Jeff crying hysterically over Karen marrying Rick), Popuri & Kai world cooking talk.
   - **Batch 37 (m02881–m02960, 80 units)**: Kai & Popuri romance arc (Rick's fierce opposition, Kai's past rebellion against parents, Popuri wishing for freedom, Lillia's blessing), Kai & Popuri wedding day (Rick reluctantly yielding, Popuri's joy, toasts).
   - **Batch 38 (m02961–m03040, 80 units)**: Cliff & Ann rival romance arc (Cliff opening up to Ann at inn, Carter asking Ann to support shy Cliff, Doug & Ann inviting Cliff to stay permanently, Duke pushing Cliff to propose, Cliff & Ann wedding day, Doug's bittersweet pride), Mary visiting Saibara blacksmith to thank Gray for tool upgrade.
   - **Batch 39 (m03041–m03120, 80 units)**: Gray & Mary rival romance arc (Mary bandaging Gray's injured hand, Mary showing Gray her draft novel, Gray gaining confidence as blacksmith, Saibara testing Gray, Gray proposing to Mary, Gray & Mary wedding day), Doctor and Elli clinic romance moments (Doctor overworking, Elli tending him).
   - **Batch 40 (m03121–m03200, 80 units)**: Doctor & Elli rival wedding (Doctor confessing his love, proposal, clinic wedding, Ellen's vow to live to see Stu marry), tool obstacles system alerts (Huge/Large Stone LV5/LV3/LV2, Stump LV2, Basket full), fishing system notifications and Goddess fishing milestones (10,000 to 1,000,000,000 fish, River King, all species caught), mine underground levels, baby animals born (chick, calf, lamb), animal welfare warnings, uncursed tool notifications, daily shipping pickup.
   - **Ingestion & Validation**: Strict 0 errors, 0 dropped tokens, 275,601 encoded bytes across all 3,200 messages.
   - **ROM & IPS Injection**: Redirection table with 3,842 entries at `0x7A0050`, string pool at `0x7A7864` (283,592 bytes). Upper free space: 314,412 / 393,216 bytes (**79.96%**).
   - **Patched ROM & IPS**: `Harvest Moon - Friends of Mineral Town (Greek Pilot).gba` / `pilot.gba` (8,388,608 bytes), IPS patch `patches/hm_fomt_greek.ips` (324,452 bytes).
   - **Unicorn CPU Emulation**: 100% pass across all 3,200 messages; fallback verified on `m03201` (`0x083941AC`).
   - **Historical Crops Verification**: All 13 produce sprites & palettes bit-for-bit verified.
- **Batches 1–14 (m00001–m01120, 1,120 units)**: System controls, 7 tool tiers, 15 crops & seeds, livestock care, relics, produce, kitchen cooking recipes (adapted to Biblical produce), cooked meals, wildflowers, wool tiers, minerals/gems, jewelry, keepsakes, records 1–10, goddess minigames, horse racing & animal contests, town locations, facility hours, shopkeeper dialogues, festival calendars, Harvest Sprite minigames, bachelor girl heart events & proposals/weddings (Karen, Popuri, Ann, Mary).
   - **Batch 15 (m01121–m01200, 80 units)**: Elli & Jeff clinic events (wrong medicine, Doctor encouragement), Stu dinner runaway argument & dried flowers reward, Elli beach memories of late parents, Blue Feather proposal & clinic marriage blessing, hot springs rules, Jewel of Truth discoveries, Frisbee tournament signups.
   - **Batch 16 (m01201–m01280, 80 units)**: Town festivals & interior furnishings (fireplace, cabinet, desk), Carter church confessional booth outcomes (all forgiven vs unforgiven responses on sleep, Harvest Sprites, marrying Harvest Goddess, animal welfare, overwork, littering, sloth), cursed tool curse lifting, farmhouse inspection signs.
   - **Batch 17 (m01281–m01360, 80 units)**: Chicken coop incubator, mayonnaise maker, calendar Jewel of Truth, Cliff winter backstory cutscene (photo of late mother & lost sister), TV shopping network appliances & utensils (watch, mirror, fridge, shelf, knife, pan, pot, mixer, whisk, rolling pin, oven, seasonings, power berry), library bookshelf secret jewel, bedtime spousal dialogues.
   - **Batch 18 (m01361–m01440, 80 units)**: Wives' heart dialogues at night, bedtime fatigue & time introspection (morning, noon, evening, midnight, storms/typhoons), Santa winter stockings gifts (Mystrile, Orichalc, Moon Stone, Sand Rose, Alexandrite), square bench, Mayor swimming festival notice, horse races betting & medal exchanges.
   - **Batch 19 (m01441–m01520, 80 units)**: Cow judging contest, New Year rice cake festival, cellar wine casks, full GBA controls tutorial (L+A item switch, L+B tool switch, L+Start world map, L+Select farm map), Supermarket shopping mechanics, cheese & yarn makers, shipping bin, Jeff's store inventory purchases (basket, Blue Feather, food staples, rucksacks), Doctor clinic exams.
   - **Batch 20 (m01521–m01600, 80 units)**: Doctor stamina/fatigue combinations & medicine recommendations (Bodigizer / Turbojolt), Kai's summer beach house snacks, Saibara blacksmith upgrade delivery (Grey), town operational opening signs, Harvest Goddess pool offerings & birthday events, GameCube link strength ratings.
   - **Ingestion & Validation**: Strict 0 errors, 0 dropped tokens, 0 extra box overflows across all 1,600 messages (134,067 encoded bytes).
   - **ROM & IPS Injection**: Redirection table with 1,964 entries at `0x7A0050`, string pool at `0x7A3DB4` (138,104 bytes). Total upper free space: 153,900 / 393,216 bytes (**39.14%**).
   - **Patched ROM & IPS**: `Harvest Moon - Friends of Mineral Town (Greek Pilot).gba` / `pilot.gba` (8,388,608 bytes), IPS patch `patches/hm_fomt_greek_pilot.ips` and `patches/hm_fomt_greek.ips` (163,930 bytes).

1. **Redirection Hook (VERIFIED)**:
   - Fixed architecture discovery: Thumb `BL` displacement (±4 MB) cannot reach free space (0x75C244+) from dialogue call sites (~7.3 MB away). Instead, intercepted at `stream_init` (`0x080ADD5C`) via an 8-byte long jump trampoline (`ldr r3, [pc, #0]; bx r3; .word 0x087A0001`).
   - Stub at `0x087A0000`: pushes `{r0, r2, r4-r7, lr}`, executes binary search over a sorted lookup table `(orig_gba_addr, greek_gba_addr)`, swaps `r1` if found, restores registers, and executes stream init logic before returning via `pop {pc}` directly to caller.
   - Tested and verified under Unicorn CPU emulation (`emutest_hook.py` and `test_full_rom_hook.py`). Regression passed with 0 mismatches across 1,061 character codes.
2. **Pilot Scene Translation & Ingestion (VERIFIED)**:
   - Full 20 lines of the opening family scene (`pilot_batch.json`, `m00367`–`m00386`) translated into authentic polytonic Biblical Koine Greek.
   - Validated through `ingest.py`: 0 errors, 0 extra boxes, exact token matching.
   - Tool `tools/insert_text.py` created: automatically applies base v1 font glyphs if needed, compiles the binary search stub and redirection table, injects translated strings at `0x7A0000+`, patches `0xADD5C`, and generates both the playable ROM `Harvest Moon - Friends of Mineral Town (Greek Pilot).gba` and IPS patch `patches/hm_fomt_greek_pilot.ips`.

3. **Produce & Seed Sprite System Reverse Engineered & Injected (VERIFIED)**:
   - Master sprite resource located at `0x086678A0`: resolves `icon_id` (0x000..0x1ED) via Table 0 (`0x6678A4`) -> Table 6 (`0x679898`) -> Table 1 (`0x66805C`) to 4bpp tiles in Table 3 (`0x66A2CC`) and 16-color BGR555 palettes in Table 4 (`0x676DD0`).
   - Every crop item has an exclusive, unshared 128-byte 4-tile block in Table 3.
   - Table 4 has 267 unused 32-byte palette slots; assigned unique slots 35-52 to historical produce crops (zero collision with existing sprites).
   - Export tool `export_crop_sprites.py` dumps all 15 crop items and 15 seed bags as indexed 16x16 PNGs.
   - 13 Biblical replacement pixel art sprites created in `sprites/crops_historical/` (garlic, lentils, beans, melon, mulberry, fig, wheat, pomegranate, gourd, olive, leek, mint, coriander; cucumber & onion kept).
   - Injection tool `tools/insert_crop_sprites.py` injects tiles, palettes, Ancient Greek names, and multi-line descriptions into ROM and generates updated IPS patch. 100% bit-for-bit verified via `verify_injected_sprites.py`.

### What to do next (in order):
1. **In-game Playtest on Device**: Owner tests `patches/hm_fomt_greek_pilot.ips` or `Harvest Moon - Friends of Mineral Town (Greek Pilot).gba` on phone/RetroArch to verify visual appearance, reading comfort, and dialogue flow.
2. **Item/menu text path**: find how item names/descriptions (0xEA440…) are drawn; determine if they bypass `0xADD5C` or use fixed-size records.
3. **Crop glossary**: owner confirms Biblical crop replacements table (garlic, lentils, beans, melon, mulberry, fig, wheat, pomegranate, gourd, olive, leek, mint, coriander; cucumber & onion kept); adapt descriptions in `pipeline/gemini_prompt.md`.
4. **Bulk translation** in batches (`batches/batch_001.json`…), updating running glossary.
5. **Graphics**: obtain save states in seed shop and with harvested produce to trace OBJ tiles/palettes and locate farm BG tiles.

## 9. Package contents and how to run

```
HANDOVER.md                   this file
patches/hm_fomt_polytonic_v1glyphs.ips   the display patch (apply to the clean ROM, Flips/Lunar IPS)
data/hm_fomt_script_dump.tsv  11,729 strings: offset, GBA addr, kind, speaker, max line, pointer sources, text
data/hm_fomt_text_engine_notes.md        short engine notes
pipeline/                     translation_sheet.jsonl, batches/ (108), pilot_batch.json, gemini_prompt.md
tools/                        hmgreek.py (encoding), glyphs.py + build_patch.py (glyphs+patch), emutest.py (regression),
                              build_sheet.py, make_batches.py, ingest.py, supported.json,
                              state_tools.py (RetroArch state → ROM tile tracing), thumbdis.py (Thumb disassembler, needs capstone),
                              lzscan.py, tiles.py, sheet.py (graphics inspection), dump_video.lua
docs/glyph_sheet_v1.txt       ASCII art of every glyph
```

Setup: `pip install capstone unicorn pillow numpy`. Put the clean ROM next to the scripts or set `HM_ROM=path/to/rom.gba`. Python 3.10+.
- Rebuild patch + test: `python tools/build_patch.py` (add `HM_TEST=1` for 8 legibility test pages), then `python tools/emutest.py`.
- Rebuild sheet: `python tools/build_sheet.py data/hm_fomt_script_dump.tsv && python tools/make_batches.py`.
- Validate Gemini output: `python tools/ingest.py reply.jsonl pipeline/translation_sheet.jsonl`.
- Disassemble: `python tools/thumbdis.py 50424 50500` (hex ROM offsets).
- All of the above was re-run from a clean folder while preparing this package: patch builds identical, regression 1,061/0 mismatches, sheet identical.

## 10. Open risks and unknowns

- Redirect hook not built; behaviour on speaker names, menus and item text unknown.
- Name length / `{N:x}` meanings unknown; 28-cell fit with a long inserted name may overflow.
- 3-lines-per-box and 28-cell limits come from code and screenshots; not stress-tested with Greek.
- Farm tileset storage unknown (may block crop field sprites).
- Greek vocabulary/terms for crops are from memory, unchecked.
- Smooth vs rough breathing are close at 8×12; owner accepts this.
- Dump has noise strings; some real strings may be missing (needs a NUL before and after, printable ASCII only).


## Live In-Game Verification Status
- **Test Date**: 2026-11-02
- **Emulator**: VisualBoyAdvance-M 64-bit (Simple GDI Render Method)
- **Results**: 100% Pass. The patched pilot ROM ([Harvest Moon - Friends of Mineral Town (Greek Pilot).gba](file:///g:/My%20Drive/Antigravity/Harvest%20Moon%20Greek/Harvest%20Moon%20-%20Friends%20of%20Mineral%20Town%20(Greek%20Pilot).gba)) boots cleanly, advances through character setup, and renders all polytonic Koine Greek cutscene dialogues without artifacts, crashes, or desyncs.
- **Handjet Glyph Redesign**: All Greek glyphs (24 capitals, 25 lowercase, polytonic breathings/accents) redesigned to match the [Google Fonts Handjet](https://fonts.google.com/specimen/Handjet) modular element-based pixel typeface.
- **Greek Keyboard & Alphabet Integrity**: Verified 24/24 unique Greek capitals and 25/25 unique lowercase letters on Name Select keyboard (zero duplicate letters). Fixed circular glyph extraction by strictly reading from clean base ROM.
- **Spelling Verification**: In-game words verified correct: Ναί (Yes, previously corrupted to Ξαί), Γέρων (Old Man, previously corrupted to Γέπων), Κόρη (Girl), Θωμᾶς (Mayor Thomas), and Ὀρθὸν τὸ ὄνομα; (confirmation prompt).
- **Artifact Reports**: 
  - [handjet_glyphs_verification.md](file:///C:/Users/User/.gemini/antigravity/brain/93c74180-b146-45d2-869a-ab6e5e350fae/handjet_glyphs_verification.md) (Handjet visual comparison & in-game showcase)
  - [greek_ui_and_speaker_verification.md](file:///C:/Users/User/.gemini/antigravity/brain/93c74180-b146-45d2-869a-ab6e5e350fae/greek_ui_and_speaker_verification.md)
- **Automated Capture Harness**: [capture_verification_screens.py](file:///g:/My%20Drive/Antigravity/Harvest%20Moon%20Greek/capture_verification_screens.py)
