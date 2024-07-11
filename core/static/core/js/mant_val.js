$(document).ready(function() {
    $.validator.addMethod("noWeekends", function(value, element) {
        // Verificar si la fecha seleccionada es fin de semana
        var date = new Date(value);
        var day = date.getDay();
        return this.optional(element) || (day != 5 && day != 6);
    }, "La fecha programada no puede ser un sábado o domingo.");

    $("#mantenimiento-form").validate({
        rules: {
            fecha_programada: {
                required: true,
                date: true,
                noWeekends: true
            },
            hora_programada: {
                required: true,
                time: true
            },
            descripcion_problema: {
                required: true
            }
        },
        messages: {
            fecha_programada: {
                required: "Por favor, selecciona una fecha.",
                date: "Por favor, ingresa una fecha válida."
            },
            hora_programada: {
                required: "Por favor, ingresa una hora.",
                time: "Por favor, ingresa una hora válida."
            },
            descripcion_problema: {
                required: "Por favor, ingresa una descripción del problema."
            }
        },
        submitHandler: function(form) {
            form.submit();
        }
    });
});
