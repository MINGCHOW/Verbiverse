from Functions.LanguageType import ExplainLanguage
from langchain_core.prompts import (
    PromptTemplate,
)
from LLMServerInfo import (
    getChatModelByCfg,
    getExplainPrompt,
    getMotherTongue,
    getTargetLanguage,
)
from ModuleLogger import logger
from PySide6.QtCore import QThread, Signal


class ExplainWorkerThread(QThread):
    messageCallBackSignal = Signal(str)

    def __init__(
        self,
        selected_text: str,
        all_text: str,
        language_type: ExplainLanguage,
        stream=True,
    ):
        super().__init__()
        self.chain = None
        self.stream = stream
        self.type = language_type
        self.createExplainChain()
        self.msg = {
            "word": selected_text,
            "data": all_text,
            "language": self.target_language,
            "answer_language": self.answer_language,
        }
        logger.info(f"explain request msg is:\n {self.msg}\n")
        self.quit = False

    def createExplainChain(self) -> None:
        self.chain_with_trimming = None
        try:
            self.chat = getChatModelByCfg()
        except Exception as e:
            logger.error("get chat model error: %s", e)
            return
        self.target_language = getTargetLanguage()
        if self.type == ExplainLanguage.TARGET_LANGUAGE:
            self.answer_language = self.target_language
        else:
            self.answer_language = getMotherTongue()

        self.prompt = PromptTemplate.from_template(getExplainPrompt(self.type))
        self.chain = self.prompt | self.chat

    def stop(self):
        self.quit = True

    def run(self):
        if self.chain is None:
            logger.error("explain chain is not set")
            return
        if self.stream:
            content = self.chain.stream(self.msg)
            for chunk in content:
                if self.quit:
                    logger.debug("explanation thread quit")
                    return
                self.messageCallBackSignal.emit(chunk.content)
        else:
            content = self.chain.invoke(self.msg)
            if self.quit:
                logger.debug("explanation thread quit")
                return
            self.messageCallBackSignal.emit(content)