📊 Calculadora de Salário Líquido
Este projeto é uma Calculadora de Salário Líquido baseada em Flask, Python e MongoDB Atlas. Ele permite que os usuários autenticados calculem seu salário líquido, considerando rendimentos e descontos diversos, além de oferecer funcionalidades para gerenciar e salvar diferentes perfis de cálculo.

✨ Funcionalidades Principais
Autenticação de Usuários: Sistema completo de registro, login e logout para proteger os dados dos usuários.

Cálculo Preciso: Calcula o INSS e o IRPF com base nas tabelas de 2025, além de considerar outros rendimentos (quinquênio, premiação) e descontos (vale alimentação, plano de saúde, previdência privada, odontológico).

Gerenciamento de Perfis: Permite salvar e carregar múltiplos perfis de cálculo, facilitando a comparação e o acompanhamento de diferentes cenários financeiros.

Simulação de Aumento Salarial: Ferramenta interativa para aplicar um percentual de aumento ao salário base e visualizar o impacto no salário líquido, com a opção de salvar o novo cenário como um perfil.

Interface Responsiva: Design moderno e adaptável para garantir uma boa experiência em dispositivos móveis e desktops.

Persistência de Dados: Utiliza MongoDB Atlas para armazenar de forma segura as informações de usuários e perfis.

🚀 Tecnologias Utilizadas
Backend: Python 🐍

Framework Web: Flask

Segurança: werkzeug.security para hash de senhas.

Banco de Dados: pymongo (Driver MongoDB)

Banco de Dados: MongoDB Atlas

Frontend: HTML, CSS e JavaScript

Estilização: CSS puro para um design limpo e responsivo.

Interatividade: JavaScript para funcionalidades como seções colapsíveis e aplicação de aumentos percentuais.

⚙️ Configuração do Ambiente
Siga os passos abaixo para configurar e rodar o projeto localmente.

Pré-requisitos
Python 3.x

Conta no MongoDB Atlas e um cluster configurado.

pip (gerenciador de pacotes do Python)

1. Clonar o Repositório
git clone https://github.com/seu-usuario/seu-projeto.git
cd seu-projeto


2. Configurar Variáveis de Ambiente
Crie um arquivo .env na raiz do projeto (o mesmo diretório de app.py) e adicione a URI de conexão do seu MongoDB Atlas:

MONGODB_URI="mongodb+srv://<seu-usuario>:<sua-senha>@<seu-cluster>.mongodb.net/?retryWrites=true&w=majority"


Importante: Substitua <seu-usuario>, <sua-senha> e <seu-cluster> pelas suas credenciais do MongoDB Atlas.

3. Instalar Dependências
Crie um ambiente virtual (recomendado) e instale as bibliotecas necessárias:

python -m venv venv
source venv/bin/activate  # No Windows: venv\Scripts\activate
pip install Flask pymongo python-dotenv werkzeug


4. Inicializar o Banco de Dados
O aplicativo tentará inicializar a conexão com o banco de dados e criar os índices necessários ao iniciar. Certifique-se de que sua MONGODB_URI esteja correta e que o IP de onde você está rodando o aplicativo esteja na lista de IPs permitidos do seu cluster MongoDB Atlas.

5. Executar a Aplicação
flask run


Ou, se preferir rodar diretamente o script:

python app.py


A aplicação estará disponível em http://127.0.0.1:5000 (ou a porta configurada, geralmente 5000).

💡 Como Usar
Acesse a Aplicação: Abra seu navegador e navegue para http://172.0.0.1:5000.

Registro/Login:

Se for seu primeiro acesso, clique em "Cadastre-se aqui" para criar uma nova conta.

Após o registro, faça login com suas credenciais.

Calcular Salário Líquido:

Preencha os campos nos painéis "Rendimentos" e "Descontos".

Utilize o botão "Calcular" para ver o salário líquido estimado.

Gerenciar Perfis:

Expanda a seção "Gerenciar Perfis".

Salvar: Digite um nome no campo "Nome do Perfil para Salvar" e clique em "Salvar Perfil".

Carregar: Selecione um perfil salvo na lista suspensa "Carregar Perfil".

Simular Aumento Salarial:

Expanda a seção "Ajustar Salário por Aumento (%)".

Insira o percentual de aumento e clique em "Aplicar Aumento" para atualizar o "Salário Base" no formulário.

Clique em "Salvar como novo perfil" para criar um novo perfil com o salário ajustado.

🤝 Contribuição
Contribuições são bem-vindas! Se você tiver sugestões de melhorias, detecção de bugs ou novas funcionalidades, sinta-se à vontade para:

Abrir uma issue para discutir a mudança proposta.

Criar um fork do projeto.

Criar uma branch para sua feature (git checkout -b feature/MinhaNovaFeature).

Realizar suas alterações e fazer commit (git commit -m 'feat: Minha nova feature').

Fazer push para a branch (git push origin feature/MinhaNovaFeature).

Abrir um Pull Request.

📄 Licença
Este projeto está licenciado sob a licença MIT. Consulte o arquivo LICENSE para mais detalhes.