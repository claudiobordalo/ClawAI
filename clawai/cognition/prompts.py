BASE_SYSTEM_PROMPT = (
    "Você é o ClawAI, um agente de desenvolvimento dentro do próprio projeto. "
    "Responda como o ClawAI e seja direto."
)

SUPERVISOR_PROMPT = (
    "Classifique a solicitação e responda em JSON puro com intent, primary_role, "
    "strategy, should_parallel, confidence e rationale."
)

PLANNER_PROMPT = (
    "Produza um plano curto com objetivo, subtarefas numeradas, riscos e critério de pronto."
)

CODER_PROMPT = (
    "Proponha a implementação concreta: arquivos prováveis, mudanças e próximos passos."
)

REVIEWER_PROMPT = (
    "Revise a proposta, aponte lacunas, riscos e melhorias objetivas."
)

SYNTH_PROMPT = (
    "Sintetize a melhor resposta final ao usuário em português, sem mencionar etapas internas."
)

CODER_HINTS = (
    "implemente",
    "corrija",
    "refatore",
    "ajuste",
    "arquivo",
    "frontend",
    "backend",
    "react",
    "tsx",
    "py",
    "python",
    "ui",
    "interface",
)

PLANNER_HINTS = (
    "planeje",
    "plano",
    "backlog",
    "roadmap",
    "arquitetura",
    "priorize",
    "organize",
)

REVIEWER_HINTS = (
    "revise",
    "review",
    "avaliar",
    "audite",
    "compare",
    "analisar",
)

VISION_SUFFIXES = {
    ".png",
    ".jpg",
    ".jpeg",
    ".webp",
    ".bmp",
    ".gif",
    ".tiff",
    ".tif",
}