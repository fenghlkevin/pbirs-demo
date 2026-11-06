# P6 / PBIRS integration videos

Three 1080p, 24 fps MP4 editions with embedded subtitles, neural synthetic narration and 15 chapter markers.

- zh/output/P6_PBIRS_中文版_修正版.mp4 — Chinese. Written 行级权限 is unchanged. Narration uses the unambiguous homophone 杭 for the row-related 行 to obtain háng; 运行 remains unchanged.
- pt/output/P6_PBIRS_Portugues.mp4 — Portuguese content, with Portuguese vocabulary suitable for the Angola demonstration. Microsoft currently exposes no pt-AO voice in this service; the voice is pt-PT-RaquelNeural, not an Angolan native speaker recording.
- en/output/P6_PBIRS_English.mp4 — English content and en-GB-SoniaNeural narration.

Titles, explanatory labels, diagrams, subtitles and narration are localised. Actual application screenshots are combined with pan/zoom and explanatory animation, rather than continuous live screen recording. English Demo screens are browser-only interface previews, not a newly deployed English application. PBIRS report/portal screenshots retain their actual data and receive localised explanatory UI overlays. Identifiers such as Province_A and report paths are intentionally preserved. No credentials, keys or internal server URLs appear in the narration sent for speech synthesis.

The application and PBIRS server configuration were not changed during video production. Business-role expansion remains a future design; FullTrust remains unchanged. Each output/validation.json records full decode validation, duration and file size. Reproduction: prepare.py, render.py <zh|pt|en>, finalize.py <zh|pt|en>.
