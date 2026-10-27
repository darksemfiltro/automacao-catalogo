# Fonética PT-BR — o roteiro antes do TTS

> O OmniVoice lê o que está escrito, não o que você quis dizer. `pipeline/fonetica.py`
> transforma o roteiro legível em **texto falável** antes de gerar o áudio.

## 1. Regra de ouro

**Escreva como se pronuncia.** O roteiro aprovado (legível) é o `roteiro.md`; o texto que
vai para o TTS é o `roteiro_fonetico.json`, gerado pelo script.

## 2. O que o script já converte (pt-BR)

| Escrito | Falado |
|---|---|
| `6` | seis |
| `75%` | setenta e cinco por cento |
| `2500 e 3500 Kelvin` | dois mil e quinhentos e três mil e quinhentos Kélvin |
| `5,5 toneladas` | cinco vírgula cinco toneladas |
| `1 trilhão` | um trilhão |
| `13,8 bilhões` | treze bilhões e oitocentos milhões |
| `1700x` | mil e setecentas vezes |
| `10000 K` | dez mil Kélvin |
| `km/s` | quilômetros por segundo |
| `massas solares` | massas solares |
| `R$ 1.500` | mil e quinhentos reais |
| `&` `+` `=` `@` `°` | e · mais · igual a · arroba · graus |

## 3. Siglas e classes espectrais

Soletradas ou lidas como palavra:

| Sigla | Para o TTS |
|---|---|
| NASA | nássa |
| ESA | éssa |
| JPL | jota pê éle |
| JWST | jota duplo u |
| SGR | ésse gê érre |
| UV | u vê |

Classe espectral: `tipo K` → `tipo cá`, `tipo G` → `tipo gê`, `tipo M` → `tipo eme`.

## 4. Estrangeirismos e nomes próprios

| Escrito | Para o TTS |
|---|---|
| YouTube | iutúbi |
| Google | gúgol |
| site | saite |
| Wolf-Rayet | Volf Raiet |
| Betelgeuse | Beteljeuse |
| UY Scuti | u ipsilon Escúti |
| Jocelyn Bell Burnell | Jósselin Bel Burnel |
| LGM-1 | éle gê eme um |

Nomes próprios brasileiros e termos já aportuguesados ficam como estão
(Pantanal, Cerrado, Kelvin).

## 5. Ritmo e pausa

O TTS respeita pontuação:
- vírgula = meia pausa · ponto = pausa · reticências = suspensão · parágrafo = respiração maior.
- Frase de uma palavra em linha própria = pausa dramática.
- Evite ponto-e-vírgula e parênteses longos (o TTS lê mal).

## 6. Regerar uma frase só

Escreva `@2` no fim do id (`- \`av03@2\``) e rode `build_tts_manifest.py` + o batch de novo.
A semente é `90000 + n*1000 + (tentativa-1)`, então só aquela frase muda.

## 7. Checklist antes do TTS

- [ ] `python pipeline/fonetica.py --in segments.json --check` com 0 pendências
- [ ] Cada sigla na forma falada (tabela acima)
- [ ] Nenhum `%`, `R$`, `km`, `m²`, `&`, `@`, `K` cru sobrou
- [ ] Li em voz alta mentalmente sem travar
