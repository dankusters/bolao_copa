import json
import os
from typing import Any

aguardando_resposta: set[str] = set()

_ESTADO_FILE = os.path.join(os.path.dirname(__file__), ".estado.json")


def _carregar() -> dict[str, dict[str, Any]]:
    try:
        with open(_ESTADO_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {}


def _salvar(estados: dict):
    with open(_ESTADO_FILE, "w", encoding="utf-8") as f:
        json.dump(estados, f, ensure_ascii=False)


def get_estado(numero: str) -> dict | None:
    return _carregar().get(numero)


def set_estado(numero: str, etapa: str, dados: dict):
    estados = _carregar()
    estados[numero] = {"etapa": etapa, "dados": dados}
    _salvar(estados)


def limpar_estado(numero: str):
    estados = _carregar()
    estados.pop(numero, None)
    _salvar(estados)
    aguardando_resposta.discard(numero)
