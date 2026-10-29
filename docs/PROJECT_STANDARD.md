# Project standard: names, colours and groups

Every project this system builds or tidies looks the same: a part has one colour and one name style wherever it shows up (channel rack, mixer, pattern list, playlist). The code is `src/coproducer/projorg.py`; the module is `apply_project_standard`; `build_remix_project` applies it by default.

FL Studio has no official colour standard. The nearest published habit is red for drums, blue for melodic parts, green for sends and yellow for buses ([Audeobox channel rack guide](https://www.audeobox.com/learn/fl-studio/fl-studio-channel-rack-template-setup-guide/)). This standard is Mark's own, chosen 2026-10-24: it keeps the buses yellow and the drums green as in that habit's spirit, and gives bass, synths, vocals and FX their own colours.

## Colours

| Family | Colour | Hex | Holds |
|---|---|---|---|
| Drums | green | #4CAF50 | kick, snare, clap, hats, shaker, rim, tom, crash, drum patterns |
| Bass | orange | #FF9814 | reese, sub, bass |
| Synths | purple | #9C27B0 | stab, chord, pad, arp, lead, pluck |
| Vocals | blue | #2196F3 | chops, vocal, vox |
| FX | red | #F44336 | fx, riser, impact, sweep, downlifter, noise |
| Buses | yellow | #FFEB3B | reserved for group buses (not created yet) |

| Automation | blue grey | #78909C | every automation clip, whatever its name says (a pick made 2026-10-25, not one of the person's families; change it freely) |

A part whose name has no known family is left alone and reported as unclassified. Master and utility tracks stay as they are.

## Names

- Channels and mixer inserts: no `CP_` prefix, no underscores or hashes, Title Case. Acronyms stay capitals (FX, BPM). Closed and open hats are `Hat Closed` and `Hat Open`. A repeated name gets a number (`Chop Hook`, `Chop Hook 2`).
- A mixer insert with one channel takes that channel's name; an insert with several takes the role name (Chops, Hats, Perc).
- Playlist rows take the role of what they hold (Drums, Reese Bass, Sub Bass, Stab, Arp, Chops, Vocal, FX). A row of mixed families is left alone.
- Patterns keep their names and take the colour of their family.
- Automation clips sit in a block of rows right below the music, one row per clip channel in the order they first play, each row named after its clip and coloured blue grey (approved 2026-10-25, copied from the Future House reference, which parks every clip in rows 16 to 27 under its music). A clip found anywhere else is moved into the block; `check` reports one that is not there.

## Channel rack groups

Drums, Bass, Synths, Vocals and FX, added after the groups the project already has. A channel's group is its family. Automation clips go into an Automation group (approved 2026-10-25). An audio clip channel with no family goes into Audio (FL 26 creates that group in every project); an audio clip with a family (the vocal, the FX bed) stays in its family's group so the family keeps one colour and one place.

## Silent channels

A channel with no notes in any pattern and no playlist clip is listed as silent, unless a Layer channel plays it (the Layer holds the notes). A silent channel that is routed to no mixer insert (track 0) is a stray and is removed when `drop_unused` is set. A silent channel that sits on an insert is kept and only reported: it may be a kit voice held for later.

## Buses

Drums, Vocals and FX each get a yellow bus insert, named `Drums Bus`, `Vocals Bus` and `FX Bus`, on the first free inserts after the last used one. Each family's inserts send to their bus, their direct route to the master is turned off, and each bus goes to the master. Bass and synths stay on the master until a reason appears.

Buses are built live in FL by `build_family_buses` (a recipe over `list_family_inserts`, `check_open_project`, `route_tracks_through_bus` and `set_track_color_verified`). Every step is read back. The reasons it is done in the open session and not in the file: no project we have contains a send, so the route flags in the file cannot be checked against anything, and FL's own API reports what it did.

- The saved copy of the project must be the one that is open. `check_open_project` compares insert names first and refuses to write when they differ.
- A send keeps the level its insert had to the master, so the mix does not change. FL's default send level is 0.8 (read from a live project), not 1.0; 0.8 is unity on a send.
- The bus colour is written in the byte order FL reports for a family colour it already shows, and read back. FL returns colours as signed 32-bit integers with an alpha byte on top.
- The person saves a copy afterwards. FL has no save call.

## What is not changed

Faders, plugins, notes and clips. The organizer alone makes no routing changes.

## Checked against

Event ids are from [PyFLP](https://github.com/demberto/PyFLP) (channel colour 128, group 145, group name 231, pattern colour 150, insert colour 149 and name 204, playlist track 238 and name 239), read back from FL 26.1.7 projects.

Confirmed in a live FL session on 2026-10-24, by reading the mixer through FL's API after opening an organized copy: insert names land on the right inserts (insert N is the Nth block of the file, master not counted), and colours show once the insert's appearance flag (event 42) is 1. FL ignores an insert colour while that flag is 0; the first version of the organizer missed this and inserts without an earlier colour stayed grey. Found by reading a project FL itself saved (v13_5, 2026-10-24): FL keeps what the file says only when the flags that go with it are set. Channel colour needs the channel appearance flag (event 41) to be 1, or FL resets it to default grey. Channel rack group names are sorted by FL when it loads, while each channel keeps its stored index, so the organizer writes group names in sorted order and remaps every channel's index by name. Playlist row colour needs the one-byte flag event (43) that follows each track record to be 1; the colour bytes in the record alone are ignored. Confirmed 2026-10-24 by painting nine rows through FL's API, saving as v13_7, and diffing against the unpainted file: the only changes were that flag going 0 to 1 on those nine rows (and the bass channel colour, below). FL also rewrote the bass channel colour from blue 0 to blue 20 in its own save, so the standard bass orange is #FF9814 (FL keeps what it writes; the earlier #FF9800 was nudged by FL on every save). Mixer routing flags sit one block after the name blocks in the file. `check` therefore compares what FL would show (`shown_channel_color`, `shown_group`, `shown_insert_color`, `shown_row_color`), not only the stored events.

Channel colours, insert names and colours, bus colours and playlist row colours (painted live) were read back from FL's API on v13_6. Channel rack groups can only be judged by eye or from a file FL saves: v13_7, saved by FL from v13_6, kept the group names and every channel's group index exactly as the organizer wrote them.
