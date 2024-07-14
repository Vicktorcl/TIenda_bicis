from django.urls import path
from .views import inicio, registro, nosotros, productos
from .views import bodega, ventas, boleta, ingresar, mantenedor_usuarios
from .views import misdatos, miscompras, salir, carrito, ficha
from .views import cambiar_estado_boleta, poblar, obtener_productos, eliminar_producto_en_bodega
from .views import api_ropa, eliminar_producto_en_carrito, agregar_producto_al_carrito, agendar_mantenimiento, arrendar_bicicleta
from .views import vaciar_carrito, contraseña, fechas_no_disponibles, cambiar_password, comprar_ahora, administrar_tienda, cancelar_reserva, cancelar_arriendo
from .views import mantenedor_arriendos, editar_arriendo, eliminar_arriendo
from . import views

urlpatterns = [
    path('', inicio, name='inicio'),
    path('inicio', inicio, name='inicio'),
    path('registro', registro, name='registro'),
    path('nosotros', nosotros, name='nosotros'),
    path('productos/<accion>/<id>', productos, name='productos'),
    path('mantenedor_usuarios/<accion>/<id>', mantenedor_usuarios, name='mantenedor_usuarios'),
    path('cambiar_password', cambiar_password, name='cambiar_password'),
    path('bodega', bodega, name='bodega'),
    path('obtener_productos', obtener_productos, name='obtener_productos'),
    path('eliminar_producto_en_bodega/<bodega_id>', eliminar_producto_en_bodega, name='eliminar_producto_en_bodega'),
    path('ventas', ventas, name='ventas'),
    path('boleta/<nro_boleta>', boleta, name='boleta'),
    path('cambiar_estado_boleta/<nro_boleta>/<estado>', cambiar_estado_boleta, name='cambiar_estado_boleta'),
    path('ingresar', ingresar, name='ingresar'),
    path('misdatos', misdatos, name='misdatos'),
    path('contraseña', contraseña, name='contraseña'),
    path('miscompras', miscompras, name='miscompras'),
    path('salir', salir, name='salir'),
    path('carrito', carrito, name='carrito'),
    path('eliminar_producto_en_carrito/<carrito_id>', eliminar_producto_en_carrito, name='eliminar_producto_en_carrito'),
    path('vaciar_carrito', vaciar_carrito, name='vaciar_carrito'),
    path('agregar_producto_al_carrito/<producto_id>', agregar_producto_al_carrito, name='agregar_producto_al_carrito'),
    path('ficha/<producto_id>', ficha, name='ficha'),
    path('comprar_ahora', comprar_ahora, name='comprar_ahora'),
    path('api_ropa', api_ropa, name='api_ropa'),
    path('poblar', poblar, name='poblar'),
    path('administrar_tienda', administrar_tienda, name='administrar_tienda'),
    path('agendar_mantenimiento', agendar_mantenimiento, name='agendar_mantenimiento'),
    path('api/horas-disponibles/', views.horas_disponibles, name='api_horas_disponibles'),
    path('reservas/cancelar/<int:reserva_id>/', cancelar_reserva, name='cancelar_reserva'),
    path('listar_mantenimientos/', views.lista_mantenimientos, name='lista_mantenimientos'),
    path('eliminar_mantenimiento/<int:mantenimiento_id>/', views.eliminar_mantenimiento, name='eliminar_mantenimiento'),
    path('arrendar_bicicleta/', arrendar_bicicleta, name='arrendar_bicicleta'),
    path('cancelar_arriendo/<int:arriendo_id>/', cancelar_arriendo, name='cancelar_arriendo'),
    path('api/precio-arriendo/', views.calcular_precio_arriendo, name='calcular_precio_arriendo'),
    path('api/fechas-no-disponibles/', fechas_no_disponibles, name='fechas_no_disponibles'),
    path('mantenedor_bicicletas/', views.mantenedor_bicicletas, name='mantenedor_bicicletas'),
    path('mantenedor_arriendos/', mantenedor_arriendos, name='mantenedor_arriendos'),
    path('editar_arriendo/<int:id>/', editar_arriendo, name='editar_arriendo'),
    path('eliminar_arriendo/<int:id>/', eliminar_arriendo, name='eliminar_arriendo'),
    path('iniciar_pago/', views.iniciar_pago, name='iniciar_pago'),
    path('pago_exitoso/', views.pago_exitoso, name='pago_exitoso'),

]