// Plugin opencode do Catálogo: transforma a regra do AGENTS.md em bloqueio.
//
// O AGENTS.md diz que final só sai por `pipeline/render_final.py` e a
// FLUXO-NIVEL-1.md admite que a CLI direta contorna os gates. Instrução que o
// agente pode ignorar não é gate. Aqui a CLI direta que produz MP4 é recusada
// na raiz, e o HyperFrames continua disponível para check, snapshot e preview —
// que é o que a documentação permite.
//
// Cobre: `npx hyperframes render`, `npx hyperframes batch`, `pnpm/yarn/bunx`
// equivalentes e qualquer `hyperframes` empacotado que renderize. Não é uma
// barreira de segurança: um processo pode contornar. Barreira de segurança é
// `render_final.py`, que revalida hashes e roda os gates antes de renderizar.

const RENDER = /\bhyperframes(\s+|[\\/]|$)/;

function commandOf(args) {
  if (!args) return "";
  if (typeof args === "string") return args;
  return [args.command, ...(args.args || [])].join(" ");
}

function renderIntent(command) {
  const normalized = command.replace(/\\/g, "/");
  if (!RENDER.test(normalized)) return false;
  // help/doctor/version não renderizam nada e ficam liberados.
  return /\b(render|batch)\b/.test(normalized) && !/--help|\bhelp\b|\bdoctor\b|\bversion\b/.test(normalized);
}

export default async () => {
  return {
    "tool.execute.before": async (input, output) => {
      if (input.tool !== "bash") return;
      const command = commandOf(output.args);
      if (!renderIntent(command)) return;
      throw new Error(
        [
          "Render direto recusado pelo plugin do Catálogo.",
          "",
          `Comando: ${command.trim()}`,
          "",
          "A CLI do HyperFrames contorna os gates e não constitui final validado.",
          "Use, a partir da raiz do clone:",
          "  python pipeline/render_final.py episodios/EPxx-<slug>/producao --validate-only",
          "  python pipeline/render_final.py episodios/EPxx-<slug>/producao --output final-v1.mp4",
          "",
          "Para preview curto (60 s, sem narração) use prepare_preview.py + a CLI — isso é demo,",
          "não final. Pela CLI, check, snapshot, preview e doctor continuam liberados.",
        ].join("\n"),
      );
    },
  };
};