# How to Django



## Setting up git and environment:


### Adding .gitignore

Make a copy of the .gitignore located in this folder


### Clone your project directory

```bash
git clone <project-repo>
```


### Set up your environment 

Open a powershell and type

```powershell
py -<version> -m venv <env-name>
```

```powershell
<env_name>/Scripts/activate
```

Restart terminals if needed


### Set your requirements

```powershell
pip install django
pip install pillow
pip install django-registration-redux #if using built in registration
```

Freeze the requirements:

```powershell
pip freeze > requirements.txt
```


### Creating a branch

Make your branch:

```bash
git checkout -b <branch-name>
```

Push it to the repository:

```bash
git push -u origin <branch-name>
```


### Using branches

Always make sure you are working on your branch:

```bash
git checkout <branch-name>
```

Pull from main

```bash
git pull origin main
```

Make your changes to the code and when done:

```bash
git add *
git commit -m <commit-message>
git push
```

Now take those changes from your branch and publish them on the remote repo:

```bash
git checkout main
git merge <branch-name>
git push origin main
```



## Starting Django app


```powershell
django-admin.py startproject <project-name> .
```

```powershell
python manage.py startapp <app-name>
```



## Settings.py + Urls.py


### Templates, static and media

Go to the settings page and add your app name to the list of ```INSTALLED_APPS ```

Add in the following lines:

```python
TEMPLATE_DIR = os.path.join(BASE_DIR, 'templates')
STATIC_DIR = os.path.join(BASE_DIR, 'static')
STATICFILES_DIRS = [STATIC_DIR, ]
MEDIA_DIR = os.path.join(BASE_DIR, 'media')
```

To the ```TEMPLATES['DIRS']``` put the ```TEMPLATE_DIR```

Now add at the end of your code the following lines above the ```STATIC_URL```

```python
MEDIA_ROOT = MEDIA_DIR
MEDIA_URL = '/media/'
```

Now in the ```TEMPLATES['OPTIONS'['context_processors']]``` list add the following to the list:

```python
'django.template.context_processors.media',
```

Create a media, templates, and static folder

Add in urls.py at the end of the ```urlpatterns``` list:

```python
+ static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
```

Finally add the following imports:

```python
from django.conf import settings
from django.conf.urls.static import static
```

### Using your app urls

```python
from django import include
from <app-name> import views
```

create a urls.py within your app directory and add the following line inside ```urlpatterns```:

```python
path('<app-name>/', include('<app-name>.urls')),
```

Now in your apps urls.py add the app name above ```urlpatterns```

```python
app_name = '<app-name>'
```


### Login

Put the following

```python
REGISTRATION_OPEN = True
REGISTRATION_AUTO_LOGIN = True
LOGIN_REDIRECT_URL = '<app-name>:<view-name>'
LOGIN_URL = '<app-name>:login'
```

If using django's built in registration use:

```python
LOGIN_URL = 'auth_login'
```

Also add in the urls.py:

```python
path('accounts/register/', MyRegistrationView.as_view(), name='registration_register'),
path('accounts/', include('registration.backends.simple.urls')),
```

As well as above ```urlpatterns``` if making your own user with the built in user redirect to your own user registration with the following:

```python
class MyRegistrationView(RegistrationView):
    def get_success_url(self, user):
        return reverse('<app-name>:<profile-registration>')
```

Add the imports:

```python
from registration.backends.simple.views import RegistrationView
from django.urls import reverse
```


### Only if using built in registration

Add a registration folder in your templates

Add the following templates:

1. login.html
    - Just output the form
    - Input to login
    - Add a not registered button underneath if needed
    - Link: auth_login
2. logout.html
    - Just a message saying logout successful
    - Link: auth_logout
3. password_change_form.html
    - Just output the form
    - Input to submit
    - Link: auth_password_change
3. password_change_done.html
    - Just a message saying password change successful
4. registration_closed.html
    - Just a message saying registration is closed
5. registration_form.html
    - Just output the form
    - Add a button to register
    - Link: registration_register



## Making a base.html template


Create a base.html in templates/<app-name>

if needed add blocks with:

```html
{% block <block-name> %}
{% endblock %}
```

### Template tags

Create a templatetags folder in your app folder then add an __init__.py as well as an <app-name>_template_tags.py and in that folder add:

```python
from django import template
from <app-name>.models import <model>

register = template.Library()

@register.inclusion_tag('<app-name>/<model-name-plural>.html')
def get_<model>_list():
    return {'<model-to-pass>': <model>.objects.all()}
```

This is to be able to pass models to be able to use in base without having to pass a context_dict down

In base.html add:

```html
{% load rango_template_tags %}
```

And add an extra template as shown on the inclusion tag that just displays the model however you want it to and in base it can just be gotten by running the function


### Other templates

Any templates made can just extend the base template and use the given blocks\
Remember to use the following in every template including base:

```html
{% load static %}
```


## Models and population script



### Adding models

In you apps folder in models.py add your model as a class that extends models.Model\
Make sure to import models:

```python
from django.db import models
```

For field type see: https://docs.djangoproject.com/es/2.1/ref/models/fields/#model-field-types

For the string representation add:

```python
def __str__(self):
    return self.name
```

To slugify something import:

```python
from django.template.defaultfilters import slugify
```

Then add a slug field and add an extra save function:

```python
def save(self, *args, **kwargs):
    self.slug = slugify(self.name)
    super(<model-name>, self).save(*args, **kwargs)
```

To change the plural of the model:

```python
class Meta:
    verbose_name_plural = '<model-name-plural>'
```

If using the default User from django import:

```python
from django.contrib.auth.models import User
```

Then apply migrations by running:

```powershell
python manage.py makemigrations
python manage.py migrate
```


### Using admin

On the projects admin.py add the following lines and imports:

```python
from <app-name>.models import <model-name>

admin.site.register(<model-name>)
```


### Population script

use the following lines:

```python
import os
os.environ.setdefualt('DJANGO_SETTINGS_MODULE', '<project-name>.settings')
import django
django.setup()
from <app-name>.models import <model-name>

def populate():
    # Population scripts

def add_<model-name>(<model-categories>):
    <model> = <model-name>.objects.get_or_create(<model-category> = <model-category>)[0]
    return <model>

if __name__ == '__main__':
    print('Starting population script...')
    populate()
```

Add this file in the root directory and call it ```populate_<app-name>.py```\
Call ```python populate_<app-name>.py``` to run the population script

To list models in the views to display in template you can do the following:

```python
context_dict['<name>'] = <model-name>.objects.order_by('<+/-><model-characteristic>')[<index-or-range>]
```



## Forms


Create a forms.py for simplicity in you app directory\
import forms from django as well as the models you need\
create the following class:

```python
class <model-name>Form(forms.ModelForm):
    <model-characteristic> = forms.<field>(max_length=<length>, help_text="<help text>", initial=<initial_value>, required=<True/False>, widget=<forms.HiddenInput() """optional""">)

    class Meta:
        model = <model-name>
        fields = ('<fields-to-include>') / exclude = ('<fields-to-exclude>')
```

The form must contain either ```fields =``` or ```exclude =``` ```fields = __all__``` will include all the fields

In the views now you can add the following:

```python
from django.contrib.auth.decorators import login_required
from <app-name>.forms import *

@login_required() #if wanting to force being logged in
def add_<model-name>(request):
    form = <model-name>Form()

    if request.method == 'POST':
        #meaning the form has been submited
        if form.is_valid():
            form.save(commit=True)
            #automatically save as a new model as defined in the forms.py
            return redirect(reverse('<name-of-redirect>'))
            #make sure they are not staying in the forms
        else:
            print(form.erros)
    return render(request, '<template-for-form>', {'form': form})
```

This can also be written as a view class:

```python
from django.views import View
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from <app-name>.forms import *

class Add<model-name>(View):
    @method_decorator(login_required)
    def get(self, request):
        #get is when the user requests the information from the page
        form = <model-name>Form()
        return render(request, '<template-for-form>', {'form': form})

    @method_decorator(login_required)
    def post(self, request):
        form = <model-name>Form(request.POST, request.FILES)
        if form.is_valid(commit=True):
            return redirect(reverse('<name-of-redirect>'))
        else:
            print(form.errors)
```

Finally to put it all in a template create a new template to host your form and write:

```html
<form method="post" action=".">
    {% csrf_token %}
    {{ form.as_p }}
    <input type="submit" value="<text-to-put>">
    ### for the registration login and password change add a hidden next to allow for functional redirect
    <input type="hidden" name="next" value="{{ next }}">
</form>
```



## Cookies

Below are views to get and use server side cookies, this one is functional just to track the last visit and how many visits a user has done

```python
def get_server_side_cookie(request, cookie, default_val=None):
    val = request.session.get(cookie)
    if not val:
        val = default_val
    return val

def visitor_cookie_handler(request):
    visits = int(get_server_side_cookie(request, 'visits', 1))
    last_visit_cookie = get_server_side_cookie(request, 'last_visit', str(datetime.now()))
    last_visit_time = datetime.strptime(last_visit_cookie[:-7], '%Y-%m-%d %H:%M:%S')
    if (datetime.now() - last_visit_time).days > 0:
        visits = visits + 1
        request.session['last_visit'] = str(datetime.now())
    else:
        request.session['last_visit'] = last_visit_cookie
    request.session['visits'] = visits
```

To pass it all in a context dict this can be done like below:

```python
visitor_cookie_handler(request)
context_dict['visits'] = request.session['visits']
```

This is highly customisable