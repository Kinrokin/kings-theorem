import unittest
import time
import asyncio
from src.kernels.student_v42 import StudentKernelV42


class DummyLLM:
    def __init__(self, response, delay=0):
        self.response = response
        self.delay = delay

    def __call__(self, **kwargs):
        if self.delay:
            time.sleep(self.delay)
        return self.response


class DummyLLMAsync:
    def __init__(self, response, delay=0):
        self.response = response
        self.delay = delay

    async def __call__(self, **kwargs):
        if self.delay:
            await asyncio.sleep(self.delay)
        return self.response


class TestStudentKernelV42(unittest.TestCase):
    def test_successful_response(self):
        llm = DummyLLM("This is a test solution.")
        sk = StudentKernelV42(llm_call=llm, model_name="test-model")
        problem = {"task": "Solve X", "data": "some data", "constraint": "none"}
        res = sk.staged_solve_pipeline(problem)
        self.assertEqual(res["status"], "PASS (Student)")
        self.assertIn("test solution", res["solution"].lower())
        self.assertEqual(res["model_used"], "test-model")

    def test_error_marker_causes_sit(self):
        llm = DummyLLM("[ERROR] Backend down")
        sk = StudentKernelV42(llm_call=llm, max_retries=0)
        problem = {"task": "T", "data": "", "constraint": ""}
        res = sk.staged_solve_pipeline(problem)
        self.assertEqual(res["status"], "SIT")
        self.assertIsNone(res["solution"])

    def test_exception_with_retries(self):
        class Flakey:
            def __init__(self):
                self.calls = 0

            def __call__(self, **kwargs):
                self.calls += 1
                if self.calls < 2:
                    raise RuntimeError("transient")
                return "recovered"

        f = Flakey()
        sk = StudentKernelV42(llm_call=f, max_retries=2)
        res = sk.staged_solve_pipeline({"task": "t"})
        self.assertEqual(res["status"], "PASS (Student)")
        self.assertIn("recovered", res["solution"]) 

    def test_async_variant(self):
        async def run_async_test():
            async_llm = DummyLLMAsync("async result")
            sk = StudentKernelV42(model_name="async-model")
            res = await sk.async_staged_solve_pipeline({"task": "a"}, async_llm_call=async_llm)
            self.assertEqual(res["status"], "PASS (Student)")
            self.assertIn("async result", res["solution"])

        asyncio.run(run_async_test())


if __name__ == "__main__":
    unittest.main()
