# Reloj Inteligente Avanzado

Aplicación de escritorio completa con interfaz moderna y múltiples funcionalidades avanzadas.

## ✨ Características Principales

### 🕐 Reloj Principal
- **Vista Analógica**: Reloj clásico con manecillas animadas y números romanos
- **Vista Digital**: Display grande con formato HH:MM:SS
- **Animaciones**: Péndulo decorativo y transiciones suaves (opcionales)
- **Offset Horario**: Ajuste de zona horaria de -12 a +12 horas
- **Fecha Completa**: Muestra día, fecha y mes en español

### 🌍 Relojes Mundiales
- **Múltiples Zonas**: Agrega relojes de diferentes ciudades del mundo
- **Zonas Disponibles**: UTC, Nueva York, Los Ángeles, Londres, París, Moscú, Tokio, Shanghái, Sídney, São Paulo
- **Actualización en Tiempo Real**: Todos los relojes se actualizan simultáneamente
- **Gestión Dinámica**: Agregar/eliminar zonas horarias fácilmente

### ⏰ Sistema de Alarmas
- **Alarmas Persistentes**: Se guardan automáticamente en archivo JSON
- **Sonidos Personalizados**: Diferentes tonos (predeterminado, suave, urgente)
- **Historial Completo**: Registro de todas las alarmas activadas
- **Notificaciones Visuales**: Pop-ups informativos al activarse

### ⏱️ Cronómetro Avanzado
- **Precisión de Milisegundos**: Medición exacta hasta centésimas
- **Vueltas (Laps)**: Registra tiempos parciales durante la carrera
- **Controles Completos**: Iniciar, pausar, continuar y reiniciar
- **Historial de Vueltas**: Lista completa de tiempos registrados

### ⏳ Temporizador Profesional
- **Configuración Flexible**: Horas, minutos y segundos independientes
- **Cuenta Regresiva Visual**: Display grande con formato HH:MM:SS
- **Notificación Final**: Alerta sonora y visual al terminar
- **Controles Avanzados**: Iniciar, pausar, detener y reiniciar

### 🎨 Personalización
- **3 Temas Disponibles**: Claro, Oscuro y Azul
- **Cambio Dinámico**: Aplicación instantánea sin reiniciar
- **Pantalla Completa**: Modo inmersivo opcional
- **Sonido On/Off**: Control global de audio

### ⚙️ Configuración Avanzada
- **Persistencia**: Todas las configuraciones se guardan automáticamente
- **Historial de Alarmas**: Registro completo con timestamps
- **Limpieza de Datos**: Opción para borrar historial
- **Configuración JSON**: Archivo estructurado para datos

## 🚀 Cómo Ejecutar

1. **Requisitos**: Python 3.6+ con Tkinter (incluido por defecto)
2. **Dependencias Opcionales**:
   ```bash
   pip install pygame  # Para sonidos avanzados
   ```
3. **Ejecutar**:
   ```bash
   python clock_app.py
   ```

## 📁 Estructura del Proyecto

```
taller_reloj/
├── clock_app.py          # Aplicación principal
├── clock_config.json     # Configuración persistente (auto-generado)
├── alarms.json          # Alarmas guardadas (auto-generado)
└── README.md            # Esta documentación
```

## 🎯 Funcionalidades Técnicas

- **Arquitectura Modular**: Clases separadas para cada funcionalidad
- **Hilos Independientes**: Monitoreo de alarmas sin bloquear UI
- **Gestión de Memoria**: Limpieza automática de recursos
- **Manejo de Errores**: Validación robusta de entradas
- **Interfaz Responsiva**: Adaptable a diferentes tamaños de ventana
- **Rendimiento Optimizado**: Actualizaciones eficientes cada 100ms

## 🎨 Interfaz de Usuario

- **Diseño Moderno**: Inspirado en aplicaciones profesionales
- **Navegación por Pestañas**: Organización clara de funcionalidades
- **Controles Intuitivos**: Botones, deslizadores y listas interactivas
- **Feedback Visual**: Estados, colores y animaciones informativas
- **Accesibilidad**: Fuentes legibles y contrastes adecuados

## 🔧 Personalización Avanzada

### Temas Disponibles
- **Claro**: Colores suaves, alta legibilidad
- **Oscuro**: Ahorro de batería, cómodo en ambientes oscuros
- **Azul**: Tema corporativo, profesional

### Configuración de Audio
- **Sistema Nativo**: Usa sonidos del sistema operativo
- **Pygame (Opcional)**: Sonidos generados programáticamente
- **Control Global**: Silenciar todas las notificaciones

### Gestión de Datos
- **Archivos JSON**: Configuración y datos estructurados
- **Backup Automático**: Copias de seguridad de configuraciones
- **Importación/Exportación**: Posibilidad futura de migración

## 🐛 Solución de Problemas

### Audio no funciona
- Verifica que pygame esté instalado: `pip install pygame`
- En Windows: Asegúrate de tener permisos de audio
- Alternativa: El sistema usa sonidos nativos como fallback

### Configuración no se guarda
- Verifica permisos de escritura en la carpeta del proyecto
- Los archivos se crean automáticamente al guardar

### Rendimiento lento
- Desactiva animaciones en "Configuración > Animaciones"
- Cierra otras aplicaciones que consuman recursos

## 🔮 Características Futuras

- **Sincronización NTP**: Hora precisa desde servidores
- **Zonas Horarias Personalizadas**: Crear zonas personalizadas
- **Temas Personalizados**: Editor de colores
- **Exportación de Datos**: CSV/PDF de historiales
- **Recordatorios**: Notas con fechas específicas
- **Integración Calendario**: Sincronización con Google Calendar

---

**Desarrollado con Python y Tkinter** | **Interfaz Moderna y Profesional** | **Funcionalidades Avanzadas**
