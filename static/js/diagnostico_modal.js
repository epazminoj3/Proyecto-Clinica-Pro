// Script de diagnóstico para el modal de medicamentos
console.log('🔍 DIAGNÓSTICO MODAL MEDICAMENTOS - INICIANDO');

// Función para verificar elementos
function verificarElementos() {
    console.log('📋 VERIFICANDO ELEMENTOS...');
    
    // 1. Verificar que el botón existe
    const boton = document.querySelector('button[onclick="mostrarModalMedicamento()"]');
    console.log('🔘 Botón "Nuevo Medicamento":', boton ? '✅ ENCONTRADO' : '❌ NO ENCONTRADO');
    
    if (boton) {
        console.log('   - Texto del botón:', boton.innerText);
        console.log('   - Función onclick:', boton.getAttribute('onclick'));
        console.log('   - Clases CSS:', boton.className);
    }
    
    // 2. Verificar que el modal existe
    const modal = document.getElementById('modal-medicamento');
    console.log('🔘 Modal #modal-medicamento:', modal ? '✅ ENCONTRADO' : '❌ NO ENCONTRADO');
    
    if (modal) {
        console.log('   - Clases CSS:', modal.className);
        console.log('   - Display actual:', window.getComputedStyle(modal).display);
        console.log('   - Visibility:', window.getComputedStyle(modal).visibility);
        console.log('   - Z-index:', window.getComputedStyle(modal).zIndex);
    }
    
    // 3. Verificar el formulario
    const form = document.getElementById('form-medicamento');
    console.log('🔘 Formulario #form-medicamento:', form ? '✅ ENCONTRADO' : '❌ NO ENCONTRADO');
    
    // 4. Verificar funciones JavaScript
    console.log('🔘 Función mostrarModalMedicamento:', typeof mostrarModalMedicamento === 'function' ? '✅ DISPONIBLE' : '❌ NO DISPONIBLE');
    console.log('🔘 Función cerrarModalMedicamento:', typeof cerrarModalMedicamento === 'function' ? '✅ DISPONIBLE' : '❌ NO DISPONIBLE');
    
    // 5. Verificar contexto de Django
    console.log('🔘 Contexto tipos_medicamento:', typeof tipos_medicamento !== 'undefined' ? '✅ DISPONIBLE' : '❌ NO DISPONIBLE');
    console.log('🔘 Contexto marcas_medicamento:', typeof marcas_medicamento !== 'undefined' ? '✅ DISPONIBLE' : '❌ NO DISPONIBLE');
    console.log('🔘 Contexto vias_administracion:', typeof vias_administracion !== 'undefined' ? '✅ DISPONIBLE' : '❌ NO DISPONIBLE');
}

// Función para probar el modal
function probarModal() {
    console.log('🧪 PROBANDO MODAL...');
    
    try {
        // Intentar mostrar el modal
        console.log('🔍 Intentando mostrar modal...');
        mostrarModalMedicamento();
        
        // Verificar que se mostró
        setTimeout(() => {
            const modal = document.getElementById('modal-medicamento');
            if (modal) {
                const isVisible = !modal.classList.contains('hidden');
                const computedDisplay = window.getComputedStyle(modal).display;
                
                console.log('📊 Estado después de mostrar:');
                console.log('   - Clase "hidden" removida:', isVisible ? '✅ SÍ' : '❌ NO');
                console.log('   - Display computado:', computedDisplay);
                console.log('   - Overflow del body:', document.body.style.overflow);
                
                if (isVisible) {
                    console.log('✅ MODAL SE MOSTRÓ CORRECTAMENTE');
                    
                    // Intentar cerrar después de 2 segundos
                    setTimeout(() => {
                        console.log('🔍 Intentando cerrar modal...');
                        cerrarModalMedicamento();
                        
                        setTimeout(() => {
                            const isHidden = modal.classList.contains('hidden');
                            console.log('📊 Estado después de cerrar:');
                            console.log('   - Clase "hidden" agregada:', isHidden ? '✅ SÍ' : '❌ NO');
                            console.log('   - Overflow del body:', document.body.style.overflow);
                            
                            if (isHidden) {
                                console.log('✅ MODAL SE CERRÓ CORRECTAMENTE');
                            } else {
                                console.log('❌ MODAL NO SE CERRÓ CORRECTAMENTE');
                            }
                        }, 100);
                    }, 2000);
                    
                } else {
                    console.log('❌ MODAL NO SE MOSTRÓ CORRECTAMENTE');
                }
            }
        }, 100);
        
    } catch (error) {
        console.error('❌ ERROR AL PROBAR MODAL:', error);
    }
}

// Función para buscar posibles conflictos
function buscarConflictos() {
    console.log('🔍 BUSCANDO POSIBLES CONFLICTOS...');
    
    // Buscar otros elementos con ID similar
    const elementosModal = document.querySelectorAll('[id*="modal"]');
    console.log('🔘 Elementos con ID que contiene "modal":', elementosModal.length);
    elementosModal.forEach((el, index) => {
        console.log(`   ${index + 1}. ${el.id} - ${el.tagName}`);
    });
    
    // Buscar estilos CSS que puedan interferir
    const modal = document.getElementById('modal-medicamento');
    if (modal) {
        const computedStyle = window.getComputedStyle(modal);
        console.log('🔘 Estilos computados del modal:');
        console.log('   - Position:', computedStyle.position);
        console.log('   - Display:', computedStyle.display);
        console.log('   - Visibility:', computedStyle.visibility);
        console.log('   - Z-index:', computedStyle.zIndex);
        console.log('   - Opacity:', computedStyle.opacity);
    }
    
    // Verificar errores en consola
    console.log('🔘 Revisar consola para errores JavaScript adicionales');
}

// Función principal de diagnóstico
function diagnosticarModal() {
    console.log('🚀 INICIANDO DIAGNÓSTICO COMPLETO...');
    console.log('================================================');
    
    verificarElementos();
    console.log('================================================');
    
    buscarConflictos();
    console.log('================================================');
    
    // Esperar un poco antes de probar
    setTimeout(() => {
        probarModal();
    }, 1000);
}

// Exportar funciones al window para uso manual
window.diagnosticarModal = diagnosticarModal;
window.verificarElementos = verificarElementos;
window.probarModal = probarModal;
window.buscarConflictos = buscarConflictos;

// Ejecutar diagnóstico cuando se cargue el DOM
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', diagnosticarModal);
} else {
    diagnosticarModal();
}

console.log('📋 FUNCIONES DISPONIBLES EN CONSOLA:');
console.log('   - diagnosticarModal(): Ejecuta diagnóstico completo');
console.log('   - verificarElementos(): Verifica elementos del DOM');
console.log('   - probarModal(): Prueba abrir y cerrar el modal');
console.log('   - buscarConflictos(): Busca posibles conflictos CSS/JS');
