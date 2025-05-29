from typing import Any, Dict, Tuple

class Protocol:
    def __init__(self):
        self.agents = {}

    def register_agent(self, agent_name: str, agent: Any) -> None:
        self.agents[agent_name] = agent

    def route_input(self, input_data: Dict[str, Any]) -> Tuple[str, Any]:
        input_type = input_data.get("type")
        intent = input_data.get("intent")

        if input_type == "email":
            return "email_agent", self.agents["email_agent"].process(input_data)
        elif input_type == "json":
            return "json_agent", self.agents["json_agent"].process(input_data)
        elif input_type == "pdf":
            return "classifier_agent", self.agents["classifier_agent"].process(input_data)
        else:
            raise ValueError("Unsupported input type")

    def get_agent_status(self) -> Dict[str, str]:
        return {name: agent.get_status() for name, agent in self.agents.items()}