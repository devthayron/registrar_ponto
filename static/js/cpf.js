const cpfInput = document.getElementById('cpf');

if (cpfInput) {
  cpfInput.addEventListener('input', function (e) {
    let value = e.target.value;

    // Limita a 14 caracteres (formato: 000.000.000-00)
    value = value.substring(0, 14);

    // Remove qualquer caractere inválido (exceto números, ponto e traço)
    value = value.replace(/[^\d.-]/g, '');

    // Aplica a máscara apenas se necessário
    // Remove pontos e traços para aplicar corretamente a máscara
    let numericValue = value.replace(/\D/g, '');

    if (numericValue.length > 9) {
      value = numericValue.replace(/^(\d{3})(\d{3})(\d{3})(\d{0,2}).*/, '$1.$2.$3-$4');
    } else if (numericValue.length > 6) {
      value = numericValue.replace(/^(\d{3})(\d{3})(\d{0,3}).*/, '$1.$2.$3');
    } else if (numericValue.length > 3) {
      value = numericValue.replace(/^(\d{3})(\d{0,3}).*/, '$1.$2');
    } else {
      value = numericValue;
    }

    e.target.value = value;

    // ❌ Aqui NÃO deve submeter automaticamente
  });
}


  // Se quiser ocultar mensagens (se você tiver mensagens no template)
  window.addEventListener('DOMContentLoaded', function () {
    const mensagens = document.querySelectorAll('.messages p');

    mensagens.forEach((msg) => {
      const isErro = msg.classList.contains('erro');
      const tempo = isErro ? 3000 : 1000;

      setTimeout(() => {
        msg.style.display = 'none';
      }, tempo);
    });
  });
