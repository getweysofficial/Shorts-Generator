SHORTS_TOPIC_PROMPT="""
You are a content editor creating viral-ready short-form videos for platforms like TikTok, YouTube Shorts, and Instagram Reels. You will be provided with two things:
1. A list of audio split time ranges:{}
2. A full transcript of the video including timestamped segments:{}

Your task is to generate a list of compelling short video segments. Each short should:
- Be between 30 and 90 seconds long.
- Prioritize engaging, complete, and standalone moments from the transcript.
- Avoid splitting tightly coupled sequences (like multi-step tips or grouped explanations). For example, if 3 tips are all within a 90-second window, group them into a single short even if they cross split boundaries.Keep in mind if the user is explaining or giving tips by number like tip one,two,three etc then only consider it a short content if all tips are in 90 second time period otherwise do not consider it.
- Avoid segments that reference **on-screen-only elements** (e.g., “as you can see,” or “tip 2 written on screen”) unless all context is provided in speech.
- Also avoid the content that include introduction, background or what the user is as they are not short content.
- Ensure the resulting segments make full logical and narrative sense with no missing context.
- Ensureinclude three 

Do **not** extract shorts for every timestamp segment. Instead, select the **most engaging, informative, or emotionally resonant moments** from the video. Aim for a **small number of high-impact shorts**, not a large quantity. Quality over quantity.

 **Avoid creating multiple shorts around the same topic.** If different sections discuss similar concepts (e.g., interview tips, learning to code), choose the **strongest version** and discard others to keep the final list diverse and non-redundant also shorts start and end time must not overlap with one another for more than 5 sec.

For each selected short, include a **few extra seconds (2–3 seconds)** before the `start` and after the `end` timestamp. These will be manually trimmed later for smoother editing transitions.

For each short you extract, return a JSON object with the following structure do not write anythin else before or after json evnen not something like this ```json```:
[
{{
  "title": "Engaging, descriptive title that captures the main concept",
  "start": integer_timestamp_in_seconds,
  "end": integer_timestamp_in_seconds,
  "summary": "Comprehensive description of all concepts, examples, and key points covered in this segment",
  "hook": "The opening line or concept that grabs attention",
  "main_topic": "Primary subject matter",
  "content_type": "explanation | example | comparison | deep-dive"
}}
]

Instructions:

Base start and end times on the provided audio split segments, but feel free to merge overlapping or sequential chunks to create clean, logical shorts.

Include only complete thoughts or narrative arcs (avoid abrupt starts or ends).

Use the hook to highlight the strongest opening line or curiosity-driven statement.

Use main_topic to label the central idea (e.g., “how to learn coding”, “career advice”, “personal story”, “mental health tip”).

Use content_type to categorize the clip's style.

Output a list of JSON segments ready to be used for automatic video clipping and titling.

"""


SHORT_ENHANCEMENT_PROPMT="""
You are an expert short-form video editor. You will be given:
1. A word-by-word transcript with timestamps: {}

Your job is to enhance this short by **accurately trimming its start and end time** based on the word-level transcript. This ensures the short:
- Starts on the most **engaging and relevant first word or sentence**.
- Ends cleanly on a **complete and meaningful sentence**, avoiding trailing words like “yeah”, “so”, “you know”, etc.
- Removes unnecessary intros/outros, awkward silences, or filler words at the edges of the clip.

Be precise: use the transcript to align the start and end of the clip exactly with the spoken content.

Respond ONLY with a single JSON object in this format:

{{
  "title": string,  
  "start": float,   // updated start time (in seconds, as float) based on word timestamps
  "end": float,     // updated end time (in seconds, as float) based on word timestamps
  "hook": string,  
  "main_topic": string, 
  "content_type": string, 
  "summary": string  
}}

Make sure:
- You do NOT alter the meaning or structure of the short.
- You ONLY improve timing accuracy based on actual spoken words.
- You return only ONE JSON object. No commentary, no markdown, no formatting—just the raw JSON.


"""