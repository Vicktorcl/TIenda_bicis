document.addEventListener('DOMContentLoaded', function() {
  const fechaInput = document.querySelector('#id_fecha_programada');

  fechaInput.addEventListener('change', function() {
      const fechaSeleccionada = this.value;
      obtenerHorasDisponibles(fechaSeleccionada);
  });

  function obtenerHorasDisponibles(fecha) {
      fetch(`/api/horas-disponibles/?fecha=${fecha}`)
          .then(response => response.json())
          .then(data => mostrarHorasDisponibles(data))
          .catch(error => console.error('Error al obtener las horas disponibles:', error));
  }

  function mostrarHorasDisponibles(horasDisponibles) {
      const selectHora = document.querySelector('#id_hora_programada');
      selectHora.innerHTML = '<option value="">Selecciona una hora</option>';

      const noHorasDisponibles = document.querySelector('#no-horas-disponibles');
      const noHoras = document.querySelector('#no-horas');

      if (horasDisponibles.length === 0) {
          noHorasDisponibles.style.display = 'block';
          noHoras.style.display = 'none';  // Ocultar el mensaje de no horas disponibles
      } else {
          noHorasDisponibles.style.display = 'none';
          horasDisponibles.forEach(hora => {
              const option = document.createElement('option');
              option.textContent = hora;
              option.value = hora;
              selectHora.appendChild(option);
          });
      }
  }
});