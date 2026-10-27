# 03 · Voz por API

O provedor `openai` de `pipeline/tts.py` chama `POST {base_url}/audio/speech`, o
formato da API de voz da OpenAI. Muitos serviços e servidores locais imitam essa
rota, então o mesmo código serve para vários.

## Configuração mínima

1. Guarde a chave no `.env` (copie o `.env.example` para `.env` e preencha `OPENAI_API_KEY`).
   O git ignora esse arquivo e o `tts.py` o lê sozinho. Ou defina a variável no terminal:

```powershell
$env:OPENAI_API_KEY = "cole-sua-chave-aqui"
```

   No Linux e no macOS: `export OPENAI_API_KEY="cole-sua-chave-aqui"`.

2. Crie `sistema/voz.local.json` (o git ignora este arquivo):

```json
{
  "provedor": "openai",
  "api": {
    "base_url": "https://api.openai.com/v1",
    "modelo": "gpt-4o-mini-tts",
    "voz": "alloy",
    "instrucoes": "Fale em português do Brasil, em tom claro e direto.",
    "chave_env": "OPENAI_API_KEY"
  }
}
```

3. Gere o manifesto sem referência de voz e teste:

```bash
python pipeline/build_tts_manifest.py episodios/EP06-meu-tema/producao roteiro_fonetico_v1.json v1 --sem-referencia
python pipeline/tts.py episodios/EP06-meu-tema/producao/tts_manifest_v1.json --check
python pipeline/tts.py episodios/EP06-meu-tema/producao/tts_manifest_v1.json
```

Confira o nome do modelo e das vozes, o preço, se o modelo aceita o campo `speed` (alguns o
ignoram) e os termos de uso na documentação atual do serviço. Eles mudam. Quem paga a API é você, e a licença do projeto
continua valendo: você não pode vender o projeto nem trabalhos feitos com ele para clientes.

O que o código já faz: tenta de novo em erro 429, 500, 502, 503 e 504 e em falha de rede, não repete erro 4xx,
converte a resposta para WAV com o ffmpeg se a API devolver mp3, grava cada WAV num arquivo temporário e só o troca depois de validar, não segue redirecionamentos, tem `--retomar` para continuar depois de uma falha sem pagar de novo, não imprime a
chave e recusa sobrescrever WAVs sem `--overwrite`.

## Prompt: usar outra API de voz

```text
Você está ajudando num projeto aberto chamado Catálogo (vídeos explicativos em
português). Leia AGENTS.md, sistema/CONSTRAINTS.md, pipeline/tts.py,
pipeline/test_tts.py e sistema/voz.json antes de começar.

Quero narrar com a API [nome do serviço]. A documentação está em [link]. Minha chave
fica na variável de ambiente [NOME_DA_VARIAVEL]; não vou colar a chave aqui.

Tarefa:
1. Leia a documentação atual do serviço e me diga: rota, formato do pedido, formato da
   resposta (WAV, MP3 ou JSON com base64), limites de tamanho de texto, preço por
   caractere e se a licença permite uso em vídeo publicado. Se algo não estiver claro
   na documentação, diga em vez de supor.
2. Se o serviço imitar a API da OpenAI, não escreva código: só mostre o JSON para
   sistema/voz.local.json.
3. Se não imitar, acrescente um provedor novo em pipeline/tts.py seguindo o padrão de
   sintetizar_openai: função sintetizar_[nome](data, config), campo "[nome]" no
   sistema/voz.json com valores padrão sem segredo, a chave vinda de variável de
   ambiente, reintentos só para 429 e 5xx, conversão para WAV com ffmpeg quando
   preciso, verificação de WAV não vazio e mensagem de erro que nunca inclua a chave.
   Inclua o nome na tupla PROVEDORES e no ramo de main().
4. Escreva testes em pipeline/test_tts.py com um servidor HTTP simulado (a classe
   Servidor do arquivo mostra como). Nenhum teste pode chamar a rede de verdade.
5. Rode python -m unittest discover -s pipeline -p "test_*.py" e mostre o resultado.
6. Atualize prompts/03-voz-api.md com um exemplo de configuração do novo provedor.

Não afrouxe nenhum limite de sistema/CONSTRAINTS.md, não grave a chave em arquivo e não
altere o formato do manifesto (id, text, output, speed, seed).
```

## Prompt: trocar a voz, a velocidade ou o tom

```text
Leia sistema/voz.json, pipeline/tts.py e sistema/FONETICA-PTBR.md. Quero que a
narração fique [mais lenta / mais rápida / mais séria / mais animada] e com a voz
[nome]. Mostre o que posso mudar só em sistema/voz.local.json (voz, modelo,
instrucoes) e em build_tts_manifest.py (--speed). Gere uma frase de teste, me diga
onde está o WAV e só depois regenere o episódio inteiro com um manifesto novo
(versão v2), sem sobrescrever os WAVs da v1.
```
