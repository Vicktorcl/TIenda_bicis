$(document).ready(function() {
  $('#Mantenimiento-Form').validate({
    // Configuración de reglas y mensajes de validación
    rules: {
      fecha_programada: {
        required: true,
        date: true,
        customDateValidation: true
      },
      hora_programada: {
        required: true,
        time: true,
      },
      descripcion_problema: {
        required: true
      }
      // Agrega más reglas según sea necesario para otros campos
    },
    messages: {
      // Mensajes de error personalizados
      fecha_programada: {
        required: 'Este campo es requerido',
        date: 'Ingresa una fecha válida'
      },
      hora_programada: {
        required: 'Este campo es requeridoaaa',
        time: 'Ingresa una hora válida'
      },
      descripcion_problema: {
        required: 'Este campo es requerido10'
      }
      // Agrega más mensajes personalizados según sea necesario
    },
    errorPlacement: function(error, element) {
      error.insertAfter(element); // Inserta el mensaje de error después del elemento
      error.addClass('error-message'); // Aplica una clase al mensaje de error
    },
  });

  // Definición de la regla personalizada para validar que sea de lunes a viernes
  $.validator.addMethod('customDateValidation', function(value, element) {
    var date = new Date(value);
    // Verifica que el día no sea sábado (5) ni domingo (6)
    return date.getDay() !== 5 && date.getDay() !== 6;
  }, 'Los mantenimientos solo se pueden programar de lunes a viernes.');
});
