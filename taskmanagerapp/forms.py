from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User

class SignupForm(UserCreationForm):
    class Meta: #specifies the model to be used, which is the default User model
        model = User
        fields = ['username', 'password', 'password2'] #password2 is the password confirmation

class LoginForm(forms.Form):
    username = forms.CharField()
    password = forms.CharField(widget=forms.PasswordInput)