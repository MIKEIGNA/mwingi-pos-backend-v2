
class IgnoreRegNoErrorMixin:
    def add_error(self, field, error):
        
        """
        Ignore all the reg_no errors that might be raised by the tracker's model
        clean method since we dont use reg_no in this form's fields
        """
        if not "registration number" in str(error):
            super(IgnoreRegNoErrorMixin, self).add_error(field, error)