from enum import StrEnum


class IncidentType(StrEnum):
    # Seguridad y acceso
    INTRUSION = "intrusion"  # Intento de entrada no autorizada
    LOST_KEY = "lost_key"  # Pérdida de llaves o tarjeta
    BROKEN_LOCK = "broken_lock"  # Cerradura dañada o forzada

    # Servicios básicos
    WATER_LEAK = "water_leak"  # Fuga de agua
    GAS_LEAK = "gas_leak"  # Fuga de gas
    ELECTRICAL_FAILURE = "electrical_failure"  # Falla eléctrica
    INTERNET_OUTAGE = "internet_outage"  # Fallo en Wi-Fi o router

    # Instalaciones
    BROKEN_APPLIANCE = "broken_appliance"  # Electrodoméstico dañado
    AIR_CONDITIONING_FAILURE = "ac_failure"  # Aire acondicionado no funciona
    ELEVATOR_ISSUE = "elevator_issue"  # Problema con el elevador
    LIGHTING_FAILURE = "lighting_failure"  # Foco o luminaria fundida

    # Limpieza y mantenimiento
    GARBAGE_OVERFLOW = "garbage_overflow"  # Acumulación de basura
    PEST_INFESTATION = "pest_infestation"  # Plaga (insectos, roedores, etc.)
    DIRTY_COMMON_AREA = "dirty_common_area"  # Áreas comunes sucias
    STRUCTURAL_DAMAGE = "structural_damage"  # Daño en pared, piso, techo, etc.

    # Convivencia y ruido
    NOISE_COMPLAINT = "noise_complaint"  # Queja por ruido
    ILLEGAL_PARKING = "illegal_parking"  # Estacionamiento indebido
    PET_DISTURBANCE = "pet_disturbance"  # Mascota causa molestias
    GUEST_BEHAVIOR = "guest_behavior"  # Conducta inapropiada de huésped

    # Emergencias
    FIRE = "fire"  # Incendio o conato
    MEDICAL_EMERGENCY = "medical_emergency"  # Emergencia médica
    NATURAL_EVENT = "natural_event"  # Sismo, tormenta, etc.

    # Administrativos
    PAYMENT_ISSUE = "payment_issue"  # Retraso o falta de pago
    RESERVATION_ISSUE = "reservation_issue"  # Error o disputa de reserva
    OTHER = "other"  # Otro tipo no categorizado


class IncidentStatus(StrEnum):
    # Ciclo de vida básico
    REPORTED = "reported"  # El incidente fue reportado por un huésped o residente
    IN_REVIEW = "in_review"  # En revisión por parte del administrador
    ASSIGNED = "assigned"  # Asignado a personal de mantenimiento o proveedor
    IN_PROGRESS = "in_progress"  # En proceso de atención o reparación
    WAITING_PARTS = "waiting_parts"  # Esperando refacciones o materiales
    ON_HOLD = "on_hold"  # Pausado temporalmente (clima, acceso, proveedor)
    RESOLVED = "resolved"  # Solucionado, pendiente de validación
    VERIFIED = "verified"  # Validado por el administrador o residente
    CLOSED = "closed"  # Cerrado oficialmente, sin acciones pendientes
    CANCELLED = "cancelled"  # Cancelado (reporte duplicado o error)
