from __future__ import unicode_literals

from django.contrib.auth.hashers import make_password, check_password
from django.contrib.postgres.fields import JSONField
from django.contrib.auth.models import User
from django.db import models


from django.db.models import Max
from django.utils import timezone

import string
import random

from django.db.models import signals

from phonenumber_field.modelfields import PhoneNumberField

from project_template.settings import BANK_ACCOUNT_NUMBER_SEED
from .tasks import *
# Create your models here.


class BankAccount(models.Model):
  user = models.ForeignKey(User)
  number = models.CharField(max_length=12, unique=True)
  mobile_num = PhoneNumberField()
  balance = models.DecimalField(max_digits=20, decimal_places=2, default=0)
  password3d = models.CharField(max_length=128)
  grid = JSONField()
  cvv = models.CharField(max_length=3)

  created_at = models.DateTimeField(default=timezone.now)
  updated_at = models.DateTimeField(default=timezone.now)

  def save(self, force_insert=False, force_update=False, using=None,
           update_fields=None):
    if self.pk is None:
      self.initialize_account()

    # Update timestamp
    self.updated_at = timezone.now()

    return super(BankAccount, self).save(
      force_insert=force_insert,
      force_update=force_update,
      using=using,
      update_fields=update_fields
    )

  def initialize_account(self):
    # Account Number generation
    prev_acc_num = BankAccount.objects.aggregate(max=Max('number'))['max']
    if not prev_acc_num:
      prev_acc_num = BANK_ACCOUNT_NUMBER_SEED
    self.number = str(int(prev_acc_num) + 1).zfill(12)

    # 3dpassword generation
    self._raw_password3d = ''.join(random.choice(string.digits) for _ in range(6))
    self.set_password3d(self._raw_password3d)

    # CVV Generation
    self.cvv = ''.join(random.choice(string.digits) for _ in range(3))

    # grid generation
    key = 'A'
    self._raw_grid = {}
    self.grid = {}

    for i in range(16):
      rnd = ''.join(random.choice(string.digits) for _ in range(2))
      self._raw_grid[key] = rnd
      self.set_grid_single(rnd, key)
      key = chr(ord(key) + 1)

  def set_password3d(self, raw_password):
    self.password3d = make_password(raw_password)

  def check_password3d(self, raw_password):

    def setter(raw_password):
      self.set_password3d(raw_password)

      self._raw_password3d = None
      self.save(update_fields=["password3d"])

    return check_password(raw_password, self.password3d, setter)

  def set_grid_single(self, raw_code, char):
    self.grid[char] = make_password(raw_code)

  def check_grid_single(self, raw_code, char):
    def setter(raw_password, key=char):
      self.set_grid_single(raw_password, key)

      self.save(update_fields=["grid"])

    return check_password(raw_code, self.grid[char], setter)

  def get_raw_password3d(self):
    if self._raw_password3d:
      return self._raw_password3d
    else:
      return None

  def get_raw_grid(self):
    if self._raw_grid:
      return self._raw_grid
    else:
      return None


def create_bank_account(sender, instance, created, **kwargs):
    if created:
        acc = BankAccount(user=instance)
        acc.save()
        create_pdf.delay(acc.id)


signals.post_save.connect(create_bank_account, sender=User)
