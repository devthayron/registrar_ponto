document.addEventListener('DOMContentLoaded', function () {
    const cpfInput = document.getElementById('cpf');
    const form = document.getElementById('pontoForm');

    cpfInput.addEventListener('input', function () {
      const value = cpfInput.value;

      // Verifica se bate com o pattern (CPF completo com pontos e traço)
      const cpfPattern = /^\d{3}\.\d{3}\.\d{3}-\d{2}$/;

      if (cpfPattern.test(value)) {
        // Aguarda levemente para garantir que o preenchimento esteja concluído
        setTimeout(() => {
          form.submit();
        }, 200);
      }
    });
  });