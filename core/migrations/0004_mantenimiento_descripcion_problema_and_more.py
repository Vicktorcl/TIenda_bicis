# Generated by Django 4.2.13 on 2024-07-06 23:57

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0003_alter_bodega_table'),
    ]

    operations = [
        migrations.AddField(
            model_name='mantenimiento',
            name='descripcion_problema',
            field=models.TextField(default='Sin descripción', verbose_name='Descripción del problema'),
        ),
        migrations.AlterField(
            model_name='mantenimiento',
            name='cliente',
            field=models.ForeignKey(on_delete=django.db.models.deletion.DO_NOTHING, to='core.perfil', verbose_name='Cliente'),
        ),
        migrations.AlterUniqueTogether(
            name='mantenimiento',
            unique_together={('fecha_programada', 'hora_programada')},
        ),
        migrations.RemoveField(
            model_name='mantenimiento',
            name='bicicleta',
        ),
        migrations.RemoveField(
            model_name='mantenimiento',
            name='tipo_servicio',
        ),
    ]
