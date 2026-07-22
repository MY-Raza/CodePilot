from enum import Enum
from typing import Literal

from pydantic import BaseModel, Field


class MessageRole(str, Enum):
    """Role of a single message within a chat conversation."""

    SYSTEM = "system"
    USER = "user"
    ASSISTANT = "assistant"


class ChatMessage(BaseModel):
    """A single message within a chat conversation.

    Attributes:
        role: Who authored this message.
        content: The message text.
    """

    role: MessageRole
    content: str = Field(..., min_length=1)


class SystemMessage(ChatMessage):
    """A system-role message, fixing `role` to `MessageRole.SYSTEM`."""

    role: Literal[MessageRole.SYSTEM] = MessageRole.SYSTEM


class UserMessage(ChatMessage):
    """A user-role message, fixing `role` to `MessageRole.USER`."""

    role: Literal[MessageRole.USER] = MessageRole.USER


class AssistantMessage(ChatMessage):
    """An assistant-role message, fixing `role` to `MessageRole.ASSISTANT`."""

    role: Literal[MessageRole.ASSISTANT] = MessageRole.ASSISTANT


class TokenUsage(BaseModel):
    """Token accounting for a single generation request.

    Attributes:
        prompt_tokens: Tokens consumed by the input messages.
        completion_tokens: Tokens generated in the response.
        total_tokens: Sum of `prompt_tokens` and `completion_tokens`.
    """

    prompt_tokens: int = Field(ge=0)
    completion_tokens: int = Field(ge=0)
    total_tokens: int = Field(ge=0)


class LLMRequest(BaseModel):
    """A provider-agnostic request to generate a chat completion.

    Attributes:
        messages: The conversation history to generate a response to.
        model: The model identifier to use. Falls back to the
            configured default model when omitted.
        temperature: Sampling temperature. Falls back to the configured
            default when omitted.
        max_tokens: Maximum tokens to generate. Falls back to the
            configured default when omitted.
        top_p: Nucleus sampling parameter. Falls back to the configured
            default when omitted.
        stop: Up to a provider-defined number of sequences where
            generation should stop.
        stream: Whether this request will be issued via `stream()`
            rather than `generate()`. Informational only when passed to
            `generate()`/`generate_sync()`; those methods always return
            a single complete response regardless of this flag.
        response_format: Requests structured JSON output when set to
            "json", on models that support it (see
            `ModelInfo.supports_json_mode`).
    """

    messages: list[ChatMessage] = Field(..., min_length=1)
    model: str | None = None
    temperature: float | None = Field(default=None, ge=0.0, le=2.0)
    max_tokens: int | None = Field(default=None, gt=0)
    top_p: float | None = Field(default=None, ge=0.0, le=1.0)
    stop: list[str] | None = Field(default=None, max_length=4)
    stream: bool = False
    response_format: Literal["text", "json"] = "text"


class LLMResponse(BaseModel):
    """A complete, non-streaming generation result.

    Attributes:
        id: The provider's identifier for this completion.
        provider: Identifier of the provider that generated this
            response (e.g. "groq").
        model: The model actually used to generate this response.
        content: The generated text.
        finish_reason: Why generation stopped (e.g. "stop", "length"),
            if reported by the provider.
        usage: Token accounting for this request.
        latency_seconds: Wall-clock time the request took, if measured.
    """

    id: str
    provider: str
    model: str
    content: str
    finish_reason: str | None = None
    usage: TokenUsage
    latency_seconds: float | None = None


class StreamingChunk(BaseModel):
    """A single incremental chunk of a streaming generation.

    Attributes:
        id: The provider's identifier for the completion this chunk
            belongs to (shared across all chunks in one stream).
        provider: Identifier of the provider that generated this chunk.
        model: The model generating this stream.
        delta: The incremental text content in this chunk. May be empty
            for chunks that only carry metadata (e.g. the final chunk).
        finish_reason: Set on the final chunk of a stream to indicate
            why generation stopped; None for all preceding chunks.
        is_final: True only on the last chunk of a stream.
    """

    id: str
    provider: str
    model: str
    delta: str = ""
    finish_reason: str | None = None
    is_final: bool = False


class ModelInfo(BaseModel):
    """Static capability/limits information about a supported model.

    Attributes:
        provider: Identifier of the provider hosting this model.
        model_name: The model's identifier, as passed to the provider's
            API.
        context_window: Maximum combined prompt + completion tokens the
            model supports.
        max_output_tokens: Maximum tokens the model can generate in a
            single response.
        supports_streaming: Whether this model supports streaming
            responses.
        supports_json_mode: Whether this model supports structured JSON
            output mode.
        supports_tool_calling: Whether this model supports function/tool
            calling.
        supports_vision: Whether this model supports image inputs.
            Reserved for future use — no currently supported model sets
            this to True.
    """

    provider: str
    model_name: str
    context_window: int = Field(gt=0)
    max_output_tokens: int = Field(gt=0)
    supports_streaming: bool = True
    supports_json_mode: bool = False
    supports_tool_calling: bool = False
    supports_vision: bool = False