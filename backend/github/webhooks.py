import hashlib
import hmac
import logging

from fastapi import APIRouter, Header, HTTPException, Request, status

from backend.core.config import get_settings
from backend.github.exceptions import WebhookVerificationError
from backend.github.schemas import WebhookPayload

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/webhooks/github", tags=["GitHub Webhooks"])

SIGNATURE_HEADER = "X-Hub-Signature-256"
EVENT_HEADER = "X-GitHub-Event"
DELIVERY_HEADER = "X-GitHub-Delivery"

# Event types this receiver is prepared to accept. Each maps to a stub
# handler below; extend SUPPORTED_EVENTS and add a matching handler as
# new automation is built.
SUPPORTED_EVENTS = {"push", "pull_request", "issues", "repository", "ping"}


def verify_github_signature(payload_body: bytes, signature_header: str | None, secret: str) -> None:
    """Verify a webhook payload's HMAC-SHA256 signature.

    Args:
        payload_body: The raw, undecoded request body bytes.
        signature_header: The value of the `X-Hub-Signature-256` header.
        secret: The shared webhook secret configured in GitHub and in
            application settings.

    Raises:
        WebhookVerificationError: If the header is missing or the
            signature does not match.
    """
    if not signature_header or not signature_header.startswith("sha256="):
        raise WebhookVerificationError(
            "Missing or malformed X-Hub-Signature-256 header."
        )

    expected_digest = hmac.new(
        secret.encode("utf-8"), payload_body, hashlib.sha256
    ).hexdigest()
    expected_signature = f"sha256={expected_digest}"

    if not hmac.compare_digest(expected_signature, signature_header):
        raise WebhookVerificationError("Webhook signature verification failed.")


async def _handle_ping(payload: WebhookPayload) -> None:
    """Handle a GitHub 'ping' event (sent when a webhook is first created).

    Args:
        payload: The normalized webhook envelope.
    """
    logger.info("Webhook received: ping (delivery_id=%s)", payload.delivery_id)


async def _handle_push(payload: WebhookPayload) -> None:
    """Handle a GitHub 'push' event.

    Args:
        payload: The normalized webhook envelope.
    """
    logger.info("Webhook received: push (delivery_id=%s)", payload.delivery_id)
    # NOTE: Future automation (e.g. triggering GitHubService.sync_repository)
    # will be wired in here. Intentionally left as a no-op per Module 6 scope.


async def _handle_pull_request(payload: WebhookPayload) -> None:
    """Handle a GitHub 'pull_request' event.

    Args:
        payload: The normalized webhook envelope.
    """
    logger.info(
        "Webhook received: pull_request (delivery_id=%s)", payload.delivery_id
    )


async def _handle_issues(payload: WebhookPayload) -> None:
    """Handle a GitHub 'issues' event.

    Args:
        payload: The normalized webhook envelope.
    """
    logger.info("Webhook received: issues (delivery_id=%s)", payload.delivery_id)


async def _handle_repository(payload: WebhookPayload) -> None:
    """Handle a GitHub 'repository' event (e.g. renamed, archived, deleted).

    Args:
        payload: The normalized webhook envelope.
    """
    logger.info(
        "Webhook received: repository (delivery_id=%s)", payload.delivery_id
    )


_EVENT_HANDLERS = {
    "ping": _handle_ping,
    "push": _handle_push,
    "pull_request": _handle_pull_request,
    "issues": _handle_issues,
    "repository": _handle_repository,
}


@router.post(
    "",
    status_code=status.HTTP_202_ACCEPTED,
    summary="Receive a GitHub webhook delivery",
    description=(
        "Verifies the request's HMAC-SHA256 signature and dispatches it "
        "to a per-event-type stub handler. No business automation is "
        "triggered yet — this endpoint only validates and logs receipt."
    ),
)
async def receive_github_webhook(
    request: Request,
    x_hub_signature_256: str | None = Header(default=None, alias=SIGNATURE_HEADER),
    x_github_event: str | None = Header(default=None, alias=EVENT_HEADER),
    x_github_delivery: str | None = Header(default=None, alias=DELIVERY_HEADER),
) -> dict[str, str]:
    """Receive, verify, and dispatch a GitHub webhook delivery.

    Args:
        request: The raw incoming request, used to access the undecoded
            body for signature verification.
        x_hub_signature_256: The delivery's HMAC-SHA256 signature.
        x_github_event: The event type being delivered.
        x_github_delivery: The unique delivery ID.

    Returns:
        A minimal acknowledgement payload.

    Raises:
        HTTPException: 401 if signature verification fails, 400 if the
            event type is missing/unsupported or the body is not valid
            JSON, 500 if the webhook secret is not configured.
    """
    settings = get_settings()
    webhook_secret = settings.github_webhook_secret
    if not webhook_secret:
        logger.error("GITHUB_WEBHOOK_SECRET is not configured.")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Webhook receiver is not configured on this server.",
        )

    raw_body = await request.body()

    try:
        verify_github_signature(raw_body, x_hub_signature_256, webhook_secret)
    except WebhookVerificationError as exc:
        logger.warning("Webhook signature verification failed.")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail=str(exc)
        ) from exc

    if not x_github_event or x_github_event not in SUPPORTED_EVENTS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported or missing event type: {x_github_event!r}",
        )

    try:
        parsed_body = await request.json()
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Webhook payload is not valid JSON.",
        ) from exc

    payload = WebhookPayload(
        event=x_github_event,
        delivery_id=x_github_delivery,
        payload=parsed_body,
    )

    handler = _EVENT_HANDLERS[x_github_event]
    await handler(payload)

    return {"status": "accepted", "event": x_github_event}