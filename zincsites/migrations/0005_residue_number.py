# -*- coding: utf-8 -*-
# Generated by Django 1.10.7 on 2017-10-16 16:37
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('zincsites', '0004_zincsite_residues'),
    ]

    operations = [
        migrations.AddField(
            model_name='residue',
            name='number',
            field=models.IntegerField(default=100),
            preserve_default=False,
        ),
    ]
