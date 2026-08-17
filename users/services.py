import stripe
from stripe import StripeClient
from config.settings import STRIPE_SECRET_KEY, STRIPE_WEBHOOK_SECRET
from users.models import Payments


class StripePaymentService:
    """Класс для взаимодествия с сервисом Stripe API."""

    def __init__(self):
        # Инициализируем клиент Stripe
        self.client = StripeClient(STRIPE_SECRET_KEY)
        self.webhook_secret = STRIPE_WEBHOOK_SECRET

    def create_checkout_session(self, payment_record: Payments) -> tuple[str, str]:
        """
        Генерирует сессию Stripe Checkout на основе записи платежа из aurora.
        Возвращает кортеж: (session_id, payment_url)
        """
        # Определяем имя продукта для страницы оплаты
        if payment_record.paid_course:
            product_name = f"Оплата курса: {payment_record.paid_course.title}"
        elif payment_record.paid_lesson:
            product_name = f"Оплата урока: {payment_record.paid_lesson.title}"
        else:
            product_name = "Оплата обучения"

        # Конвертируем Decimal сумму в центы (Stripe принимает только int)
        stripe_amount = int(payment_record.payment_amount * 100)

        try:
            # Создаем сессию в Stripe API
            checkout_session = self.client.v1.checkout.sessions.create(
                {
                    "payment_method_types": ["card"],
                    "line_items": [
                        {
                            "price_data": {
                                "currency": "usd",  # Валюта вашего аккаунта Stripe
                                "unit_amount": stripe_amount,
                                "product_data": {"name": product_name},
                            },
                            "quantity": 1,
                        }
                    ],
                    "mode": "payment",  # Разовый платеж
                    "success_url": "http://127.0.0.1:8000/",  # В рамках дестирования платежей
                    "cancel_url": "http://127.0.0.1:8000/",  # В рамках дестирования платежей
                    "metadata": {
                        "payment_record_id": payment_record.id  # Передаем ID для Вебхука
                    },
                }
            )
            return checkout_session.id, checkout_session.url

        except stripe.error.StripeError as e:
            raise RuntimeError(f"Ошибка Stripe API при генерации сессии: {str(e)}")

    def verify_and_process_webhook(self, payload: bytes, sig_header: str) -> bool:
        """
        Верифицирует криптографическую подпись вебхука от Stripe
        и автоматически переводит статус платежа в базе Aurora в 'succeeded'.
        """
        try:
            # Безопасно проверяем подпись с помощью нашего webhook_secret
            event = stripe.Webhook.construct_event(
                payload, sig_header, self.webhook_secret
            )
        except ValueError, stripe.error.SignatureVerificationError:
            return False

        # Если пользователь успешно оплатил курс на странице Stripe Checkout
        if event["type"] == "checkout.session.completed":
            session = event["data"]["object"]
            payment_record_id = session.get("metadata", {}).get("payment_record_id")

            if payment_record_id:
                try:
                    # Находим нужный платеж в приложении aurora и закрываем его
                    payment = Payments.objects.get(id=payment_record_id)
                    payment.status = "succeeded"
                    payment.save()

                    if payment.paid_course:
                        # get_or_create защитит от ошибок, если подписка уже почему-то была
                        Subscribe.objects.get_or_create(
                            user=payment.user,
                            course=payment.paid_course,
                            is_archived=False,
                        )
                        print(
                            f"Пользователь {payment.user} успешно подписан на курс {payment.paid_course.title}"
                        )

                    return True
                except Payments.DoesNotExist:
                    pass
        return False

    def retrieve_checkout_session(self, session_id: str) -> str:
        """
        Запрашивает актуальный статус сессии из Stripe по её идентификатору.
        Возвращает статус платежа: 'paid' или 'unpaid' (из поля payment_status).
        """
        try:
            # Вызываем метод v1.checkout.sessions.retrieve как указано в документации
            session = self.client.v1.checkout.sessions.retrieve(session_id)

            # Извлекаем поле payment_status, которое показывает факт оплаты сессии
            return session.payment_status  # Вернет 'paid' или 'unpaid'

        except stripe.error.StripeError as e:
            raise RuntimeError(f"Ошибка Stripe API при получении сессии: {str(e)}")
