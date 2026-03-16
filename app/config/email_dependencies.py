from app.notifications.email_sender import EmailSender
from app.notifications.interfaces import EmailSenderInterface


def get_email_sender() -> EmailSenderInterface:
    return EmailSender(
        hostname="mailhog",
        port=1025,
        email="noreply@example.com",
        password="",
        use_tls=False,
        template_dir="app/templates/emails",
        activation_email_template_name="activation_request.html",
        activation_complete_email_template_name="activation_complete.html",
        password_email_template_name="password_reset_request.html",
        password_complete_email_template_name="password_reset_complete.html",
    )
