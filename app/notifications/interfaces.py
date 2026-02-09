from abc import ABC, abstractmethod


class EmailSenderInterface(ABC):

    @abstractmethod
    async def send_activation_email(self, email: str, activation_link: str) -> None:
        """
        Asynchronously send an account activation email.

        Args:
            email (str): The recipient's email address.
            activation_link (str): The activation link to include in the email.
        """
        pass

    @abstractmethod
    async def send_activation_complete_email(self, email: str, login_link: str) -> None:
        """
        Asynchronously send an email confirming that the account has been activated.

        Args:
            email (str): The recipient's email address.
            login_link (str): The login link to include in the email.
        """
        pass

    @abstractmethod
    async def send_password_reset_email(self, email: str, reset_link: str) -> None:
        """
        Asynchronously send a password reset request email.

        Args:
            email (str): The recipient's email address.
            reset_link (str): The password reset link to include in the email.
        """
        pass

    @abstractmethod
    async def send_password_reset_complete_email(
        self, email: str, login_link: str
    ) -> None:
        """
        Asynchronously send an email confirming that the password has been reset.

        Args:
            email (str): The recipient's email address.
            login_link (str): The login link to include in the email.
        """
        pass

    @abstractmethod
    async def send_email(
            self, recipient: str, subject: str, html_content: str
    ) -> None:
        """
        Send a generic email with custom subject and content.

        Args:
            recipient (str): The recipient's email address.
            subject (str): The subject of the email.
            html_content(str): The HTML content to include in the email.
        """
        pass
