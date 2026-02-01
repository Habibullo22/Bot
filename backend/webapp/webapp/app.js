const tg = window.Telegram.WebApp;
tg.ready();

const user = tg.initDataUnsafe?.user;
const userId = user?.id;

document.getElementById("user").textContent = user?.username ? `@${user.username}` : "Telegram user";

async function loadBalance() {
  if (!userId) return;

  const res = await fetch(`/api/balance/${userId}`);
  const data = await res.json();

  document.getElementById("b_usdt").textContent = data.usdt ?? 0;
  document.getElementById("b_rub").textContent  = data.rub ?? 0;
  document.getElementById("b_uzs").textContent  = data.uzs ?? 0;
}

document.getElementById("btnDeposit").onclick = async () => {
  if (!userId) return tg.showAlert("User topilmadi");

  // oddiy deposit so'rov (keyin to'lov tizimi qo'shamiz)
  const currency = prompt("Valyuta: usdt / rub / uzs", "usdt");
  const amountStr = prompt("Miqdor:", "10");
  const amount = Number(amountStr);

  if (!currency || !amount || amount <= 0) return;

  const res = await fetch(`/api/deposit/request?user_id=${userId}&currency=${currency}&amount=${amount}`, { method: "POST" });
  if (res.ok) tg.showAlert("✅ So‘rov yuborildi. Admin tekshiradi.");
  else tg.showAlert("❌ Xatolik. Qayta urinib ko‘ring.");
};

document.getElementById("btnHistory").onclick = () => {
  tg.showAlert("Tarix keyin qo‘shiladi ✅");
};

loadBalance();
