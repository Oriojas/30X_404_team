"""Inyección de dependencias de FastAPI: entrega los casos de uso armados en el composition root."""

from fastapi import Request

from ....container import Container


def get_container(request: Request) -> Container:
    return request.app.state.container
