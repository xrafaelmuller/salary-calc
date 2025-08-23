// Elementos do DOM (permanecem os mesmos)
const totalBalanceEl = document.getElementById('total-balance');
const incomeListEl = document.getElementById('accounts-list-income');
const expenseListEl = document.getElementById('accounts-list-expense');
const addAccountBtn = document.getElementById('add-account-btn');
const themeToggleBtn = document.getElementById('theme-toggle');
const backBtn = document.getElementById('back-btn');
const body = document.body;

const modalContainer = document.getElementById('account-modal-container');
const modalTitle = document.getElementById('modal-title');
const accountForm = document.getElementById('account-form');
const editIdInput = document.getElementById('edit-id');
const accountNameInput = document.getElementById('account-name');
const accountTagInput = document.getElementById('account-tag');
const accountBalanceInput = document.getElementById('account-balance');
const cancelBtn = document.getElementById('cancel-btn');

// Ícones (permanecem os mesmos)
const brandIcons = {
    nubank: `<svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg"><rect width="24" height="24" rx="12" fill="#820AD1"/><path d="M16.6667 7.42859C16.6667 7.42859 13.9048 7.42859 12.5238 7.42859C10.4762 7.42859 8.85714 8.61906 8.85714 10.8572V10.9524C8.85714 11.9048 9.33333 12.1905 9.71429 12.381C10.1905 12.6191 10.4762 12.8095 10.4762 13.2381C10.4762 13.6667 10.1905 13.9048 9.71429 13.9048C8.57143 13.9048 7.33333 13.9048 7.33333 13.9048M16.6667 16.5714C16.6667 16.5714 14.8571 16.5714 13.8095 16.5714C12.4286 16.5714 11.5238 15.9762 11.5238 14.8572V12.381C11.5238 11.4286 12 11.1429 12.381 10.9524C12.8571 10.7143 13.1429 10.5238 13.1429 10.0952C13.1429 9.66668 12.8571 9.42859 12.381 9.42859C13.5238 9.42859 16.6667 9.42859 16.6667 9.42859" stroke="white" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/></svg>`,
    itau: `<svg viewBox="0 0 100 100" fill="none" xmlns="http://www.w3.org/2000/svg"><rect width="100" height="100" rx="50" fill="#EC7000"/><rect x="25" y="31" width="13" height="38" fill="white"/><rect x="44" y="31" width="13" height="38" fill="#0056A0"/><rect x="62" y="31" width="13" height="38" fill="white"/></svg>`
};

// A variável 'accounts' agora começa vazia e será preenchida pela API
let accounts = [];

// --- FUNÇÕES DE LÓGICA E DADOS ---

// NOVA FUNÇÃO: Busca os dados do servidor
async function fetchAccounts() {
    try {
        const response = await fetch('/api/gastos/accounts'); // Endpoint GET
        if (!response.ok) {
            throw new Error('Não foi possível carregar os dados do servidor.');
        }
        accounts = await response.json();
        renderAccounts();
        updateTotalBalance();
    } catch (error) {
        console.error('Erro ao buscar contas:', error);
        alert('Erro ao carregar suas contas. Por favor, recarregue a página.');
    }
}

// FUNÇÃO MODIFICADA: Salva a conta (nova ou editada) no servidor
async function saveAccount(e) {
    e.preventDefault();
    const name = accountNameInput.value;
    const tag = accountTagInput.value;
    const balanceValue = Math.abs(+accountBalanceInput.value);
    const balanceType = document.querySelector('input[name="balance-type-radio"]:checked').value;
    const finalBalance = balanceType === 'income' ? balanceValue : -balanceValue;
    const editingId = editIdInput.value;

    if (name.trim() === '' || isNaN(balanceValue) || balanceValue === 0) {
        alert('Por favor, preencha um nome e um valor válido (diferente de zero).');
        return;
    }
    
    const accountData = { name, tag, balance: finalBalance };
    
    try {
        let response;
        if (editingId) {
            // Atualizando conta existente
            const existingAccount = accounts.find(acc => acc.id === editingId);
            accountData.locked = existingAccount.locked; // Preserva o estado de 'locked'
            response = await fetch(`/api/gastos/accounts/${editingId}`, {
                method: 'PUT',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(accountData),
            });
        } else {
            // Criando nova conta
            accountData.locked = false; // Novas contas iniciam desbloqueadas
            response = await fetch('/api/gastos/accounts', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(accountData),
            });
        }

        if (!response.ok) {
            throw new Error('A requisição para salvar a conta falhou.');
        }
        
        await fetchAccounts(); // Recarrega os dados do servidor para atualizar a UI
        closeModal();

    } catch (error) {
        console.error('Erro ao salvar conta:', error);
        alert('Não foi possível salvar a conta. Tente novamente.');
    }
}

// FUNÇÃO MODIFICADA: Alterna o estado de bloqueio no servidor
async function toggleLock(id) {
    const account = accounts.find(acc => acc.id === id);
    if (!account) return;

    // Inverte o estado de 'locked' para a atualização
    const updatedAccount = { ...account, locked: !account.locked };

    try {
        const response = await fetch(`/api/gastos/accounts/${id}`, {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(updatedAccount),
        });
        if (!response.ok) {
            throw new Error('Não foi possível atualizar o estado de bloqueio.');
        }
        await fetchAccounts(); // Recarrega os dados para garantir consistência
    } catch (error) {
        console.error('Erro ao alternar bloqueio:', error);
        alert('Erro ao atualizar o status da conta. Tente novamente.');
    }
}

// FUNÇÃO MODIFICADA: Remove a conta do servidor
async function removeAccount(id) {
    const account = accounts.find(acc => acc.id === id);
    if (account && account.locked) {
        alert('Você não pode remover uma conta bloqueada.');
        return; 
    }

    if (confirm('Tem certeza que deseja deletar esta conta?')) {
        try {
            const response = await fetch(`/api/gastos/accounts/${id}`, {
                method: 'DELETE',
            });

            if (!response.ok) {
                throw new Error('Não foi possível deletar a conta.');
            }
            
            await fetchAccounts(); // Recarrega os dados após a exclusão
        } catch (error) {
            console.error('Erro ao remover conta:', error);
            alert('Não foi possível remover a conta. Tente novamente.');
        }
    }
}


// --- FUNÇÕES DE RENDERIZAÇÃO E UI (a maioria permanece igual) ---

function renderAccounts() {
    incomeListEl.innerHTML = '';
    expenseListEl.innerHTML = '';

    const incomeAccounts = accounts.filter(account => account.balance >= 0);
    const expenseAccounts = accounts.filter(account => account.balance < 0);

    if (incomeAccounts.length === 0) {
        incomeListEl.innerHTML = `<p class="empty-list-message">Nenhuma entrada adicionada.</p>`;
    } else {
        incomeAccounts.forEach(account => addAccountDOM(account, incomeListEl));
    }

    if (expenseAccounts.length === 0) {
        expenseListEl.innerHTML = `<p class="empty-list-message">Nenhuma saída adicionada.</p>`;
    } else {
        expenseAccounts.forEach(account => addAccountDOM(account, expenseListEl));
    }
}

function addAccountDOM(account, listElement) {
    const item = document.createElement('li');
    const isPositive = account.balance >= 0;
    item.classList.add('account-item');
    if (account.locked) {
        item.classList.add('locked');
    }

    const accountId = account.id;
    const firstLetter = account.name.charAt(0).toUpperCase();
    
    let iconContent = '';
    if (account.tag && brandIcons[account.tag]) {
        iconContent = brandIcons[account.tag];
    } else {
        iconContent = firstLetter;
    }

    const lockIcon = account.locked 
        ? `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor" width="20" height="20"><path fill-rule="evenodd" d="M10 1a4.5 4.5 0 00-4.5 4.5V9H5a2 2 0 00-2 2v6a2 2 0 002 2h10a2 2 0 002-2v-6a2 2 0 00-2-2h-.5V5.5A4.5 4.5 0 0010 1zm3 8V5.5a3 3 0 10-6 0V9h6z" clip-rule="evenodd" /></svg>` 
        : `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor" width="20" height="20"><path d="M10 1a4.5 4.5 0 00-4.5 4.5V9H5a2 2 0 00-2 2v6a2 2 0 002 2h10a2 2 0 002-2v-6a2 2 0 00-2-2h-.5V5.5A4.5 4.5 0 0010 1zm-1.5 8V5.5a1.5 1.5 0 013 0V9h-3z" /></svg>`;

    item.innerHTML = `
        <div class="account-icon">${iconContent}</div>
        <div class="account-info">
            <div class="name">${account.name}</div>
        </div>
        <div class="account-balance ${isPositive ? 'plus' : 'minus'}">
            R$ ${Math.abs(account.balance).toFixed(2)}
        </div>
        <div class="account-actions">
            <button class="lock-btn" onclick="toggleLock('${accountId}')">
                ${lockIcon}
            </button>
            <button class="edit-btn" onclick="openModal(true, '${accountId}')">✏️</button>
            <button class="delete-btn" onclick="removeAccount('${accountId}')">🗑️</button>
        </div>
    `;
    
    if (!brandIcons[account.tag]) {
         const iconElement = item.querySelector('.account-icon');
         if (iconElement) {
            // A geração de cor agora usa o ID (string) para criar um hash numérico
            const numericHash = [...accountId].reduce((acc, char) => acc + char.charCodeAt(0), 0);
            const iconBgColor = `hsl(${numericHash * 30 % 360}, 60%, 50%)`;
            iconElement.style.backgroundColor = iconBgColor;
         }
    }

    listElement.appendChild(item);
}


function openModal(isEdit = false, accountId = null) {
    accountForm.reset();
    
    if (isEdit) {
        modalTitle.innerText = 'Editar Conta';
        const account = accounts.find(acc => acc.id === accountId);
        editIdInput.value = account.id;
        accountNameInput.value = account.name;
        accountTagInput.value = account.tag || 'other';
        accountBalanceInput.value = Math.abs(account.balance);
        
        if (account.balance < 0) {
            document.getElementById('radio-expense').checked = true;
        } else {
            document.getElementById('radio-income').checked = true;
        }
    } else {
        modalTitle.innerText = 'Adicionar Nova Conta';
        editIdInput.value = '';
        accountTagInput.value = 'other';
        document.getElementById('radio-income').checked = true;
    }
    modalContainer.classList.add('show');
}

const closeModal = () => modalContainer.classList.remove('show');

const updateTotalBalance = () => {
    const total = accounts.reduce((acc, account) => acc + account.balance, 0);
    totalBalanceEl.innerText = `R$ ${total.toFixed(2)}`;

    if (total < 0) {
        totalBalanceEl.classList.add('negative-alert');
    } else {
        totalBalanceEl.classList.remove('negative-alert');
    }
};

// --- Funções e Lógica do Tema (localStorage ainda é adequado aqui) ---
function applyTheme(theme) {
    if (theme === 'dark') {
        body.classList.add('dark-mode');
        themeToggleBtn.textContent = '☀️';
    } else {
        body.classList.remove('dark-mode');
        themeToggleBtn.textContent = '🌙';
    }
}

function toggleTheme() {
    const currentTheme = body.classList.contains('dark-mode') ? 'light' : 'dark';
    localStorage.setItem('theme', currentTheme);
    applyTheme(currentTheme);
}

// --- INICIALIZAÇÃO E EVENT LISTENERS ---

// FUNÇÃO MODIFICADA: init agora busca os dados do tema e chama a função para buscar as contas
function init() {
    const savedTheme = localStorage.getItem('theme') || 'light';
    applyTheme(savedTheme);
    fetchAccounts(); // Ponto de entrada principal para carregar os dados das contas
}

themeToggleBtn.addEventListener('click', toggleTheme);
addAccountBtn.addEventListener('click', () => openModal(false));
cancelBtn.addEventListener('click', closeModal);
accountForm.addEventListener('submit', saveAccount);
modalContainer.addEventListener('click', (e) => {
    if (e.target === modalContainer) closeModal();
});

backBtn.addEventListener('click', () => {
    window.location.href = backBtn.dataset.backUrl || '/';
});

// Inicia a aplicação
init();