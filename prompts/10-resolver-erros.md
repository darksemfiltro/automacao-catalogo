# 10 · Resolver um erro

Cole o erro inteiro, não só a última linha, e diga o que você estava fazendo.

```text
Estou usando o projeto aberto Catálogo (vídeos explicativos em português, com
HyperFrames) e deu erro.

O que eu fazia: [comando exato que rodei]
Meu sistema: [Windows 11 / Ubuntu / macOS]
Saída do erro, inteira:
[cole aqui]

Leia AGENTS.md e o script que aparece no erro. Diagnostique em três passos:
1. Qual é a causa mais provável, em português simples, e que evidência no erro ou no
   arquivo mostra isso. Se houver mais de uma causa possível, liste todas e diga como
   distinguir.
2. A correção mais simples. Se envolver mudar código do projeto, explique por que o
   código estava errado e não só o sintoma.
3. Como confirmar que resolveu (um comando e o resultado esperado).
Não apague arquivos, não use sudo nem administrador, não afrouxe nenhum limite de
sistema/CONSTRAINTS.md e não pule uma etapa de verificação para fazer o erro sumir.
Se faltar informação, me pergunte em vez de supor.
```

## Erros que aparecem muito

| Mensagem | Onde olhar |
| --- | --- |
| `gauntlet: ... [repetido]`, `[texto_obj]` | Edite `cenas.json`: troque o objeto repetido ou tire o texto de cima de um painel |
| `buracos >0.6s` em `checa_densidade.py` | Falta conteúdo num trecho. Acrescente uma cena ou um objeto nesse segmento |
| `WAV já existe` | Proteção contra sobrescrita. Use uma versão nova (`v2`) ou `--overwrite` de propósito |
| Alinhamento em 0% | Use `--device cpu` no `align_mms.py` |
| `A API de voz falhou: HTTP 401` | Chave errada ou variável não definida no terminal atual |
| `Programa não encontrado` no provedor `comando` | `comando.argv[0]` precisa estar no PATH ou ser um caminho completo |
| `render_final` recusa | Storyboard, revisão ou composição ficaram velhos. Regenere e registre a revisão de novo |
