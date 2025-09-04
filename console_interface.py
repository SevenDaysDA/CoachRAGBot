import sys
import logging
from typing import Optional
from ragchatbot import RAGChatbot

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger(__name__)


class ConsoleInterface:
    """Console interface for interacting with the RAG chatbot."""

    def __init__(self):
        self.chatbot: Optional[RAGChatbot] = None
        self.show_reasoning = False

    def initialize_chatbot(self) -> bool:
        logging.info("Initializing Bundesliga Coaching Assistant...")
        try:
            self.chatbot = RAGChatbot()
            logging.info("Chatbot ready! Ask me about Bundesliga coaches.")
            return True
        except Exception as e:
            logging.error(f"Failed to initialize chatbot: {e}")
            return False

    def print_welcome(self):
        logging.info("=" * 60)
        logging.info("BUNDESLIGA COACHING ASSISTANT")
        logging.info("=" * 60)
        logging.info("Ask about current Bundesliga coaches or clubs.")
        logging.info("Commands: /debug, /help, /quit, /exit")
        logging.info("-" * 60)

    def process_command(self, cmd: str) -> bool:
        cmd = cmd.lower()
        if cmd in ["/quit", "/exit", "/q"]:
            logging.info("Goodbye!")
            return False
        elif cmd == "/debug":
            self.show_reasoning = not self.show_reasoning
            logging.info(f"Debug mode {'ON' if self.show_reasoning else 'OFF'}")
        elif cmd == "/help":
            self.print_welcome()
        else:
            logging.warning(f"Unknown command: {cmd}")
        return True

    def format_response(self, prompt: dict) -> str:
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
        if not self.initialize_chatbot():
            sys.exit(1)
        self.print_welcome()

        while True:
            try:
                user_input = input("\nYour question: ").strip()
            except (EOFError, KeyboardInterrupt):
                logging.info("\nGoodbye!")
                break

            if not user_input:
                continue
            if user_input.startswith("/"):
                if not self.process_command(user_input):
                    break
                continue

            logging.info("Thinking...")
            try:
                prompt = self.chatbot.process_query(user_input)
                logging.info(f"\n{self.format_response(prompt)}")
            except Exception as e:
                logging.error(f"Error processing query: {e}")


if __name__ == "__main__":
    ConsoleInterface().run()
