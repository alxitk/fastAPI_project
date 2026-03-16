from app.notifications.email_sender import EmailSenderInterface


class CommentNotificationService:
    def __init__(self, email_sender: EmailSenderInterface) -> None:
        self._email_sender = email_sender

    async def notify_reply(
        self, parent_user_email: str, reply_text: str, movie_name: str
    ) -> None:
        subject = f"You get answer on comment on movie: {movie_name}"
        body = f"Somebody answer your comment: \n\n{reply_text}"
        await self._email_sender.send_email(
            recipient=parent_user_email, subject=subject, html_content=body
        )

    async def notify_like(self, parent_user_email: str, movie_name: str) -> None:
        subject = f"Your comment on  {movie_name} get like"
        body = f"Somebody just liked your comment on movie: {movie_name}."
        await self._email_sender.send_email(
            recipient=parent_user_email, subject=subject, html_content=body
        )
