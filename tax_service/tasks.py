import csv
import io
import traceback
from django.utils import timezone
from django.utils.dateparse import parse_datetime
from django.db import transaction
from celery import shared_task
from .models import ImportJob
from .services import TaxCalculationService
import logging

logger = logging.getLogger(__name__)


def process_batch(task_self, service, job_id, batch):
    success_count = 0
    errors = []

    for row_idx, row in batch:
        try:
            with transaction.atomic():
                lat = float(row.get("lat") or row.get("latitude"))
                lon = float(row.get("lon") or row.get("longitude"))
                subtotal = row.get("subtotal") or row.get("amount") or "0.00"
                timestamp_str = row.get("timestamp") or row.get("date")
                if timestamp_str:
                    dt = parse_datetime(timestamp_str)
                    if dt and timezone.is_naive(dt):
                        order_timestamp = timezone.make_aware(dt)
                    else:
                        order_timestamp = dt or timezone.now()
                else:
                    order_timestamp = timezone.now()

                service.process_order(
                    lat=lat, lon=lon, subtotal=subtotal, order_timestamp=order_timestamp
                )
                success_count += 1
        except Exception as e:
            errors.append({"row": row_idx, "error": str(e)})

    return success_count, errors


@shared_task(bind=True)
def import_orders_task(self, job_id, file_content):
    try:
        job = ImportJob.objects.get(id=job_id)
    except ImportJob.DoesNotExist:
        logger.error(f"ImportJob {job_id} not found.")
        return

    job.status = "PROCESSING"
    job.started_at = timezone.now()
    # Pre-compute total rows approximately
    total_lines = len(file_content.strip().split("\n")) - 1
    job.total_rows = max(total_lines, 0)
    job.save()

    service = TaxCalculationService()
    batch_size = 500
    batch = []

    total_processed = 0
    total_success = 0
    total_failed = 0
    errors = []

    try:
        f = io.StringIO(file_content)
        reader = csv.DictReader(f)

        for row_idx, row in enumerate(reader, start=1):
            batch.append((row_idx, row))

            if len(batch) >= batch_size:
                s, f_err = process_batch(self, service, job_id, batch)
                total_success += s
                errors.extend(f_err)
                total_failed += len(f_err)
                total_processed += len(batch)
                batch = []

                job.processed_rows = total_processed
                job.save(update_fields=["processed_rows"])

        if batch:
            s, f_err = process_batch(self, service, job_id, batch)
            total_success += s
            errors.extend(f_err)
            total_failed += len(f_err)
            total_processed += len(batch)

        job.status = "COMPLETED"
        job.total_rows = total_processed
        job.processed_rows = total_processed
        job.success_rows = total_success
        job.failed_rows = total_failed
        job.error_report = errors
        job.finished_at = timezone.now()
        job.save()

    except Exception as e:
        logger.exception(f"Critical error in import jobs: {e}")
        job.status = "FAILED"
        job.error_report.append(
            {"global_error": str(e), "trace": traceback.format_exc()}
        )
        job.finished_at = timezone.now()
        job.save()
