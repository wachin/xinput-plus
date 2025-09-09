Cosas por arreglar

* **El programa sólo aplica la configuración cuando seleccionas un dispositivo en la lista.**
  Al hacer clic, `on_device_selected()` carga la config guardada, mueve el *slider* y **ese movimiento** dispara `on_speed_changed()`, que es la función que realmente llama a `xinput --set-prop` para aplicar la velocidad. Si no hay clic, **no se ejecuta** esa ruta de código al iniciar.&#x20;

* En el arranque, se hace `load_devices()` y se muestra la ventana, pero **no se selecciona ningún dispositivo ni se invoca ninguna aplicación de ajustes**; por eso parece “inactivo” hasta que haces clic.&#x20;

* **Aplicación “extendida”:** cuando está activada, usa `Coordinate Transformation Matrix`; cuando no, usa `libinput Accel Speed`. Todo eso sólo corre dentro de `on_speed_changed()`, que depende del evento de selección/cambio del *slider*.&#x20;
