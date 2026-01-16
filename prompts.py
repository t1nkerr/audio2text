SINGLE_PASS_PROMPT = f"""Generate a clean, readable English-language transcript of this entire podcast episode.

#background:
The podcast is produced by Trivium China, a consultancy on China policy. The speakers are usually Andrew Polk, Dinny Macmahon, Kendra Schaefer, Joe Mazur, Ether Yin, Joe Peissel, and occasionally other guests.

#instructions:
- Identify speaker names based on the conversation and label them consistently throughout
- Include a timestamp at the start of each speaker turn showing when they begin speaking
- Remove filler words (um, uh, like, you know, etc.)
- Remove false starts, unnecessary repetitions, and miscellaneous noise
- Correct misspellings
- Make edits when necessary to improve readability and coherence
- No markdown formatting

#output format:
[HH:MM:SS] Speaker Name: their transcript text

[HH:MM:SS] Speaker Name: their transcript text
...

#example format:
[00:00:00] Andrew Polk: Hi everybody, and welcome to the latest Trivium China podcast...

[00:00:45] Ether Yin: Doing great. Thank you, Andrew.

[00:00:52] Andrew Polk: It's great to have you on...
"""
