# Contribuir com o Catálogo

Contribuições para corrigir a pipeline, ampliar a biblioteca visual e melhorar a documentação são bem-vindas. Abra uma issue para discutir mudanças grandes; para correções pequenas, envie uma pull request com o motivo e um exemplo do resultado.

## Antes de enviar

1. Trabalhe em uma branch e mantenha cada PR focada em um problema.
2. Rode os testes Python: `python -m unittest discover -s pipeline -p "test_*.py" -v`.
3. Se alterou o plano ou a composição, rode `python pipeline/gauntlet.py episodios/EP05-tipos-de-tempestade/producao/episode.json --strict`, gere o HTML com `python pipeline/gen_comp.py episodios/EP05-tipos-de-tempestade/producao --spec episode.json --seconds 30 --out-dir hyperframes_demo`, depois rode `python pipeline/checa_densidade.py episodios/EP05-tipos-de-tempestade/producao/hyperframes_demo/index.html` e `npx --no-install hyperframes check episodios/EP05-tipos-de-tempestade/producao/hyperframes_demo --at "5,15,25" --timeout 30000` após `npm ci`. Anexe quadros ou um vídeo curto quando a mudança for visual.
4. Explique no PR o que mudou, por que mudou e quais verificações fez. Registre os limites que restaram.

Não inclua no PR modelos, pesos, voz de referência, áudio ou vídeo de terceiros, caches, renders ou caminhos absolutos da sua máquina. Para novo material factual, registre links das fontes e confira números, unidades e contexto. Para mídia e código externos, identifique a origem e a licença no PR; o arquivo [THIRD_PARTY.md](THIRD_PARTY.md) resume as dependências atuais.

## Cuidado com a configuração de voz

O provedor `comando` de `sistema/voz.json` executa o programa indicado em `comando.argv`. Ao revisar um PR, leia com atenção qualquer mudança nesse arquivo, e nunca rode um `voz.json` de origem que você não conhece.

## Formato e compatibilidade

- Preserve os IDs dos segmentos quando uma correção não mudar a fala; eles ligam roteiro, áudio e alinhamento.
- Documente mudanças no formato de `segments_*.json`, `alignment_*.json` ou `episode.json`, e atualize os exemplos afetados.
- Os scripts devem aceitar caminhos do usuário e funcionar sem diretórios locais fixos. Prefira `pathlib` ou caminhos recebidos por argumento.
- Um `--fix` do gauntlet altera o `episode.json`; revise o diff antes de incluí-lo.
- Testes devem cobrir o comportamento que pode falhar, com entradas pequenas e sem exigir voz, GPU ou render completo quando isso não for necessário.

## A barra não se afrouxa no mesmo PR

Os limites vivem em [`sistema/CONSTRAINTS.md`](sistema/CONSTRAINTS.md). Três
regras para quem mexe neles:

1. **Leia de lá, não escreva o número no código.** Um literal repetido vira
   documentação mentirosa: a skill já anunciava `--max-gap 2.8` onde o motor
   usava 0,9 s. Use `from constraints import value as limite`.
2. **Toda linha com número declara o comando que produz o veredicto.** Limite
   sem comando é aspiração.
3. **Afrouxar é decisão explícita, com responsável e data.** Escreva a exceção
   na tabela do arquivo, com o motivo. `python pipeline/floor_guard.py` acusa
   limite editado, flag passada na mão, teste pulado, verificador calado e stub
   no motor — e o `verifica.py` roda o mesmo guard.

Dependência externa nova entra em `vendor/PINS.json` com versão, origem e
sha256, e o arquivo é copiado sem alteração para a composição, para que o hash
de `build.json` a cubra.

Ao enviar conteúdo original para este repositório, você concorda que sua contribuição seja disponibilizada sob a [licença do projeto](LICENSE), que é gratuita e proíbe vender. Não envie material sobre o qual não tenha direito de redistribuição nesses termos.

## Fluxo Nível 1

Leia `AGENTS.md`, `sistema/CONSTRAINTS.md` e `sistema/FLUXO-NIVEL-1.md` ao
contribuir com produção. Mudanças em inputs, referências, barra ou motor
invalidam revisões anteriores. A suíte inclui os gates de storyboard e não
baixa modelos. Testes reais com OmniVoice, Faster-Whisper e FFmpeg devem
registrar ambiente e resultados separadamente. Não inclua voz, modelo, manifesto
com caminhos privados ou prints de terceiros em uma contribuição.
`referencias/base/layout.svg` é exemplo original, sob a licença do projeto.

