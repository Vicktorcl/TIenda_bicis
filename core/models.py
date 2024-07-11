from django.contrib.auth.models import User
from django.core.validators import MaxValueValidator, MinValueValidator
from core.templatetags.custom_filters import formatear_dinero
from django.db import models
from django.db.models import Min
from django.db import connection
from django.db.models import UniqueConstraint
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _
from datetime import timedelta, date
from django.utils import timezone


class Categoria(models.Model):
    nombre = models.CharField(max_length=100, blank=False, null=False, verbose_name='Nombre categoría')
    
    class Meta:
        db_table = 'CateProd'
        verbose_name = "Categoría de producto"
        verbose_name_plural = "Categorías de productos"
        ordering = ['nombre']
    
    def __str__(self):
        return f'{self.nombre}'
    
    def acciones():
        return {
            'accion_eliminar': 'eliminar la Categoría',
            'accion_actualizar': 'actualizar la Categoría'
        }

class Producto(models.Model):
    categoria = models.ForeignKey(Categoria, on_delete=models.DO_NOTHING, verbose_name='Categoría')
    nombre = models.CharField(max_length=100, blank=False, null=False, verbose_name='Nombre producto')
    descripcion = models.CharField(max_length=800, blank=False, null=False, verbose_name='Descripción')
    precio = models.IntegerField(blank=False, null=False, verbose_name='Precio')
    descuento_subscriptor = models.IntegerField(
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        blank=False,
        null=False,
        verbose_name='% Descuento subscriptor'
    )
    descuento_oferta = models.IntegerField(
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        blank=False,
        null=False,
        verbose_name='% Descuento oferta'
    )
    imagen = models.ImageField(upload_to='productos/', blank=False, null=False, verbose_name='Imagen')
    
    class Meta:
        db_table = 'Prod'
        verbose_name = "Producto"
        verbose_name_plural = "Productos"
        ordering = ['categoria', 'nombre']

    def __str__(self):
        return f'{self.nombre} (ID {self.id})'
    
    def acciones():
        return {
            'accion_eliminar': 'eliminar el Producto',
            'accion_actualizar': 'actualizar el Producto'
        }

class Perfil(models.Model):
    USUARIO_CHOICES = [
        ('Cliente', 'Cliente'),
        ('Administrador', 'Administrador'),
        ('Superusuario', 'Superusuario'),
    ]
    usuario = models.OneToOneField(User, on_delete=models.CASCADE)
    tipo_usuario = models.CharField(
        choices=USUARIO_CHOICES,
        max_length=50,
        blank=False,
        null=False,
        verbose_name='Tipo de usuario'
    )
    rut = models.CharField(max_length=15, blank=False, null=False, verbose_name='RUT')
    direccion = models.CharField(max_length=800, blank=False, null=False, verbose_name='Dirección')
    subscrito = models.BooleanField(blank=False, null=False, verbose_name='Subscrito')
    imagen = models.ImageField(upload_to='perfiles/', blank=False, null=False, verbose_name='Imagen')
    
    class Meta:
        db_table = 'Usuario'
        verbose_name = "Perfil de usuario"
        verbose_name_plural = "Perfiles de usuarios"
        ordering = ['tipo_usuario']

    def __str__(self):
        subscrito = ''
        if self.tipo_usuario == 'Cliente':
            subscrito = ' subscrito' if self.subscrito else ' no subscrito'
        return f'{self.usuario.first_name} {self.usuario.last_name} (ID {self.id} - {self.tipo_usuario}{subscrito})'
    
    def acciones():
        return {
            'accion_eliminar': 'eliminar el Perfil',
            'accion_actualizar': 'actualizar el Perfil'
        }

class Carrito(models.Model):
    cliente = models.ForeignKey(Perfil, on_delete=models.DO_NOTHING)
    producto = models.ForeignKey(Producto, on_delete=models.DO_NOTHING)
    precio = models.IntegerField(blank=False, null=False, verbose_name='Precio')
    descuento_subscriptor = models.IntegerField(
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        blank=False,
        null=False,
        verbose_name='Descto subs'
    )
    descuento_oferta = models.IntegerField(
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        blank=False,
        null=False,
        verbose_name='Descto oferta'
    )
    descuento_total = models.IntegerField(
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        blank=False,
        null=False,
        verbose_name='Descto total'
    )
    descuentos = models.IntegerField(blank=False, null=False, verbose_name='Descuentos')
    precio_a_pagar = models.IntegerField(blank=False, null=False, verbose_name='Precio a pagar')
    
    class Meta:
        db_table = 'Carro'
        verbose_name = "Carrito de compras"
        verbose_name_plural = "Carritos de compras"
        ordering = ['cliente', 'producto']

    def __str__(self):
        return f'{self.id} Carrito de {self.cliente.usuario.first_name} {self.cliente.usuario.last_name} (Producto {self.producto.categoria.nombre} - {self.producto.nombre} - {formatear_dinero(self.precio)})'
    
    def acciones():
        return {
            'accion_eliminar': 'eliminar el Carrito',
            'accion_actualizar': 'actualizar el Carrito'
        }

class Boleta(models.Model):
    ESTADO_CHOICES = [
        ('Anulado', 'Anulado'),
        ('Vendido', 'Vendido'),
        ('Despachado', 'Despachado'),
        ('Entregado', 'Entregado'),
    ]
    nro_boleta = models.IntegerField(primary_key=True, blank=False, null=False, verbose_name='Nro boleta')
    cliente = models.ForeignKey(Perfil, on_delete=models.DO_NOTHING)
    monto_sin_iva = models.IntegerField(blank=False, null=False, verbose_name='Monto sin IVA')
    iva = models.IntegerField(blank=False, null=False, verbose_name='IVA')
    total_a_pagar = models.IntegerField(blank=False, null=False, verbose_name='Total a pagar')
    fecha_venta = models.DateField(blank=False, null=False, verbose_name='Fecha de venta')
    fecha_despacho = models.DateField(blank=True, null=True, verbose_name='Fecha de despacho')
    fecha_entrega = models.DateField(blank=True, null=True, verbose_name='Fecha de entrega')
    estado = models.CharField(choices=ESTADO_CHOICES, max_length=50, blank=False, null=False, verbose_name='Estado')
    
    class Meta:
        db_table = 'Boleta'
        verbose_name = "Boleta"
        verbose_name_plural = "Boletas"

    def __str__(self):
        return f'Boleta {self.nro_boleta} de {self.cliente.usuario.first_name} {self.cliente.usuario.last_name} por {formatear_dinero(self.total_a_pagar)}'
    
    def acciones():
        return {
            'accion_eliminar': 'eliminar la Boleta',
            'accion_actualizar': 'actualizar la Boleta'
        }

class Bodega(models.Model):
    producto = models.ForeignKey(Producto, on_delete=models.DO_NOTHING, verbose_name='Producto')

    class Meta:
        db_table = 'Bodega'
        verbose_name = "Bodega"
        verbose_name_plural = "Bodegas"

    def __str__(self):
        consulta_sql = f'SELECT boleta_id FROM BoletaDet WHERE bodega_id={self.id}'
        with connection.cursor() as cursor:
            cursor.execute(consulta_sql)
            resultado = cursor.fetchone()
        info = f'Vendido (Boleta {resultado[0]})' if resultado else 'En bodega'
        return f'{self.producto.nombre} (ID {self.id}) - {info}'
    
    def acciones():
        return {
            'accion_eliminar': 'eliminar el producto de la Bodega',
            'accion_actualizar': 'actualizar el producto de la Bodega'
        }

class DetalleBoleta(models.Model):
    boleta = models.ForeignKey(Boleta, on_delete=models.DO_NOTHING)
    bodega = models.ForeignKey(Bodega, on_delete=models.DO_NOTHING)
    precio = models.IntegerField(blank=False, null=False, verbose_name='Precio')
    descuento_subscriptor = models.IntegerField(
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        blank=False,
        null=False,
        verbose_name='Descto subs'
    )
    descuento_oferta = models.IntegerField(
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        blank=False,
        null=False,
        verbose_name='Descto oferta'
    )
    descuento_total = models.IntegerField(
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        blank=False,
        null=False,
        verbose_name='Descto total'
    )
    descuentos = models.IntegerField(blank=False, null=False, verbose_name='Descuentos')
    precio_a_pagar = models.IntegerField(blank=False, null=False, verbose_name='Precio a pagar')
    
    class Meta:
        db_table = 'BoletaDet'
        verbose_name = "Detalle de boleta"
        verbose_name_plural = "Detalles de boletas"

    def __str__(self):
        minimo_id = DetalleBoleta.objects.filter(boleta_id=self.boleta.nro_boleta).aggregate(minimo_id=Min('id'))['minimo_id']
        nro_item = self.id - minimo_id + 1
        return f'Boleta {self.boleta.nro_boleta} Item {nro_item} {self.bodega.producto.nombre} - {formatear_dinero(self.precio_a_pagar)}'
    
    def acciones():
        return {
            'accion_eliminar': 'eliminar el Detalle de la Boleta',
            'accion_actualizar': 'actualizar el Detalle de la Boleta'
        }


class Mantenimiento(models.Model):
    cliente = models.ForeignKey(Perfil, on_delete=models.DO_NOTHING, verbose_name='Cliente', blank=False, null=False)
    fecha_programada = models.DateField(verbose_name='Fecha programada', blank=False, null=False)
    hora_programada = models.TimeField(verbose_name='Hora programada', blank=False, null=False)
    descripcion_problema = models.TextField(verbose_name='Descripción del problema', blank=False, null=False)

    class Meta:
        db_table = 'Mantenimiento'
        verbose_name = 'Mantenimiento'
        verbose_name_plural = 'Mantenimientos'
        ordering = ['fecha_programada', 'hora_programada']
        constraints = [
            models.UniqueConstraint(fields=['fecha_programada', 'hora_programada'], name='unique_fecha_hora')
        ]

    def clean(self):
        if self.hora_programada:
            # Validar que la hora esté en intervalos de una hora exacta
            if self.hora_programada.minute != 0 or self.hora_programada.second != 0:
                raise ValidationError('La hora del mantenimiento debe estar en intervalos de una hora exacta.')

            # Verificar si ya existe un mantenimiento en la misma fecha y hora
            if Mantenimiento.objects.filter(fecha_programada=self.fecha_programada, hora_programada=self.hora_programada).exists():
                raise ValidationError('Ya existe un mantenimiento programado para esa fecha y hora.')
        else:
            raise ValidationError('Debe especificar una hora programada para el mantenimiento.')

    def __str__(self):
        return f'Mantenimiento el {self.fecha_programada} a las {self.hora_programada} por {self.cliente.usuario.first_name} {self.cliente.usuario.last_name}'
    
    
class Bicicleta(models.Model):
    MARCAS = [
        ('TREK', 'Trek'),
        ('GIANT', 'Giant'),
        ('SPECIALIZED', 'Specialized'),
        ('CANNONDALE', 'Cannondale'),
    ]

    marca = models.CharField(max_length=50, choices=MARCAS)
    modelo = models.CharField(max_length=100)
    año = models.PositiveIntegerField()
    precio_por_dia = models.IntegerField(blank=False, null=False, verbose_name='Precio_Por_Dia')
    disponible = models.BooleanField(default=True)
    
    class Meta:
        db_table = 'bicicletas'
        verbose_name = 'Bicicleta'
        verbose_name_plural = 'Bicicletas'

    def __str__(self):
        return f"{self.marca} {self.modelo} ({self.año})"

    def fechas_disponibles(self):
        arriendos = self.arriendo_set.all()

        if not arriendos.exists():
            return None

        fechas_ocupadas = set()
        for arriendo in arriendos:
            fechas_ocupadas.update(self.get_dates_range(arriendo.fecha_inicio, arriendo.fecha_fin))

        fechas_totales = set()
        fecha_actual = timezone.now().date()
        while fecha_actual.year <= self.año:
            if fecha_actual.weekday() < 5:  # Excluir sábado y domingo
                fechas_totales.add(fecha_actual)
            fecha_actual += timedelta(days=1)

        fechas_disponibles = fechas_totales - fechas_ocupadas
        return fechas_disponibles

    def get_dates_range(self, start_date, end_date):
        dates = []
        current_date = start_date
        while current_date <= end_date:
            dates.append(current_date)
            current_date += timedelta(days=1)
        return dates


class Arriendo(models.Model):
    bicicleta = models.ForeignKey(Bicicleta, on_delete=models.CASCADE)
    cliente = models.ForeignKey(Perfil, on_delete=models.DO_NOTHING, verbose_name='Cliente', blank=False, null=False)
    fecha_inicio = models.DateField()
    fecha_fin = models.DateField()
    precio_total = models.IntegerField(blank=False, null=False, verbose_name='Precio_Total')

    class Meta:
        db_table = 'arriendos'
        verbose_name = 'Arriendo'
        verbose_name_plural = 'Arriendos'

    def __str__(self):
        return f"Arriendo de {self.bicicleta} por {self.cliente.usuario.first_name} {self.cliente.usuario.last_name}"

    def save(self, *args, **kwargs):
        # Calcular el precio total basado en la duración del arriendo
        dias_arriendo = (self.fecha_fin - self.fecha_inicio).days + 1
        self.precio_total = dias_arriendo * self.bicicleta.precio_por_dia
        super().save(*args, **kwargs)

    def clean(self):
        if self.fecha_inicio < timezone.now().date():
            raise ValidationError({'fecha_inicio': _("La fecha de inicio no puede ser anterior a la fecha actual.")})
        if self.fecha_inicio > self.fecha_fin:
            raise ValidationError({
                'fecha_inicio': _("La fecha de inicio no puede ser posterior a la fecha de fin."),
                'fecha_fin': _("La fecha de fin no puede ser anterior a la fecha de inicio.")
            })
        # Verificar la disponibilidad de la bicicleta en el rango de fechas
        arriendos_existentes = Arriendo.objects.filter(
            bicicleta=self.bicicleta,
            fecha_fin__gte=self.fecha_inicio,
            fecha_inicio__lte=self.fecha_fin
        ).exclude(pk=self.pk)
        if arriendos_existentes.exists():
            raise ValidationError(_("La bicicleta no está disponible en el rango de fechas seleccionado."))