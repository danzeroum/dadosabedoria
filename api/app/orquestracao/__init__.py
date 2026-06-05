"""Orquestração (Dagster) — Degrau 1: job agendado da esteira CAGED (doc técnico §2.1).

O runtime do Dagster é dependência opcional (extra ``orquestracao``); só o contêiner
``orchestrator`` o instala. A lógica de pipeline é testável sem Dagster (ver ``app.ingestao``).
"""
