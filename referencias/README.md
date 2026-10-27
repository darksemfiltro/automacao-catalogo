# Referências visuais

`base/` contém um desenho original, sob a licença do projeto, e o contrato de tokens. `novo_episodio.py`
copia essa base para `producao/referencias/` em cada episódio. Em projetos existentes,
copie a pasta manualmente. Prints de terceiros permanecem locais.

Para cada imagem, acrescente uma entrada em `manifest.json`: `file` relativo à pasta,
`source` com origem, `license` com permissão conhecida e `observations` com regras
concretas de composição. Exemplo: “objeto à esquerda; valor com unidade à direita”.
Ver a imagem é trabalho do agente ou revisor; o script não faz compreensão visual.

O agente traduz as observações em `tokens` e ajustes em `cenas.json`. O gerador
consome cores `title_color`, `callout_color`, `list_color`, `frase_color` (hex RGB)
e tamanhos `title_size`, `callout_size`, `list_size`, `frase_size` (24–160px).
Esses tokens alteram texto; posição de objetos e movimento continuam no plano de cenas.
Não se aceita CSS arbitrário. Não se copia a imagem de referência para o vídeo.

Depois de alterar uma referência ou token, regenere composição e storyboard e
revise os quadros. A revisão anterior perde validade pelo hash dos arquivos.
