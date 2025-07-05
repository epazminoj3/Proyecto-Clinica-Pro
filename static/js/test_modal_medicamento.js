// Script de prueba directo para el modal de medicamentos
console.log('🚀 SCRIPT DE PRUEBA MODAL MEDICAMENTOS');

// Verificar elementos cuando carga la página
document.addEventListener('DOMContentLoaded', function() {
    console.log('📋 VERIFICANDO ELEMENTOS...');
    
    // 1. Verificar el botón
    const boton = document.querySelector('button[onclick="mostrarModalMedicamento()"]');
    console.log('🔘 Botón encontrado:', boton ? '✅ SÍ' : '❌ NO');
    if (boton) {
        console.log('   - Texto:', boton.textContent.trim());
        console.log('   - Visible:', window.getComputedStyle(boton).display !== 'none');
    }
    
    // 2. Verificar el modal
    const modal = document.getElementById('modal-medicamento');
    console.log('🔘 Modal encontrado:', modal ? '✅ SÍ' : '❌ NO');
    if (modal) {
        console.log('   - Clases CSS:', modal.className);
        console.log('   - Está oculto:', modal.classList.contains('hidden'));
    }
    
    // 3. Verificar la función
    console.log('🔘 Función disponible:', typeof mostrarModalMedicamento === 'function' ? '✅ SÍ' : '❌ NO');
    
    // 4. Agregar event listener manual al botón como respaldo
    if (boton) {
        boton.addEventListener('click', function(e) {
            console.log('🎯 CLICK EN BOTÓN DETECTADO');
            e.preventDefault();
            
            // Intentar mostrar modal manualmente
            const modal = document.getElementById('modal-medicamento');
            if (modal) {
                console.log('📂 Modal encontrado, intentando mostrar...');
                modal.classList.remove('hidden');
                modal.style.display = 'block';
                modal.style.position = 'fixed';
                modal.style.top = '0';
                modal.style.left = '0';
                modal.style.width = '100%';
                modal.style.height = '100%';
                modal.style.zIndex = '9999';
                document.body.style.overflow = 'hidden';
                console.log('✅ Modal mostrado manualmente');
            } else {
                console.log('❌ Modal no encontrado');
            }
        });
        console.log('🔗 Event listener agregado al botón');
    }
});

// Función de prueba global
window.testModal = function() {
    console.log('🧪 PROBANDO MODAL MANUALMENTE...');
    const modal = document.getElementById('modal-medicamento');
    if (modal) {
        modal.classList.remove('hidden');
        modal.style.display = 'block';
        modal.style.zIndex = '10000';
        document.body.style.overflow = 'hidden';
        console.log('✅ Modal mostrado con testModal()');
    } else {
        console.log('❌ Modal no encontrado con testModal()');
    }
};

window.closeTestModal = function() {
    console.log('🔒 CERRANDO MODAL...');
    const modal = document.getElementById('modal-medicamento');
    if (modal) {
        modal.classList.add('hidden');
        modal.style.display = 'none';
        document.body.style.overflow = 'auto';
        console.log('✅ Modal cerrado');
    }
};

console.log('📋 FUNCIONES DISPONIBLES:');
console.log('   - testModal() : Mostrar modal manualmente');
console.log('   - closeTestModal() : Cerrar modal');
console.log('   - mostrarModalMedicamento() : Función original');
