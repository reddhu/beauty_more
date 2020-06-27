from django.test import TestCase
import os

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'my_first_project.settings.dev')
import django

django.setup()
from areas.models import Areas

province = Areas.objects.get(name='河北省')
print(province.__dict__)
print(province.parent)

list1 =[1,2,3]
list2=[]
list2.append(list1)
list2.append(list1[:])