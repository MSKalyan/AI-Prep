from pydantic import BaseModel


class LLMMessageSchema(BaseModel):
    content: str


class LLMChoiceSchema(BaseModel):
    message: LLMMessageSchema


class LLMUsageSchema(BaseModel):
    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0


class LLMResponseSchema(BaseModel):
    choices: list[LLMChoiceSchema]
    usage: LLMUsageSchema = LLMUsageSchema()