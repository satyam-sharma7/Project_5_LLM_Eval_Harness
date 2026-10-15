from openai import OpenAI
from dotenv import load_dotenv
import tomllib
import json
import os

load_dotenv()

with open("llm_config.toml", 'rb') as f:
    config = tomllib.load(f)

ACTIVE_MODEL = "gemini"
model_config = config["models"][ACTIVE_MODEL]

from sentence_transformers import SentenceTransformer, util        # consider moving to module level so it doesn't reload on every call
model = SentenceTransformer('all-MiniLM-L6-v2')

client = OpenAI(
    base_url=model_config["url"],
    api_key=os.getenv(model_config['api'])
)


def exact_match(expected: str, actual: str):
    expected_answer = expected.lower().strip()
    actual_response = actual.lower().strip()

    if expected_answer == actual_response:
        return 1
    else:
        return 0


def semantic_similarity(expected: str, actual: str):
    expected_answer = expected.lower()
    actual_response = actual.lower()

    expected_answer_embedding = model.encode(expected_answer, convert_to_tensor=True)
    actual_answer_embedding = model.encode(actual_response, convert_to_tensor=True)

    score = util.cos_sim(expected_answer_embedding, actual_answer_embedding)
    return score.item()



def llm_judge(expected: str, actual: str):
    sys_prompt = """
    You will be given two inputs you have to give score between 0 to 1 there is some example:
    0: There is no logical similiraty between inputs. both inputs have different meanings.
    0.5: There is some logical similiratiy in these inputs. both inputs have almost similar meaning
    1: Both inputs have completely same meaning.
    provide answer in given formate:
    {
        "score": 0.89
    }
    """

    usr_prompt = f"""
    input1: {expected}
    input2: {actual}
    """
    response = client.chat.completions.create(
        model=model_config['name'],
        messages= [
            {"role": "system", "content":sys_prompt},
            {"role": "user", "content": usr_prompt}
        ],
        response_format={"type": "json_object"} 
    )
    print(response.choices[0].message.content)
    score = json.loads(response.choices[0].message.content)
    return score['score']


def evaluate_score(answers):
    answers_score = []
    for answer in answers:
        expected = answer['expected']
        actual = answer['actual']

        answer["exact_match_score"] = exact_match(expected, actual)
        answer["similarity_score"] = semantic_similarity(expected, actual)
        answer["llm_score"] = llm_judge(expected, actual)

        answers_score.append(answer)

    return answers_score

