from django import forms
from django.forms import ModelForm, Form
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm
from .models import Categoria, Producto, Perfil, Mantenimiento, Arriendo, Bicicleta
from bootstrap_datepicker_plus.widgets import DateTimePickerInput
from django.core.exceptions import ValidationError
from datetime import date, datetime
from django.utils import timezone
from datetime import time, timedelta
from django.utils.translation import gettext_lazy as _

                                                                                                
class ProductoForm(ModelForm):
    class Meta:
        model = Producto
        fields = '__all__'
        widgets = {
            'descripcion': forms.Textarea(),
            'imagen': forms.FileInput()
        }
        labels = {
            'nombre': 'Nombre',
            'descuento_subscriptor': 'Subscriptor(%)',
            'descuento_oferta': 'Oferta(%)',
        }

class BodegaForm(Form):
    categoria = forms.ModelChoiceField(queryset=Categoria.objects.all(), label='Categoría')
    producto = forms.ModelChoiceField(queryset=Producto.objects.none(), label='Producto')
    cantidad = forms.IntegerField(label='Cantidad')
    class Meta:
        fields = '__all__'

class IngresarForm(Form):
    username = forms.CharField(widget=forms.TextInput(), label="Cuenta")
    password = forms.CharField(widget=forms.PasswordInput(), label="Contraseña")
    class Meta:
        fields = ['username', 'password']

# PARA LA PAGINA DE REGISTRO DE NUEVO CLIENTE:
# Crea RegistroUsuarioForm como una clase que hereda de UserCreationForm
# asocialo con el modelo User
# muestra los campos: 
#    'username', 'first_name', 'last_name', 'email', 'password1' y 'password2'
# renombra la etiqueta del campo 'email' por 'E-mail'
class RegistroUsuarioForm(UserCreationForm):
   class Meta:
        model = User
        fields = ['username', 'first_name', 'last_name', 'email', 'password1', 'password2']
        labels = {
            'email': 'E-mail'
        }

# PARA LA PAGINA DE REGISTRO DE NUEVO CLIENTE Y MIS DATOS:
# Crear RegistroPerfilForm como una clase que hereda de ModelForm
# asocialo con el modelo Perfil
# muestra los campos: 'rut', 'direccion', 'subscrito', 'imagen'
# excluye el campo 'tipo_usuario', pues sólo los administradores asignan el tipo
# crea los widgets para:
#   - direccion como Textarea,
#   - imagen como FileInput()
class RegistroPerfilForm(ModelForm):
    class Meta:
        model = Perfil
        fields = ['rut', 'direccion', 'subscrito', 'imagen']
        exclude = ['tipo_usuario']
        widgets = {
            'direccion': forms.Textarea(),
            'imagen': forms.FileInput(),
        }
        labels = {
            'subscrito': 'Usuario Premium'
        }

# PARA LA PAGINA MIS DATOS Y MANTENEDOR DE USUARIOS:
# Crear UsuarioForm como una clase que hereda de ModelForm
# asocialo con el modelo User
# muestra todos los campos: 'username', 'first_name', 'last_name' e 'email'
# renombra la etiqueta del campo 'email' por 'E-mail'
class UsuarioForm(ModelForm):
   class Meta:
        model = User
        fields = ['username', 'first_name', 'last_name', 'email']

        labels = {
            'email': 'E-mail'
        }

# PARA LA PAGINA MANTENEDOR DE USUARIOS:
# Crear PerfilForm como una clase que hereda de ModelForm
# asocialo con el modelo Perfil
# muestra todos los campos: 
#    'tipo_usuario', 'rut', 'direccion', 'subscrito'e 'imagen'
# crea los widgets para:
#   - direccion como Textarea,
#   - imagen como FileInput()
class PerfilForm(ModelForm):
    class Meta:
        model = Perfil
        fields = ['tipo_usuario', 'rut', 'direccion', 'subscrito', 'imagen']
        widgets = {
            'direccion': forms.Textarea(),
            'imagen': forms.FileInput(),
        }
        labels = {
            'subscrito': 'Usuario Premium'
        }

class MantenimientoForm(forms.ModelForm):
    class Meta:
        model = Mantenimiento
        fields = ['fecha_programada', 'hora_programada', 'descripcion_problema']
        widgets = {
            'fecha_programada': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'hora_programada': forms.Select(attrs={'class': 'form-control'}),
            'descripcion_problema': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['hora_programada'].choices = []

        if 'fecha_programada' in self.data:
            fecha = self.data['fecha_programada']
            if fecha:
                horas_disponibles = self.get_horas_disponibles(fecha)
                self.fields['hora_programada'].choices = horas_disponibles

    def clean_hora_programada(self):
        hora = self.cleaned_data['hora_programada']
        
        if isinstance(hora, str):
            try:
                hora = datetime.strptime(hora, '%H:%M').time()
            except ValueError:
                raise ValidationError('Formato de hora no válido.')

        if hora.minute != 0 or hora.second != 0:
            raise ValidationError('La hora del mantenimiento debe estar en intervalos de una hora exacta.')

        return hora

    def clean_descripcion_problema(self):
        descripcion = self.cleaned_data['descripcion_problema']
        if not descripcion:
            raise ValidationError('La descripción del problema es obligatoria.')
        return descripcion

    def clean_fecha_programada(self):
        fecha = self.cleaned_data['fecha_programada']
        if fecha.weekday() in [5, 6]:  # 5 es sábado y 6 es domingo
            raise ValidationError('No se pueden agendar mantenimientos los fines de semana. Seleccione un día entre lunes y viernes.')
        return fecha

    def clean(self):
        cleaned_data = super().clean()
        fecha_programada = cleaned_data.get('fecha_programada')
        hora_programada = cleaned_data.get('hora_programada')

        if fecha_programada and hora_programada:
            if Mantenimiento.objects.filter(fecha_programada=fecha_programada, hora_programada=hora_programada).exists():
                raise ValidationError('Ya hay un mantenimiento programado para esta fecha y hora.')

    def get_horas_disponibles(self, fecha):
        mantenimientos_programados = Mantenimiento.objects.filter(fecha_programada=fecha).values_list('hora_programada', flat=True)
        horas_disponibles = []

        hora_inicio = time(8, 0)  # Hora de inicio de disponibilidad
        hora_fin = time(19, 0)   # Hora de fin de disponibilidad
        intervalo = timedelta(hours=1)  # Intervalo de una hora

        hora_actual = datetime.combine(datetime.today(), hora_inicio)
        hora_fin_datetime = datetime.combine(datetime.today(), hora_fin)

        while hora_actual.time() <= hora_fin:
            if hora_actual.time() not in mantenimientos_programados:
                hora_str = hora_actual.time().strftime('%H:%M')
                horas_disponibles.append((hora_str, hora_str))
            hora_actual += intervalo

        return horas_disponibles


class ArriendoForm(forms.ModelForm):
    class Meta:
        model = Arriendo
        fields = ['bicicleta', 'fecha_inicio', 'fecha_fin']
        widgets = {
            'bicicleta': forms.Select(attrs={'class': 'form-control'}),
            'fecha_inicio': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'fecha_fin': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Reiniciar el queryset de bicicleta
        self.fields['bicicleta'].queryset = Bicicleta.objects.filter(disponible=True)

        if 'bicicleta' in self.data:
            try:
                bicicleta_id = int(self.data.get('bicicleta'))
                self.fields['fecha_inicio'].queryset = Bicicleta.objects.get(id=bicicleta_id).fechas_disponibles()
            except (ValueError, TypeError, Bicicleta.DoesNotExist):
                pass  # Manejo de error si no se puede convertir el id de la bicicleta o no se encuentra

    def clean(self):
        cleaned_data = super().clean()
        fecha_inicio = cleaned_data.get('fecha_inicio')
        fecha_fin = cleaned_data.get('fecha_fin')
        bicicleta = cleaned_data.get('bicicleta')

        if fecha_inicio and fecha_fin and bicicleta:
            # Verificar la disponibilidad de la bicicleta en el rango de fechas
            arriendos_existentes = Arriendo.objects.filter(
                bicicleta=bicicleta,
                fecha_fin__gte=fecha_inicio,
                fecha_inicio__lte=fecha_fin
            ).exclude(pk=self.instance.pk if self.instance else None)  # Excluir el arriendo actual si se está editando

            if arriendos_existentes.exists():
                self.add_error(None, forms.ValidationError("La bicicleta no está disponible en el rango de fechas seleccionado."))

            # Validar fechas no disponibles en la base de datos
            fechas_no_disponibles = bicicleta.fechas_disponibles()
            if fechas_no_disponibles is not None:
                if fecha_inicio in fechas_no_disponibles or fecha_fin in fechas_no_disponibles:
                    raise forms.ValidationError({
                        'fecha_inicio': _("La fecha de inicio seleccionada no está disponible."),
                        'fecha_fin': _("La fecha de fin seleccionada no está disponible.")
                    })

            if fecha_inicio.weekday() >= 5 or fecha_fin.weekday() >= 5:
                raise forms.ValidationError(_("Las fechas de inicio y fin deben ser días hábiles (de lunes a viernes)."))

        return cleaned_data
    
class BicicletaForm(forms.ModelForm):
    class Meta:
        model = Bicicleta
        fields = ['marca', 'modelo', 'año', 'precio_por_dia', 'disponible']
        widgets = {
            'marca': forms.Select(attrs={'class': 'form-control'}),
            'modelo': forms.TextInput(attrs={'class': 'form-control'}),
            'año': forms.NumberInput(attrs={'class': 'form-control'}),
            'precio_por_dia': forms.NumberInput(attrs={'class': 'form-control'}),
            'disponible': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }