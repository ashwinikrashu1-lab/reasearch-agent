"""
IBM watsonx.ai client — wraps ibm-watsonx-ai SDK for Granite model calls.
"""
import os
from ibm_watsonx_ai import APIClient, Credentials
from ibm_watsonx_ai.foundation_models import ModelInference
from ibm_watsonx_ai.metanames import GenTextParamsMetaNames as GenParams
from agent.instructions import get_system_prompt

_client = None
_model = None


def _get_client():
    global _client
    if _client is None:
        creds = Credentials(
            url=os.getenv("WATSONX_URL", "https://us-south.ml.cloud.ibm.com"),
            api_key=os.getenv("IBM_API_KEY"),
        )
        _client = APIClient(creds)
    return _client


def _get_model():
    global _model
    if _model is None:
        client = _get_client()
        _model = ModelInference(
            model_id=os.getenv("GRANITE_MODEL_ID", "ibm/granite-3-8b-instruct"),
            api_client=client,
            project_id=os.getenv("WATSONX_PROJECT_ID"),
            params={
                GenParams.MAX_NEW_TOKENS: 2048,
                GenParams.TEMPERATURE: 0.3,
                GenParams.TOP_P: 0.9,
                GenParams.REPETITION_PENALTY: 1.1,
            },
        )
    return _model


def generate(prompt: str, system: str = None, max_tokens: int = 2048) -> str:
    model = _get_model()
    sys_msg = system or get_system_prompt()
    full_prompt = f"<|system|>\n{sys_msg}\n<|user|>\n{prompt}\n<|assistant|>\n"
    result = model.generate_text(
        prompt=full_prompt,
        params={GenParams.MAX_NEW_TOKENS: max_tokens},
    )
    return result.strip() if result else "No response generated."


def generate_stream(prompt: str, system: str = None):
    model = _get_model()
    sys_msg = system or get_system_prompt()
    full_prompt = f"<|system|>\n{sys_msg}\n<|user|>\n{prompt}\n<|assistant|>\n"
    for chunk in model.generate_text_stream(prompt=full_prompt):
        yield chunk
