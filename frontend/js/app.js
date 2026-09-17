// ---------- Utilities ----------
function fmt(amount) {
  const n = Number(amount || 0);
  const sign = n < 0 ? "-" : "";
  return `${sign}Rs. ${Math.abs(n).toLocaleString("en-LK", { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;
}

function todayISO() {
  return new Date().toISOString().slice(0, 10);
}

function showToast(message, isError = false) {
  const toast = document.getElementById("toast");
  toast.textContent = message;
  toast.classList.toggle("error", isError);
  toast.classList.add("show");
  clearTimeout(showToast._t);
  showToast._t = setTimeout(() => toast.classList.remove("show"), 2600);
}

// ---------- Cache of reference data (for populating <select>s) ----------
let cache = { accounts: [], cards: [], goals: [] };

async function refreshReferenceData() {
  const [accounts, cards, goals] = await Promise.all([
    api.get("/accounts"),
    api.get("/credit-cards"),
    api.get("/savings-goals"),
  ]);
  cache.accounts = accounts;
  cache.cards = cards;
  cache.goals = goals;
  fillAllSelects();
}

function fillAllSelects() {
  document.querySelectorAll('[data-fill="accounts"]').forEach((el) => {
    const current = el.value;
    el.innerHTML = cache.accounts
      .map((a) => `<option value="${a.id}">${a.name} (${a.type}) — ${fmt(a.balance)}</option>`)
      .join("");
    if (current) el.value = current;
  });

  document.querySelectorAll('[data-fill="cards"]').forEach((el) => {
    el.innerHTML = cache.cards
      .map((c) => `<option value="${c.id}">${c.card_name} — owed ${fmt(c.current_balance)}</option>`)
      .join("");
  });

  document.querySelectorAll('[data-fill="goals"]').forEach((el) => {
    el.innerHTML = cache.goals
      .map((g) => `<option value="${g.id}">${g.name}</option>`)
      .join("");
  });

  // "Paid with" combines accounts + credit cards for the expense form
  const source = document.querySelector('select[name="source"]');
  if (source) {
    const accOptions = cache.accounts.map((a) => `<option value="account:${a.id}">${a.name} (${a.type})</option>`);
    const cardOptions = cache.cards.map((c) => `<option value="card:${c.id}">${c.card_name} (credit card)</option>`);
    source.innerHTML = `<option value="">Select a source…</option>` + accOptions.join("") + cardOptions.join("");
  }
}

// ---------- Navigation ----------
function setupNav() {
  document.querySelectorAll(".nav-link").forEach((link) => {
    link.addEventListener("click", (e) => {
      e.preventDefault();
      const view = link.dataset.view;
      document.querySelectorAll(".nav-link").forEach((l) => l.classList.toggle("active", l === link));
      document.querySelectorAll(".view").forEach((v) => v.classList.toggle("active", v.id === `view-${view}`));
      loadView(view);
    });
  });
}

function loadView(view) {
  const loaders = {
    dashboard: loadDashboard,
    transactions: loadTransactions,
    accounts: loadAccounts,
    cards: loadCards,
    budgets: loadBudgets,
    savings: loadSavings,
    bills: loadBills,
  };
  loaders[view] && loaders[view]();
}

// ---------- Dashboard ----------
async function loadDashboard() {
  const d = await api.get("/dashboard");

  document.getElementById("stat-balance").textContent = fmt(d.current_balance);
  document.getElementById("stat-income").textContent = fmt(d.monthly_income);
  document.getElementById("stat-expenses").textContent = fmt(d.monthly_expenses);
  document.getElementById("stat-remaining-budget").textContent =
    d.remaining_budget === null ? "No budget set" : fmt(d.remaining_budget);
  document.getElementById("stat-cash").textContent = fmt(d.cash_balance);
  document.getElementById("stat-bank").textContent = fmt(d.bank_balance);
  document.getElementById("stat-savings").textContent = fmt(d.total_savings);
  document.getElementById("stat-debt").textContent = fmt(d.credit_card_debt);

  const warningsEl = document.getElementById("warnings");
  warningsEl.innerHTML = d.warnings.length
    ? d.warnings.map((w) => `<div class="warning-item ${w.level}">${w.level === "critical" ? "🚨" : "⚠️"} ${w.message}</div>`).join("")
    : "";

  const budgetsEl = document.getElementById("dash-budgets");
  budgetsEl.innerHTML = d.budget_status.length
    ? d.budget_status.map((b) => `
        <div>
          <div class="list-row">
            <span>${b.category}</span>
            <span class="amount">${fmt(b.spent)} / ${fmt(b.limit)}</span>
          </div>
          <div class="progress-track"><div class="progress-fill ${b.percent_used >= 100 ? "over" : ""}" style="width:${Math.min(b.percent_used, 100)}%"></div></div>
        </div>`).join("")
    : `<div class="empty-state">No budgets set yet.</div>`;

  const goalsEl = document.getElementById("dash-goals");
  goalsEl.innerHTML = d.savings_goals.length
    ? d.savings_goals.map((g) => `
        <div>
          <div class="list-row">
            <span>${g.name}</span>
            <span class="amount">${fmt(g.current_amount)} / ${fmt(g.target_amount)}</span>
          </div>
          <div class="progress-track"><div class="progress-fill" style="width:${Math.min(g.progress_percent, 100)}%"></div></div>
        </div>`).join("")
    : `<div class="empty-state">No savings goals yet.</div>`;

  const billsEl = document.getElementById("dash-bills");
  billsEl.innerHTML = d.upcoming_bills.length
    ? d.upcoming_bills.map((b) => `<div class="list-row"><span>${b.name} — due ${b.due_date}</span><span class="amount">${fmt(b.amount)}</span></div>`).join("")
    : `<div class="empty-state">Nothing due in the next 7 days.</div>`;
}

// ---------- Transactions ----------
async function loadTransactions() {
  await refreshReferenceData();
  const [income, expenses] = await Promise.all([api.get("/income"), api.get("/expenses")]);

  const rows = [
    ...income.map((i) => ({ ...i, kind: "Income" })),
    ...expenses.map((e) => ({ ...e, kind: "Expense" })),
  ].sort((a, b) => (a.date < b.date ? 1 : -1));

  const body = document.getElementById("txn-table-body");
  body.innerHTML = rows.length
    ? rows.map((r) => `
        <tr>
          <td>${r.date}</td>
          <td>${r.kind}</td>
          <td>${r.category}</td>
          <td>${r.description || ""}</td>
          <td class="amount ${r.kind.toLowerCase()}">${r.kind === "Expense" ? "-" : "+"}${fmt(r.amount)}</td>
          <td><button class="btn-small" data-del="${r.kind === "Income" ? "income" : "expenses"}:${r.id}">Delete</button></td>
        </tr>`).join("")
    : `<tr><td colspan="6" class="empty-state">No transactions yet.</td></tr>`;

  body.querySelectorAll("[data-del]").forEach((btn) => {
    btn.addEventListener("click", async () => {
      const [kind, id] = btn.dataset.del.split(":");
      try {
        await api.del(`/${kind}/${id}`);
        showToast("Transaction removed");
        loadTransactions();
        loadDashboard();
      } catch (err) {
        showToast(err.message, true);
      }
    });
  });
}

document.getElementById("form-income").addEventListener("submit", async (e) => {
  e.preventDefault();
  const fd = new FormData(e.target);
  try {
    await api.post("/income", {
      amount: parseFloat(fd.get("amount")),
      category: fd.get("category"),
      date: fd.get("date"),
      account_id: parseInt(fd.get("account_id")),
      description: fd.get("description") || null,
    });
    showToast("Income added");
    e.target.reset();
    e.target.querySelector('[name="date"]').value = todayISO();
    await refreshReferenceData();
    loadTransactions();
  } catch (err) { showToast(err.message, true); }
});

document.getElementById("form-expense").addEventListener("submit", async (e) => {
  e.preventDefault();
  const fd = new FormData(e.target);
  const [kind, id] = (fd.get("source") || "").split(":");
  if (!kind) { showToast("Choose a payment source", true); return; }
  const payload = {
    amount: parseFloat(fd.get("amount")),
    category: fd.get("category"),
    date: fd.get("date"),
    description: fd.get("description") || null,
    account_id: kind === "account" ? parseInt(id) : null,
    credit_card_id: kind === "card" ? parseInt(id) : null,
  };
  try {
    await api.post("/expenses", payload);
    showToast("Expense added");
    e.target.reset();
    e.target.querySelector('[name="date"]').value = todayISO();
    await refreshReferenceData();
    loadTransactions();
  } catch (err) { showToast(err.message, true); }
});

// ---------- Accounts ----------
async function loadAccounts() {
  await refreshReferenceData();
  const el = document.getElementById("accounts-list");
  el.innerHTML = cache.accounts.length
    ? cache.accounts.map((a) => `
        <div class="entity-card">
          <h3>${a.name}</h3>
          <div class="meta">${a.type === "bank" ? (a.bank_name || "Bank account") : "Cash"}</div>
          <div class="figure">${fmt(a.balance)}</div>
        </div>`).join("")
    : `<div class="empty-state">No accounts yet — add one to get started.</div>`;
}

document.getElementById("form-account").addEventListener("submit", async (e) => {
  e.preventDefault();
  const fd = new FormData(e.target);
  try {
    await api.post("/accounts", {
      name: fd.get("name"),
      type: fd.get("type"),
      bank_name: fd.get("bank_name") || null,
      balance: parseFloat(fd.get("balance") || 0),
    });
    showToast("Account added");
    e.target.reset();
    loadAccounts();
  } catch (err) { showToast(err.message, true); }
});

document.getElementById("form-transfer").addEventListener("submit", async (e) => {
  e.preventDefault();
  const fd = new FormData(e.target);
  try {
    await api.post("/transfers", {
      from_account_id: parseInt(fd.get("from_account_id")),
      to_account_id: parseInt(fd.get("to_account_id")),
      amount: parseFloat(fd.get("amount")),
      date: fd.get("date"),
    });
    showToast("Transfer complete");
    e.target.reset();
    e.target.querySelector('[name="date"]').value = todayISO();
    loadAccounts();
  } catch (err) { showToast(err.message, true); }
});

// ---------- Credit cards ----------
async function loadCards() {
  await refreshReferenceData();
  const el = document.getElementById("cards-list");
  el.innerHTML = cache.cards.length
    ? cache.cards.map((c) => `
        <div class="entity-card">
          <h3>${c.card_name}</h3>
          <div class="meta">${c.bank_name || ""} · Limit ${fmt(c.credit_limit)}</div>
          <div class="figure debt">${fmt(c.current_balance)} owed</div>
        </div>`).join("")
    : `<div class="empty-state">No credit cards yet.</div>`;
}

document.getElementById("form-card").addEventListener("submit", async (e) => {
  e.preventDefault();
  const fd = new FormData(e.target);
  try {
    await api.post("/credit-cards", {
      card_name: fd.get("card_name"),
      bank_name: fd.get("bank_name") || null,
      credit_limit: parseFloat(fd.get("credit_limit")),
      current_balance: parseFloat(fd.get("current_balance") || 0),
      billing_date: fd.get("billing_date") ? parseInt(fd.get("billing_date")) : null,
      due_date: fd.get("due_date") ? parseInt(fd.get("due_date")) : null,
      minimum_payment: parseFloat(fd.get("minimum_payment") || 0),
    });
    showToast("Card added");
    e.target.reset();
    loadCards();
  } catch (err) { showToast(err.message, true); }
});

document.getElementById("form-card-payment").addEventListener("submit", async (e) => {
  e.preventDefault();
  const fd = new FormData(e.target);
  try {
    await api.post("/credit-cards/pay", {
      credit_card_id: parseInt(fd.get("credit_card_id")),
      account_id: parseInt(fd.get("account_id")),
      amount: parseFloat(fd.get("amount")),
    });
    showToast("Payment recorded");
    e.target.reset();
    await refreshReferenceData();
    loadCards();
  } catch (err) { showToast(err.message, true); }
});

// ---------- Budgets ----------
async function loadBudgets() {
  const budgets = await api.get("/budgets");
  const el = document.getElementById("budgets-list");
  el.innerHTML = budgets.length
    ? budgets.map((b) => `
        <div class="list-row">
          <span>${b.category}</span>
          <span class="amount">${fmt(b.monthly_limit)} / month</span>
          <button class="btn-small" data-del="${b.id}">Delete</button>
        </div>`).join("")
    : `<div class="empty-state">No budgets set yet.</div>`;

  el.querySelectorAll("[data-del]").forEach((btn) => {
    btn.addEventListener("click", async () => {
      await api.del(`/budgets/${btn.dataset.del}`);
      showToast("Budget removed");
      loadBudgets();
    });
  });
}

document.getElementById("form-budget").addEventListener("submit", async (e) => {
  e.preventDefault();
  const fd = new FormData(e.target);
  try {
    await api.post("/budgets", {
      category: fd.get("category"),
      monthly_limit: parseFloat(fd.get("monthly_limit")),
    });
    showToast("Budget saved");
    e.target.reset();
    loadBudgets();
  } catch (err) { showToast(err.message, true); }
});

// ---------- Savings ----------
async function loadSavings() {
  await refreshReferenceData();
  const el = document.getElementById("goals-list");
  el.innerHTML = cache.goals.length
    ? cache.goals.map((g) => {
        const pct = g.target_amount ? Math.min((g.current_amount / g.target_amount) * 100, 100) : 0;
        return `
        <div class="entity-card">
          <h3>${g.name}</h3>
          <div class="meta">${g.deadline ? "Deadline " + g.deadline : "No deadline set"}</div>
          <div class="figure">${fmt(g.current_amount)} / ${fmt(g.target_amount)}</div>
          <div class="progress-track"><div class="progress-fill" style="width:${pct}%"></div></div>
        </div>`;
      }).join("")
    : `<div class="empty-state">No savings goals yet.</div>`;
}

document.getElementById("form-goal").addEventListener("submit", async (e) => {
  e.preventDefault();
  const fd = new FormData(e.target);
  try {
    await api.post("/savings-goals", {
      name: fd.get("name"),
      target_amount: parseFloat(fd.get("target_amount")),
      current_amount: parseFloat(fd.get("current_amount") || 0),
      deadline: fd.get("deadline") || null,
    });
    showToast("Goal created");
    e.target.reset();
    loadSavings();
  } catch (err) { showToast(err.message, true); }
});

document.getElementById("form-contribute").addEventListener("submit", async (e) => {
  e.preventDefault();
  const fd = new FormData(e.target);
  try {
    await api.post(`/savings-goals/${fd.get("goal_id")}/contribute`, {
      amount: parseFloat(fd.get("amount")),
      account_id: parseInt(fd.get("account_id")),
    });
    showToast("Contribution added");
    e.target.reset();
    await refreshReferenceData();
    loadSavings();
  } catch (err) { showToast(err.message, true); }
});

// ---------- Bills ----------
async function loadBills() {
  await refreshReferenceData();
  const bills = await api.get("/bills");
  const el = document.getElementById("bills-list");
  el.innerHTML = bills.length
    ? bills.map((b) => `
        <div class="list-row">
          <span>${b.name} · ${b.frequency} · due ${b.due_date} ${b.status === "paid" ? "· paid" : ""}</span>
          <span class="amount">${fmt(b.amount)}</span>
          ${b.status === "unpaid" ? `<button class="btn-small" data-pay="${b.id}">Mark paid</button>` : ""}
          <button class="btn-small" data-del="${b.id}">Delete</button>
        </div>`).join("")
    : `<div class="empty-state">No bills added yet.</div>`;

  el.querySelectorAll("[data-pay]").forEach((btn) => {
    btn.addEventListener("click", async () => {
      try {
        await api.post(`/bills/${btn.dataset.pay}/pay`, {});
        showToast("Bill marked paid");
        loadBills();
        loadDashboard();
      } catch (err) { showToast(err.message, true); }
    });
  });
  el.querySelectorAll("[data-del]").forEach((btn) => {
    btn.addEventListener("click", async () => {
      await api.del(`/bills/${btn.dataset.del}`);
      showToast("Bill removed");
      loadBills();
    });
  });
}

document.getElementById("form-bill").addEventListener("submit", async (e) => {
  e.preventDefault();
  const fd = new FormData(e.target);
  try {
    await api.post("/bills", {
      name: fd.get("name"),
      amount: parseFloat(fd.get("amount")),
      due_date: fd.get("due_date"),
      frequency: fd.get("frequency"),
      account_id: fd.get("account_id") ? parseInt(fd.get("account_id")) : null,
    });
    showToast("Bill added");
    e.target.reset();
    loadBills();
  } catch (err) { showToast(err.message, true); }
});

// ---------- Init ----------
window.addEventListener("DOMContentLoaded", async () => {
  document.getElementById("today-label").textContent = new Date().toLocaleDateString("en-US", {
    weekday: "long", year: "numeric", month: "long", day: "numeric",
  });
  document.querySelectorAll('input[type="date"]').forEach((el) => { if (!el.value) el.value = todayISO(); });

  setupNav();
  try {
    await refreshReferenceData();
    await loadDashboard();
  } catch (err) {
    showToast("Could not reach the API. Is the backend running on port 8000?", true);
  }
});
