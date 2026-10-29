# The demo study pipeline

How `docs/DEMO_STUDY.md`, `docs/demo_study/` and the demo half of the option bank were made (2026-10-28), in the order to run it again
on the host from `C:\coproducer`. Everything works on sandbox copies; the FL demo folder is only read, by the copy in step 1. Steps that
render need FL Studio closed, and the person's go-ahead.

1. Copy the demos: `robocopy "C:\Program Files (x86)\Image-Line\FL Studio 2026\Data\Demo projects\Demo songs" sandbox\demo_study\flp *.flp`.
2. `tools/demo_study/data.py`: read every project into `docs/demo_study/data/<song>.json` (what plays: muted clips left out, the
   master pitch applied, the render's audio key added once step 5 has run).
3. `tools/demo_study/render_prep.py`: render copies in `sandbox\demo_study\render` with plugins this FL edition lacks emptied.
4. Render the copies (FL closed): `render_folder_via_cli` from `sandbox\demo_study\render` to `sandbox\demo_study\wav`.
5. `tools/demo_study/keys.py` (the render's key), `tools/demo_study/sections.py`, then `tools/demo_study/measure.py`; copy
   `sandbox\demo_study\measure\all.json` to `docs/demo_study/measure_full.json`. Run step 2 again so the pages get the audio key.
6. `tools/demo_study/solo_plan.py`, then `tools/demo_study/solo.py build` and `solo.py redo FOLDER` (only what is new or changed),
   render FOLDER to `sandbox\demo_study\solo_wav` (FL closed), then `solo.py measure`; copy `sandbox\demo_study\solo_measure.json` to
   `docs/demo_study/solo_measure.json`.
7. `tools/gen_demo_options.py` (kits and instruments with their measured sound) and `tools/demo_study_docs.py` (the pages), then
   `python -m pytest tests/test_variety.py`.

The hand-written options (forms, grooves, bass lines, chords, arps, harmony, fx, mix, vocal, automation) and the fifteen style packs were
written from the pages and cite their songs; a change in the data means rereading the options that cite that song.
