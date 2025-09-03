from typing import Optional, Dict, Any


class PromptBuilder:
    """Builds structured prompts for LLM APIs with proper system/user separation."""

    def __init__(self):
        self.system_prompt = (
            "You are a German Bundesliga football expert assistant. "
            "You have access to current, verified information about football clubs and their coaches. "
            "Answer questions about coaches clearly and concisely using only the provided context. "
            "Be specific about coach names and include relevant background information."
        )

    def build_manager_prompt(
        self,
        user_query: str,
        club_name: str,
        city_name: str,
        manager_name: str,
        manager_info: Optional[str],
    ) -> Dict[str, Any]:
        """
        Build structured prompt with system and user messages.

        Returns:
            Dict with 'system', 'user', and 'context' keys for LLM API
        """
        # Context information to inject into user message
        context = (
            "CONTEXT: "
            f"Club: {club_name} "
            f"City: {city_name} "
            f"Current Manager: {manager_name} "
            f"Manager Background: {manager_info or 'Additional information not available'}"
        )

        # User message with context and original query
        user_message = f"{context} USER QUESTION: {user_query}"

        return {
            "system": self.system_prompt,
            "user": user_message,
            "context": {
                "club_name": club_name,
                "manager_name": manager_name,
                "manager_info": manager_info,
            },
        }

    def build_error_prompt(self, user_query: str, error_msg: str) -> Dict[str, Any]:
        """Build structured error prompt."""
        error_system = (
            "You are a helpful assistant for German Bundesliga information. "
            "When you cannot access the required information, explain the limitation clearly and suggest alternatives."
        )

        error_user = (
            f"I asked: {user_query} "
            f"System message: {error_msg} "
            f"Please explain why this information isn't available and suggest how I can rephrase my question."
        )

        return {"system": error_system, "user": error_user, "context": {"error": error_msg}}

    def get_context_only(self, prompt_dict: Dict[str, Any]) -> Dict[str, Any]:
        """Extract just the context information for logging/debugging."""
        return prompt_dict.get("context", {})
