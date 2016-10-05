#:inside:company/human_resources:section:human_resources#

===============================
Controlar los turnos de trabajo
===============================

Nos permite gestionar los trabajos e intervenciones de nuestros empleados a 
través de turnos, que podremos definir e identificar fácilmente. Podremos tener 
el control de los turnos de trabajo y la configuración de estos en: 

.. inheritref:: working_shift/working_shift:paragraph:configuracion

- **Configuración de turnos de trabajo**: añadimos la secuencia de los turnos 
  de trabajo e intervenciones, que podremos crear des de 
  :ref:`admin-secuencias`. 
  
- **Especialidades**: en este apartado podremos crear las especialidades que
  posteriormente se usarán en los turnos de trabajo. Al crear una especialidad, 
  deberemos darle un nombre y además añadir todos los contratos de cliente en 
  los que podremos encontrar esta especialidad. Las especialidades són importantes
  porque en algunos casos el precio del turno puede ir asociado a su especialidad.
  
- **Procedimientos**: donde se crean los procedimientos. Cada procedimiento tendrá
  asociada una especialidad y un grupo de facturación. También tendremos que indicar
  los contratos de cliente a los que se les aplicará los procedimientos.
  
- **Grupos de facturación**: donde crearemos los grupos de facturación. 
  
Por otra parte, fuera del menú de **Configuración** tenemos el menú principal, 
**Turnos de trabajo**, con el submenú **Intervenciones**. Al crear un turno de 
trabajo deberemos de añadir el empleado, la nómina de este, la fecha inicial y 
final del turno, las intervenciones y las observaciones, si estas son 
necesarias. Los turnos pasan por cuatro estados:

- Borrador: estado de creación y edición del turno de trabajo.
- Confirmado: estado en el que ya no podemos editar el turno y estamos 
  esperando a realizarlo.
- Realizado: estado de finalización del turno de trabajo, una vez realizado tan 
  sólo podemos cancelarlo. Esto lo haremos si queremos editar información del 
  turno, cancelarlo o si es necesario, acabar eliminándolo. A partir de este
  punto, el turno se podrá facturar. 
- Cancelado: estado que nos permite pasar nuevamente a borrador si es necesario.

Una vez el turno de trabajo ha sido facturado, quedará asociado al mismo:

- Línea de factura de cliente
- Regla de contrato de cliente que se haya aplicado
- Importe del turno

O, en el caso de que se haya facturado a través de nóminas: 

- Nómina que se está facturando
- Regla de contracto de empleado que se está aplicando

En el menú intervenciones veremos el listado de intervenciones que se han 
creado, pero no veremos que empleado las ha realizado. Aunque tendremos el 
número de trabajo al que pertenece cada intervención, las fechas, el tercero al 
que se le ha realizado la intervención (si es necesario), la referencia, la 
especialidad (historia clínica) el nombre de contacto (si hay) y las horas que ha consumido 
la intervención.  
