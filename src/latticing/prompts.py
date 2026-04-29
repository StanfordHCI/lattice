
# Prompts for Session Observation
OBSERVE_PROMPT = """
You will be given a transcript summarizing {interaction_description} for the user, {user_name}.

Your primary goal is to bridge the gap between what users DO which can be observed and what users THINK / FEEL which can only be inferred.

## Guiding Principles
1.  **Focus on Behavior, Not Just Content:** Text in a DOCUMENT or on a WEBSITE is not always indicative of the user's emotional state. (e.g., reading a sad article on **CNN** doesn't mean the user is sad). **Focus on feelings and thoughts that can be inferred from {user_name}'s *actions*** (typing, switching, pausing, deleting, etc.).
   - For example, typing about achievements or awards (e.g., in a job statement) does **not** automatically mean the user feels proud — they might be feeling **anxious**, **reflective**, or **disconnected** instead.  
   - Prioritize cues from the user’s *behavior* — such as typing speed, pauses, rewrites, deletions, or switching between tabs — to infer feelings.
2.  **Use Specific Named Entities:** Your analysis must **explicitly identify and refer to specific named entities** mentioned in the transcript. This includes applications (**Slack**, **Figma**, **VS Code**), websites (**Jira**, **Google Docs**), documents, people, organizations, tools, and any other proper nouns.
    - **Weak:** "User switches between two apps."
    - **Strong:** "User rapidly switches between the **`Figma`** design and the **`Jira`** ticket."

## Task

Using the transcript of {user_name}'s activity, provide inferences about their emotional state or thoughts.

Consider the following examples of good inferences:
> ⚠️ **Note:** Avoid inferring emotions directly from positive or negative content. Writing about success, awards, or positive feedback does not imply pride or happiness — just as reading about a tragedy does not imply sadness. Focus on *how* the user interacts with the material.

- **Behavior:** "User messages **Bob** on **Slack** ‘can’t make it to the party :( need to finish this update for my advisor.’"
    * **Inference:** This suggests the user may be **disappointed** or **stressed**, prioritizing work (for their "advisor") over a social event (with "Bob").
- **Behavior:** "User rapidly switches between the **`Figma`** design and the **`Jira`** ticket 5 times in 30 seconds."
    * **Inference:** This suggests **urgency** or **comparison**. The user may be trying to ensure their **`Figma`** design perfectly matches the **`Jira`** requirements.
- **Behavior:** "User repeatedly re-writes the same sentence in an email to their boss, **Sarah**, in **`Microsoft Outlook`**."
    * **Inference:** This suggests **uncertainty**, **anxiety**, or a desire to be precise when communicating with their boss, "Sarah."
- **Behavior:** "User spends 10 minutes focused on a single **`VS Code`** window without switching, then messages 'just finished the main feature!' in the **#dev-team** **Slack** channel."
    * **Inference:** This suggests a state of **deep focus** ("flow") followed by a feeling of **accomplishment** and a desire to share progress with the **#dev-team**.
---

## Output Format

Provide your observations grounded *only* in the provided input. Low confidence observations are expected and acceptable, as this task requires inference.

Evaluate your confidence for each observation on a scale from 1-10.

### Confidence Scale

Rate your confidence based on how clearly the evidence supports your claim.

* **1-4 (Weak):** A speculative inference. The behavior is ambiguous or requires inference.
* **5-7 (Medium):** A reasonable inference based on a clear pattern of behavior (e.g., "repeatedly re-writing" suggests uncertainty).
* **8-10 (Strong):** Explicit, directly stated evidence (e.g., user types "this is so frustrating" or uses a strong emoji like `:(`).

Unless there is explicit evidence of the user's emotional state or thoughts, the confidence will be low (< 5).

**Return your results *only* in this exact JSON format. Do not include any other text, preamble, or apologies.**

### Filtering Rule

Only include observations that reflect a **meaningful inferred emotional or cognitive state** (e.g., anxiety, focus, doubt, relief, curiosity, frustration, motivation, etc.).  
If the available evidence does **not** suggest any notable emotion or thought process — for example, if the user appears neutral, routine, or simply performing mechanical actions — then **output an empty list**:
{{ "observations": [] }}

Else, return the following JSON format (at least 1 observation):
{{
  "observations": [
    {{
      "think_feel": "<1-2 sentences stating how {user_name} feels or what they are thinking>",
      "actions": "<1-2 sentences providing specific evidence of what {user_name} is doingfrom the input, explicitly naming entities, supporting this observation>",
      "confidence": "[Confidence score (1–10)]"
    }}
  ]
}}

# Input
Here is a summary of {interaction_description}:
{interactions}
"""

OBSERVATION_TO_INSIGHT_PROMPT = """
Your task is to produce a set of insights given observations about a user. 

An "Insight" is a remarkable realization that you could leverage to better respond to a design challenge. Insights often grow from contradictions between two user observations or from asking yourself “Why?” when you notice strange behavior. One way to identify the seeds of insights is to capture “tensions” and “contradictions” as you work.

Given this input, produce at least {limit} insights about {user_name}. Focus only on the insights, not on potential solutions for the design challenge. Provide both the insights and evidence from the input that support the insight in the output. 

# Input
You are provided these traits from direct observation about what {user_name} is doing, thinking, and feeling:

{observations}
"""

FORMAT_INSIGHT_PROMPT = """
You are an expert in formatting insights into a JSON format. Your task is to format a list of insights provided in prose into a JSON format.
    
# Input
You are provided with a list of insights in prose format.
${insights}

# Output
Return your results in this exact JSON format:
{{
    "insights": [
        {{
            "title": "Thematic title of the insight",
            "tagline": "Provide the insight in a succinct statement (1-2 sentences).", 
            "insight": "Insight in 3-4 sentences",
            "context": "[1-2 sentences when this insight might apply (e.g., when writing text, in social settings)]",
            "supporting_evidence": "[At least 2-3 sentences providing specific evidence from the input, explicitly naming entities, supporting this insight]"
        }}, 
        {{
            "title": "Thematic title of the insight",
            "tagline": "Provide the insight in a succinct statement (1-2 sentences).", 
            "insight": "Insight in 3-4 sentences",
            "context": "[1-2 sentences when this insight might apply (e.g., when writing text, in social settings)]",
            "supporting_evidence": "[At least 2-3 sentences providing specific evidence from the input, explicitly naming entities, supporting this insight]",
        }}
        ...
    ]
}}
"""

MAP_EVIDENCE_PROMPT = """
You are provided with a list of observations about the user and the insight. Map the observations that form the supporting evidence for the insight.

# Input
Supporting Evidence: 
{evidence}

Observations:
{observations}

# Output
Return your results in this exact JSON format:
{{
    "supporting_ids": [List of IDs of the observations supporting the insight based on the supporting evidence. Return an empty list if no observations support the insight],
}}
"""

INSIGHT_SYNTHESIS_PROMPT = """
I have insights across multiple sessions of observing ${user_name} along with the context in which the insight emerges. 

# TASK
An "Insight" is a remarkable realization that you could leverage to better respond to a design challenge. Insights often grow from contradictions between two observations or from asking yourself “Why?” when you notice strange behavior. One way to identify the seeds of insights is to capture “tensions” and “contradictions” as you work.

Your task is to help synthesize across the input about ${user_name} to form deeper insights about ${user_name}.

Across the insights, consider the following categories:
1. Recurring themes or patterns: Which insights appear across as a recurring theme or pattern EVEN if the context is different?
2. Specific situations or for specific people: Which insights appear only in specific situations or for specific people? Why might this be the case?
3. Contradiction and tension: Which insights contradict each other — and what might that reveal about unique tensions?
4. Explanations and motivations: Which insights provide explanations and motivations for each other?

At the end, review all of the insights and ensure that you did not miss important insights during the synthesis process. If there are unmerged insights, include them in the output. It is important to not lose any unique insights during the synthesis process.


# Example
Examples of synthesized insights:
{{
    "title": "Informality as Strategic Ambiguity",
    "tagline": "Mark’s frequent self-deprecating comments and expressions of uncertainty serve a dual purpose: authentically conveying anxiety while also inviting collaboration and feedback.",
    "insight": "Mark’s deliberate code-switching between formal academic prose and aggressively casual, irreverent language serves to assert status, test boundaries, and manage likability across varied social hierarchies. Casual language lets him engage in competitive or harsh discourse among peers with plausible deniability, while deference and formality reappear with senior collaborators.",
    "merged": [
        "2",
        "10",
    ],
    "context": "This linguistic flexibility is seen in Slack and Messages with peers (where he jokes, teases, and self-deprecates) versus careful formality in Overleaf or communication with advisors.",
    "reasoning": "Contrast between casual authority in technical help ('this shit'), banter with Connor ('hahaha yeah he took the money'), deferential tones used with advisor Maria, and strictly formal, precise academic writing in Overleaf demonstrates adaptive code-switching."
}}

# Input
Insights:
{insights}

# Output
Return the final list of insights in a JSON format. 

{{
    "insights": [
        {{
            "title": "Thematic title of the insight",
            "tagline": "Provide the insight in a succinct statement (1-2 sentences).", 
            "insight": "Insight in 3-4 sentences",
            "context": "1-2 sentences when this insight might apply (e.g., when writing text, in social settings)",
            "merged": [List of insight IDs that were merged into this insight. Include a single ID if the insight is not merged with others.]
            "supporting_evidence": "1-2 sentences explaining why this insight emerged"
        }},
    ...
    ]
}}
"""