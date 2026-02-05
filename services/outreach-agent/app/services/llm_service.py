"""LLM integration: Claude (primary) + GPT-4o-mini (fallback for cheap tasks)."""

import json
import logging
from typing import Optional

import anthropic
import openai

from app.config import settings

logger = logging.getLogger(__name__)


class LLMService:
    """Unified interface for Claude and GPT-4o LLM calls."""

    def __init__(self):
        self._anthropic = None
        self._openai = None

    @property
    def claude(self):
        if not self._anthropic and settings.anthropic_api_key:
            self._anthropic = anthropic.Anthropic(api_key=settings.anthropic_api_key)
        return self._anthropic

    @property
    def gpt(self):
        if not self._openai and settings.openai_api_key:
            self._openai = openai.OpenAI(api_key=settings.openai_api_key)
        return self._openai

    # ── Email Composition ─────────────────────────────────────

    async def compose_initial_email(
        self,
        contact_name: str,
        contact_title: str,
        firm_name: str,
        one_pager: str,
    ) -> dict:
        """
        Compose a personalised initial outreach email using Claude.

        Returns: {"subject": str, "body_text": str, "body_html": str}
        """
        prompt = f"""You are Suchi, a professional executive search agent. You are reaching out to executive search firms on behalf of your client, Rajamohan, who is an exceptional CTO candidate targeting a 5 Cr+ package.

Write a brief, professional, and compelling initial outreach email to:
- Contact: {contact_name} ({contact_title})
- Firm: {firm_name}

Here is Rajamohan's one-pager brief:
---
{one_pager}
---

GUIDELINES:
- Be respectful of their time — keep it under 150 words
- Introduce yourself as Suchi, an executive search agent representing Rajamohan
- Briefly highlight Rajamohan's CTO credentials from the one-pager
- State that he is open to CTO opportunities with 5 Cr+ packages
- Ask if they have any relevant openings or would like to connect
- Sound professional but warm — NOT salesy or pushy
- End with a clear call to action (reply or schedule a call)
- Sign off as "Suchi" with "Executive Search Agent"

Return JSON only:
{{"subject": "subject line", "body_text": "plain text email body", "body_html": "HTML version with simple formatting"}}"""

        return await self._call_claude_json(prompt)

    async def compose_followup(
        self,
        contact_name: str,
        firm_name: str,
        thread_history: list[dict],
        escalation_level: int,
        strategy: str,
    ) -> dict:
        """
        Compose a context-aware follow-up email.

        Returns: {"subject": str, "body_text": str, "body_html": str}
        """
        history_text = self._format_thread_history(thread_history)

        strategy_guidance = {
            "standard": "Send a polite follow-up referencing the original email. Keep it brief.",
            "different_angle": "Try a different angle — highlight a specific achievement or skill that might be relevant to their current searches.",
            "urgent": "Create a sense of urgency — mention Rajamohan is in final discussions with other firms and the window is closing.",
            "warm_intro": "Take a softer approach — ask if there's a better person at the firm to connect with, or if timing is better later this quarter.",
        }

        prompt = f"""You are Suchi, an executive search agent. You're following up on a previous email to {contact_name} at {firm_name}.

CONVERSATION HISTORY:
{history_text}

ESCALATION LEVEL: {escalation_level} (higher = more persistent)
STRATEGY: {strategy}
STRATEGY GUIDANCE: {strategy_guidance.get(strategy, strategy_guidance["standard"])}

GUIDELINES:
- Reference the previous email naturally
- Keep it under 100 words for follow-ups
- Be respectful — they may be busy
- Vary the approach from previous emails (don't repeat yourself)
- Sign off as "Suchi"

Return JSON only:
{{"subject": "Re: original subject or new subject", "body_text": "plain text email body", "body_html": "HTML version"}}"""

        return await self._call_claude_json(prompt)

    async def compose_response(
        self,
        contact_name: str,
        firm_name: str,
        thread_history: list[dict],
        inbound_message: str,
        analysis: dict,
    ) -> dict:
        """
        Compose a reply to an inbound message based on LLM analysis.

        Returns: {"subject": str, "body_text": str, "body_html": str}
        """
        history_text = self._format_thread_history(thread_history)

        prompt = f"""You are Suchi, an executive search agent representing Rajamohan (CTO candidate, 5 Cr+ target).

{contact_name} at {firm_name} has replied to your outreach.

CONVERSATION HISTORY:
{history_text}

THEIR LATEST MESSAGE:
{inbound_message}

YOUR ANALYSIS OF THEIR MESSAGE:
Sentiment: {analysis.get('sentiment', 'unknown')}
Interest level: {analysis.get('interest_level', 'unknown')}
Key points: {json.dumps(analysis.get('key_points', []))}

GUIDELINES:
- Respond appropriately to their message
- If positive/interested: express enthusiasm, suggest a call with Rajamohan, provide availability
- If asking for more info: provide relevant details from Rajamohan's background
- If negative: be gracious, thank them, ask to keep Rajamohan in mind for future opportunities
- If they suggest another contact: thank them and ask for the introduction
- Keep it professional and concise (under 150 words)
- Your ultimate goal: get Rajamohan a CTO job with 5 Cr package
- Sign off as "Suchi"

Return JSON only:
{{"subject": "Re: appropriate subject", "body_text": "plain text email body", "body_html": "HTML version"}}"""

        return await self._call_claude_json(prompt)

    # ── Analysis ──────────────────────────────────────────────

    async def analyze_response(
        self,
        message_body: str,
        thread_context: list[dict],
    ) -> dict:
        """
        Analyse an inbound email response.

        Returns: {
            "sentiment": str,
            "interest_level": str,  # high | medium | low | none
            "key_points": list[str],
            "suggested_action": str,
            "summary": str,
        }
        """
        context_text = self._format_thread_history(thread_context[-3:])  # last 3 messages for context

        prompt = f"""Analyse this email response from an executive search firm contact.

PREVIOUS CONTEXT:
{context_text}

THEIR RESPONSE:
{message_body}

Provide analysis as JSON:
{{
    "sentiment": "positive" | "neutral" | "negative" | "interested" | "not_interested",
    "interest_level": "high" | "medium" | "low" | "none",
    "key_points": ["point 1", "point 2"],
    "suggested_action": "reply_with_details" | "schedule_call" | "thank_and_close" | "redirect_to_other_contact" | "wait",
    "summary": "One sentence summary of their response"
}}

Return JSON only."""

        return await self._call_claude_json(prompt)

    async def classify_sentiment(self, text: str) -> str:
        """Cheap sentiment classification using GPT-4o-mini (fallback)."""
        if self.gpt:
            try:
                response = self.gpt.chat.completions.create(
                    model=settings.openai_model,
                    messages=[
                        {"role": "user", "content": f"Classify the sentiment of this text as exactly one word: positive, neutral, or negative.\n\nText: {text}\n\nSentiment:"}
                    ],
                    max_tokens=10,
                    temperature=0,
                )
                sentiment = response.choices[0].message.content.strip().lower()
                if sentiment in ("positive", "neutral", "negative"):
                    return sentiment
            except Exception as e:
                logger.warning(f"GPT-4o sentiment fallback failed: {e}")

        # Fallback to Claude if GPT not available
        result = await self._call_claude_json(
            f'Classify sentiment as JSON: {{"sentiment": "positive"|"neutral"|"negative"}}.\n\nText: {text}'
        )
        return result.get("sentiment", "neutral")

    # ── Strategic Decision Making ─────────────────────────────

    async def decide_next_action(
        self,
        contact_info: dict,
        thread_history: list[dict],
        escalation_level: int,
        days_since_last_contact: int,
    ) -> dict:
        """
        Strategic decision on what to do next for a contact.

        Returns: {
            "action": "send_followup" | "send_response" | "change_strategy" | "mark_cold" | "wait" | "escalate",
            "reasoning": str,
            "new_strategy": str | None,
            "wait_days": int | None,
        }
        """
        history_text = self._format_thread_history(thread_history[-5:])

        prompt = f"""You are an autonomous outreach agent. Decide the next action for this contact.

CONTACT: {contact_info.get('name')} ({contact_info.get('title', 'Unknown')}) at {contact_info.get('firm_name', 'Unknown')}
STATUS: {contact_info.get('status', 'new')}
ESCALATION LEVEL: {escalation_level} / 5
DAYS SINCE LAST CONTACT: {days_since_last_contact}
TOTAL CONTACTS MADE: {contact_info.get('contact_count', 0)}
LAST RESPONSE SENTIMENT: {contact_info.get('last_sentiment', 'none')}

CONVERSATION HISTORY:
{history_text or "No conversation yet."}

ESCALATION POLICY:
- Level 0: Initial outreach (day 0)
- Level 1: Soft follow-up (+4 days)
- Level 2: Different angle (+7 days)
- Level 3: Urgent (+10 days)
- Level 4: Final attempt (+14 days)
- Level 5: Mark cold

RULES:
- Be respectful of their time
- If they responded positively, focus on scheduling a call
- If no response and it's too early for follow-up, wait
- If exhausted all attempts, mark cold
- Think strategically about timing and approach

Return JSON only:
{{
    "action": "send_followup" | "send_response" | "change_strategy" | "mark_cold" | "wait" | "escalate",
    "reasoning": "2-3 sentence explanation",
    "new_strategy": "standard" | "different_angle" | "urgent" | "warm_intro" | null,
    "wait_days": number or null
}}"""

        return await self._call_claude_json(prompt)

    # ── Daily Briefing ────────────────────────────────────────

    async def compose_daily_briefing(
        self,
        stats: dict,
        yesterday_stats: dict,
        notable_events: list[dict],
    ) -> str:
        """Compose a 3-4 line daily briefing for Rajamohan."""
        prompt = f"""Write a 3-4 line morning briefing email for Rajamohan about his job search progress.

TODAY'S STATS:
- Total firms: {stats.get('total_firms', 0)}
- Contacted: {stats.get('contacted', 0)}
- Responded: {stats.get('responded', 0)}
- In conversation: {stats.get('in_conversation', 0)}
- Converted (interested): {stats.get('converted', 0)}
- Cold (no response): {stats.get('cold', 0)}

YESTERDAY'S STATS:
- Contacted: {yesterday_stats.get('contacted', 0)}
- New responses: {yesterday_stats.get('new_responses', 0)}

NOTABLE EVENTS (last 24h):
{json.dumps(notable_events, default=str) if notable_events else "No notable events."}

GUIDELINES:
- Address him as "Hi Rajamohan"
- Be concise: exactly 3-4 lines
- Include key changes from yesterday
- Highlight any positive responses or conversions
- If nothing notable, reassure that the pipeline is active
- Sign off as "— Suchi, your search agent"

Return the briefing text only (no JSON, no markdown)."""

        if self.claude:
            try:
                response = self.claude.messages.create(
                    model=settings.anthropic_model,
                    max_tokens=300,
                    messages=[{"role": "user", "content": prompt}],
                )
                return response.content[0].text.strip()
            except Exception as e:
                logger.error(f"Claude briefing error: {e}")

        return f"Hi Rajamohan,\n\nYour search pipeline has {stats.get('total_firms', 0)} firms with {stats.get('responded', 0)} responses so far. Working on it.\n\n— Suchi, your search agent"

    # ── Internal Helpers ──────────────────────────────────────

    async def _call_claude_json(self, prompt: str) -> dict:
        """Call Claude and parse JSON response. Returns empty dict on failure."""
        if not self.claude:
            logger.error("Anthropic client not configured")
            return {}

        try:
            response = self.claude.messages.create(
                model=settings.anthropic_model,
                max_tokens=2000,
                messages=[{"role": "user", "content": prompt}],
            )
            content = response.content[0].text.strip()

            # Strip markdown code blocks if present
            if content.startswith("```"):
                content = content.split("\n", 1)[1] if "\n" in content else content[3:]
            if content.endswith("```"):
                content = content[:-3]
            content = content.strip()

            return json.loads(content)

        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse Claude JSON response: {e}")
            logger.debug(f"Raw response: {content if 'content' in dir() else 'N/A'}")
            return {}
        except anthropic.APIError as e:
            logger.error(f"Claude API error: {e}")
            return {}
        except Exception as e:
            logger.error(f"LLM call failed: {e}")
            return {}

    def _format_thread_history(self, messages: list[dict]) -> str:
        """Format message history for prompt context."""
        if not messages:
            return "No conversation history."

        lines = []
        for msg in messages:
            direction = msg.get("direction", "unknown")
            sender = "Suchi (Agent)" if direction == "outbound" else "Contact"
            body = msg.get("body_text", "")[:500]  # Truncate long messages
            timestamp = msg.get("sent_at", "")
            lines.append(f"[{timestamp}] {sender}:\n{body}\n")

        return "\n".join(lines)


# Singleton instance
llm_service = LLMService()
