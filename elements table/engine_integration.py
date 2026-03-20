from core_models import Universe
from element_resources import Element
from physics_engine.src.physics_engine.engine import PhysicsEngine
from physics_engine.src.physics_engine.config import EngineConfig
from map_element_to_physics import map_element_to_physics_params

# Example: Use the first element in the first material in the first room in the first environment

def run_physics_engine_from_hierarchy(universe: Universe):
    element = universe.environments[0].rooms[0].materials[0].elements[0]
    params = map_element_to_physics_params(element)
    # Map params to EngineConfig fields as needed
    config = EngineConfig(
        N=40,
        hbar=1.0,
        omega=1.0,
        phi=2.718,
        dt=0.01,
        lam=0.0,
        kappa=0.0
        # Add more mappings if needed
    )
    engine = PhysicsEngine(config)
    # Example: run a dummy simulation (details depend on your engine)
    # psi0, times = ... (initialize as needed)
    # result = engine.simulate_with_logs(psi0, times, ...)
    print(f"Initialized engine for element: {element.symbol}, params: {params}")
    return engine
