import traceback
from townlet.config.effects_config import CommandConfig, EffectDefinitionConfig
def t(label, fn):
    try:
        r = fn(); print(f"[{label}] OK -> {r}")
    except Exception as e:
        print(f"[{label}] REFUSED {type(e).__name__}: {str(e).splitlines()[0][:160]}")
# do alias collision
t("for_each do", lambda: (lambda c: (c.do, c.delay_do))(CommandConfig.model_validate({"for_each": "all_agents", "as": "a", "do": [{"modify": "bar.energy", "value": "1.0"}]})))
t("delay do", lambda: (lambda c: (c.do, c.delay_do))(CommandConfig.model_validate({"delay": "1", "do": [{"modify": "bar.energy", "value": "1.0"}]})))
t("delay delay_do", lambda: (lambda c: (c.do, c.delay_do))(CommandConfig.model_validate({"delay": "1", "delay_do": [{"modify": "bar.energy", "value": "1.0"}]})))
# effect-level intensity (effects.md:286)
base = dict(id="x", scope="agent", duration=1, reapply_policy="stack", observable=True, on_spawn=[], on_tick=[], on_despawn=[], on_interrupt=[])
t("effect intensity field", lambda: EffectDefinitionConfig(**base, intensity=1.0))
t("observable omitted", lambda: EffectDefinitionConfig(**{k: v for k, v in base.items() if k != "observable"}))
# spawn_item quantity / initial_state / for_each radius
t("spawn_item quantity", lambda: CommandConfig.model_validate({"spawn_item": "apple", "position": "self", "quantity": 3}))
t("spawn_item initial_state", lambda: CommandConfig.model_validate({"spawn_item": "apple", "position": "self", "initial_state": {"durability": 1.0}}))
t("for_each radius", lambda: CommandConfig.model_validate({"for_each": "nearby_agents", "radius": 2.0, "do": [{"modify": "bar.energy", "value": "1.0"}]}))
t("switch case typo key", lambda: CommandConfig.model_validate({"switch": "1", "cases": [{"when": "1", "doo": [{"modify": "bar.energy", "value": "1.0"}]}]}))
t("spawn_effect target 'agent'", lambda: CommandConfig.model_validate({"spawn_effect": "poison", "target": "agent", "intensity": 1.0}))
