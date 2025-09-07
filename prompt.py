from langchain_core.prompts.chat import HumanMessagePromptTemplate
from langchain_core.prompts import ChatPromptTemplate
import logging
from logging_config import configure_logging


# ロギング初期化
configure_logging()
logger = logging.getLogger(__name__)


system_prompt = "あなたは設計書の内容を読み取り回答する優秀なAIです。質問に対して丁寧に回答してください。"
human_prompt = """
以下の参考情報をもとに、ユーザーの質問に対して簡潔に回答してください。
また、画像のリンクが含まれている場合は画像を添付しますので、画像も参照して回答してください。
回答にあたって、画像が参考になる場合は、回答中に画像を挿入してください。その際は参考情報のMarkdown形式の画像リンクをそのまま使用してください。
質問：
{question}

参考情報:
{references}
"""


def create_prompt_with_images(image_templates):

    list_prompt = [human_prompt]
    logger.debug("List Prompt before extending: %d", len(list_prompt))
    list_prompt.extend(image_templates)
    logger.debug("List Prompt after extending: %d", len(list_prompt))
    human_message_template = HumanMessagePromptTemplate.from_template(list_prompt)
    prompt = ChatPromptTemplate.from_messages([("system", system_prompt), human_message_template])
    return prompt
