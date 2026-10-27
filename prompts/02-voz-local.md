# 02 · Voz local (sem pagar API)

A narração sai por `pipeline/tts.py`. Ele lê um manifesto (um texto por segmento)
e grava um WAV por segmento. O resto do pipeline só vê os WAVs, então você pode
trocar de modelo de voz sem mexer em mais nada.

Três jeitos de rodar uma voz na sua máquina:

| Jeito | Provedor | Quando escolher |
| --- | --- | --- |
| Servidor local que imita a API da OpenAI (Kokoro-FastAPI, por exemplo) | `openai` | Quer a mesma configuração da API, mas rodando no seu computador |
| Programa de linha de comando (Piper) | `comando` | Quer algo leve, que roda até sem placa de vídeo |
| OmniVoice, que clona uma voz a partir de uma gravação | `omnivoice` | Quer a sua própria voz. Os pesos do modelo são só para uso não comercial |

Confira a licença de cada modelo e de cada voz antes de publicar. Use só uma voz
sua ou uma voz que você tem autorização para usar.

## Como o projeto escolhe o provedor

`sistema/voz.json` é público e vale para todos. O que é só da sua máquina vai em
`sistema/voz.local.json`, que o git ignora. Você escreve nele só as chaves que
quer trocar. Também dá para escolher na hora: `--provedor comando`.

Teste sempre sem sintetizar nada primeiro:

```bash
python pipeline/tts.py episodios/EP06-meu-tema/producao/tts_manifest_v1.json --check
```

Para gerar o manifesto sem voz de referência use `--sem-referencia`:

```bash
python pipeline/build_tts_manifest.py episodios/EP06-meu-tema/producao roteiro_fonetico_v1.json v1 --sem-referencia
```

## Exemplo A: Piper, pelo provedor `comando`

`sistema/voz.local.json`:

```json
{
  "provedor": "comando",
  "comando": {
    "argv": ["piper", "--model", "CAMINHO/pt_BR-faber-medium.onnx", "--output_file", "{saida}"],
    "entrada": "stdin"
  }
}
```

O texto entra por stdin e `{saida}` vira o caminho do WAV. Com `"entrada": "arquivo"`
o texto vai num arquivo temporário e você usa `{texto_arquivo}` no lugar do stdin.
Os campos aceitos são `{saida}`, `{texto_arquivo}` e `{id}`.

## Exemplo B: Kokoro-FastAPI, pelo provedor `openai`

`sistema/voz.local.json`:

```json
{
  "provedor": "openai",
  "api": {
    "base_url": "http://localhost:8880/v1",
    "modelo": "kokoro",
    "voz": "pf_dora",
    "exige_chave": false
  }
}
```

A porta e os nomes das vozes dependem do servidor. Peça a lista em
`GET /v1/audio/voices` e use o nome exato.

## Prompt: montar a voz local com a IA

```text
Você está ajudando a configurar a narração de um projeto aberto chamado Catálogo
(vídeos explicativos em português). Leia AGENTS.md, sistema/CONSTRAINTS.md,
sistema/voz.json e pipeline/tts.py antes de começar. A narração sai por
pipeline/tts.py, que tem três provedores: omnivoice, openai (qualquer servidor que
imite POST /v1/audio/speech) e comando (um programa local chamado por segmento).

Meu computador: [sistema operacional, RAM, placa de vídeo ou "sem placa de vídeo"].
Quero narrar em [português do Brasil] com uma voz [masculina / feminina / minha própria voz].

Tarefa:
1. Recomende UMA opção local para o meu computador entre: Piper (provedor comando),
   um servidor local compatível com a API da OpenAI, como o Kokoro-FastAPI (provedor
   openai), e OmniVoice (provedor omnivoice). Explique a escolha em 5 linhas, com o
   peso do download, a velocidade esperada e a licença do modelo e da voz.
   Confirme as informações na documentação atual do projeto escolhido, porque comandos
   e nomes de voz mudam. Se não conseguir confirmar algo, diga.
2. Me mostre os comandos de instalação e espere minha aprovação. Instale em uma pasta
   própria (por exemplo .venv-voz ou uma pasta fora do repositório), nunca no ambiente
   do projeto e nunca em disco que eu não indicar.
3. Crie ou atualize sistema/voz.local.json com a configuração. Não edite
   sistema/voz.json e não grave caminhos da minha máquina em nenhum arquivo versionado.
4. Gere o manifesto de teste de um episódio (build_tts_manifest.py, com
   --sem-referencia se o provedor não clona voz), rode "python pipeline/tts.py
   <manifesto> --check" e depois sintetize 2 frases. Toque os WAVs com ffplay ou me
   diga o caminho para eu ouvir.
5. Meça a duração de cada WAV com pipeline/measure_durations.py e confira que o
   pipeline segue normal até assemble.py.
6. Escreva, em até 10 linhas, como repetir isso numa máquina nova.

Se o modelo pronunciar mal nomes, siglas ou números, não mude o código: proponha
ajustes em sistema/FONETICA-PTBR.md ou no dicionário de pipeline/fonetica.py.
Rode python -m unittest discover -s pipeline -p "test_*.py" no fim e mostre o resultado.
```

## Prompt: ligar um modelo de voz que não tem servidor nem comando

```text
Leia pipeline/tts.py (funções sintetizar_openai e sintetizar_comando) e
pipeline/test_tts.py. Quero usar o modelo de voz [nome do modelo], que roda em Python
com esta chamada: [cole o exemplo de uso da documentação do modelo].

Crie um script pipeline/voz_[nome].py que receba "--manifest <arquivo>" e grave um
WAV por segmento, igual ao contrato do manifesto (campos id, text, output). Depois
configure o provedor comando para chamar esse script, sem alterar tts.py.
Escreva testes em pipeline/test_voz_[nome].py que não baixem o modelo (use um
substituto simples) e rode a suíte inteira. O script deve falhar com mensagem clara
se o modelo não estiver instalado.
```
