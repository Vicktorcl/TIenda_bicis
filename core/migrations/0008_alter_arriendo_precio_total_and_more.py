# Generated by Django 4.2.13 on 2024-07-10 00:31

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0007_alter_arriendo_options_alter_bicicleta_options_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='arriendo',
            name='precio_total',
            field=models.IntegerField(verbose_name='Precio_Total'),
        ),
        migrations.AlterField(
            model_name='bicicleta',
            name='precio_por_dia',
            field=models.IntegerField(verbose_name='Precio_Por_Dia'),
        ),
    ]
