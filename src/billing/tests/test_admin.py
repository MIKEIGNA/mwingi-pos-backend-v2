
from core.test_utils.custom_testcase import TestCase
from billing.admin import SubscriptionAdmin, PaymentAdmin

class TestBillingAppAdminTestCase(TestCase):
    def test_if_admin_classes_are_implementing_audit_log_mixin(self):
        """
        We make sure that billing's admin classes we are implementing 
        AdminUserActivityLogMixin
        """
        admin_classes = (
            SubscriptionAdmin, 
            PaymentAdmin)

        for admin_class in admin_classes:
            self.assertTrue(getattr(admin_class, "adux_collect_old_values", None))


