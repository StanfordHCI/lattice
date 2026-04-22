from typing import List, Any
from AsyncLLM import AsyncLLM
from SyncLLM import SyncLLM
from utils import batched_call, parse_model_json, parse_model_json_with_fallback
from prompts import OBSERVE_PROMPT
from models import Observation, Interaction, Session
import logging

logger = logging.getLogger(__name__)

class Observer:
    def __init__(self, name: str, model: AsyncLLM, format_model: SyncLLM, description: str = "the user's actions and screen activities", params: dict = {"window_size": 10, "max_concurrent": 100}):
        self.name = name
        self.model = model
        self.format_model = format_model
        self.description = description
        self.window_size = params["window_size"]
        self.max_concurrent = params["max_concurrent"]

    async def make_session_observation(self, session: Interaction, observer_types: List[str] = ["default"]) -> List[dict | str]:
        """
        Make observations for a single session.
        Args:
            session: The session to make observations for.
            observer_types: The types of observers to make observations for.

        Returns:
            A list of observations for the session.
        """

        session_length = len(session)
        tasks = []
        for index in range(0, session_length, self.window_size):
            sel_trace = session[index:index+self.window_size]
            sel_interactions = [i['interaction'] for i in sel_trace]
            sel_metadata = [i['metadata'] for i in sel_trace]
            trace_info = []
            for trace, metadata in zip(sel_interactions, sel_metadata):
                for item in metadata.keys():
                    trace_info.append(item)
                    trace_info.append(metadata[item])
                trace_info.append(trace)
            fmt_trace = "\n".join(trace_info)
            if "default" in observer_types:
                fmt_prompt = OBSERVE_PROMPT.format(interaction_description=self.description, user_name=self.name, interactions=fmt_trace)
            else:
                logger.error("Other types of observers are not supported yet")
            tasks.append(self.model.call(fmt_prompt))
        return await batched_call(tasks, max_concurrent=self.max_concurrent)

    async def observe(self, interactions: List[Session], observer_types: List[str] = ["default"]) -> List[List[dict]]: 
        """
        Make observations for a list of sessions.
        Args:
            interactions: The list of sessions to make observations for.
            observer_types: The types of observers to make observations for.

        Returns:
            A list of observations for the list of sessions.
        """

        tasks = []
        for session in interactions:
            tasks.append(self.make_session_observation(session['interactions'], observer_types))
        observations = await batched_call(tasks, max_concurrent=self.max_concurrent)

        output_observations = []

        obs_id = 0
        for sid, session_observations in enumerate(observations):
            fmt_observations = [self._fmt_observation(observation) for observation in session_observations if observation is not None]
            for observations in fmt_observations:
                if "observations" not in observations:
                    logger.error(f"No observations found for session {sid}")
                    continue
                for obs in observations["observations"]:
                    for obs_type in ["think_feel", "actions"]:
                        if obs_type in obs:
                            obs_node = {
                                "id": obs_id,
                                "observation": obs[obs_type],
                                "confidence": obs["confidence"],
                                "metadata": {
                                    "input_session": sid
                                }
                            }
                            if "time" in session:
                                obs_node["metadata"]["time"] = session["time"]
                            output_observations.append(obs_node)
                            obs_id += 1
        return output_observations
    
    def _fmt_observation(self, observation: str) -> dict:
        """
        Format an observation into a dictionary.
        Args:
            observation: The observation to format.

        Returns:
            A dictionary of the observation.
        """
        try:
            fmt_observation = parse_model_json(observation)
            return fmt_observation
        except Exception as e:
            logger.error(f"Error parsing observation: {e}")
            logger.info(f"Using fallback parser")
            try: 
                fmt_observation = parse_model_json_with_fallback(
                    observation, 
                    self.format_model,
                    Observation
                )
                return fmt_observation
            except Exception as e:
                logger.error(f"Error parsing observation: {e} | {observation}")
                return {"observations": []}
