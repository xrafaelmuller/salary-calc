document.addEventListener('DOMContentLoaded', function() {
    const entradasContainer = document.getElementById('entradas-container');
    const saidasContainer = document.getElementById('saidas-container');
    const addEntradaBtn = document.getElementById('add-entrada-btn');
    const addSaidaBtn = document.getElementById('add-saida-btn');
    const mainForm = document.getElementById('main-calc-form');

    let itemId = 0;

    // Função para criar um novo item (entrada ou saída)
    function createItem(type, data = {}) {
        itemId++;
        const itemDiv = document.createElement('div');
        itemDiv.className = 'dynamic-item';
        
        itemDiv.innerHTML = `
            <input type="text" placeholder="${type === 'entrada' ? 'Ex: Salário, Freelance' : 'Ex: Aluguel, Supermercado'}" class="item-description" value="${data.desc || ''}" required>
            <div class="input-group-currency">
                <input type="text" placeholder="0,00" class="item-value" value="${data.value || ''}" required>
            </div>
            <button type="button" class="lock-btn" title="Bloquear/Desbloquear Item" aria-label="Bloquear ou desbloquear item">🔓</button>
            <button type="button" class="remove-btn" title="Remover Item" aria-label="Remover item">&times;</button>
        `;
        
        if (data.locked) {
            itemDiv.classList.add('locked');
            itemDiv.querySelector('.item-description').readOnly = true;
            itemDiv.querySelector('.item-value').readOnly = true;
            itemDiv.querySelector('.lock-btn').textContent = '🔒';
        }

        return itemDiv;
    }

    // Função para adicionar um item a um container
    function addItem(type, container, data) {
        const newItem = createItem(type, data);
        container.appendChild(newItem);
    }
    
    // Adiciona os primeiros itens ao carregar a página
    addItem('entrada', entradasContainer);
    addItem('saida', saidasContainer);
    
    addEntradaBtn.addEventListener('click', () => addItem('entrada', entradasContainer));
    addSaidaBtn.addEventListener('click', () => addItem('saida', saidasContainer));
    
    // Gerenciador de eventos para todo o formulário (remover, bloquear e calcular)
    mainForm.addEventListener('click', function(e) {
        if (e.target.classList.contains('remove-btn')) {
            e.target.closest('.dynamic-item').remove();
            calculateTotals();
        }
        
        if (e.target.classList.contains('lock-btn')) {
            const itemDiv = e.target.closest('.dynamic-item');
            const descInput = itemDiv.querySelector('.item-description');
            const valueInput = itemDiv.querySelector('.item-value');
            const isLocked = itemDiv.classList.toggle('locked');
            
            descInput.readOnly = isLocked;
            valueInput.readOnly = isLocked;
            e.target.textContent = isLocked ? '🔒' : '🔓';
        }
    });

    // Calcula em tempo real ao digitar
    mainForm.addEventListener('input', calculateTotals);

    // Função para calcular os totais e o saldo
    window.calculateTotals = function() {
        const resultContainer = document.getElementById('result-container');
        const totalEntradasEl = document.getElementById('total-entradas');
        const totalSaidasEl = document.getElementById('total-saidas');
        const saldoFinalEl = document.getElementById('saldo-final');

        let totalEntradas = 0;
        let totalSaidas = 0;

        document.querySelectorAll('#entradas-container .item-value').forEach(input => {
            totalEntradas += parseFloat(input.value.replace(/\./g, '').replace(',', '.')) || 0;
        });

        document.querySelectorAll('#saidas-container .item-value').forEach(input => {
            totalSaidas += parseFloat(input.value.replace(/\./g, '').replace(',', '.')) || 0;
        });

        const saldo = totalEntradas - totalSaidas;
        
        const formatCurrency = (value) => `R$ ${value.toLocaleString('pt-BR', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;

        totalEntradasEl.textContent = formatCurrency(totalEntradas);
        totalSaidasEl.textContent = formatCurrency(totalSaidas);
        saldoFinalEl.textContent = formatCurrency(saldo);
        
        saldoFinalEl.className = saldo >= 0 ? 'saldo-positivo' : 'saldo-negativo';
        resultContainer.style.display = 'block';
    }

    // Lógica para o painel flutuante de perfis/orçamentos
    document.querySelectorAll('.floating-action-group').forEach(group => {
        let hideTimeout;
        group.addEventListener('mouseenter', () => {
            clearTimeout(hideTimeout);
            document.querySelectorAll('.floating-action-group').forEach(other => { if (other !== group) other.classList.remove('active'); });
            group.classList.add('active');
        });
        group.addEventListener('mouseleave', () => {
            hideTimeout = setTimeout(() => group.classList.remove('active'), 300);
        });
    });

    // Função para exibir mensagens rápidas (flash messages)
    function flashMessage(message, category = 'info') {
        const container = document.querySelector('.flash-messages-js-container');
        const msgDiv = document.createElement('div');
        msgDiv.className = `flash-message ${category}`;
        msgDiv.textContent = message;
        container.prepend(msgDiv);
        setTimeout(() => {
            msgDiv.style.opacity = '1';
            msgDiv.style.transform = 'translateY(0)';
        }, 10);
        setTimeout(() => {
            msgDiv.style.opacity = '0';
            msgDiv.style.transform = 'translateY(-20px)';
            msgDiv.addEventListener('transitionend', () => msgDiv.remove());
        }, 5000);
    }

    // --- Lógica de Salvar e Carregar Orçamentos ---
    const saveBtn = document.getElementById('save-profile-btn');
    const profileNameInput = document.getElementById('profile_name');
    const profileSelect = document.getElementById('profile_select');

    function populateProfileSelect() {
        profileSelect.innerHTML = '<option value="">-- Selecione --</option>';
        const profiles = Object.keys(localStorage).filter(k => k.startsWith('budget_'));
        profiles.forEach(key => {
            const option = document.createElement('option');
            option.value = key;
            option.textContent = key.replace('budget_', '');
            profileSelect.appendChild(option);
        });
    }
    
    saveBtn.addEventListener('click', () => {
        const profileName = profileNameInput.value.trim();
        if (!profileName) {
            flashMessage('Por favor, insira um nome para o orçamento.', 'danger');
            return;
        }

        const budgetData = { entradas: [], saidas: [] };

        document.querySelectorAll('#entradas-container .dynamic-item').forEach(item => {
            budgetData.entradas.push({
                desc: item.querySelector('.item-description').value,
                value: item.querySelector('.item-value').value,
                locked: item.classList.contains('locked')
            });
        });
        
        document.querySelectorAll('#saidas-container .dynamic-item').forEach(item => {
            budgetData.saidas.push({
                desc: item.querySelector('.item-description').value,
                value: item.querySelector('.item-value').value,
                locked: item.classList.contains('locked')
            });
        });

        localStorage.setItem(`budget_${profileName}`, JSON.stringify(budgetData));
        flashMessage(`Orçamento "${profileName}" salvo com sucesso!`, 'success');
        populateProfileSelect();
    });

    profileSelect.addEventListener('change', () => {
        const profileKey = profileSelect.value;
        if (!profileKey) return;

        const dataString = localStorage.getItem(profileKey);
        if (!dataString) return;

        const data = JSON.parse(dataString);
        profileNameInput.value = profileKey.replace('budget_', '');

        entradasContainer.innerHTML = '';
        saidasContainer.innerHTML = '';

        data.entradas.forEach(itemData => addItem('entrada', entradasContainer, itemData));
        data.saidas.forEach(itemData => addItem('saida', saidasContainer, itemData));

        flashMessage(`Orçamento "${profileNameInput.value}" carregado.`, 'info');
        calculateTotals();
    });
    
    // Inicializa a lista de orçamentos e os cálculos
    populateProfileSelect();
    calculateTotals();
});