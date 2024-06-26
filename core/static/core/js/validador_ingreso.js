$(document).ready(function() {
   
  $('#id_username').attr('placeholder', 'Ej: cgomezv, cevans, sjohasson');
  $('#id_password').attr('placeholder', 'Ingesa tu contraseña actual');

  $("#formulario-ingreso").validate({
      rules: {
        username: {
          required: true,
        },
        password: {
          required: true,
          minlength: 5,
          maxlength: 15,
        },
      }, // --> Fin de reglas
      messages: {
        username: {
          required: "El nombre de usuario es un campo requerido",
        },
        password: {
          required: "La contraseña es un campo requerido",
          minlength: "Su contraseña es de un mínimo de 5 caracteres",
          maxlength: "Su contraseña es de un máximo de 15 caracteres",
        },
    },
    errorPlacement: function(error, element) {
      error.insertAfter(element); // Inserta el mensaje de error después del elemento
      error.addClass('error-message'); // Aplica una clase al mensaje de error
    },
  });

  $('#user-select').change(function() {
    var username = $(this).val();
    var password = 'Duoc@123';
    if ('cevans eolsen tholland sjohansson cpratt mruffalo super'.includes(username)) {
      password = '123';
    };
    $('#id_username').val(username);
    $('#id_password').val(password);
  });
  
});
