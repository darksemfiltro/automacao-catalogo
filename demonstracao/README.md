# Demonstração: tipos de tempestade

<p align="center">
  <img src="EP05-preview.gif" alt="Prévia animada do vídeo de exemplo" width="640">
</p>

[`EP05-tipos-de-tempestade-final-v2.mp4`](EP05-tipos-de-tempestade-final-v2.mp4)
é o vídeo de exemplo do projeto. Ele foi produzido de ponta a ponta com este
repositório e renderizado por `pipeline/render_final.py`.

| | |
| --- | --- |
| Tema | Todos os tipos de tempestade |
| Duração | 58,8 s |
| Formato | 1920x1080, 30 fps, H.264 e AAC |
| Áudio | Narração a −16 LUFS, pico de −1,6 dBTP |
| Capítulos | Abertura, tornado, furacão, nevasca, tempestade de raios, fechamento |
| Segmentos | 18 frases, alinhadas ao áudio em 100% |
| Fonte do roteiro | [`episodios/EP05-tipos-de-tempestade/roteiro.md`](../episodios/EP05-tipos-de-tempestade/roteiro.md) |
| Fontes dos números | [`producao/fontes.md`](../episodios/EP05-tipos-de-tempestade/producao/fontes.md) |

## O que ele mostra do motor

- **Cenas em tela cheia (fenômenos):** vento (`wind_field`), vórtice do tornado
  (`vortex`), espiral do furacão (`spiral_storm`) e neve com vento (`snowstorm`).
- **Painéis de dados, sempre com unidade:** velocímetro (320 km/h), termômetro
  (26,5 °C e 28.000 °C), barra de duração (3 horas) e comparação Sol × raio.
- **Objetos vetoriais animados:** tornado, furacão, nevasca, raio, ampulheta e nuvem.
- **Cartelas de capítulo** e legendas em movimento, ligadas à palavra falada.
- **Plano de cenas decidido antes da montagem** e validado pelo `gauntlet`, sem
  buraco de tela e sem texto sobre objeto.

## Como foi feito

O episódio inteiro cabe em três arquivos que você edita:

| Arquivo | Papel |
| --- | --- |
| `episodios/EP05-tipos-de-tempestade/roteiro.md` | As frases, com id e pausa |
| `episodios/EP05-tipos-de-tempestade/producao/cenas.json` | Objetos, painéis e textos escolhidos à mão |
| `episodios/EP05-tipos-de-tempestade/producao/episode.json` | O plano com os tempos de cada elemento |

Os comandos, na ordem, estão no [README principal](../README.md#crie-o-seu-episódio).
A narração deste vídeo usou o OmniVoice com uma voz de referência do canal, que não
faz parte do repositório. Para narrar o mesmo roteiro com a sua voz, veja
[`prompts/02-voz-local.md`](../prompts/02-voz-local.md) e
[`prompts/03-voz-api.md`](../prompts/03-voz-api.md).

## Limites deste exemplo

- A revisão registrada antes do render foi feita por uma IA e declara isso. Quem
  publicar um vídeo seu deve revisar quadros e áudio pessoalmente.
- O motor não tem uma cena de raio. O capítulo usa o objeto `lightning` e o campo de
  vento.
- O painel Sol × raio compara temperaturas com o tamanho de duas esferas: é uma razão
  visual, não uma escala.
- O vídeo é uma demonstração curta, abaixo da faixa de 10 a 15 minutos do canal
  original.

## Refazer o render

O MP4 não é gerado ao baixar o repositório: ele está aqui pronto. Para ver a
composição sem narração, use o quickstart do README. Um render final exige a sua
voz e a sua revisão, como descreve o [fluxo](../sistema/FLUXO-NIVEL-1.md).
