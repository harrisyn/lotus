from __future__ import absolute_import, unicode_literals
from lotus.celery import app
from datetime import datetime
from .models import Subscription
from .generate_invoice import generate_invoice
from django_tenants.utils import get_tenant_model, tenant_context


@app.task
def calculate_invoice():
    for tenant in get_tenant_model().objects.exclude(schema_name="public"):
        with tenant_context(tenant):
            ending_subscriptions = Subscription.objects.filter(
                status="active", end_date__lte=datetime.now()
            )
            for subscription in ending_subscriptions:
                # Generate the invoice
                try:
                    generate_invoice(subscription)
                except Exception as e:
                    print(e)
                    print(
                        "Error generating invoice for subscription {}".format(
                            subscription
                        )
                    )
                    continue
                # Renew the subscription
                subscription.start_date = datetime.now()
                subscription.end_date = subscription.billing_plan.subscription_end_date(
                    subscription.start_date
                )
                subscription.save()