# AGENTS.md

# Objetivo

O objetivo deste projeto é construir o ClawAI, um assistente de IA desktop modular,
autônomo e extensível.

Toda alteração deve aproximar o projeto deste objetivo.

---

# Prioridades

Sempre priorize, nesta ordem:

1. Manter o projeto funcional.
2. Melhorar a arquitetura.
3. Reduzir complexidade.
4. Eliminar código morto.
5. Melhorar desempenho.
6. Melhorar documentação.

Nunca sacrifique funcionamento por organização.

---

# Arquitetura

Siga Clean Architecture sempre que possível.

Preferências:

- módulos pequenos
- baixo acoplamento
- alta coesão
- responsabilidades únicas
- interfaces bem definidas

Evite dependências circulares.

---

# Antes de criar código

Antes de criar qualquer arquivo:

- procure implementação semelhante;
- reutilize código existente;
- evite duplicação.

Antes de criar uma nova classe:

- verifique se uma já resolve o problema.

---

# Refatoração

É permitido refatorar.

Ao encontrar:

- código morto
- arquivos duplicados
- funções não utilizadas
- pastas abandonadas

não remova imediatamente.

Marque-os em:

docs/APAGAR.md

incluindo:

- caminho
- motivo
- impacto
- dependências

Só remova quando houver segurança.

---

# Estrutura

Prefira:

```
core/
services/
providers/
plugins/
ui/
desktop/
frontend/
memory/
planner/
tools/
```

Evite criar novas pastas de primeiro nível sem necessidade.

---

# Desktop

Existe apenas UMA implementação oficial do desktop.

Não introduza uma segunda arquitetura.

Sempre reutilize a existente.

---

# Build

Sempre preserve o fluxo:

Frontend > Backend > Desktop > Executável

Qualquer alteração deve manter o build funcionando.

---

# Dependências

Antes de adicionar uma biblioteca:

- justificar necessidade
- verificar se já existe solução equivalente

Reduzir dependências é preferível.

---

# Logging

Logs devem ser úteis.

Evite:

print()

Prefira logging estruturado.

---

# Configuração

Nunca espalhe constantes.

Toda configuração deve estar centralizada.

---

# Segurança

Nunca:

- gravar segredos
- gravar tokens
- gravar senhas

Utilize variáveis de ambiente.

---

# Performance

Prefira:

- lazy loading
- cache quando apropriado
- processamento assíncrono

Evite trabalho duplicado.

---

# Testes

Sempre que possível:

- atualizar testes existentes
- não quebrar testes

---

# Documentação

Toda alteração significativa deve atualizar:

README.md
ou
docs/

---

# Estilo

Prefira código simples.

Código legível é mais importante que código "inteligente".

---

# Objetivo final

O ClawAI deve permanecer:

- modular
- estável
- extensível
- fácil de manter
- pronto para distribuição desktop.