from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User

class SignupForm(UserCreationForm):

    email = forms.EmailField(required=True, help_text='Required. Enter a valid email address.')

    class Meta: #specifies the model to be used, which is the default User model
        model = User
        fields = ['username', 'email', 'password', 'password2'] #password2 is the password confirmation

    def save(self, commit=True):
        user = super(SignupForm, self).save(commit=False)
        user.email = self.cleaned_data['email']
        if commit:
            user.save()
        return user

class LoginForm(forms.Form):
    username = forms.CharField()
    password = forms.CharField(widget=forms.PasswordInput)