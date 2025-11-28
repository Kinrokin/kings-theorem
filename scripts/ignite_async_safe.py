import argparse
import asyncio
import json
from pathlib import Path
from typing import Dict

import aiofiles
from tqdm.asyncio import tqdm

from src.config.loader import load_constitution
from src.governance.paradox_harmonizer import ParadoxHarmonizer
from src.governance.semantic_guard import SemanticGuard

# KT imports (thread-safe adapters per task)
from src.models.adapters import OpenAIAdapter
from src.mtl.mtl_runtime_stub import MTLEngineStub
from src.primitives.event_log_adapter import SimpleEventLog
from src.runtime.guarded_executor import KTGuardedExecutor
from src.runtime.tools import ToolRegistry
from src.trinity.society import ArbiterCouncil, StudentCouncil, TeacherCouncil

# Safety & Concurrency Config
CONCURRENCY_LIMIT = 10  # Conservative start
SAFETY_STOP_WORDS = ["bio-weapon", "explosive", "hack", "exploit"]  # Hard stop filter


class AsyncBackend:
    def __init__(self):
        self.trace = []

    def append_event(self, event):
        self.trace.append(event)


def build_safe_executor(model_name: str):
    constitution = load_constitution()
    adapter = OpenAIAdapter("Teacher", {"model": model_name})
    executor = KTGuardedExecutor(
        students=StudentCouncil([adapter]),
        teachers=TeacherCouncil([adapter]),
        arbiters=ArbiterCouncil([adapter]),
        semantic_guard=SemanticGuard(),
        mtl_engine=MTLEngineStub(),
        harmonizer=ParadoxHarmonizer(constitution),
        event_log=SimpleEventLog(AsyncBackend()),
        tool_registry=ToolRegistry(),
    )
    executor.backend_ref = executor.event_log.backend
    return executor


async def process_crucible(sem, crucible: Dict, teacher_model: str):
    async with sem:
        prompt_lower = crucible["prompt"].lower()
        if any(w in prompt_lower for w in SAFETY_STOP_WORDS):
            return {"status": "SKIPPED_SAFETY", "id": crucible["id"]}

        executor = build_safe_executor(teacher_model)
        request = {
            "actor": "ignition",
            "intent": "echo",
            "payload": {"prompt": crucible["prompt"]},
            "context": {"crucible_id": crucible["id"]},
        }
        result = await asyncio.to_thread(executor.execute, request)
        trace = list(executor.backend_ref.trace)
        status = "GOLDEN"
        final_output = result.get("result") or result.get("reason")
        if result["status"] != "OK":
            status = "LAZARUS_ATTEMPT"
            veto_reason = result.get("reason", "Unknown Violation")
            repair_prompt = (
                f"SCENARIO: {crucible['prompt']}\n\n"
                f"ERROR: The previous attempt was blocked because: {veto_reason}\n\n"
                "INSTRUCTION: Provide a corrected, constitutionally compliant response "
                "that resolves the paradox/violation explicitly. Do not bypass safety."
            )
            repair_req = {"actor": "lazarus", "intent": "echo", "payload": {"prompt": repair_prompt}}
            repair_res = await asyncio.to_thread(executor.execute, repair_req)
            if repair_res["status"] == "OK":
                status = "LAZARUS_RECOVERED"
                trace.extend(executor.backend_ref.trace[len(trace) :])
                final_output = repair_res.get("result")
            else:
                status = "FAILED"
        return {
            "crucible_id": crucible["id"],
            "input": crucible["prompt"],
            "status": status,
            "final_output": final_output,
            "full_trace": trace,
        }


async def main_async(input_path: Path, output_path: Path, teacher: str):
    sem = asyncio.Semaphore(CONCURRENCY_LIMIT)
    with open(input_path) as f:
        data = [json.loads(line) for line in f]
    print(f"⚡ Safe Ignition: Processing {len(data)} crucibles...")
    async with aiofiles.open(output_path, "a") as f_out:
        for fut in tqdm(asyncio.as_completed([process_crucible(sem, c, teacher) for c in data]), total=len(data)):
            res = await fut
            if res["status"] in ["GOLDEN", "LAZARUS_RECOVERED"]:
                await f_out.write(json.dumps(res) + "\n")
            elif res["status"] == "SKIPPED_SAFETY":
                print(f"⚠️ Skipped potentially unsafe prompt: {res['id']}")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--teacher", default="gpt-4o")
    args = parser.parse_args()
    asyncio.run(main_async(Path(args.input), Path(args.output), args.teacher))


if __name__ == "__main__":
    main()
