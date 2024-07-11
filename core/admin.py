from django.contrib import admin
from .models import Categoria, Producto, Carrito, Mantenimiento, Perfil, Boleta, DetalleBoleta, Bodega, Bicicleta, Arriendo

admin.site.register(Categoria)
admin.site.register(Producto)
admin.site.register(Carrito)
admin.site.register(Perfil)
admin.site.register(Boleta)
admin.site.register(DetalleBoleta)
admin.site.register(Bodega)
admin.site.register(Bicicleta)
admin.site.register(Arriendo)
admin.site.register(Mantenimiento)
