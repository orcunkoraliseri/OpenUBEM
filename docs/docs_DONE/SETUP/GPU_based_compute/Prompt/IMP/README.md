# IMP — External opinions on the GPU heat-balance engine

This folder holds prompts for outside evaluators (Gemini) and their results. Our own spec lives two levels up in `../../BUILD_SPEC_gpu_heat_balance_engine.md`.

| File | What |
|---|---|
| `IMP01_prompt_second_opinion_blind.md` | Second opinion. An independent design prompt that does **not** include our spec, to avoid anchoring. Run it first. |
| `IMP02_prompt_third_opinion_redteam.md` | Third opinion. A red-team review of our spec; paste the spec into it. |
| `IMP03_prompt_owner_decisions.md` | Decision advice on D1–D5 (owner decisions). Self-contained prompt; save to `results/IMP03_result.md`. |
| `results/` | Save `IMP01_result.md`, `IMP02_result.md` and `IMP03_result.md` here. |

Run order: IMP01, then IMP02 in a separate session. Then reconcile the results into `../../BUILD_SPEC_gpu_heat_balance_engine.md` as rev. 2. IMP03 runs after rev. 2, in a new session; the owner then takes decisions D1–D5.
