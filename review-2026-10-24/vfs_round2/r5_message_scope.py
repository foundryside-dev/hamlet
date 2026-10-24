"""R5: message scope end to end — append_event writes the SENDER's own buffer, a zero payload is
indistinguishable from an empty slot, a nonzero initial value makes every slot 'occupied' so every
append is silently dropped, a full buffer drops silently, and nothing can read the buffer."""
from harness import *  # noqa


def run(label, inbox_decl, write_spec, steps, n=2, slots=3, actions_seq=None):
    def vars_(v):
        v["declarations"].append(inbox_decl)
        v["extents"]["num_message_slots"] = slots

    def acts(a):
        for ca in a["custom_actions"]:
            if ca["name"] == "ADVANCE":
                ca["writes"] = [write_spec]

    print(f"--- {label}")
    try:
        u = compile_pack(make_pack(f"r5_{label}", variables=vars_, actions=acts))
        print("   compile: OK")
    except Exception as exc:  # noqa: BLE001
        print(f"   compile: REFUSED {type(exc).__name__}: {str(exc)[:400]}")
        return None
    env = build_env(u, num_agents=n)
    adv, wait = action_index(env, "ADVANCE"), action_index(env, "WAIT")
    for k in range(steps):
        acts_t = torch.tensor(actions_seq[k] if actions_seq else [adv] + [wait] * (n - 1))
        env.step(acts_t)
        print(f"   step{k+1} actions={acts_t.tolist()}: inbox = {reg(env, 'inbox').tolist()}")
    return env


@probe("R5 message scope")
def main():
    base = dict(id="inbox", scope="message", lifetime="episode")
    # 1. sender writes; who receives? (agent 0 sends, agent 1 waits)
    run("append_basic", decl(**base, initial_value=0.0), write("inbox", "agent_id + 1.0", composition="append_event"), steps=4)
    # 2. payload 0.0 is 'free': appends overwrite the same slot forever
    run("append_zero_payload", decl(**base, initial_value=0.0), write("inbox", "0.0", composition="append_event"), steps=2)
    # 3. sentinel initial value -1.0: every slot is 'occupied' from reset; appends silently vanish
    run("append_sentinel_init", decl(**base, initial_value=-1.0), write("inbox", "5.0", composition="append_event"), steps=2)
    # 4. exposure refused; agent expression reading the buffer
    def try_consumer(label, extra):
        print(f"--- {label}")
        try:
            def vars_(v):
                v["declarations"].append(decl(**base, initial_value=0.0))
                v["declarations"].append(extra)
                v["extents"]["num_message_slots"] = 3
            compile_pack(make_pack(f"r5_{label}", variables=vars_))
            print("   compile: OK")
        except Exception as exc:  # noqa: BLE001
            print(f"   compile: REFUSED {type(exc).__name__}: {str(exc)[:300]}")
    try_consumer("agent_expr_reads_inbox", decl("heard", expression="inbox", initial_value=0.0))
    try_consumer("agent_expr_reads_inbox_sum", decl("heard", expression="sum(inbox)", initial_value=0.0))


main()
