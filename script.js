document.addEventListener('DOMContentLoaded', () => {
    const formCadastro = document.getElementById('formCadastro'); // Formulário de cadastro de produto
    const feedbackCadastro = document.getElementById('feedbackCadastro'); // Área de feedback
    const listaProdutos = document.getElementById('produtos'); // Elemento da lista de produtos
    const btnRelatorio = document.getElementById('btnRelatorio'); // Botão de relatório
    const relatorioResultado = document.getElementById('relatorioResultado'); // Exibição de relatório
    const pesquisaInput = document.getElementById('pesquisaInput'); // Campo de pesquisa

    // Função principal para gerenciar o cadastro de produtos
    const gerenciarProduto = {
        async cadastrarProduto(produto) {
            try {
                const response = await fetch('/api/produtos', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(produto),
                });

                if (response.ok) {
                    this.exibirFeedback("Produto cadastrado com sucesso!", 'green');
                    formCadastro.reset();
                    await this.atualizarListaProdutos();
                } else {
                    throw new Error("Erro ao cadastrar produto");
                }
            } catch (error) {
                this.exibirFeedback(error.message, 'red');
            }
        },

        async atualizarListaProdutos(pesquisa = '') {
            try {
                const response = await fetch('/api/produtos');
                const produtos = await response.json();
                listaProdutos.innerHTML = ""; // Limpa lista antes de atualizar

                produtos.forEach((produto) => {
                    if (produto.nome.toLowerCase().includes(pesquisa.toLowerCase())) {
                        const itemProduto = document.createElement('li');
                        itemProduto.innerHTML = `
                            ${produto.nome} - ${produto.categoria} - Qtd: ${produto.quantidade} - R$${produto.preco.toFixed(2)} - Localização: ${produto.localizacao}
                            <button onclick="gerenciarProduto.removerProduto(${produto.id})">Remover</button>
                        `;
                        listaProdutos.appendChild(itemProduto);
                    }
                });
            } catch (error) {
                console.error("Erro ao carregar produtos:", error);
            }
        },

        async removerProduto(id) {
            try {
                const response = await fetch(`/api/produtos/${id}`, { method: 'DELETE' });

                if (response.ok) {
                    this.exibirFeedback("Produto removido com sucesso!", 'red');
                    await this.atualizarListaProdutos(); // Atualizar a lista após remoção
                } else {
                    throw new Error("Erro ao remover produto");
                }
            } catch (error) {
                this.exibirFeedback(error.message, 'red');
            }
        },

        exibirFeedback(mensagem, cor) {
            feedbackCadastro.textContent = mensagem;
            feedbackCadastro.style.color = cor;
        }
    };

    // Evento para o cadastro de produtos
    formCadastro.addEventListener('submit', async (e) => {
        e.preventDefault();
        const produto = {
            nome: document.getElementById('nome').value,
            categoria: document.getElementById('categoria').value,
            quantidade: parseInt(document.getElementById('quantidade').value),
            preco: parseFloat(document.getElementById('preco').value),
            localizacao: document.getElementById('localizacao').value,
        };
        await gerenciarProduto.cadastrarProduto(produto);
    });

    // Evento para pesquisar produtos
    pesquisaInput.addEventListener('input', (e) => {
        const pesquisa = e.target.value;
        gerenciarProduto.atualizarListaProdutos(pesquisa);
    });

    // Evento para gerar relatórios
    btnRelatorio.addEventListener('click', async () => {
        try {
            const response = await fetch('/api/relatorios');
            const relatorios = await response.json();
            relatorioResultado.innerHTML = `
                <h3>Relatório de Estoque</h3>
                <h4>Produtos com Estoque Baixo:</h4>
                <ul>
                    ${relatorios.baixo_estoque.map(p => `<li>${p.nome} - Qtd: ${p.quantidade} - Localização: ${p.localizacao}</li>`).join('')}
                </ul>
                <h4>Produtos com Excesso de Estoque:</h4>
                <ul>
                    ${relatorios.excesso_estoque.map(p => `<li>${p.nome} - Qtd: ${p.quantidade} - Localização: ${p.localizacao}</li>`).join('')}
                </ul>
            `;
        } catch (error) {
            console.error("Erro ao gerar relatório:", error);
        }
    });

    // Carregar produtos na inicialização
    gerenciarProduto.atualizarListaProdutos();
});
