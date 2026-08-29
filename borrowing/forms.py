from django import forms
from django.utils import timezone
from items.models import CONDITION_CHOICES
from .models import BorrowRequest
from .services import overlapping_requests


class BorrowRequestForm(forms.ModelForm):
    """Form for initiating tool loan requests with conflict and date bounds checking."""
    class Meta:
        model = BorrowRequest
        fields = ['start_date', 'end_date', 'message']
        widgets = {
            'start_date': forms.DateInput(attrs={
                'type': 'date',
                'class': 'form-control'
            }),
            'end_date': forms.DateInput(attrs={
                'type': 'date',
                'class': 'form-control'
            }),
            'message': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Describe your intended DIY project, tools familiarity, or pickup timeline...'
            }),
        }

    def __init__(self, *args, item=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.item = item or getattr(self.instance, 'item', None)

    def clean(self):
        cleaned_data = super().clean()
        start_date = cleaned_data.get('start_date')
        end_date = cleaned_data.get('end_date')

        if start_date and end_date:
            today = timezone.now().date()
            if start_date < today:
                self.add_error('start_date', 'Start date cannot be in the past.')

            if end_date < start_date:
                self.add_error('end_date', 'End date must be on or after start date.')

            if (end_date - start_date).days > 30:
                self.add_error('end_date', 'Maximum borrow window is 30 days.')

            if self.item and start_date >= today and end_date >= start_date:
                exclude_id = self.instance.id if self.instance and self.instance.pk else None
                conflicts = overlapping_requests(self.item, start_date, end_date, exclude_id=exclude_id)
                if conflicts.exists():
                    raise forms.ValidationError('This tool is already booked or active for the selected dates.')

        return cleaned_data


class ReturnItemForm(forms.ModelForm):
    """Form for tool return confirmation and condition audit."""
    class Meta:
        model = BorrowRequest
        fields = ['return_condition', 'return_note']
        widgets = {
            'return_condition': forms.Select(attrs={
                'class': 'form-control form-select'
            }),
            'return_note': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Document tool cleanliness, operational status, or any accessories checked...'
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['return_condition'].required = True
        self.fields['return_condition'].choices = [('', 'Select Return Condition')] + list(CONDITION_CHOICES)


class DeclineRequestForm(forms.ModelForm):
    """Form for owner specifying decline reasons."""
    class Meta:
        model = BorrowRequest
        fields = ['decline_reason']
        widgets = {
            'decline_reason': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Provide a brief explanation for declining this request...'
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['decline_reason'].required = True
