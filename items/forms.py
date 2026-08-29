from django import forms
from .models import Item, Category


class ItemForm(forms.ModelForm):
    """Form for listing and modifying tool catalog entries."""
    class Meta:
        model = Item
        fields = ['category', 'title', 'description', 'condition', 'photo']
        widgets = {
            'category': forms.Select(attrs={
                'class': 'form-control form-select'
            }),
            'title': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'e.g., DeWalt 20V Cordless Circular Saw'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'Include specifications, included accessories/blades, and usage tips...'
            }),
            'condition': forms.Select(attrs={
                'class': 'form-control form-select'
            }),
            'photo': forms.FileInput(attrs={
                'class': 'form-control-file'
            })
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['category'].empty_label = "Select a category"
