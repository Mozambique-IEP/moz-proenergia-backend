import logging

from django.conf import settings
from django.core.mail import EmailMultiAlternatives

logger = logging.getLogger(__name__)


def send_dataset_approval_email(dataset_name: str, link: str, email_list: list[str]):
    url = f"{settings.BACKEND_URL}{link}"
    from_email = (
        f"{settings.UNFOLD.get('SITE_TITLE')} <{settings.DEFAULT_FROM_EMAIL}>"
        if hasattr(settings, "DEFAULT_FROM_EMAIL")
        else f"{settings.UNFOLD.get('SITE_TITLE')} <noreply@proenergia.mz>"
    )
    email = EmailMultiAlternatives(
        f"Dataset {dataset_name} waiting for approval",
        f"A new version of the dataset {dataset_name} has been uploaded and is waiting for approval. Access {url} to approve it.",
        from_email,
        email_list,
    )
    html_content = f"""
    <p>A new version of the dataset <b>{dataset_name}</b> has been uploaded and is waiting for approval.</p>
    <p>Access <a href="{url}">{url}</a> to approve it.</p>
    """
    email.attach_alternative(html_content, "text/html")
    try:
        email.send()
    except Exception as e:
        logger.debug(
            f"Failed to send approval request email for dataset {dataset_name}: {e}"
        )
