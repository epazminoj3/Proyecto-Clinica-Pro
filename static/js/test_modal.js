// Script para probar el modal de medicamentos
console.log('🚀 Iniciando prueba del modal...');

// Esperar a que cargue el DOM
document.addEventListener('DOMContentLoaded', function() {
    console.log('✅ DOM cargado');
    
    // Verificar elementos
    const btnNuevoMedicamento = document.getElementById('btn-nuevo-medicamento');
    const modal = document.getElementById('modal-medicamento-simple');
    const closeBtn = document.getElementById('close-modal-medicamento-simple');
    const cancelBtn = document.getElementById('cancel-medicamento-simple');
    
    console.log('Elementos encontrados:');
    console.log('- Botón Nuevo Medicamento:', btnNuevoMedicamento ? '✅' : '❌');
    console.log('- Modal Simple:', modal ? '✅' : '❌');
    console.log('- Botón Cerrar:', closeBtn ? '✅' : '❌');
    console.log('- Botón Cancelar:', cancelBtn ? '✅' : '❌');
    
    // Probar función global
    setTimeout(() => {
        console.log('🔍 Probando función global...');
        if (typeof mostrarModalMedicamentoSimple === 'function') {
            console.log('✅ Función mostrarModalMedicamentoSimple disponible');
        } else {
            console.log('❌ Función mostrarModalMedicamentoSimple NO disponible');
        }
        
        if (typeof cerrarModalMedicamentoSimple === 'function') {
            console.log('✅ Función cerrarModalMedicamentoSimple disponible');
        } else {
            console.log('❌ Función cerrarModalMedicamentoSimple NO disponible');
        }
    }, 1000);
    
    // Agregar listener de prueba al botón
    if (btnNuevoMedicamento) {
        btnNuevoMedicamento.addEventListener('click', function() {
            console.log('🎯 Botón clickeado - evento capturado');
        });
    }
});

// Función de prueba manual
window.testModal = function() {
    console.log('🧪 Prueba manual del modal...');
    const modal = document.getElementById('modal-medicamento-simple');
    if (modal) {
        modal.style.display = 'flex';
        modal.style.zIndex = '10000';
        document.body.style.overflow = 'hidden';
        console.log('✅ Modal mostrado manualmente');
    } else {
        console.error('❌ Modal no encontrado');
    }
};

window.testCloseModal = function() {
    console.log('🧪 Cerrando modal manualmente...');
    const modal = document.getElementById('modal-medicamento-simple');
    if (modal) {
        modal.style.display = 'none';
        document.body.style.overflow = 'auto';
        console.log('✅ Modal cerrado manualmente');
    } else {
        console.error('❌ Modal no encontrado');
    }
};

console.log('📋 Funciones de prueba disponibles:');
console.log('- testModal(): Mostrar modal manualmente');
console.log('- testCloseModal(): Cerrar modal manualmente');
