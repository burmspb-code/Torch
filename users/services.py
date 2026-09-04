import logging
from datetime import timedelta
from datetime import timezone

import stripe
from django.db import transaction
from django.utils import timezone
from stripe import StripeClient

from aurora.models import Subscribe
from config.settings import STRIPE_SECRET_KEY, STRIPE_WEBHOOK_SECRET
from users.models import Payments, CustomUser

logger = logging.getLogger(__name__)


class StripePaymentService:
    """Класс для взаимодействия с сервисом Stripe API."""

    def __init__(self):
        # Инициализируем клиент Stripe
        self.client = StripeClient(STRIPE_SECRET_KEY)
        self.webhook_secret = STRIPE_WEBHOOK_SECRET

    def create_checkout_session(self, payment_record: Payments) -> tuple[str, str]:
        """
        Генерирует сессию Stripe Checkout на основе записи платежа из aurora.
        Последовательно создает Product, Price и Session, сохраняя ID и URL в БД.
        """
        if payment_record.paid_course:
            product_name = f"Оплата курса: {payment_record.paid_course.title}"
        elif payment_record.paid_lesson:
            product_name = f"Оплата урока: {payment_record.paid_lesson.title}"
        else:
            product_name = "Оплата обучения"

        # Конвертируем Decimal сумму в центы (Stripe принимает только int)
        stripe_amount = int(round(payment_record.payment_amount * 100))

        try:
            # Отдельно создаем Stripe Product и сохраняем его ID
            product = self.client.v1.products.create(params={"name": product_name})
            payment_record.stripe_product_id = product.id

            # Отдельно создаем Stripe Price, связав его с product_id
            price = self.client.v1.prices.create(
                params={
                    "currency": "usd",
                    "unit_amount": stripe_amount,
                    "product": product.id,  # Связка с только что созданным продуктом
                }
            )
            payment_record.stripe_price_id = price.id

            # Создаем Checkout Session с использованием полученного price_id
            checkout_session = self.client.v1.checkout.sessions.create(
                params={
                    "payment_method_types": ["card"],
                    "line_items": [
                        {
                            "price": price.id,  # Передаем готовый ID цены вместо price_data
                            "quantity": 1,
                        }
                    ],
                    "mode": "payment",
                    "success_url": "http://127.0.0.1:8000/",  # Для локального тестирования
                    "cancel_url": "http://127.0.0.1:8000/",
                    "metadata": {"payment_record_id": str(payment_record.id)},
                }
            )

            # Сохраняем все необходимые Stripe ID и ссылку на оплату в модель
            payment_record.stripe_session_id = checkout_session.id
            payment_record.payment_url = checkout_session.url
            payment_record.payment_method = "stripe"  # Фиксируем метод платежа

            # Принудительно сохраняем все изменения в базу данных Aurora
            payment_record.save()

            return checkout_session.id, checkout_session.url

        except stripe.StripeError as e:
            logger.error(f"Ошибка Stripe API при генерации платежной сессии: {e}")
            raise RuntimeError(f"Ошибка Stripe API при генерации сессии: {str(e)}")

    def verify_and_process_webhook(self, payload: bytes, sig_header: str) -> bool:
        """
        Верифицирует криптографическую подпись вебхука от Stripe
        и автоматически переводит статус платежа в базе Aurora в 'succeeded'.
        """
        try:
            # ИСПРАВЛЕНО: В новых версиях SDK верификация делается через self.client.webhooks
            event = self.client.webhooks.construct_event(
                payload=payload, sig_header=sig_header, secret=self.webhook_secret
            )
        except (ValueError, stripe.SignatureVerificationError) as e:
            logger.error(f"Ошибка верификации подписи Stripe: {e}")
            return False

        if event["type"] == "checkout.session.completed":
            session = event["data"]["object"]
            payment_record_id = session.get("metadata", {}).get("payment_record_id")

            if not payment_record_id:
                logger.warning(
                    "Вебхук получен, но 'payment_record_id' отсутствует в metadata."
                )
                return False

            try:
                with transaction.atomic():
                    payment = Payments.objects.select_for_update().get(
                        id=payment_record_id
                    )

                    if payment.status == "succeeded":
                        logger.info(
                            f"Платеж {payment_record_id} уже был успешно обработан ранее."
                        )
                        return True

                    payment.status = "succeeded"
                    payment.save()

                    # Обработка подписки на КУРС
                    if payment.paid_course:
                        Subscribe.objects.get_or_create(
                            user=payment.user,
                            course=payment.paid_course,
                            is_archived=False,
                        )
                        logger.info(
                            f"Пользователь {payment.user.id} успешно подписан на курс {payment.paid_course.title}"
                        )

                    elif payment.paid_lesson:
                        logger.info(
                            f"Пользователь {payment.user.id} успешно оплатил отдельный урок {payment.paid_lesson.title}"
                        )

                    return True

            except Payments.DoesNotExist:
                logger.error(
                    f"Запись платежа с ID {payment_record_id} не найдена в БД Aurora."
                )
                return False
            except Exception as e:
                logger.critical(
                    f"Непредвиденная ошибка при обработке платежа {payment_record_id}: {e}"
                )
                return False

        return False

    def retrieve_checkout_session(self, session_id: str) -> str:
        """
        Запрашивает актуальный статус сессии из Stripe по её идентификатору.
        Возвращает статус платежа: 'paid' или 'unpaid'.
        """
        try:
            session = self.client.v1.checkout.sessions.retrieve(session_id)
            return session.payment_status

        except stripe.StripeError as e:
            logger.error(f"Ошибка Stripe API при получении сессии: {e}")
            raise RuntimeError(f"Ошибка Stripe API при получении сессии: {str(e)}")


class UserActivityService:
    """Сервис для управления жизненным циклом и активностью пользователей."""

    def __init__(self, inactivity_days: int = 30):
        self.inactivity_days = inactivity_days
        self.cutoff_date = timezone.now() - timedelta(days=self.inactivity_days)

    def _get_inactive_users(self):
        """Приватный метод: ищет пользователей по последней дате входа,
        кроме администраторов и модераторов.
        """
        return CustomUser.objects.filter(
            last_login__lt=self.cutoff_date, is_active=True
        ).exclude(is_superuser=True, is_staff=True)

    def _block_users(self, queryset) -> int:
        """Приватный метод: блокирует переданный кверисет."""
        count = queryset.count()
        if count > 0:
            queryset.update(is_active=False)
        return count

    def enable_blocking(self) -> int:
        """Главная точка входа: запускает массовую блокировку."""
        inactive_users = self._get_inactive_users()
        return self._block_users(inactive_users)

    @property
    def is_monthly_user_activity(self):
        """Определение месячной активновти пользователя.

        Возвращает
            True,  если пользователь логинился в течении месяца,
            False, в противном случае.

        """
        one_month_ago = timezone.now() - timedelta(days=30)
        return True if self.user.last_login >= one_month_ago else False
