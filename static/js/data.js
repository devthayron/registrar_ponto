//Script para preencher data e hora automaticamente 

  window.addEventListener('DOMContentLoaded', () => {
    const dataInput = document.getElementById('data');
    const horaInput = document.getElementById('hora');

    const agora = new Date();
    
    const ano = agora.getFullYear();
    const mes = String(agora.getMonth() + 1).padStart(2, '0');
    const dia = String(agora.getDate()).padStart(2, '0');

    const horas = String(agora.getHours()).padStart(2, '0');
    const minutos = String(agora.getMinutes()).padStart(2, '0');

    dataInput.value = `${ano}-${mes}-${dia}`;
    horaInput.value = `${horas}:${minutos}`;

    // Garante que o cursor esteja no CPF
    document.getElementById('cpf').focus();
  });