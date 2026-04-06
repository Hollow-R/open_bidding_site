from django import forms
from .models import Bid, Auction

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
        if self.auction:
            minimum_amount = self.auction.get_minimum_bid_amount()
            if amount < minimum_amount:
                raise forms.ValidationError(
                    f"Teklifiniz en az {minimum_amount} TL olmalıdır. (Mevcut: {self.auction.current_price} TL)"
                )
        return amount
    
class AuctionForm(forms.ModelForm):
    class Meta:
        model = Auction
        fields = ['owner', 'title', 'description', 'starting_price', 'end_time']
        widgets = {
            'owner': forms.Select(attrs={'class': 'form-control'}),
            'title': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'İhale Başlığı'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Ürün detayları...'}),
            'starting_price': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'end_time': forms.DateTimeInput(attrs={'class': 'form-control', 'type': 'datetime-local'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['owner'].queryset = User.objects.filter(is_active=True).order_by('username')