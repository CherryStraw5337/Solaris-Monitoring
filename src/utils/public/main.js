// Observador que detecta cuando el elemento entra en pantalla
const observer = new IntersectionObserver((entries) => {
    entries.forEach(entry => {
        if (entry.isIntersecting) {
            // Le agregamos la clase 'visible' para detonar el CSS
            entry.target.classList.add('visible');
        }
    });
}, { threshold: 0.3 }); // Se activa cuando el 30% de la tarjeta es visible

// Le decimos al observador que vigile nuestra tarjeta de cristal
observer.observe(document.getElementById('info-card'));