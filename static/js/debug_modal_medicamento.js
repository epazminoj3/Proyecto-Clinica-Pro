// Script de debug para modal de medicamentos
console.log('🔍 Script de debug cargado');

// Función para debuggear el modal
function debugModalMedicamento() {
    console.log('=== DEBUG MODAL MEDICAMENTO ===');
    
    // 1. Verificar que el modal existe
    const modal = document.getElementById('modal-medicamento');
    console.log('Modal encontrado:', modal);
    if (modal) {
        console.log('Clases del modal:', modal.className);
        console.log('Estilo computed:', window.getComputedStyle(modal).display);
    }
    
    // 2. Verificar que la función existe
    console.log('Función mostrarModalMedicamento:', typeof mostrarModalMedicamento);
    console.log('Función global:', typeof window.mostrarModalMedicamento);
    
    // 3. Verificar el botón
    const boton = document.querySelector('button[onclick="mostrarModalMedicamento()"]');
    console.log('Botón encontrado:', boton);
    if (boton) {
        console.log('Onclick del botón:', boton.getAttribute('onclick'));
    }
    
    // 4. Intentar mostrar el modal directamente
    if (modal) {
        console.log('Intentando mostrar modal directamente...');
        modal.classList.remove('hidden');
        document.body.style.overflow = 'hidden';
        console.log('Modal mostrado. Clases actuales:', modal.className);
        
        // Ocultar después de 3 segundos
        setTimeout(() => {
            modal.classList.add('hidden');
            document.body.style.overflow = 'auto';
            console.log('Modal ocultado automáticamente');
        }, 3000);
    }
    
    console.log('=== FIN DEBUG ===');
}

// Hacer disponible globalmente
window.debugModalMedicamento = debugModalMedicamento;

// Ejecutar debug cuando se cargue el DOM
document.addEventListener('DOMContentLoaded', function() {
    console.log('DOM cargado, ejecutando debug...');
    debugModalMedicamento();
});
