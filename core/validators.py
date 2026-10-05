from django.core.exceptions import ValidationError


class PersianMinimumLengthValidator:

    def __init__(self, min_length=8):
        self.min_length = min_length

    def validate(self, password, user=None):

        if len(password) < self.min_length:
            raise ValidationError(
                f"کلمه عبور باید حداقل {self.min_length} کاراکتر داشته باشد."
            )

    def get_help_text(self):

        return (
            f"کلمه عبور باید حداقل {self.min_length} کاراکتر داشته باشد."
        )