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
const pontoForm = document.getElementById("pontoForm");
if (pontoForm) {
  pontoForm.addEventListener("submit", function (e) {
    const cpfInput = document.getElementById("cpf");
    const mensagem = document.getElementById("mensagem");
    const cpf = cpfInput.value.trim();
    const cpfNumerico = cpf.replace(/\D/g, "");

    if (cpfNumerico.length !== 11) {
      e.preventDefault();
      mensagem.textContent = "CPF inválido. Tente novamente.";
      mensagem.className = "mensagem erro";
    } else {
      mensagem.textContent = "";
      mensagem.className = "";
    }
  });
}

// Eventos dos botões (fora do submit)
document.getElementById("btnFiltrar")?.addEventListener("click", () => {
  alert("Função de filtro ainda não implementada (somente front)");
});

document.getElementById("btnExportar")?.addEventListener("click", () => {
  alert("Exportação para Excel será implementada no backend ou com libs JS.");
});

// Popup "Esqueceu a senha?"
const forgotLink = document.getElementById("forgot-password-link");
const popup = document.getElementById("popup");
const closeBtn = document.querySelector(".close-btn");

if (forgotLink && popup && closeBtn) {
  forgotLink.addEventListener("click", function (e) {
    e.preventDefault();
    popup.style.display = "flex";
  });

  closeBtn.addEventListener("click", function () {
    popup.style.display = "none";
  });
}
