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


def _make_service(monkeypatch, *, gpu_enabled, force_cpu, cuda_present, mem_limit=0):
    """Build a fresh AIService with config + onnxruntime simulated via env/reload."""
    monkeypatch.setenv("GPU_ENABLED", "true" if gpu_enabled else "false")
    monkeypatch.setenv("FORCE_CPU", "true" if force_cpu else "false")
    monkeypatch.setenv("CUDA_GPU_MEM_LIMIT", str(mem_limit))

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
    assert providers[-1] == "CPUExecutionProvider"
    assert svc._gpu_active is True
    assert svc._default_model() == "birefnet-general"


def test_no_gpu_mem_limit_by_default(monkeypatch):
    """
    With CUDA_GPU_MEM_LIMIT at its default of 0 the arena must be left uncapped,
    so onnxruntime can grow it to fit large models such as BiRefNet. Setting a
    fixed cap here previously caused "Available memory of 0 is smaller than
    requested bytes".
    """
    svc = _make_service(
        monkeypatch, gpu_enabled=True, force_cpu=False, cuda_present=True, mem_limit=0
    )
    cuda_opts = svc._resolve_providers()[0][1]
    assert "gpu_mem_limit" not in cuda_opts


def test_gpu_mem_limit_applied_when_configured(monkeypatch):
    """A positive CUDA_GPU_MEM_LIMIT must be passed through to the provider."""
    limit = 2 * 1024 * 1024 * 1024
    svc = _make_service(
        monkeypatch, gpu_enabled=True, force_cpu=False, cuda_present=True, mem_limit=limit
    )
    cuda_opts = svc._resolve_providers()[0][1]
    assert cuda_opts["gpu_mem_limit"] == limit


def test_gpu_enabled_but_cuda_missing_falls_back(monkeypatch):
    svc = _make_service(monkeypatch, gpu_enabled=True, force_cpu=False, cuda_present=False)
    providers = svc._resolve_providers()
    assert providers == ["CPUExecutionProvider"]
    assert svc._gpu_active is False
