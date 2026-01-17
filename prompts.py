TRIVIUM_PROMPT = f"""Generate a clean, readable English-language transcript of this entire podcast episode.

#background:
The podcast is produced by Trivium China, a consultancy on China policy. The speakers are usually Andrew Polk, Dinny Macmahon, Kendra Schaefer, Joe Mazur, Ether Yin, Joe Peissel, Trey McArver, and occasionally other guests.

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


# Build prompt with episode context
CHINESE_PROMPT = f"""你的任务是逐字转录这段中文播客节目的对话。

#podcast show notes for background:
{episode['show_notes']}


#instructions:
1. 逐字转录，完整记录每一句话，包括所有口头禅、语气词.
2. 每当说话人轮换时，添加时间戳，格式为[HH:MM:SS]。
3. 明确标注说话人名字
6. 技术术语和出现的英文词保留原样。


#output format:
[HH:MM:SS] 主持人名字: 转录文字

[HH:MM:SS] 嘉宾名字: 转录文字
...

#example format:
[00:00:00] 主持人名字: 欢迎来到XYZ播客...

[00:00:45] 嘉宾名字: 大家好，我是陈亦伦，很高兴来到XYZ。

[00:00:52] 主持人名字: 其实大家对你的简历非常好奇。

"""