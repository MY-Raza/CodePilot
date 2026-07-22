import logging
from abc import ABC, abstractmethod

from backend.llm.exceptions import TokenLimitExceededError
from backend.llm.schemas import ChatMessage

logger = logging.getLogger(__name__)

# Characters-per-token approximation used by the default counter. A
# coarse, model-agnostic heuristic commonly cited for English prose
# with BPE-style tokenizers; not exact for any particular model.
_CHARS_PER_TOKEN_ESTIMATE = 4

# Per-message formatting overhead added when estimating prompt tokens,
# approximating the small number of tokens chat APIs spend on role/
# separator formatting around each message's content (a convention
# popularized by OpenAI's chat-format token-counting guidance; treated
# here as a reasonable cross-provider approximation, not an exact figure
# for any specific model).
_PER_MESSAGE_OVERHEAD_TOKENS = 4
_PRIMING_OVERHEAD_TOKENS = 2


class TokenCounter(ABC):
    """Interface for counting tokens in a piece of text.

    Concrete implementations may be a cheap heuristic (the default,
    `HeuristicTokenCounter`) or a real provider-specific tokenizer,
    injected into `Tokenizer` without changing any of its call sites.
    """

    @abstractmethod
    def count(self, text: str) -> int:
        """Count the number of tokens in a piece of text.

        Args:
            text: The text to count tokens in.

        Returns:
            The estimated or exact token count.
        """
        raise NotImplementedError


class HeuristicTokenCounter(TokenCounter):
    """Default token counter using a characters-per-token approximation."""

    def count(self, text: str) -> int:
        """Approximate a text's token count.

        Args:
            text: The text to estimate.

        Returns:
            An approximate token count. Always at least 1 for non-empty
            text, 0 for empty text.
        """
        if not text:
            return 0
        return max(1, len(text) // _CHARS_PER_TOKEN_ESTIMATE)


class Tokenizer:
    """Estimates prompt/completion token counts and validates context limits."""

    def __init__(self, counter: TokenCounter | None = None) -> None:
        """Initialize the tokenizer.

        Args:
            counter: The token-counting strategy to use. Defaults to
                `HeuristicTokenCounter`.
        """
        self._counter = counter or HeuristicTokenCounter()

    def count_tokens(self, text: str) -> int:
        """Count tokens in a single piece of text.

        Args:
            text: The text to count.

        Returns:
            The token count, per the configured `TokenCounter`.
        """
        return self._counter.count(text)

    def estimate_prompt_tokens(self, messages: list[ChatMessage]) -> int:
        """Estimate the total prompt token count for a list of messages.

        Args:
            messages: The conversation history that will be sent as the
                prompt.

        Returns:
            The estimated prompt token count, including a small
            per-message formatting overhead.
        """
        content_tokens = sum(
            self._counter.count(message.content) + _PER_MESSAGE_OVERHEAD_TOKENS
            for message in messages
        )
        return content_tokens + _PRIMING_OVERHEAD_TOKENS

    def estimate_completion_tokens(self, text: str) -> int:
        """Estimate the token count of a (partial or complete) completion.

        Args:
            text: The completion text.

        Returns:
            The estimated completion token count.
        """
        return self._counter.count(text)

    def total_tokens(self, prompt_tokens: int, completion_tokens: int) -> int:
        """Sum prompt and completion token counts.

        Args:
            prompt_tokens: The prompt token count.
            completion_tokens: The completion token count.

        Returns:
            The combined total.
        """
        return prompt_tokens + completion_tokens

    def validate_context_window(
        self,
        prompt_tokens: int,
        requested_max_output_tokens: int,
        context_window: int,
    ) -> None:
        """Validate that a request fits within a model's context window.

        Args:
            prompt_tokens: The (estimated or exact) prompt token count.
            requested_max_output_tokens: The maximum output tokens being
                requested for this generation.
            context_window: The target model's total context window.

        Raises:
            TokenLimitExceededError: If `prompt_tokens +
                requested_max_output_tokens` exceeds `context_window`.
        """
        total_requested = prompt_tokens + requested_max_output_tokens
        if total_requested > context_window:
            raise TokenLimitExceededError(
                f"Request requires an estimated {total_requested} tokens "
                f"({prompt_tokens} prompt + {requested_max_output_tokens} "
                f"requested output), exceeding the model's context window "
                f"of {context_window} tokens."
            )