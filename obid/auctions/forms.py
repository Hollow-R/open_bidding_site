from django import forms
from .models import Bid

class BidForm(forms.ModelForm):
    class Meta:
        model = Bid
        fields = ['amount']
        widgets = {
            'amount': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'})
        }

    def __init__(self, *args, **kwargs):
        self.auction = kwargs.pop('auction', None)
        super().__init__(*args, **kwargs)

    def clean_amount(self):
        amount = self.cleaned_data.get('amount')
        if self.auction and amount <= self.auction.current_price:
            raise forms.ValidationError(f"Teklifiniz güncel fiyattan ({self.auction.current_price} TL) yüksek olmalıdır!")
        return amount