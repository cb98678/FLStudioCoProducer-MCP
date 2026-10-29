# Complaint to measurement

Each row names the measure to run before and after. Thresholds come from the targets file or the reference track, never from this file.

| Complaint | Measure | What to compare |
| --- | --- | --- |
| Muddy | `measure_band_energy` (low mid band) | Against the reference's low-mid level |
| Harsh | `measure_band_energy` (high mid and presence bands), `measure_spectral_centroid` | Against the reference; a high centroid with strong high-mid energy points here |
| Thin | `measure_band_energy` (bass and low mid) | Fundamental and low-mid balance against the reference |
| Boomy or too much sub | `measure_band_energy` (sub and bass), `measure_low_end_mono_ratio` | Sub level against the reference; side content in the lows |
| Dull | `measure_band_energy` (presence and air), `measure_spectral_centroid` | Against the reference |
| Too wide | `measure_mid_side_ratio`, `measure_stereo_correlation` | Against targets; negative correlation is a mono-compatibility problem |
| Too narrow | `measure_mid_side_ratio` | Against the reference |
| Squashed, no punch | `measure_crest_factor`, `measure_loudness_range` | Against the targets file range |
| Parts fighting | `measure_masking_overlap` between the two stems | Overlap before and after the change |
| Clipping or distortion | `measure_true_peak`, `count_clipped_samples` | Ceiling in the targets file |
| Too quiet or too loud | `measure_integrated_loudness` | Targets file (a mastering task) |
