class LLMManager:

    def __init__(self, router):

        self.router = router

        self.metrics = LLMMetrics()

    def ask(
        self,
        role,
        prompt,
        system_prompt
    ):

        self.metrics.before_call()

        if self.metrics.should_abort():

            raise RuntimeError(
                "Maximum LLM calls exceeded."
            )

        response = self.router.ask(
            role=role,
            prompt=prompt,
            system_prompt=system_prompt,
        )

        self.metrics.after_call()

        return response