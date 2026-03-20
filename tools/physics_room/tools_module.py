from __future__ import annotations

"""Compatibility facade for split probes/interpreters modules."""

from .probes import DataAcquisition, DemoManifold, ManifoldLike, STMTool, SpectroscopyTool, ToolType
from .interpreters import MicroscopistExpert, OllamaToolExpert, SpectroscopistExpert


__all__ = [
    "ToolType",
    "ManifoldLike",
    "DataAcquisition",
    "STMTool",
    "SpectroscopyTool",
    "DemoManifold",
    "OllamaToolExpert",
    "MicroscopistExpert",
    "SpectroscopistExpert",
]


if __name__ == "__main__":
    manifold = DemoManifold(temperature=6.0)
    stm = STMTool(kappa=1.25, setpoint_current=0.8, z_surface=0)
    spectroscopy = SpectroscopyTool(sample_rate=198.0, instrument="raman")

    scan_result = stm.scan(manifold, x_range=(0, 32), y_range=(0, 32))
    spectrum_result = spectroscopy.probe_manifold(manifold, ticks=256)

    print("STM scan complete")
    print(f"height map size: {len(scan_result['height_map'])}x{len(scan_result['height_map'][0])}")
    print(f"spectral peaks found: {len(spectrum_result['peaks'])}")
