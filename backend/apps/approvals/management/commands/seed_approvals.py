import random

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.utils import timezone
from django_seed import Seed

from backend.apps.approvals.models import Approval

User = get_user_model()


class Command(BaseCommand):
    help = "Seed database with Approval test data"

    def handle(self, *args, **kwargs):
        seeder = Seed.seeder()

        # 테스트용 유저 미리 생성(50명)
        User.objects.filter(username__startswith="test-user").delete()
        test_users = [
            User.objects.create_user(username=f"test-user{i}", password="1234")
            for i in range(50)
        ]

        status = ["pending"] * 5 + ["approved"] * 3 + ["rejected"] * 2

        def generate_processed_at(x):
            print(x)
            submitted = x["submitted_at"]
            status_value = x["status"]

            if status_value in ["approved", "rejected"]:
                delta_seconds = (timezone.now() - submitted).total_seconds()
                random_seconds = seeder.faker.random_int(min=0, max=int(delta_seconds))
                return submitted + timezone.timedelta(seconds=random_seconds)

            return None

        seeder.add_entity(
            Approval,
            1000,
            {
                "applicant": lambda x: seeder.faker.random_element(test_users),
                "approved_by": lambda x: seeder.faker.random_element(test_users),
                "status": lambda x: seeder.faker.random_element(status),
                "submitted_at": lambda x: seeder.faker.date_time_between(
                    start_date="-30d",
                    end_date="now",
                    tzinfo=timezone.get_current_timezone(),
                ),
                "processed_at": None,
                "title": lambda x: seeder.faker.sentence(),
                "content": lambda x: seeder.faker.text(),
            },
        )

        inserted_pks = seeder.execute()
        self.stdout.write(
            self.style.SUCCESS(f"Seeded {len(inserted_pks[Approval])} Approvals")
        )

        # processed_at 설정
        approvals_to_update = list(
            Approval.objects.filter(status__in=["approved", "rejected"])
        )

        for approval in approvals_to_update:
            delta_seconds = (timezone.now() - approval.submitted_at).total_seconds()
            random_seconds = random.randint(0, int(delta_seconds))
            approval.processed_at = approval.submitted_at + timezone.timedelta(
                seconds=random_seconds
            )

        Approval.objects.bulk_update(approvals_to_update, ["processed_at"])
