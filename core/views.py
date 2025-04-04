from datetime import date
from .zpoblar import poblar_bd
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.models import User
from django.contrib.auth.forms import PasswordChangeForm
from django.urls import reverse
from django.utils.safestring import SafeString
from django.contrib.auth.decorators import login_required, user_passes_test
from .models import Producto, Boleta, Carrito, DetalleBoleta, Bodega, Perfil, Mantenimiento
from .models import Bicicleta, Arriendo
from .forms import ProductoForm, BodegaForm, IngresarForm, UsuarioForm, PerfilForm, ArriendoForm
from .forms import RegistroUsuarioForm, RegistroPerfilForm, MantenimientoForm, BicicletaForm
from .templatetags.custom_filters import formatear_dinero, formatear_numero
from .tools import eliminar_registro, verificar_eliminar_registro, show_form_errors
from django.core.mail import send_mail
from django.utils import timezone
from datetime import timedelta, time, datetime, date
from django.http import JsonResponse, HttpResponseRedirect
from django.views.decorators.http import require_GET
from django.urls import reverse
from django.utils.timezone import now
from django.template import loader
from core.templatetags.custom_filters import add_class
from django.views.decorators.http import require_GET, require_POST
# from transbank.sdk.webpay.webpay_plus.transaction import Transaction
# from transbank.sdk.webpay.webpay_plus.options import WebpayOptions
# from transbank.sdk import Transaction, WebpayOptions
from django.conf import settings

# *********************************************************************************************************#
#                                                                                                          #
# INSTRUCCIONES PARA EL ALUMNO, PUEDES SEGUIR EL VIDEO TUTORIAL, COMPLETAR EL CODIGO E INCORPORAR EL TUYO: #
#                                                                                                          #
# https://drive.google.com/drive/folders/1ObwMnpKmCXVbq3SMwJKlSRE0PCn0buk8?usp=drive_link                  #
#                                                                                                          #
# *********************************************************************************************************#

# Se usará el decorador "@user_passes_test" para realizar la autorización básica a las páginas.
# De este modo sólo entrarán a las páginas las personas que sean del tipo_usuario permitido.
# Si un usuario no autorizado intenta entrar a la página, será redirigido al inicio o a ingreso

# Revisar si el usuario es personal de la empresa (staff administrador o superusuario) autenticado y con cuenta activa
def es_personal_autenticado_y_activo(user):
    return (user.is_staff or user.is_superuser) and user.is_authenticated and user.is_active

# Revisar si el usuario no está autenticado, es decir, si aún está navegando como usuario anónimo
def es_usuario_anonimo(user):
    return user.is_anonymous

# Revisar si el usuario es un cliente (no es personal de la empresa) autenticado y con cuenta activa
def es_cliente_autenticado_y_activo(user):
    return (not user.is_staff and not user.is_superuser) and user.is_authenticated and user.is_active

def inicio(request):

    if request.method == 'POST':
        # Si la vista fue invocada con un POST es porque el usuario presionó el botón "Buscar" en la página principal.
        # Por lo anterior, se va a recuperar palabra clave del formulario que es el campo "buscar" (id="buscar"), 
        # que se encuentra en la página Base.html. El formulario de búsqueda se encuentra bajo el comentario 
        # "FORMULARIO DE BUSQUEDA" en la página Base.html.
        buscar = request.POST.get('buscar')

        # Se filtrarán todos los productos que contengan la palabra clave en el campo nombre
        registros = Producto.objects.filter(nombre__icontains=buscar).order_by('nombre')
    
    if request.method == 'GET':
        # Si la vista fue invocada con un GET, se devolverán todos los productos a la PAGINA
        registros = Producto.objects.all().order_by('nombre')

    # Como los productos tienen varios cálculos de descuentos por ofertas y subscripción, estos se realizarán
    # en una función a parte llamada "obtener_info_producto", mediante la cuál se devolverán las filas de los
    # productos, pero con campos nuevos donde los cálculos ya han sido realizados.
    productos = []
    for registro in registros:
        productos.append(obtener_info_producto(registro.id))

    context = { 'productos': productos }
    
    return render(request, 'core/inicio.html', context)

def ficha(request, producto_id):
    context = obtener_info_producto(producto_id)
    return render(request, 'core/ficha.html', context)

def nosotros(request):
    # CREAR: renderización de página
    return render(request, 'core/nosotros.html')

def administrar_tienda(request):
    # CREAR: renderización de página
    return render(request, 'core/administrar_tienda.html')

def api_ropa(request):
    return render(request, 'core/api_ropa.html')

@user_passes_test(es_usuario_anonimo, login_url='inicio')
def ingresar(request):

    if request.method == "POST":
        form = IngresarForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data['username']
            password = form.cleaned_data['password']
            user = authenticate(username=username, password=password)
            if user is not None:
                if user.is_active:
                    login(request, user)
                    messages.success(request, f'¡Bienvenido(a) {user.first_name} {user.last_name}!')
                    return redirect(inicio)
                else:
                    messages.error(request, 'La cuenta está desactivada.')
            else:
                messages.error(request, 'La cuenta o la password no son correctos')
        else:
            messages.error(request, 'No se pudo ingresar al sistema')
            show_form_errors(request, [form])

    if request.method == "GET":

        form = IngresarForm()

    context = {
        'form':  IngresarForm(),
        'perfiles': Perfil.objects.all().order_by('tipo_usuario', 'subscrito'),
    }

    return render(request, "core/ingresar.html", context)

@login_required
def salir(request):
    nombre = request.user.first_name
    apellido = request.user.last_name
    messages.success(request, f'¡Hasta pronto {nombre} {apellido}!')
    logout(request)
    return redirect(inicio)

@user_passes_test(es_usuario_anonimo)
def registro(request):
    
    if request.method == 'POST':
        
        form_usuario = RegistroUsuarioForm(request.POST)
        form_perfil = RegistroPerfilForm(request.POST, request.FILES)
        
        if form_usuario.is_valid() and form_perfil.is_valid():
            usuario = form_usuario.save(commit=False)
            usuario.is_staff = False
            perfil = form_perfil.save(commit=False)
            usuario.save()
            perfil.usuario_id = usuario.id
            perfil.tipo_usuario = 'Cliente'
            perfil.save()
            # premium = ' y aprovecha tus descuentos especiales como cliente PREMIUN' if perfil.es
            mensaje = f'Tu cuenta usuario: "{usuario.username}" ha sido creada con éxito. ¡Ya'
            messages.success(request, mensaje)
            return redirect(ingresar)
        else:
            messages.error(request, f'Error al crear la cuenta. Verifique los datos ingresados')
            show_form_errors(request, [form_usuario, form_perfil])
    
    if request.method == 'GET':
        
        form_usuario = RegistroUsuarioForm()
        form_perfil = RegistroPerfilForm()
        # CREAR: un formulario RegistroUsuarioForm vacío
        # CREAR: un formulario RegistroPerfilForm vacío
    # CREAR: variable de contexto para enviar formulario de usuario y perfil
    context = {
        'form_usuario': form_usuario,
        'form_perfil': form_perfil,
    }

    return render(request, 'core/registro.html', context)

@login_required
def misdatos(request):

    if request.method == 'POST':
        
        form_usuario = UsuarioForm(request.POST, instance=request.user)
        form_perfil = RegistroPerfilForm(request.POST, request.FILES, instance=request.user.perfil)
        
        if form_usuario.is_valid() and form_perfil.is_valid():
            usuario = form_usuario.save(commit=False)
            perfil = form_perfil.save(commit=False)
            usuario.save()
            perfil.usuario_id = usuario.id
            perfil.save()
            if perfil.tipo_usuario in ['Administrador', 'Superusuario']:
                tipo_cuenta = perfil.tipo_usuario
            else:
                tipo_cuenta = 'CLIENTE PREMIUM' if perfil.subscrito else 'cliente'
            messages.success(request, f'Tu cuenta de {tipo_cuenta} ha sido actualizada con exito')
            return redirect(misdatos)
        else:
            messages.error(request, f'No fue posible guardar tus datos.')
            show_form_errors(request, [form_usuario, form_perfil])
        # CREAR: un formulario UsuarioForm para recuperar datos del formulario asociados al usuario actual
        # CREAR: un formulario RegistroPerfilForm para recuperar datos del formulario asociados al perfil del usuario actual
        # CREAR: lógica para actualizar los datos del usuario
    if request.method == 'GET':

        form_usuario = UsuarioForm(instance=request.user)
        form_perfil = RegistroPerfilForm(instance=request.user.perfil)
        # CREAR: un formulario UsuarioForm con los datos del usuario actual
        # CREAR: un formulario RegistroPerfilForm con los datos del usuario actual
    # CREAR: variable de contexto para enviar formulario de usuario y perfil
    context = {
        'form_usuario': form_usuario,
        'form_perfil': form_perfil,
    }

    return render(request, 'core/misdatos.html', context)

@login_required
def boleta(request, nro_boleta):

    boleta = None
    detalle_boleta = None

    if Boleta.objects.filter(nro_boleta=nro_boleta).exists():
        boleta = Boleta.objects.get(nro_boleta=nro_boleta)
        boleta_es_del_usuario = Boleta.objects.filter(nro_boleta=nro_boleta, cliente=request.user.perfil).exists()
        if boleta_es_del_usuario or request.user.is_staff:
            detalle_boleta = DetalleBoleta.objects.filter(boleta=boleta)
        else:
            messages.error(request, f'Lo siento la boleta N° {nro_boleta} pertenece a {boleta.cliente}')
            boleta = None
    else:
        messages.error(request, f'La boleta N° {nro_boleta} no existe en la base de datos.')
    # CREAR: lógica para ver la boleta
    
    # CREAR: variable de contexto para enviar boleta y detalle de la boleta
    context = { 
        'boleta': boleta,
        'detalle_boleta': detalle_boleta
    }

    return render(request, 'core/boleta.html', context)

@user_passes_test(es_personal_autenticado_y_activo)
def ventas(request):
    
    boletas = Boleta.objects.all()
    historial =[]
    for boleta in boletas:
        boleta_historial = {
            'nro_boleta': boleta.nro_boleta,
            'nom_cliente': f'{boleta.cliente.usuario.first_name} {boleta.cliente.usuario.last_name}',
            'fecha_venta': boleta.fecha_venta,
            'fecha_despacho': boleta.fecha_despacho,
            'fecha_entrega': boleta.fecha_entrega,
            'subscrito': 'Sí' if boleta.cliente.subscrito else 'No',
            'total_a_pagar': boleta.total_a_pagar,
            'estado': boleta.estado,
        }
        historial.append(boleta_historial)
    # CREAR: lógica para ver las ventas

    # CREAR: variable de contexto para enviar historial de ventas
    context = {
        'historial': historial
     }

    return render(request, 'core/ventas.html', context)

@user_passes_test(es_personal_autenticado_y_activo)
def productos(request, accion, id):
    
    if request.method == 'POST':
        
        if accion == 'crear':
            form = ProductoForm(request.POST, request.FILES)
            
        elif accion == 'actualizar':
            form = ProductoForm(request.POST, request.FILES, instance=Producto.objects.get(id=id))
            
        if form.is_valid():
            
            producto = form.save()
            ProductoForm(instance=producto)
            messages.success(request, f'El producto "{str(producto)}" se logró {accion} correctamente')
            return redirect(productos, 'actualizar', producto.id)
        else:
            show_form_errors(request, [form])

    if request.method == 'GET':

        if accion == 'crear':
            form = ProductoForm()
            
        elif accion == 'actualizar':
            form = ProductoForm(instance=Producto.objects.get(id=id))
            
        elif accion == 'eliminar':
            eliminado, mensaje = eliminar_registro(Producto, id)
            messages.error(request, mensaje)
            if eliminado:
                return redirect(productos, 'crear', '0')
            form = ProductoForm(instance=Producto.objects.get(id=id))
    
    context ={
        'form': form,
        'productos': Producto.objects.all()
    }
    
    return render(request, 'core/productos.html', context)

@require_GET
def horas_disponibles(request):
    fecha_seleccionada = request.GET.get('fecha')
    if fecha_seleccionada:
        fecha = datetime.strptime(fecha_seleccionada, '%Y-%m-%d').date()
        mantenimientos_ocupados = Mantenimiento.objects.filter(fecha_programada=fecha).values_list('hora_programada', flat=True)
        
        horas_disponibles = []
        hora = time(8, 0)  # Hora inicial disponible
        hora_fin = time(19, 0)  # Hora final disponible
        while hora <= hora_fin:
            hora_str = hora.strftime('%H:%M')
            if hora not in mantenimientos_ocupados:
                horas_disponibles.append(hora_str)
            hora = (datetime.combine(datetime.today(), hora) + timedelta(hours=1)).time()

        return JsonResponse(horas_disponibles, safe=False)
    else:
        return JsonResponse([], safe=False)

@login_required
def agendar_mantenimiento(request):
    if request.method == 'POST':
        form = MantenimientoForm(request.POST)
        if form.is_valid():
            mantenimiento = form.save(commit=False)
            mantenimiento.cliente = request.user.perfil  # Asignar el perfil del usuario

            # Validar que la hora esté en intervalos de una hora exacta
            hora_programada = mantenimiento.hora_programada
            if hora_programada.minute != 0 or hora_programada.second != 0:
                messages.error(request, 'La hora del mantenimiento debe estar en intervalos de una hora exacta.')
                return render(request, 'core/agendar_mantenimiento.html', {'form': form, 'reservas': Mantenimiento.objects.filter(cliente=request.user.perfil)})

            # Verificar si ya existe un mantenimiento en la misma fecha y hora
            fecha_programada = mantenimiento.fecha_programada
            if Mantenimiento.objects.filter(fecha_programada=fecha_programada, hora_programada=hora_programada).exists():
                messages.error(request, 'Ya existe un mantenimiento programado para esa fecha y hora.')
                return render(request, 'core/agendar_mantenimiento.html', {'form': form, 'reservas': Mantenimiento.objects.filter(cliente=request.user.perfil)})

            # Validar que no se pueda agendar en días pasados
            if fecha_programada < timezone.now().date():
                messages.error(request, 'No se pueden agendar mantenimientos a días anteriores a la fecha actual.')
                return render(request, 'core/agendar_mantenimiento.html', {'form': form, 'reservas': Mantenimiento.objects.filter(cliente=request.user.perfil)})

            mantenimiento.save()
            messages.success(request, 'Mantenimiento agendado correctamente.')
            return redirect('agendar_mantenimiento')
        else:
            messages.error(request, 'Por favor corrige los errores a continuación.')
    else:
        form = MantenimientoForm()

    # Obtener mantenimientos disponibles de lunes a viernes de 08:00 a 19:00
    today = timezone.now().date()
    start_of_next_week = today + timedelta(days=(7 - today.weekday()))
    end_of_next_week = start_of_next_week + timedelta(days=7)

    # Horas de inicio y fin para el filtro
    hora_inicio = time(hour=8, minute=0)
    hora_fin = time(hour=19, minute=0)

    mantenimientos_ocupados = Mantenimiento.objects.filter(
        fecha_programada__gte=start_of_next_week,
        fecha_programada__lt=end_of_next_week,
        hora_programada__gte=hora_inicio,
        hora_programada__lte=hora_fin
    ).values_list('fecha_programada', 'hora_programada')

    dias_horas_ocupadas = [(fecha_programada, hora_programada.strftime('%H:%M')) for fecha_programada, hora_programada in mantenimientos_ocupados]

    # Obtener las reservas del cliente actual
    reservas = Mantenimiento.objects.filter(cliente=request.user.perfil)

    context = {
        'form': form,
        'start_of_next_week': start_of_next_week,
        'end_of_next_week': end_of_next_week,
        'dias_horas_ocupadas': dias_horas_ocupadas,
        'reservas': reservas,  # Pasar solo las reservas del cliente actual
    }
    return render(request, 'core/agendar_mantenimiento.html', context)



@login_required
def cancelar_reserva(request, reserva_id):
    reserva = get_object_or_404(Mantenimiento, id=reserva_id, cliente=request.user.perfil)

    if request.method == 'POST':
        reserva.delete()
        messages.success(request, 'Reserva cancelada correctamente.')
        return HttpResponseRedirect(reverse('agendar_mantenimiento'))

    return HttpResponseRedirect(reverse('agendar_mantenimiento'))

@user_passes_test(es_personal_autenticado_y_activo)
def lista_mantenimientos(request):
    mantenimientos = Mantenimiento.objects.all()
    context = {
        'mantenimientos': mantenimientos
    }
    return render(request, 'core/lista_mantenimientos.html', context)

@user_passes_test(es_personal_autenticado_y_activo)
def eliminar_mantenimiento(request, mantenimiento_id):
    mantenimiento = get_object_or_404(Mantenimiento, id=mantenimiento_id)
    if request.method == 'POST':
        mantenimiento.delete()
        return redirect('lista_mantenimientos')
    context = {
        'mantenimiento': mantenimiento
    }
    return render(request, 'core/eliminar_mantenimiento.html', context)

@user_passes_test(es_personal_autenticado_y_activo)
def mantenedor_usuarios(request, accion, id):
    
    usuario = User.objects.get(id=id) if int(id) > 0 else None
    perfil = usuario.perfil if usuario else None
    # CREAR: variables de usuario y perfil
    if request.method == 'POST':
        
        form_usuario = UsuarioForm(request.POST, instance=usuario)
        
        form_perfil = PerfilForm(request.POST, request.FILES, instance=perfil)
        
        if form_usuario.is_valid() and form_perfil.is_valid():
            usuario = form_usuario.save(commit=False)
            tipo_usuario = form_perfil.cleaned_data['tipo_usuario']
            usuario.is_staff = tipo_usuario in ['Administrador', 'Superusuario']
            perfil = form_perfil.save(commit=False)
            usuario.save()
            perfil.usuario_id = usuario.id
            perfil.save()
            messages.success(request, f'El usuario {usuario.first_name} {usuario.last_name} fue guardado.')
            return redirect(mantenedor_usuarios, 'actualizar', usuario.id)
        else:
            messages.error(request, f'No fue posible guardar el nuevo usuario.')
            show_form_errors(request,[form_usuario, form_perfil])
        # CREAR: un formulario UsuarioForm para recuperar datos del formulario asociados al usuario
        # CREAR: un formulario PerfilForm para recuperar datos del formulario asociados al perfil del usuario
        # CREAR: lógica para actualizar los datos del usuario
    if request.method == 'GET':

        if accion == 'eliminar':
            eliminado, mensaje = eliminar_registro(User, id)
            messages.success(request, mensaje)
            return redirect(mantenedor_usuarios, 'crear', '0')
        else:
            form_usuario = UsuarioForm(instance=usuario)
            form_perfil = PerfilForm(instance=perfil)
            # CREAR: acción de eliminar un usuario            
            # CREAR: un formulario UsuarioForm asociado al usuario
            # CREAR: un formulario PerfilForm asociado al perfil del usuario


    # CREAR: variable de contexto para enviar el formulario de usuario, formulario de perfil y todos los usuarios
    context = {
        'form_usuario': form_usuario,
        'form_perfil': form_perfil,
        'usuarios': User.objects.all(),
     }

    return render(request, 'core/mantenedor_usuarios.html', context)

@user_passes_test(es_personal_autenticado_y_activo)
def bodega(request):

    if request.method == 'POST':

        producto_id = request.POST.get('producto')
        producto = Producto.objects.get(id=producto_id)
        cantidad = int(request.POST.get('cantidad'))
        for cantidad in range(1, cantidad + 1):
            Bodega.objects.create(producto=producto)
        if cantidad == 1:
            messages.success(request, f'Se ha agregado 1 nuevo "{producto.nombre}" a la bodega')
        else:
            messages.success(request, f'Se han agregado {cantidad} productos de "{producto.nombre}" a la bodega')

    registros = Bodega.objects.all()
    lista = []
    for registro in registros:
        vendido = DetalleBoleta.objects.filter(bodega=registro).exists()
        item = {
            'bodega_id': registro.id,
            'nombre_categoria': registro.producto.categoria.nombre,
            'nombre_producto': registro.producto.nombre,
            'estado': 'Vendido' if vendido else 'En bodega',
            'imagen': registro.producto.imagen,
        }
        lista.append(item)

    context = {
        'form': BodegaForm(),
        'productos': lista,
    }
    
    return render(request, 'core/bodega.html', context)


@user_passes_test(es_personal_autenticado_y_activo)
def obtener_productos(request):
    # La vista obtener_productos la usa la pagina "Administracion de bodega", para
    # filtrar el combobox de productos cuando el usuario selecciona una categoria
    
    categoria_id = request.GET.get('categoria_id')
    productos = Producto.objects.filter(categoria_id=categoria_id)
    # CREAR: Un JSON para devolver los productos que corresponden a la categoria

    data = [
        {
            'id': producto.id,
            'nombre': producto.nombre,
            'imagen': producto.imagen.url
        } for producto in productos
    ]
    return JsonResponse(data, safe=False)

@user_passes_test(es_personal_autenticado_y_activo)
def eliminar_producto_en_bodega(request, bodega_id):
    # La vista eliminar_producto_en_bodega la usa la pagina "Administracion de bodega", 
    # para eliminar productos que el usuario decidio sacar del inventario
    nombre_producto = Bodega.objects.get(id=bodega_id).producto.nombre
    eliminado, error = verificar_eliminar_registro(Bodega, bodega_id, True)
    # CREAR: lógica para eliminar un producto de la bodega
    if eliminado:
        messages.success(request, f'Se ha eliminado el ID {bodega_id} ({nombre_producto}) de la bodega')
    else:
        messages.error(request, error)
        
    return redirect(bodega)

@user_passes_test(es_cliente_autenticado_y_activo)
def miscompras(request):

    boletas = Boleta.objects.filter(cliente=request.user.perfil)
    historial = []
    for boleta in boletas:
        boleta_historial = {
            'nro_boleta': boleta.nro_boleta,
            'fecha_venta': boleta.fecha_venta,
            'fecha_despacho': boleta.fecha_despacho,
            'fecha_entrega': boleta.fecha_entrega,
            'total_a_pagar': boleta.total_a_pagar,
            'estado': boleta.estado,
        }
        historial.append(boleta_historial)
    # CREAR: lógica para ver las compras del cliente

    # CREAR: variable de contexto para enviar el historial de compras del cliente
    context = { 
        'historial': historial
    }

    return render(request, 'core/miscompras.html', context)


# ***********************************************************************
# FUNCIONES Y VISTAS AUXILIARES QUE SE ENTREGAN PROGRAMADAS AL ALUMNO
# ***********************************************************************

# VISTA PARA CAMBIAR ESTADO DE LA BOLETA

@user_passes_test(es_personal_autenticado_y_activo)
def cambiar_estado_boleta(request, nro_boleta, estado):
    boleta = Boleta.objects.get(nro_boleta=nro_boleta)
    if estado == 'Anulado':
        # Anular boleta, dejando la fecha de anulación como hoy y limpiando las otras fechas
        boleta.fecha_venta = date.today()
        boleta.fecha_despacho = None
        boleta.fecha_entrega = None
    elif estado == 'Vendido':
        # Devolver la boleta al estado recien vendida al dia de hoy, y sin despacho ni entrega
        boleta.fecha_venta = date.today()
        boleta.fecha_despacho = None
        boleta.fecha_entrega = None
    elif estado == 'Despachado':
        # Cambiar boleta a estado despachado, se conserva la fecha de venta y se limpia la fecha de entrega
        boleta.fecha_despacho = date.today()
        boleta.fecha_entrega = None
    elif estado == 'Entregado':
        # Cambiar boleta a estado entregado, pero hay que ver que estado actual tiene la boleta
        if boleta.estado == 'Vendido':
            # La boleta esta emitida, pero sin despacho ni entrega, entonces despachamos y entregamos hoy
            boleta.fecha_despacho = date.today()
            boleta.fecha_entrega = date.today()
        elif boleta.estado == 'Despachado':
            # La boleta esta despachada, entonces entregamos hoy
            boleta.fecha_entrega = date.today()
        elif boleta.estado == 'Entregado':
            # La boleta esta entregada, pero si se trata de un error entonces entregamos hoy
            boleta.fecha_entrega = date.today()
    boleta.estado = estado
    boleta.save()
    return redirect(ventas)

# FUNCIONES AUXILIARES PARA OBTENER: INFORMACION DE PRODUCTOS, CALCULOS DE PRECIOS Y OFERTAS

def obtener_info_producto(producto_id):

    # Obtener el producto con el id indicado en "producto_id"
    producto = Producto.objects.get(id=producto_id)

    # Se verificará cuántos productos hay en la bodega que tengan el id indicado en "producto_id".
    # Para lograrlo se filtrarán en primer lugar los productos con el id indicado. Luego, se 
    # realizará un JOIN con la tabla de "DetalleBoleta" que es donde se indican los productos
    # que se han vendido desde la bodega, sin olvidar que los modelos funcionan con Orientación
    # a Objetos, lo que hace que las consultas sean un poco diferentes a las de SQL. 
    # DetalleBoleta está relacionada con la tabla Bodega por medio de su propiedad "bodega",
    # la cual internamente agrega en la tabla DetalleBoleta el campo "bodega_id", que permite
    # que se relacione con la tabla Bodega. Para calcular cuántos productos quedan en la Bodega
    # se debe excluir aquellos que ya fueron vendidos, lo que se logra con la condición
    # "detalleboleta__isnull=False", es decir, se seleccionarán aquellos registros de Bodega
    # cuya relación con la tabla de DetalleBoleta esté en NULL, osea los que no han sido vendidos.
    # Si un producto de la Bodega estuviera vendido, entonces tendría su relación "detalleboleta"
    # con un valor diferente de NULL, ya que el campo "bodega_id" de la tabla DetalleBoleta
    # tendría el valor del id de Bodega del producto que se vendió.
    stock = Bodega.objects.filter(producto_id=producto_id).exclude(detalleboleta__isnull=False).count()
    
    # Preparar texto para mostrar estado: en oferta, sin oferta y agotado
    con_oferta = f'<span class="text-primary"> EN OFERTA {producto.descuento_oferta}% DE DESCUENTO </span>'
    sin_oferta = '<span class="text-success"> DISPONIBLE EN BODEGA </span>'
    agotado = '<span class="text-danger"> AGOTADO </span>'

    if stock == 0:
        estado = agotado
    else:
        estado = sin_oferta if producto.descuento_oferta == 0 else con_oferta

    # Preparar texto para indicar cantidad de productos en stock
    en_stock = f'En stock: {formatear_numero(stock)} {"unidad" if stock == 1 else "unidades"}'
   
    return {
        'id': producto.id,
        'nombre': producto.nombre,
        'descripcion': producto.descripcion,
        'imagen': producto.imagen,
        'html_estado': estado,
        'html_precio': obtener_html_precios_producto(producto),
        'html_stock': en_stock,
    }

def obtener_html_precios_producto(producto):
    
    precio_normal, precio_oferta, precio_subscr, hay_desc_oferta, hay_desc_subscr = calcular_precios_producto(producto)
    
    normal = f'Precio: {formatear_dinero(precio_normal)}'
    tachar = f'Precio: <span class="text-decoration-line-through"> {formatear_dinero(precio_normal)} </span>'
    oferta = f'Oferta: <span class="text-success"> {formatear_dinero(precio_oferta)} </span>'
    subscr = f'Subscrito: <span class="text-danger"> {formatear_dinero(precio_subscr)} </span>'

    if hay_desc_oferta > 0:
        texto_precio = f'{tachar}<br>{oferta}'
    else:
        texto_precio = normal

    if hay_desc_subscr > 0:
        texto_precio += f'<br>{subscr}'

    return texto_precio

def calcular_precios_producto(producto):
    precio_normal = producto.precio
    precio_oferta = producto.precio * (100 - producto.descuento_oferta) / 100
    precio_subscr = producto.precio * (100 - (producto.descuento_oferta + producto.descuento_subscriptor)) / 100
    hay_desc_oferta = producto.descuento_oferta > 0
    hay_desc_subscr = producto.descuento_subscriptor > 0
    return precio_normal, precio_oferta, precio_subscr, hay_desc_oferta, hay_desc_subscr

# VISTAS y FUNCIONES DE COMPRAS

def comprar_ahora(request):
    messages.error(request, f'El pago aún no ha sido implementado.')
    return redirect(inicio)

@user_passes_test(es_cliente_autenticado_y_activo)
def carrito(request):

    detalle_carrito = Carrito.objects.filter(cliente=request.user.perfil)

    total_a_pagar = 0
    for item in detalle_carrito:
        total_a_pagar += item.precio_a_pagar
    monto_sin_iva = int(round(total_a_pagar / 1.19))
    iva = total_a_pagar - monto_sin_iva

    context = {
        'detalle_carrito': detalle_carrito,
        'monto_sin_iva': monto_sin_iva,
        'iva': iva,
        'total_a_pagar': total_a_pagar,
    }

    return render(request, 'core/carrito.html', context)

def agregar_producto_al_carrito(request, producto_id):

    if es_personal_autenticado_y_activo(request.user):
        messages.error(request, f'Para poder comprar debes tener cuenta de Cliente, pero tu cuenta es de {request.user.perfil.tipo_usuario}.')
        return redirect(inicio)
    elif es_usuario_anonimo(request.user):
        messages.info(request, 'Para poder comprar, primero debes registrarte como cliente.')
        return redirect(registro)

    perfil = request.user.perfil
    producto = Producto.objects.get(id=producto_id)

    precio_normal, precio_oferta, precio_subscr, hay_desc_oferta, hay_desc_subscr = calcular_precios_producto(producto)

    precio = producto.precio
    descuento_subscriptor = producto.descuento_subscriptor if perfil.subscrito else 0
    descuento_total=producto.descuento_subscriptor + producto.descuento_oferta if perfil.subscrito else producto.descuento_oferta
    precio_a_pagar = precio_subscr if perfil.subscrito else precio_oferta
    descuentos = precio - precio_subscr if perfil.subscrito else precio - precio_oferta

    Carrito.objects.create(
        cliente=perfil,
        producto=producto,
        precio=precio,
        descuento_subscriptor=descuento_subscriptor,
        descuento_oferta=producto.descuento_oferta,
        descuento_total=descuento_total,
        descuentos=descuentos,
        precio_a_pagar=precio_a_pagar
    )

    return redirect(ficha, producto_id)

@user_passes_test(es_cliente_autenticado_y_activo)
def eliminar_producto_en_carrito(request, carrito_id):
    Carrito.objects.get(id=carrito_id).delete()
    return redirect(carrito)

@user_passes_test(es_cliente_autenticado_y_activo)
def vaciar_carrito(request):
    productos_carrito = Carrito.objects.filter(cliente=request.user.perfil)
    if productos_carrito.exists():
        productos_carrito.delete()
        messages.info(request, 'Se ha cancelado la compra, el carrito se encuentra vacío.')
    return redirect(carrito)

# CAMBIO DE PASSWORD Y ENVIO DE PASSWORD PROVISORIA POR CORREO

@login_required
def contraseña(request):

    if request.method == 'POST':

        form = PasswordChangeForm(user=request.user, data=request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Tu contraseña ha sido actualizada con éxito, ingresa de nuevo con tu nueva contraseña.')
            return redirect(ingresar)
        else:
            messages.error(request, 'Tu contraseña no pudo ser actualizada.')
            show_form_errors(request, [form])
    
    if request.method == 'GET':

        form = PasswordChangeForm(user=request.user)

    context = {
        'form': form
    }

    return render(request, 'core/contraseña.html', context)

@user_passes_test(es_personal_autenticado_y_activo)
def cambiar_password(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        existe = User.objects.filter(username=username).exists()
        if existe:
            user = User.objects.get(username=username)
            if user is not None:
                if user.is_active:
                    password = User.objects.make_random_password()
                    user.set_password(password)
                    user.save()
                    enviado = enviar_correo_cambio_password(request, user, password)
                    if enviado:
                        messages.success(request, f'Una nueva contraseña fue enviada al usuario {user.first_name} {user.last_name}')
                    else:
                        messages.error(request, f'No fue posible enviar la contraseña al usuario {user.first_name} {user.last_name}, intente nuevamente más tarde')
                else:
                    messages.error(request, 'La cuenta está desactivada.')
            else:
                messages.error(request, 'La cuenta o la password no son correctos')
        else:
            messages.error(request, 'El usuario al que quiere generar una nueva contraseña ya no existe en el sistema')
    return redirect(mantenedor_usuarios, 'crear', '0')

def enviar_correo_cambio_password(request, user, password):
    try:
        # Revisar "CONFIGURACIÓN PARA ENVIAR CORREOS ELECTRÓNICOS A TRAVÉS DEL SERVIDOR DE GMAIL" en settings.py 
        subject = 'Cambio de contraseña Sword Games Shop'
        url_ingresar = request.build_absolute_uri(reverse(ingresar))
        message = render(request, 'common/formato_correo.html', {
            'first_name': user.first_name,
            'last_name': user.last_name,
            'user_password': password,
            'link_to_login': url_ingresar,
        })
        from_email = 'info@faithfulpet.com'  # La dirección de correo que aparecerá como remitente
        recipient_list = []
        recipient_list.append(user.email)
        # Enviar el correo
        send_mail(subject=subject, message='', from_email=from_email, recipient_list=recipient_list
            , html_message=message.content.decode('utf-8'))
        return True
    except:
        return False

# POBLAR BASE DE DATOS CON REGISTROS DE PRUEBA

def poblar(request):
    # Permite poblar la base de datos con valores de prueba en todas sus tablas.
    # Opcionalmente se le puede enviar un correo único, para que los Administradores
    # del sistema puedan probar el cambio de password de los usuarios, en la página
    # de "Adminstración de usuarios".
    poblar_bd('vi.barrientosr@duocuc.cl')
    return redirect(inicio)


@login_required
def arrendar_bicicleta(request):
    if request.method == 'POST':
        form = ArriendoForm(request.POST)
        if form.is_valid():
            arriendo = form.save(commit=False)
            arriendo.cliente = request.user.perfil  # Asignar el perfil del usuario
            arriendo.save()
            messages.success(request, 'Bicicleta arrendada correctamente.')
            return redirect('arrendar_bicicleta')
        else:
            messages.error(request, 'Por favor corrige los errores a continuación.')
    else:
        form = ArriendoForm()

    # Reiniciar el queryset de fecha_inicio basado en la bicicleta seleccionada
    bicicleta_id = request.POST.get('bicicleta') if request.method == 'POST' else None
    if bicicleta_id:
        try:
            bicicleta = Bicicleta.objects.get(id=int(bicicleta_id))
            form.fields['fecha_inicio'].queryset = bicicleta.fechas_disponibles()
        except (ValueError, TypeError, Bicicleta.DoesNotExist):
            form.fields['fecha_inicio'].queryset = Bicicleta.objects.none()
    else:
        form.fields['fecha_inicio'].queryset = Bicicleta.objects.none()

    # Obtener los arriendos del cliente actual
    perfil_usuario = request.user.perfil
    arriendos = Arriendo.objects.filter(cliente=perfil_usuario)

    context = {
        'form': form,
        'arriendos': arriendos,
    }
    return render(request, 'core/arrendar_bicicleta.html', context)

@require_POST
def cancelar_arriendo(request, arriendo_id):
    arriendo = get_object_or_404(Arriendo, id=arriendo_id, cliente=request.user.perfil)
    arriendo.delete()
    messages.success(request, 'Arriendo cancelado correctamente.')
    return redirect('arrendar_bicicleta')

@require_GET
def calcular_precio_arriendo(request):
    bicicleta_id = request.GET.get('bicicleta_id')
    fecha_inicio = request.GET.get('fecha_inicio')
    fecha_fin = request.GET.get('fecha_fin')

    try:
        bicicleta = Bicicleta.objects.get(id=bicicleta_id)
        fecha_inicio = datetime.strptime(fecha_inicio, '%Y-%m-%d').date()
        fecha_fin = datetime.strptime(fecha_fin, '%Y-%m-%d').date()
        dias_arriendo = (fecha_fin - fecha_inicio).days + 1
        precio_total = dias_arriendo * bicicleta.precio_por_dia
        return JsonResponse({'precio_total': precio_total})
    except (Bicicleta.DoesNotExist, ValueError):
        return JsonResponse({'error': 'Datos inválidos'}, status=400)

@require_GET
def fechas_no_disponibles(request):
    bicicleta_id = request.GET.get('bicicleta_id')
    if bicicleta_id:
        try:
            bicicleta = Bicicleta.objects.get(id=bicicleta_id)
        except Bicicleta.DoesNotExist:
            return JsonResponse({'error': 'Bicicleta no encontrada'}, status=400)

        arriendos = Arriendo.objects.filter(bicicleta=bicicleta)
        fechas_no_disponibles = []

        for arriendo in arriendos:
            rango_fechas = [arriendo.fecha_inicio + timedelta(days=i) for i in range((arriendo.fecha_fin - arriendo.fecha_inicio).days + 1)]
            fechas_no_disponibles.extend(rango_fechas)

        fechas_no_disponibles = list(set(fechas_no_disponibles))  # Eliminar fechas duplicadas
        fechas_no_disponibles = [fecha.strftime('%Y-%m-%d') for fecha in fechas_no_disponibles]  # Formato ISO YYYY-MM-DD

        return JsonResponse({'fechas_no_disponibles': fechas_no_disponibles})

    return JsonResponse({'error': 'Bicicleta no especificada'}, status=400)

@user_passes_test(es_personal_autenticado_y_activo)
def mantenedor_bicicletas(request):
    bicicletas = Bicicleta.objects.all()
    form = BicicletaForm()

    if 'edit_id' in request.GET:
        bicicleta = get_object_or_404(Bicicleta, id=request.GET.get('edit_id'))
        form = BicicletaForm(instance=bicicleta)

    if request.method == 'POST':
        if 'delete_id' in request.POST:
            bicicleta = get_object_or_404(Bicicleta, id=request.POST.get('delete_id'))
            bicicleta.delete()
            return redirect('mantenedor_bicicletas')
        else:
            edit_id = request.POST.get('edit_id')
            if edit_id:
                bicicleta = get_object_or_404(Bicicleta, id=edit_id)
                form = BicicletaForm(request.POST, instance=bicicleta)
            else:
                form = BicicletaForm(request.POST)

            if form.is_valid():
                form.save()
                return redirect('mantenedor_bicicletas')

    return render(request, 'core/mantenedor_bicicletas.html', {'form': form, 'bicicletas': bicicletas, 'edit_id': request.GET.get('edit_id')})

@user_passes_test(es_personal_autenticado_y_activo)
def mantenedor_arriendos(request):
    arriendos = Arriendo.objects.all()
    if request.method == 'POST':
        if 'edit' in request.POST:
            arriendo_id = request.POST.get('arriendo_id')
            arriendo = get_object_or_404(Arriendo, id=arriendo_id)
            form = ArriendoForm(request.POST, instance=arriendo)
            if form.is_valid():
                form.save()
                messages.success(request, 'Arriendo actualizado correctamente.')
                return redirect('mantenedor_arriendos')
        elif 'delete' in request.POST:
            arriendo_id = request.POST.get('arriendo_id')
            arriendo = get_object_or_404(Arriendo, id=arriendo_id)
            arriendo.delete()
            messages.success(request, 'Arriendo eliminado correctamente.')
            return redirect('mantenedor_arriendos')
    else:
        form = ArriendoForm()

    context = {
        'arriendos': arriendos,
        'form': form,
    }
    return render(request, 'core/mantenedor_arriendos.html', context)


@user_passes_test(es_personal_autenticado_y_activo)
def editar_arriendo(request, id):
    arriendo = get_object_or_404(Arriendo, id=id)
    if request.method == 'POST':
        form = ArriendoForm(request.POST, instance=arriendo)
        if form.is_valid():
            form.save()
            messages.success(request, 'Arriendo actualizado correctamente.')
            return redirect('mantenedor_arriendos')
        else:
            messages.error(request, 'Por favor corrige los errores a continuación.')
    else:
        form = ArriendoForm(instance=arriendo)
    
    context = {
        'form': form,
        'arriendo': arriendo,
    }
    return render(request, 'core/mantenedor_arriendos.html', context)

@user_passes_test(es_personal_autenticado_y_activo)
def eliminar_arriendo(request, id):
    arriendo = get_object_or_404(Arriendo, id=id)
    if request.method == 'POST':
        arriendo.delete()
        messages.success(request, 'Arriendo eliminado correctamente.')
        return redirect('mantenedor_arriendos')
    return redirect('mantenedor_arriendos')


def iniciar_pago(request):
    perfil = request.user.perfil
    carrito_items = Carrito.objects.filter(cliente=perfil)
    
    if not carrito_items:
        return redirect('carrito')  # Redirige a la vista del carrito si está vacío

    # Obtener el último número de boleta utilizado
    ultima_boleta = Boleta.objects.last()
    if ultima_boleta:
        ultima_nro_boleta = ultima_boleta.nro_boleta
    else:
        ultima_nro_boleta = 0

    # Incrementar el número de boleta para la nueva compra
    nuevo_nro_boleta = ultima_nro_boleta + 1

    # Guarda la orden de compra temporalmente para referencias futuras
    request.session['buy_order'] = nuevo_nro_boleta

    return redirect('pago_exitoso')  # Redirige directamente al pago exitoso (simulado)


def pago_exitoso(request):
    # Obtener el número de orden de compra simulado guardado en la sesión
    buy_order = request.session.get('buy_order')

    # Simulación de la respuesta de autorización
    status = 'AUTHORIZED'

    if status == 'AUTHORIZED':
        perfil = request.user.perfil
        carrito_items = Carrito.objects.filter(cliente=perfil)
        monto_sin_iva = sum(item.precio for item in carrito_items)
        iva = monto_sin_iva * 0.19
        total_a_pagar = monto_sin_iva + iva

        # Crear boleta simulada
        boleta = Boleta.objects.create(
            nro_boleta=buy_order,
            cliente=perfil,
            monto_sin_iva=monto_sin_iva,
            iva=iva,
            total_a_pagar=total_a_pagar,
            fecha_venta=timezone.now().date(),
            estado='Vendido'
        )

        # Crear detalles de boleta simulados
        for item in carrito_items:
            # Aseguramos obtener una bodega válida para el producto del carrito
            bodega = item.producto.bodega_set.first()  # Asume que hay una relación Producto -> Bodega
            if bodega:
                DetalleBoleta.objects.create(
                    boleta=boleta,
                    bodega=bodega,
                    precio=item.precio,
                    descuento_subscriptor=item.descuento_subscriptor,
                    descuento_oferta=item.descuento_oferta,
                    descuento_total=item.descuento_total,
                    descuentos=item.descuentos,
                    precio_a_pagar=item.precio_a_pagar
                )
            else:
                print(f"No se encontró una bodega válida para el producto {item.producto.nombre}. Detalle de boleta no creado.")

        # Limpiar el carrito simulado
        carrito_items.delete()

        # Agregar un mensaje flash para mostrar al usuario
        messages.success(request, '¡Pago exitoso! Su compra ha sido procesada correctamente.')

        # Pasar los datos necesarios al contexto del template
        context = {
            'buy_order': buy_order,
            'total_a_pagar': total_a_pagar,
            'boleta': boleta,
        }

        return render(request, 'core/pago_exitoso.html', context)
    else:
        return render(request, 'core/pago_fallido.html', {'buy_order': buy_order})