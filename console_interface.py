import sys
import logging
from typing import Optional
from ragchatbot import RAGChatbot

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger(__name__)


class ConsoleInterface:
    """Console interface for interacting with the RAG chatbot."""

    def __init__(self):
        self.chatbot: Optional[RAGChatbot] = None
        self.show_reasoning = False
        logger.info("ConsoleInterface initialized")

    def initialize_chatbot(self) -> bool:
        """
        Initialize the chatbot instance.

        Returns:
            bool: True if chatbot is ready, False otherwise
        """
        logger.info("Initializing Bundesliga Coaching Assistant...")
        try:
            self.chatbot = RAGChatbot()
            logger.info("Chatbot ready! Ask me about Bundesliga coaches.")
            return True
        except Exception as e:
            logger.error(f"Failed to initialize chatbot: {e}")
            return False

    def print_welcome(self):
        """Print the welcome screen and available commands."""
        logger.info("=" * 60)
        logger.info("BUNDESLIGA COACHING ASSISTANT")
        logger.info("=" * 60)
        logger.info("Ask about current Bundesliga coaches or clubs.")
        logger.info("Commands: /debug, /help, /quit, /exit")
        logger.info("-" * 60)

    def process_command(self, cmd: str) -> bool:
        """
        Handle console commands (e.g., /quit, /debug, /help).

        Args:
            cmd (str): Command entered by the user

        Returns:
            bool: True to continue loop, False to exit
        """
        cmd = cmd.lower()
        if cmd in ["/quit", "/exit", "/q"]:
            logger.info("Goodbye!")
            return False
        elif cmd == "/debug":
            self.show_reasoning = not self.show_reasoning
            logger.info(f"Debug mode {'ON' if self.show_reasoning else 'OFF'}")
        elif cmd == "/help":
            self.print_welcome()
        else:
            logger.warning(f"Unknown command: {cmd}")
        return True

    def format_response(self, prompt: dict) -> str:
        """
        Format chatbot output into a human-readable string.

        Args:
            prompt (dict): Response dictionary from RAGChatbot

        Returns:
            str: Formatted response for console output
        """
        ctx = prompt.get("context", {})
        club = ctx.get("club_name")
        manager = ctx.get("manager_name")
        manager_info = ctx.get("manager_info")

        if manager and manager != "Unknown Manager":
            if club:
                resp = f"{manager} is currently coaching {club}."
            else:
                resp = f"The current manager is {manager}."
            if manager_info:
                resp += f"\n\nBackground: {manager_info}"
        elif club:
            resp = f"I found {club} but couldn't determine the current manager."
        else:
            resp = "I couldn't identify a specific Bundesliga club from your question."

        return resp

    def run(self):
        """Main console loop for user interaction."""
        if not self.initialize_chatbot():
            sys.exit(1)

        self.print_welcome()

        while True:
            try:
                user_input = input("\nYour question: ").strip()
            except (EOFError, KeyboardInterrupt):
                logger.info("Exiting console interface. Goodbye!")
                break

            if not user_input:
                continue

            # Handle commands starting with "/"
            if user_input.startswith("/"):
                if not self.process_command(user_input):
                    break
                continue

            # Process natural language query
            logger.info("Processing user query...")
            try:
                prompt = self.chatbot.process_query(user_input)
                formatted_response = self.format_response(prompt)
                logger.info(f"Response ready:\n{formatted_response}")
            except Exception as e:
                logger.error(f"Error processing query: {e}")


if __name__ == "__main__":
    ConsoleInterface().run()
