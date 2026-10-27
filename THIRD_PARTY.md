# Dependências e mídia de terceiros

A [licença do projeto](LICENSE) cobre somente o material original deste repositório: scripts, roteiros, documentação e SVGs autorais. Ela não muda as condições das ferramentas, modelos, fontes, vozes ou mídias usadas por cada pessoa que produz um vídeo.

| Componente | Uso neste projeto | Condição relevante |
| --- | --- | --- |
| [HyperFrames](https://github.com/heygen-com/hyperframes) | Pré-visualização e renderização; versão fixada pelo `package-lock.json`. | Código externo sob [Apache-2.0](https://github.com/heygen-com/hyperframes/blob/main/LICENSE); instalado por `npm ci`. |
| [GSAP](https://gsap.com/) | Animação da composição gerada. O arquivo vem de `vendor/gsap.min.js`, fixado por versão (3.14.2) e sha256 em `vendor/PINS.json`, e é copiado sem alteração para `assets/vendor/` dentro da composição. | Dependência externa sujeita aos [termos da GSAP](https://gsap.com/community/standard-license/); **não** é relicenciada pela licença deste projeto. Antes era buscada em CDN a cada render; vendorizá-la faz o repositório distribuir o arquivo, então a licença da GSAP passa a valer para a redistribuição. Para removê-la do pacote, apague `vendor/gsap.min.js` — `gen_comp.py` volta à CDN e avisa. |
| [Google Fonts](https://fonts.google.com/) — Baloo 2, Nunito, Patrick Hand, Caveat | Tipografia da composição. As woff2 (subconjunto latino) vêm de `vendor/fonts/`, fixadas por versão do pacote `@fontsource` 5.3.0 e sha256 em `vendor/PINS.json`, e `assets/vendor/fonts.css` é gerado a partir desses pinos. `vendor/fonts/LICENCA-OFL-1.1.txt` acompanha o pacote. | Cada família é **SIL Open Font License 1.1**, não MIT. A OFL permite redistribuição e embedding, com a exigência de manter o nome do projeto e o texto da licença; o arquivo de licença vai junto. Sem os arquivos locais, `gen_comp.py` volta ao Google Fonts e avisa. |
| [FFmpeg](https://ffmpeg.org/legal.html) | Montagem de áudio e codificação de vídeo. | Ferramenta instalada pelo usuário, com condições próprias. |
| [Faster-Whisper](https://github.com/SYSTRAN/faster-whisper) | Transcrição local opcional com timestamps de palavras. | Código MIT; modelos, CTranslate2 e demais dependências mantêm suas licenças. Pesos não são distribuídos neste repositório. |
| [OmniVoice](https://github.com/k2-fsa/OmniVoice) | Opção de síntese de voz para a produção original. | O código é Apache-2.0; os **pesos pré-treinados** de [`k2-fsa/OmniVoice`](https://huggingface.co/k2-fsa/OmniVoice) são CC-BY-NC segundo a ficha oficial. O uso comercial dos pesos exige outra solução ou licença apropriada. |
| [Pixabay](https://pixabay.com/service/terms/) | Fonte de alguns efeitos sonoros usados localmente na produção original. | Os termos proíbem distribuir conteúdo inalterado de forma independente. Os MP3 individuais não integram o pacote público. |

O repositório conserva `episodios/EP05-tipos-de-tempestade/producao/assets/sfx/manifest.json` como referência de nomes e usos. Esse arquivo não concede licença nem fornece os arquivos de áudio. Se você quiser efeitos sonoros, obtenha ou produza arquivos com direitos adequados ao seu projeto; registre a origem de cada um. Uma trilha ou efeito integrado a um vídeo pode ter condições diferentes da redistribuição do arquivo isolado.

A [licença do projeto](LICENSE) permite vídeos monetizados por anúncio, mas a licença de um componente de terceiros, como os pesos não comerciais do OmniVoice, pode não permitir. Confira cada um.

Use apenas uma voz própria ou uma voz para a qual tenha autorização. A referência vocal da produção original e os pesos dos modelos não são distribuídos aqui. Para publicação comercial, confira separadamente a licença do TTS, da voz, de cada música, imagem e efeito que inserir.

## Procedência de práticas

A barra de qualidade (`sistema/CONSTRAINTS.md`), o guard de diff
(`pipeline/floor_guard.py`), a etapa de crítica em contexto fresco
(`pipeline/critica.py`) e o pinning de dependências (`vendor/PINS.json`) foram
adaptados de **[addyosmani/agent-skills](https://github.com/addyosmani/agent-skills)**
(MIT, Addy Osmani) — em especial `constraint-driven-development`,
`doubt-driven-development` e `source-driven-development`. O que mudou na
adaptação: a barra é sobre produção de vídeo, não sobre código; os limites são
segundos, LUFS e pixels em vez de cobertura e severidade; e a aprovação humana
continua sendo `review.json`, com `critica.json` explicitamente marcada como
não-aprovação. Nenhum arquivo foi copiado literalmente.
