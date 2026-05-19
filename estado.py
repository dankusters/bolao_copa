from typing import Any

aguardando_resposta: set[str] = set()

_estados: dict[str, dict[str, Any]] = {}


def get_estado(numero: str) -> dict | None:
    return _estados.get(numero)


def set_estado(numero: str, etapa: str, dados: dict):
    _estados[numero] = {"etapa": etapa, "dados": dados}


def limpar_estado(numero: str):
    _estados.pop(numero, None)
    aguardando_resposta.discard(numero)
