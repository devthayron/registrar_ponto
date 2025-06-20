// Atualiza o relógio a cada segundo
function atualizarRelogio() {
  const agora = new Date();
  const horas = agora.toLocaleTimeString("pt-BR", { hour12: false });
  const data = agora.toLocaleDateString("pt-BR");
  document.getElementById("relogio").textContent = `${data} - ${horas}`;
}
setInterval(atualizarRelogio, 1000);
atualizarRelogio();

// Validação simples do CPF no submit do formulário
document.getElementById("pontoForm").addEventListener("submit", function (e) {
  const cpfInput = document.getElementById("cpf");
  const mensagem = document.getElementById("mensagem");
  const cpf = cpfInput.value.trim();

  const cpfNumerico = cpf.replace(/\D/g, "");

  if (cpfNumerico.length !== 11) {
    e.preventDefault(); // bloqueia o envio só se CPF inválido
    mensagem.textContent = "CPF inválido. Tente novamente.";
    mensagem.className = "mensagem erro";
  } else {
    // CPF válido, limpa mensagem para deixar o formulário enviar
    mensagem.textContent = "";
    mensagem.className = "";
  }
});

// Eventos dos botões (fora do submit)
document.getElementById("btnFiltrar")?.addEventListener("click", () => {
  alert("Função de filtro ainda não implementada (somente front)");
});

document.getElementById("btnExportar")?.addEventListener("click", () => {
  alert("Exportação para Excel será implementada no backend ou com libs JS.");
});
