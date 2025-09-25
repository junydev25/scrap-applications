from django.db import models

from backend.config import settings


# Create your models here.
class Approval(models.Model):
    applicant = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        verbose_name="신청자",
        on_delete=models.CASCADE,
        related_name="applications",
    )

    approved_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        verbose_name="승인자",
        on_delete=models.CASCADE,
        related_name="approvals",
    )

    STATUS_CHOICES = [
        ("pending", "대기중"),
        ("approved", "승인됨"),
        ("rejected", "거부됨"),
    ]
    status = models.CharField(
        max_length=10, choices=STATUS_CHOICES, default="pending", verbose_name="상태"
    )

    submitted_at = models.DateTimeField(verbose_name="신청날짜")  # 제출/신청 날짜
    processed_at = models.DateTimeField(
        null=True, blank=True, verbose_name="처리날짜"
    )  # 승인/거부 완료 날짜

    title = models.CharField(max_length=200, verbose_name="제목")
    content = models.TextField(verbose_name="신청 내역")
