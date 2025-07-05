#!/usr/bin/env python
import os
import sys
import django
from decimal import Decimal
from datetime import datetime, timedelta, date, time
import random

# Configurar Django
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'proy_clinico.settings')
django.setup()

from applications.core.models import (
    TipoSangre, Paciente, Especialidad, Doctor, Cargo, Empleado,
    TipoMedicamento, MarcaMedicamento, Medicamento, Diagnostico,
    TipoGasto, GastoMensual
)
from applications.doctor.models import (
    HorarioAtencion, CitaMedica, Atencion, DetalleAtencion,
    ServiciosAdicionales, Pago, DetallePago
)
from applications.doctor.utils.cita_medica import EstadoCitaChoices
from applications.doctor.utils.doctor import DiaSemanaChoices
from applications.doctor.utils.pago import MetodoPagoChoices, EstadoPagoChoices
from applications.core.utils.medicamento import ViaAdministracion
from applications.core.utils.paciente import EstadoCivilChoices, SexoChoices
from django.utils import timezone

def limpiar_datos():
    """Limpia datos existentes para evitar duplicados"""
    print("🧹 Limpiando datos existentes...")
    
    # Limpiar en orden inverso de dependencias
    DetallePago.objects.all().delete()
    Pago.objects.all().delete()
    DetalleAtencion.objects.all().delete()
    Atencion.objects.all().delete()
    CitaMedica.objects.all().delete()
    HorarioAtencion.objects.all().delete()
    
    GastoMensual.objects.all().delete()
    Empleado.objects.all().delete()
    Doctor.objects.filter(ruc__startswith='17').delete()  # Solo test data
    Paciente.objects.filter(cedula_ecuatoriana__startswith='17').delete()  # Solo test data
    
    print("✅ Datos de prueba limpiados")

def crear_tipos_sangre():
    """Crear tipos de sangre básicos"""
    print("🩸 Creando tipos de sangre...")
    
    tipos = [
        ('O+', 'Tipo O positivo - Donante universal de glóbulos rojos'),
        ('O-', 'Tipo O negativo - Donante universal'),
        ('A+', 'Tipo A positivo'),
        ('A-', 'Tipo A negativo'),
        ('B+', 'Tipo B positivo'),
        ('B-', 'Tipo B negativo'),
        ('AB+', 'Tipo AB positivo - Receptor universal'),
        ('AB-', 'Tipo AB negativo'),
    ]
    
    for tipo, desc in tipos:
        TipoSangre.objects.get_or_create(
            tipo=tipo,
            defaults={'descripcion': desc}
        )
    
    print(f"✅ Creados {len(tipos)} tipos de sangre")

def crear_especialidades():
    """Crear especialidades médicas"""
    print("👨‍⚕️ Creando especialidades médicas...")
    
    especialidades = [
        ('Medicina General', 'Atención médica integral y primaria'),
        ('Cardiología', 'Especialidad del corazón y sistema cardiovascular'),
        ('Pediatría', 'Atención médica especializada en niños y adolescentes'),
        ('Ginecología', 'Salud reproductiva femenina'),
        ('Dermatología', 'Enfermedades de la piel'),
        ('Traumatología', 'Lesiones del sistema musculoesquelético'),
        ('Neurología', 'Enfermedades del sistema nervioso'),
        ('Psiquiatría', 'Trastornos mentales y del comportamiento'),
        ('Oftalmología', 'Enfermedades de los ojos'),
        ('Otorrinolaringología', 'Enfermedades del oído, nariz y garganta'),
    ]
    
    for nombre, desc in especialidades:
        Especialidad.objects.get_or_create(
            nombre=nombre,
            defaults={'descripcion': desc}
        )
    
    print(f"✅ Creadas {len(especialidades)} especialidades")

def crear_cargos():
    """Crear cargos para empleados"""
    print("💼 Creando cargos...")
    
    cargos = [
        ('Médico Especialista', 'Médico con especialización'),
        ('Médico General', 'Médico de atención primaria'),
        ('Enfermero/a', 'Personal de enfermería'),
        ('Auxiliar de Enfermería', 'Asistente de enfermería'),
        ('Recepcionista', 'Atención al cliente y citas'),
        ('Administrador', 'Gestión administrativa'),
        ('Contador', 'Gestión contable y financiera'),
        ('Limpieza', 'Personal de limpieza y mantenimiento'),
        ('Seguridad', 'Personal de seguridad'),
        ('Farmaceuta', 'Gestión de medicamentos'),
    ]
    
    for nombre, desc in cargos:
        Cargo.objects.get_or_create(
            nombre=nombre,
            defaults={'descripcion': desc}
        )
    
    print(f"✅ Creados {len(cargos)} cargos")

def crear_tipos_medicamentos():
    """Crear tipos de medicamentos"""
    print("💊 Creando tipos de medicamentos...")
    
    tipos = [
        ('Analgésico', 'Medicamentos para aliviar el dolor'),
        ('Antibiótico', 'Medicamentos contra infecciones bacterianas'),
        ('Antiinflamatorio', 'Reduce inflamación y dolor'),
        ('Antihipertensivo', 'Control de presión arterial'),
        ('Antidiabético', 'Control de diabetes'),
        ('Vitaminas', 'Suplementos vitamínicos'),
        ('Antihistamínico', 'Tratamiento de alergias'),
        ('Antidepresivo', 'Tratamiento de depresión'),
        ('Ansiolítico', 'Tratamiento de ansiedad'),
        ('Broncodilatador', 'Tratamiento de asma y EPOC'),
    ]
    
    for nombre, desc in tipos:
        TipoMedicamento.objects.get_or_create(
            nombre=nombre,
            defaults={'descripcion': desc}
        )
    
    print(f"✅ Creados {len(tipos)} tipos de medicamentos")

def crear_marcas_medicamentos():
    """Crear marcas de medicamentos"""
    print("🏭 Creando marcas de medicamentos...")
    
    marcas = [
        ('Pfizer', 'Farmacéutica multinacional'),
        ('Bayer', 'Empresa farmacéutica alemana'),
        ('Novartis', 'Farmacéutica suiza'),
        ('Roche', 'Empresa farmacéutica suiza'),
        ('Johnson & Johnson', 'Corporación farmacéutica estadounidense'),
        ('Abbott', 'Empresa de salud global'),
        ('Merck', 'Farmacéutica alemana'),
        ('GSK', 'GlaxoSmithKline'),
        ('Sanofi', 'Farmacéutica francesa'),
        ('Genérico', 'Medicamentos genéricos'),
    ]
    
    for nombre, desc in marcas:
        MarcaMedicamento.objects.get_or_create(
            nombre=nombre,
            defaults={'descripcion': desc}
        )
    
    print(f"✅ Creadas {len(marcas)} marcas")

def crear_medicamentos():
    """Crear medicamentos básicos"""
    print("💉 Creando medicamentos...")
    
    # Obtener tipos y marcas
    tipos = {t.nombre: t for t in TipoMedicamento.objects.all()}
    marcas = {m.nombre: m for m in MarcaMedicamento.objects.all()}
    
    medicamentos = [
        # Analgésicos
        ('Paracetamol', tipos['Analgésico'], marcas['Genérico'], '500mg', ViaAdministracion.ORAL, 100, 0.50, True),
        ('Ibuprofeno', tipos['Antiinflamatorio'], marcas['Bayer'], '400mg', ViaAdministracion.ORAL, 80, 0.75, True),
        ('Aspirina', tipos['Analgésico'], marcas['Bayer'], '100mg', ViaAdministracion.ORAL, 120, 0.30, True),
        
        # Antibióticos
        ('Amoxicilina', tipos['Antibiótico'], marcas['GSK'], '500mg', ViaAdministracion.ORAL, 60, 2.50, True),
        ('Azitromicina', tipos['Antibiótico'], marcas['Pfizer'], '250mg', ViaAdministracion.ORAL, 30, 8.00, True),
        ('Cefalexina', tipos['Antibiótico'], marcas['Genérico'], '500mg', ViaAdministracion.ORAL, 40, 3.20, True),
        
        # Antihipertensivos
        ('Losartán', tipos['Antihipertensivo'], marcas['Merck'], '50mg', ViaAdministracion.ORAL, 90, 1.80, True),
        ('Enalapril', tipos['Antihipertensivo'], marcas['Genérico'], '10mg', ViaAdministracion.ORAL, 100, 1.20, True),
        
        # Antidiabéticos
        ('Metformina', tipos['Antidiabético'], marcas['Sanofi'], '850mg', ViaAdministracion.ORAL, 70, 2.10, True),
        ('Glibenclamida', tipos['Antidiabético'], marcas['Genérico'], '5mg', ViaAdministracion.ORAL, 50, 1.50, True),
        
        # Vitaminas
        ('Complejo B', tipos['Vitaminas'], marcas['Abbott'], '100mg', ViaAdministracion.ORAL, 150, 5.00, True),
        ('Vitamina C', tipos['Vitaminas'], marcas['Bayer'], '1g', ViaAdministracion.ORAL, 200, 3.50, True),
        
        # Antihistamínicos
        ('Loratadina', tipos['Antihistamínico'], marcas['Johnson & Johnson'], '10mg', ViaAdministracion.ORAL, 60, 4.20, True),
        ('Cetirizina', tipos['Antihistamínico'], marcas['GSK'], '10mg', ViaAdministracion.ORAL, 45, 5.80, True),
        
        # Broncodilatadores
        ('Salbutamol', tipos['Broncodilatador'], marcas['GSK'], '100mcg', ViaAdministracion.INHALATORIA, 25, 12.50, True),
    ]
    
    for nombre, tipo, marca, conc, via, cant, precio, comercial in medicamentos:
        Medicamento.objects.get_or_create(
            nombre=nombre,
            defaults={
                'tipo': tipo,
                'marca_medicamento': marca,
                'concentracion': conc,
                'via_administracion': via,
                'cantidad': cant,
                'precio': Decimal(str(precio)),
                'comercial': comercial
            }
        )
    
    print(f"✅ Creados {len(medicamentos)} medicamentos")

def crear_diagnosticos():
    """Crear diagnósticos médicos comunes"""
    print("🩺 Creando diagnósticos...")
    
    diagnosticos = [
        ('J00', 'Rinofaringitis aguda [resfriado común]', 'Infección viral del tracto respiratorio superior'),
        ('K59.0', 'Estreñimiento', 'Dificultad para evacuar'),
        ('R50.9', 'Fiebre no especificada', 'Elevación de temperatura corporal'),
        ('M25.5', 'Dolor articular', 'Dolor en articulaciones'),
        ('R51', 'Cefalea', 'Dolor de cabeza'),
        ('K30', 'Dispepsia funcional', 'Indigestión'),
        ('I10', 'Hipertensión esencial', 'Presión arterial elevada'),
        ('E11.9', 'Diabetes mellitus tipo 2 sin complicaciones', 'Diabetes tipo 2'),
        ('F32.9', 'Episodio depresivo sin especificar', 'Depresión'),
        ('J20.9', 'Bronquitis aguda no especificada', 'Inflamación de bronquios'),
        ('L20.9', 'Dermatitis atópica no especificada', 'Eczema'),
        ('N39.0', 'Infección de vías urinarias', 'ITU'),
        ('M54.5', 'Lumbago', 'Dolor lumbar'),
        ('R06.02', 'Dificultad respiratoria', 'Disnea'),
        ('K21.9', 'Enfermedad por reflujo gastroesofágico', 'ERGE'),
    ]
    
    for codigo, desc, datos in diagnosticos:
        Diagnostico.objects.get_or_create(
            codigo=codigo,
            defaults={
                'descripcion': desc,
                'datos_adicionales': datos
            }
        )
    
    print(f"✅ Creados {len(diagnosticos)} diagnósticos")

def crear_tipos_gastos():
    """Crear tipos de gastos operativos"""
    print("💰 Creando tipos de gastos...")
    
    tipos_gastos = [
        ('Arriendo', 'Alquiler del local del consultorio'),
        ('Luz', 'Servicio de energía eléctrica'),
        ('Agua', 'Servicio de agua potable'),
        ('Internet', 'Servicio de internet y telecomunicaciones'),
        ('Teléfono', 'Servicio telefónico'),
        ('Insumos Médicos', 'Material médico y de oficina'),
        ('Medicamentos', 'Compra de medicamentos para stock'),
        ('Equipos Médicos', 'Mantenimiento y compra de equipos'),
        ('Limpieza', 'Productos y servicios de limpieza'),
        ('Seguros', 'Pólizas de seguro'),
        ('Marketing', 'Publicidad y marketing'),
        ('Capacitación', 'Cursos y entrenamientos'),
    ]
    
    for nombre, desc in tipos_gastos:
        TipoGasto.objects.get_or_create(
            nombre=nombre,
            defaults={'descripcion': desc}
        )
    
    print(f"✅ Creados {len(tipos_gastos)} tipos de gastos")

def crear_doctores():
    """Crear doctores de ejemplo"""
    print("👨‍⚕️ Creando doctores...")
    
    especialidades = list(Especialidad.objects.all())
    
    doctores_data = [
        {
            'nombres': 'Carlos Eduardo',
            'apellidos': 'González Vásquez',
            'ruc': '1712345678001',
            'fecha_nacimiento': date(1975, 3, 15),
            'direccion': 'Av. 6 de Diciembre N24-253 y Lizardo García, Quito',
            'codigo_unico_doctor': 'DOC001',
            'telefonos': '0987654321',
            'email': 'carlos.gonzalez@clinica.com',
            'horario_atencion': 'Lunes a Viernes: 08:00 - 17:00, Sábados: 08:00 - 12:00',
            'duracion_atencion': 30,
            'especialidades': ['Medicina General', 'Cardiología']
        },
        {
            'nombres': 'María Fernanda',
            'apellidos': 'López Herrera',
            'ruc': '1723456789001',
            'fecha_nacimiento': date(1980, 7, 22),
            'direccion': 'Av. República del Salvador N34-377 y Moscú, Quito',
            'codigo_unico_doctor': 'DOC002',
            'telefonos': '0976543210',
            'email': 'maria.lopez@clinica.com',
            'horario_atencion': 'Lunes a Viernes: 14:00 - 20:00',
            'duracion_atencion': 45,
            'especialidades': ['Pediatría']
        },
        {
            'nombres': 'Roberto Carlos',
            'apellidos': 'Martínez Silva',
            'ruc': '1734567890001',
            'fecha_nacimiento': date(1978, 11, 8),
            'direccion': 'Av. Amazonas N39-123 y Arízaga, Quito',
            'codigo_unico_doctor': 'DOC003',
            'telefonos': '0965432109',
            'email': 'roberto.martinez@clinica.com',
            'horario_atencion': 'Martes a Sábado: 09:00 - 16:00',
            'duracion_atencion': 30,
            'especialidades': ['Dermatología']
        },
        {
            'nombres': 'Ana Lucía',
            'apellidos': 'Rodríguez Morales',
            'ruc': '1745678901001',
            'fecha_nacimiento': date(1982, 5, 18),
            'direccion': 'Av. Eloy Alfaro N32-650 y Rusia, Quito',
            'codigo_unico_doctor': 'DOC004',
            'telefonos': '0954321098',
            'email': 'ana.rodriguez@clinica.com',
            'horario_atencion': 'Lunes a Viernes: 07:00 - 15:00',
            'duracion_atencion': 40,
            'especialidades': ['Ginecología']
        },
    ]
    
    for data in doctores_data:
        especialidades_nombres = data.pop('especialidades')
        doctor, created = Doctor.objects.get_or_create(
            ruc=data['ruc'],
            defaults=data
        )
        
        if created:
            # Asignar especialidades
            for esp_nombre in especialidades_nombres:
                especialidad = Especialidad.objects.filter(nombre=esp_nombre).first()
                if especialidad:
                    doctor.especialidad.add(especialidad)
    
    print(f"✅ Creados {len(doctores_data)} doctores")

def crear_empleados():
    """Crear empleados de ejemplo"""
    print("👥 Creando empleados...")
    
    cargos = {c.nombre: c for c in Cargo.objects.all()}
    
    empleados_data = [
        {
            'nombres': 'Carmen Rosa',
            'apellidos': 'Jiménez Pérez',
            'cedula_ecuatoriana': '1756789012',
            'fecha_nacimiento': date(1985, 9, 12),
            'cargo': cargos['Recepcionista'],
            'sueldo': Decimal('450.00'),
            'fecha_ingreso': date(2023, 1, 15),
            'direccion': 'Sector La Magdalena, Quito'
        },
        {
            'nombres': 'Luis Miguel',
            'apellidos': 'Vargas Torres',
            'cedula_ecuatoriana': '1767890123',
            'fecha_nacimiento': date(1990, 2, 28),
            'cargo': cargos['Auxiliar de Enfermería'],
            'sueldo': Decimal('520.00'),
            'fecha_ingreso': date(2023, 3, 10),
            'direccion': 'Sector Solanda, Quito'
        },
        {
            'nombres': 'Patricia Elena',
            'apellidos': 'Moreno Castro',
            'cedula_ecuatoriana': '1778901234',
            'fecha_nacimiento': date(1988, 6, 14),
            'cargo': cargos['Enfermero/a'],
            'sueldo': Decimal('680.00'),
            'fecha_ingreso': date(2022, 8, 20),
            'direccion': 'Sector El Condado, Quito'
        },
        {
            'nombres': 'Gabriel Andrés',
            'apellidos': 'Ruiz Sandoval',
            'cedula_ecuatoriana': '1789012345',
            'fecha_nacimiento': date(1987, 12, 3),
            'cargo': cargos['Administrador'],
            'sueldo': Decimal('850.00'),
            'fecha_ingreso': date(2022, 4, 5),
            'direccion': 'Sector La Carolina, Quito'
        },
    ]
    
    for data in empleados_data:
        Empleado.objects.get_or_create(
            cedula_ecuatoriana=data['cedula_ecuatoriana'],
            defaults=data
        )
    
    print(f"✅ Creados {len(empleados_data)} empleados")

def crear_pacientes():
    """Crear pacientes de ejemplo"""
    print("🏥 Creando pacientes...")
    
    tipos_sangre = list(TipoSangre.objects.all())
    
    pacientes_data = [
        {
            'nombres': 'José Antonio',
            'apellidos': 'Pérez Morales',
            'cedula_ecuatoriana': '1712345679',
            'fecha_nacimiento': date(1975, 8, 20),
            'telefono': '0987654321',
            'email': 'jose.perez@email.com',
            'sexo': SexoChoices.MASCULINO,
            'estado_civil': EstadoCivilChoices.CASADO,
            'direccion': 'Av. Mariscal Sucre N45-120 y Toledo, Quito',
            'antecedentes_personales': 'Hipertensión arterial diagnosticada hace 5 años, controlada con medicamentos',
            'medicamentos_actuales': 'Losartán 50mg cada 12 horas',
            'alergias': 'Penicilina',
            'habitos_toxicos': 'Ex fumador (dejó hace 3 años)',
        },
        {
            'nombres': 'María Elena',
            'apellidos': 'García Vásquez',
            'cedula_ecuatoriana': '1723456780',
            'fecha_nacimiento': date(1988, 3, 15),
            'telefono': '0976543210',
            'email': 'maria.garcia@email.com',
            'sexo': SexoChoices.FEMENINO,
            'estado_civil': EstadoCivilChoices.SOLTERO,
            'direccion': 'Calle Guayaquil N8-55 y Esmeraldas, Quito',
            'antecedentes_familiares': 'Madre con diabetes tipo 2, padre con hipertensión',
            'antecedentes_gineco_obstetricos': 'Menarquia a los 13 años, ciclos regulares, G0P0A0',
            'alergias': 'Mariscos',
            'habitos_toxicos': 'Ninguno',
        },
        {
            'nombres': 'Carlos Andrés',
            'apellidos': 'Rodríguez Luna',
            'cedula_ecuatoriana': '1734567891',
            'fecha_nacimiento': date(1992, 11, 8),
            'telefono': '0965432109',
            'email': 'carlos.rodriguez@email.com',
            'sexo': SexoChoices.MASCULINO,
            'estado_civil': EstadoCivilChoices.SOLTERO,
            'direccion': 'Sector La Floresta, Calle Andalucía N24-03',
            'antecedentes_quirurgicos': 'Apendicectomía en 2015',
            'habitos_toxicos': 'Alcohol ocasional (fines de semana)',
            'vacunas': 'COVID-19 completa, influenza anual',
        },
        {
            'nombres': 'Ana Sofía',
            'apellidos': 'Martínez Silva',
            'cedula_ecuatoriana': '1745678902',
            'fecha_nacimiento': date(1995, 6, 25),
            'telefono': '0954321098',
            'email': 'ana.martinez@email.com',
            'sexo': SexoChoices.FEMENINO,
            'estado_civil': EstadoCivilChoices.UNION_LIBRE,
            'direccion': 'Sector Cumbayá, Calle de las Orquídeas N14-25',
            'antecedentes_gineco_obstetricos': 'G1P1A0, parto eutócico hace 2 años',
            'medicamentos_actuales': 'Anticonceptivos orales',
            'alergias': 'Polen',
            'habitos_toxicos': 'Ninguno',
        },
        {
            'nombres': 'Roberto Miguel',
            'apellidos': 'López Herrera',
            'cedula_ecuatoriana': '1756789013',
            'fecha_nacimiento': date(1960, 1, 12),
            'telefono': '0943210987',
            'email': 'roberto.lopez@email.com',
            'sexo': SexoChoices.MASCULINO,
            'estado_civil': EstadoCivilChoices.CASADO,
            'direccion': 'Av. de Los Shyris N36-188 y Naciones Unidas',
            'antecedentes_personales': 'Diabetes tipo 2 desde hace 8 años, dislipidemia',
            'medicamentos_actuales': 'Metformina 850mg c/12h, Atorvastatina 20mg/noche',
            'habitos_toxicos': 'Ex fumador (dejó hace 10 años)',
            'antecedentes_familiares': 'Padre falleció por infarto, madre con diabetes',
        },
        {
            'nombres': 'Lucía Fernanda',
            'apellidos': 'Torres Morales',
            'cedula_ecuatoriana': '1767890124',
            'fecha_nacimiento': date(2010, 9, 18),
            'telefono': '0932109876',
            'email': None,  # Menor de edad
            'sexo': SexoChoices.FEMENINO,
            'estado_civil': EstadoCivilChoices.SOLTERO,
            'direccion': 'Sector El Bosque, Calle de los Cipreses N12-34',
            'antecedentes_familiares': 'Sin antecedentes patológicos familiares relevantes',
            'vacunas': 'Esquema completo para la edad, COVID-19 pediátrica',
            'habitos_toxicos': 'Ninguno',
        },
    ]
    
    for i, data in enumerate(pacientes_data):
        data['tipo_sangre'] = random.choice(tipos_sangre)
        Paciente.objects.get_or_create(
            cedula_ecuatoriana=data['cedula_ecuatoriana'],
            defaults=data
        )
    
    print(f"✅ Creados {len(pacientes_data)} pacientes")

def crear_gastos_mensuales():
    """Crear gastos mensuales de ejemplo"""
    print("💸 Creando gastos mensuales...")
    
    tipos_gastos = list(TipoGasto.objects.all())
    
    # Crear gastos para los últimos 3 meses
    base_date = date.today().replace(day=1)
    
    gastos_data = [
        # Gastos fijos mensuales
        ('Arriendo', 800.00),
        ('Luz', 45.50),
        ('Agua', 25.30),
        ('Internet', 35.00),
        ('Teléfono', 20.00),
        ('Seguros', 120.00),
        
        # Gastos variables
        ('Insumos Médicos', 150.75),
        ('Medicamentos', 220.40),
        ('Limpieza', 40.25),
        ('Marketing', 80.00),
    ]
    
    for mes_offset in range(3):  # Últimos 3 meses
        fecha_gasto = base_date - timedelta(days=mes_offset * 30)
        
        for tipo_nombre, valor_base in gastos_data:
            tipo_gasto = TipoGasto.objects.filter(nombre=tipo_nombre).first()
            if tipo_gasto:
                # Agregar variación aleatoria ±10%
                variacion = random.uniform(0.9, 1.1)
                valor_final = round(valor_base * variacion, 2)
                
                GastoMensual.objects.get_or_create(
                    tipo_gasto=tipo_gasto,
                    fecha=fecha_gasto,
                    defaults={
                        'valor': Decimal(str(valor_final)),
                        'observacion': f'Gasto mensual de {fecha_gasto.strftime("%B %Y")}'
                    }
                )
    
    print("✅ Creados gastos mensuales de los últimos 3 meses")

def crear_horarios_atencion():
    """Crear horarios de atención"""
    print("⏰ Creando horarios de atención...")
    
    horarios = [
        # Horario matutino
        (DiaSemanaChoices.LUNES, time(8, 0), time(12, 0), None, None),
        (DiaSemanaChoices.MARTES, time(8, 0), time(12, 0), None, None),
        (DiaSemanaChoices.MIERCOLES, time(8, 0), time(12, 0), None, None),
        (DiaSemanaChoices.JUEVES, time(8, 0), time(12, 0), None, None),
        (DiaSemanaChoices.VIERNES, time(8, 0), time(12, 0), None, None),
        
        # Horario vespertino
        (DiaSemanaChoices.LUNES, time(14, 0), time(18, 0), None, None),
        (DiaSemanaChoices.MARTES, time(14, 0), time(18, 0), None, None),
        (DiaSemanaChoices.MIERCOLES, time(14, 0), time(18, 0), None, None),
        (DiaSemanaChoices.JUEVES, time(14, 0), time(18, 0), None, None),
        (DiaSemanaChoices.VIERNES, time(14, 0), time(18, 0), None, None),
        
        # Sábados
        (DiaSemanaChoices.SABADO, time(8, 0), time(12, 0), None, None),
    ]
    
    for dia, inicio, fin, int_desde, int_hasta in horarios:
        HorarioAtencion.objects.get_or_create(
            dia_semana=dia,
            hora_inicio=inicio,
            hora_fin=fin,
            defaults={
                'intervalo_desde': int_desde,
                'intervalo_hasta': int_hasta
            }
        )
    
    print(f"✅ Creados {len(horarios)} horarios de atención")

def crear_servicios_adicionales():
    """Crear servicios adicionales"""
    print("🏥 Creando servicios adicionales...")
    
    servicios = [
        ('Consulta Médica General', 25.00, 'Consulta médica de medicina general'),
        ('Consulta Especializada', 40.00, 'Consulta con médico especialista'),
        ('Electrocardiograma', 15.00, 'ECG de 12 derivaciones'),
        ('Radiografía Simple', 20.00, 'Radiografía simple de una proyección'),
        ('Ecografía Abdominal', 35.00, 'Ecografía del abdomen completo'),
        ('Laboratorio Básico', 12.00, 'Exámenes de laboratorio básicos'),
        ('Hemograma Completo', 8.00, 'Conteo sanguíneo completo'),
        ('Glicemia', 3.00, 'Medición de glucosa en sangre'),
        ('Curaciones', 5.00, 'Curación de heridas menores'),
        ('Inyecciones', 2.00, 'Aplicación de medicamentos inyectables'),
        ('Nebulizaciones', 4.00, 'Terapia respiratoria con nebulizador'),
        ('Control de Presión', 3.00, 'Medición y control de presión arterial'),
        ('Certificado Médico', 10.00, 'Emisión de certificado médico'),
        ('Papanicolaou', 18.00, 'Citología cervical'),
        ('Vacunación', 15.00, 'Aplicación de vacunas'),
    ]
    
    for nombre, costo, desc in servicios:
        ServiciosAdicionales.objects.get_or_create(
            nombre_servicio=nombre,
            defaults={
                'costo_servicio': Decimal(str(costo)),
                'descripcion': desc
            }
        )
    
    print(f"✅ Creados {len(servicios)} servicios adicionales")

def crear_citas_medicas():
    """Crear citas médicas de ejemplo"""
    print("📅 Creando citas médicas...")
    
    pacientes = list(Paciente.objects.all())
    
    # Crear citas para los próximos 7 días
    base_date = date.today()
    
    citas_data = []
    for day_offset in range(7):
        fecha_cita = base_date + timedelta(days=day_offset)
        
        # Skip domingos
        if fecha_cita.weekday() == 6:
            continue
            
        # Horarios de citas
        horarios = [
            time(8, 0), time(8, 30), time(9, 0), time(9, 30), time(10, 0),
            time(10, 30), time(11, 0), time(11, 30), time(14, 0), time(14, 30),
            time(15, 0), time(15, 30), time(16, 0), time(16, 30), time(17, 0)
        ]
        
        # Crear 3-5 citas por día
        num_citas = random.randint(3, min(5, len(pacientes)))
        horarios_seleccionados = random.sample(horarios, num_citas)
        pacientes_seleccionados = random.sample(pacientes, num_citas)
        
        for hora, paciente in zip(horarios_seleccionados, pacientes_seleccionados):
            estado = random.choice([
                EstadoCitaChoices.DISPONIBLE,
                EstadoCitaChoices.OCUPADO,
                EstadoCitaChoices.ATENDIDO if day_offset < 2 else EstadoCitaChoices.OCUPADO
            ])
            
            citas_data.append({
                'paciente': paciente,
                'fecha': fecha_cita,
                'hora_cita': hora,
                'estado': estado,
                'observaciones': f'Cita programada para {paciente.nombre_completo}'
            })
    
    for data in citas_data:
        try:
            CitaMedica.objects.get_or_create(
                paciente=data['paciente'],
                fecha=data['fecha'],
                hora_cita=data['hora_cita'],
                defaults={
                    'estado': data['estado'],
                    'observaciones': data['observaciones']
                }
            )
        except:
            # Skip si hay conflicto de horarios
            continue
    
    print(f"✅ Creadas {len(citas_data)} citas médicas")

def crear_atenciones():
    """Crear atenciones médicas"""
    print("🩺 Creando atenciones médicas...")
    
    pacientes = list(Paciente.objects.all())
    diagnosticos = list(Diagnostico.objects.all())
    
    # Crear atenciones de los últimos 30 días
    base_datetime = timezone.now()
    
    atenciones_data = [
        {
            'paciente': pacientes[0],  # José Antonio
            'dias_atras': 5,
            'motivo': 'Control de presión arterial y renovación de receta',
            'sintomas': 'Paciente asintomático, acude para control rutinario',
            'tratamiento': 'Continuar con Losartán 50mg c/12h. Control en 3 meses',
            'presion_arterial': '140/85',
            'pulso': 78,
            'peso': Decimal('78.5'),
            'altura': Decimal('1.72'),
            'diagnosticos': ['I10']  # Hipertensión
        },
        {
            'paciente': pacientes[1],  # María Elena
            'dias_atras': 3,
            'motivo': 'Dolor abdominal y náuseas',
            'sintomas': 'Dolor epigástrico, náuseas ocasionales, acidez',
            'tratamiento': 'Omeprazol 20mg en ayunas x 14 días. Dieta blanda',
            'presion_arterial': '110/70',
            'pulso': 82,
            'temperatura': Decimal('36.8'),
            'peso': Decimal('58.2'),
            'altura': Decimal('1.62'),
            'diagnosticos': ['K21.9']  # ERGE
        },
        {
            'paciente': pacientes[2],  # Carlos Andrés
            'dias_atras': 10,
            'motivo': 'Dolor de cabeza recurrente',
            'sintomas': 'Cefalea frontal, intensidad moderada, relacionada con estrés',
            'tratamiento': 'Paracetamol 500mg c/8h PRN, técnicas de relajación',
            'presion_arterial': '125/80',
            'pulso': 75,
            'peso': Decimal('72.0'),
            'altura': Decimal('1.75'),
            'diagnosticos': ['R51']  # Cefalea
        },
        {
            'paciente': pacientes[3],  # Ana Sofía
            'dias_atras': 7,
            'motivo': 'Control ginecológico rutinario',
            'sintomas': 'Asintomática, acude para control anual',
            'tratamiento': 'Continuar con anticonceptivos orales, control en 6 meses',
            'presion_arterial': '105/65',
            'pulso': 68,
            'peso': Decimal('55.8'),
            'altura': Decimal('1.58'),
            'diagnosticos': []  # Sin diagnóstico patológico
        },
        {
            'paciente': pacientes[4],  # Roberto Miguel
            'dias_atras': 2,
            'motivo': 'Control de diabetes y dislipidemia',
            'sintomas': 'Paciente con buen control metabólico',
            'tratamiento': 'Continuar Metformina y Atorvastatina. Laboratorios en 3 meses',
            'presion_arterial': '135/82',
            'pulso': 80,
            'peso': Decimal('85.2'),
            'altura': Decimal('1.68'),
            'diagnosticos': ['E11.9']  # Diabetes tipo 2
        },
        {
            'paciente': pacientes[5],  # Lucía (menor)
            'dias_atras': 15,
            'motivo': 'Consulta por fiebre y malestar general',
            'sintomas': 'Fiebre de 38.5°C, malestar general, congestión nasal',
            'tratamiento': 'Paracetamol según peso, abundantes líquidos, reposo',
            'temperatura': Decimal('38.5'),
            'pulso': 110,
            'peso': Decimal('35.0'),
            'altura': Decimal('1.42'),
            'diagnosticos': ['J00']  # Resfriado común
        },
    ]
    
    for data in atenciones_data:
        fecha_atencion = base_datetime - timedelta(days=data['dias_atras'])
        
        atencion = Atencion.objects.create(
            paciente=data['paciente'],
            fecha_atencion=fecha_atencion,
            motivo_consulta=data['motivo'],
            sintomas=data['sintomas'],
            tratamiento=data['tratamiento'],
            presion_arterial=data.get('presion_arterial'),
            pulso=data.get('pulso'),
            temperatura=data.get('temperatura'),
            peso=data.get('peso'),
            altura=data.get('altura'),
            examen_fisico='Examen físico dentro de parámetros normales',
            comentario_adicional='Paciente colaborador, comprende indicaciones'
        )
        
        # Agregar diagnósticos
        for codigo_diag in data.get('diagnosticos', []):
            diagnostico = Diagnostico.objects.filter(codigo=codigo_diag).first()
            if diagnostico:
                atencion.diagnostico.add(diagnostico)
    
    print(f"✅ Creadas {len(atenciones_data)} atenciones médicas")

def crear_detalles_atencion():
    """Crear detalles de atención (medicamentos prescritos)"""
    print("💊 Creando detalles de atención...")
    
    atenciones = list(Atencion.objects.all())
    medicamentos = list(Medicamento.objects.all())
    
    detalles_data = [
        # Para hipertensión (José Antonio)
        {
            'atencion_index': 0,
            'medicamento_nombre': 'Losartán',
            'cantidad': 30,
            'prescripcion': 'Tomar 1 tableta cada 12 horas, preferiblemente a la misma hora',
            'duracion': 30,
            'frecuencia': 2
        },
        # Para ERGE (María Elena)
        {
            'atencion_index': 1,
            'medicamento_nombre': 'Paracetamol',  # Usamos uno disponible
            'cantidad': 14,
            'prescripcion': 'Tomar 1 cápsula en ayunas por 14 días',
            'duracion': 14,
            'frecuencia': 1
        },
        # Para cefalea (Carlos Andrés)
        {
            'atencion_index': 2,
            'medicamento_nombre': 'Paracetamol',
            'cantidad': 10,
            'prescripcion': 'Tomar 1 tableta cada 8 horas solo si hay dolor',
            'duracion': 5,
            'frecuencia': 3
        },
        # Para resfriado (Lucía)
        {
            'atencion_index': 5,
            'medicamento_nombre': 'Paracetamol',
            'cantidad': 7,
            'prescripcion': 'Tomar según peso corporal cada 6 horas si hay fiebre',
            'duracion': 7,
            'frecuencia': 4
        },
        # Para diabetes (Roberto Miguel)
        {
            'atencion_index': 4,
            'medicamento_nombre': 'Metformina',
            'cantidad': 60,
            'prescripcion': 'Tomar 1 tableta cada 12 horas con las comidas',
            'duracion': 30,
            'frecuencia': 2
        },
    ]
    
    for data in detalles_data:
        if data['atencion_index'] < len(atenciones):
            atencion = atenciones[data['atencion_index']]
            medicamento = Medicamento.objects.filter(nombre=data['medicamento_nombre']).first()
            
            if medicamento:
                DetalleAtencion.objects.get_or_create(
                    atencion=atencion,
                    medicamento=medicamento,
                    defaults={
                        'cantidad': data['cantidad'],
                        'prescripcion': data['prescripcion'],
                        'duracion_tratamiento': data['duracion'],
                        'frecuencia_diaria': data['frecuencia']
                    }
                )
    
    print(f"✅ Creados {len(detalles_data)} detalles de atención")

def crear_pagos():
    """Crear pagos de ejemplo"""
    print("💳 Creando pagos...")
    
    atenciones = list(Atencion.objects.all())
    servicios = list(ServiciosAdicionales.objects.all())
    
    pagos_data = []
    
    for i, atencion in enumerate(atenciones):
        # Determinar método de pago aleatorio
        metodo = random.choice([
            MetodoPagoChoices.EFECTIVO,
            MetodoPagoChoices.TARJETA,
            MetodoPagoChoices.TRANSFERENCIA
        ])
        
        # Estado del pago
        estado = EstadoPagoChoices.PAGADO if i < 4 else EstadoPagoChoices.PENDIENTE
        
        # Monto base de consulta
        servicio_consulta = ServiciosAdicionales.objects.filter(
            nombre_servicio__icontains='Consulta'
        ).first()
        
        monto = servicio_consulta.costo_servicio if servicio_consulta else Decimal('25.00')
        
        # Crear pago
        pago = Pago.objects.create(
            atencion=atencion,
            metodo_pago=metodo,
            monto_total=monto,
            estado=estado,
            fecha_pago=atencion.fecha_atencion if estado == EstadoPagoChoices.PAGADO else None,
            nombre_pagador=atencion.paciente.nombre_completo,
            observaciones=f'Pago por consulta médica - {atencion.paciente.nombre_completo}'
        )
        
        pagos_data.append(pago)
    
    print(f"✅ Creados {len(pagos_data)} pagos")

def crear_detalles_pago():
    """Crear detalles de pago"""
    print("🧾 Creando detalles de pago...")
    
    pagos = list(Pago.objects.all())
    servicios = list(ServiciosAdicionales.objects.all())
    
    for i, pago in enumerate(pagos):
        # Servicio principal (consulta)
        if i % 3 == 0:  # Consulta general
            servicio = ServiciosAdicionales.objects.filter(
                nombre_servicio='Consulta Médica General'
            ).first()
        else:  # Consulta especializada
            servicio = ServiciosAdicionales.objects.filter(
                nombre_servicio='Consulta Especializada'
            ).first()
        
        if servicio:
            DetallePago.objects.create(
                pago=pago,
                servicio_adicional=servicio,
                cantidad=1,
                precio_unitario=servicio.costo_servicio,
                descuento_porcentaje=Decimal('0.00'),
                aplica_seguro=False
            )
        
        # Agregar servicios adicionales ocasionalmente
        if i % 4 == 0:  # 25% de las veces
            servicio_adicional = random.choice([
                'Electrocardiograma',
                'Laboratorio Básico',
                'Control de Presión'
            ])
            
            servicio = ServiciosAdicionales.objects.filter(
                nombre_servicio=servicio_adicional
            ).first()
            
            if servicio:
                DetallePago.objects.create(
                    pago=pago,
                    servicio_adicional=servicio,
                    cantidad=1,
                    precio_unitario=servicio.costo_servicio,
                    descuento_porcentaje=Decimal('0.00'),
                    aplica_seguro=False
                )
        
        # Recalcular total del pago
        from django.db.models import Sum
        total = pago.detalles.aggregate(
            total=Sum('subtotal')
        )['total'] or Decimal('0.00')
        
        pago.monto_total = total
        pago.save()
    
    print("✅ Creados detalles de pago y actualizados totales")

def main():
    """Función principal que ejecuta todo el proceso"""
    print("🚀 Iniciando creación de datos completos del sistema...")
    print("=" * 60)
    
    try:
        # Limpiar datos existentes
        limpiar_datos()
        
        # Crear datos base
        crear_tipos_sangre()
        crear_especialidades()
        crear_cargos()
        crear_tipos_medicamentos()
        crear_marcas_medicamentos()
        crear_medicamentos()
        crear_diagnosticos()
        crear_tipos_gastos()
        
        # Crear personas
        crear_doctores()
        crear_empleados()
        crear_pacientes()
        
        # Crear datos operativos
        crear_gastos_mensuales()
        crear_horarios_atencion()
        crear_servicios_adicionales()
        
        # Crear datos médicos
        crear_citas_medicas()
        crear_atenciones()
        crear_detalles_atencion()
        crear_pagos()
        crear_detalles_pago()
        
        print("=" * 60)
        print("🎉 ¡PROCESO COMPLETADO EXITOSAMENTE!")
        print()
        print("📊 RESUMEN DE DATOS CREADOS:")
        print(f"   • Pacientes: {Paciente.objects.count()}")
        print(f"   • Doctores: {Doctor.objects.count()}")
        print(f"   • Empleados: {Empleado.objects.count()}")
        print(f"   • Medicamentos: {Medicamento.objects.count()}")
        print(f"   • Diagnósticos: {Diagnostico.objects.count()}")
        print(f"   • Servicios: {ServiciosAdicionales.objects.count()}")
        print(f"   • Citas médicas: {CitaMedica.objects.count()}")
        print(f"   • Atenciones: {Atencion.objects.count()}")
        print(f"   • Pagos: {Pago.objects.count()}")
        print(f"   • Gastos mensuales: {GastoMensual.objects.count()}")
        print()
        print("🌟 El sistema ahora tiene datos realistas para pruebas")
        print("🚀 Puede ejecutar: python manage.py runserver")
        print("🌐 Y navegar a los módulos para ver los datos")
        
    except Exception as e:
        print(f"❌ Error durante la ejecución: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    main()
