import logging
from openai import OpenAI
import os
import base64

logger = logging.getLogger('Mnemo')

llm_model = os.getenv('LLM_MODEL')
openapi_api_key = os.getenv('OPENAPI_API_KEY')
openapi_base_url = os.getenv('OPENAPI_BASE_URL')
llm_temperature = os.getenv('LLM_TEMP')
llm_max_tokens = os.getenv('LLM_MAX_TOKENS')

class MnemoNarrator():
    def __init__(self, model=llm_model, api_key=openapi_api_key):
        decoded_api_key = base64.b64decode(api_key).decode("utf-8")

        self.model = model
        self.client = OpenAI(
            api_key=str(decoded_api_key),
            base_url=openapi_base_url
        )

    def summarize(self, artifacts, user_query):
        if not artifacts or not artifacts.get('documents'):
            logger.error('No artifacts found to analyze.')
            return 'No artifacts found to analyze.'

        context = '\n'.join(artifacts['documents'][0])
        
        prompt = f'''
                  You are Mnemo, a Kubernetes cluster forensics engine.

                  QUERY: {user_query}

                  KUBERNETES EVENTS (chronological, oldest first):
                  {context}

                  IMPORTANT: Your answer MUST be based ONLY on the events listed above. 
                  Do NOT use any knowledge outside of these events.
                  If an event is not listed above, it did not happen.

                  STRICT RULES:
                  - If you cannot find direct evidence in the events above, say so explicitly — do not speculate
                  - Never use "possibly", "likely", "may have" unless you explicitly state what evidence is missing
                  - Every claim must reference at least one event: kind/name + reason + message
                  - If count > 1, state it — recurring events are not one-time failures

                  REASONING GUIDELINES:
                  - Treat the event stream as a causal chain — every state has a trigger
                  - Absence of expected events is significant: no Pulled = image never fetched, no Started = container never ran
                  - CrashLoopBackOff, OOMKilled, Evicted are symptoms — find the cause event before them
                  - Correlate across objects: node pressure evicts pods, quota blocks scheduling
                  - Timestamps clustering = cascading failure, spread out = chronic degradation

                  RESPONSE:
                  **Direct Answer**: Exactly what happened, naming the specific objects involved.

                  **Event Chain**:
                  [timestamp] kind/name — reason: message (count: N)

                  **Root Cause**:
                  - Category: Infrastructure | Configuration | Application | Unknown
                  - Specific trigger: The exact event that started the failure, not the symptom
                  - Evidence: Which event(s) prove this

                  **Gaps**: What events are missing that would make this conclusion more certain
                '''

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {'role': 'user', 'content': prompt}
                ],
                temperature=float(llm_temperature),
                max_tokens=int(llm_max_tokens)
            )
            
            return response.choices[0].message.content
        except Exception as e:
            logger.error(f'Narrator failed: {e}')
            return 'Narrator connection error.'