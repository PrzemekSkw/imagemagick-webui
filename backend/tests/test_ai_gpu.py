"""
Unit tests for GPU provider resolution in AIService.

No real GPU required. The config is driven via environment variables and a
module reload (the supported way to configure pydantic-settings), and a fake
onnxruntime module is injected so CUDA availability can be simulated anywhere,
including CI runners without a GPU.
"""

import sys
import types
import importlib

import pytest


def _make_service(monkeypatch, *, gpu_enabled, force_cpu, cuda_present):
    """Build a fresh AIService with config + onnxruntime simulated via env/reload."""
    monkeypatch.setenv("GPU_ENABLED", "true" if gpu_enabled else "false")
    monkeypatch.setenv("FORCE_CPU", "true" if force_cpu else "false")

    from app.core import config
    importlib.reload(config)

    fake_ort = types.ModuleType("onnxruntime")
    providers = ["CPUExecutionProvider"]
    if cuda_present:
        providers = ["CUDAExecutionProvider", "CPUExecutionProvider"]
    fake_ort.get_available_providers = lambda: providers
    fake_ort.get_device = lambda: "GPU" if cuda_present else "CPU"
    monkeypatch.setitem(sys.modules, "onnxruntime", fake_ort)

    from app.services import ai_service as ai_mod
    importlib.reload(ai_mod)
    return ai_mod.AIService()


def test_cpu_only_when_gpu_disabled(monkeypatch):
    svc = _make_service(monkeypatch, gpu_enabled=False, force_cpu=False, cuda_present=True)
    providers = svc._resolve_providers()
    assert providers == ["CPUExecutionProvider"]
    assert svc._gpu_active is False
    assert svc._default_model() == "isnet-general-use"


def test_force_cpu_overrides_gpu(monkeypatch):
    svc = _make_service(monkeypatch, gpu_enabled=True, force_cpu=True, cuda_present=True)
    providers = svc._resolve_providers()
    assert providers == ["CPUExecutionProvider"]
    assert svc._gpu_active is False


def test_cuda_selected_with_cpu_fallback(monkeypatch):
    svc = _make_service(monkeypatch, gpu_enabled=True, force_cpu=False, cuda_present=True)
    providers = svc._resolve_providers()
    assert providers[0][0] == "CUDAExecutionProvider"
    assert providers[0][1]["gpu_mem_limit"] == 2 * 1024 * 1024 * 1024
    assert providers[-1] == "CPUExecutionProvider"
    assert svc._gpu_active is True
    assert svc._default_model() == "birefnet-general"


def test_gpu_enabled_but_cuda_missing_falls_back(monkeypatch):
    svc = _make_service(monkeypatch, gpu_enabled=True, force_cpu=False, cuda_present=False)
    providers = svc._resolve_providers()
    assert providers == ["CPUExecutionProvider"]
    assert svc._gpu_active is False
