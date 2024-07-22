# !/usr/bin/env python3
# -*- coding:utf-8 -*-

# @Time    : 2024/3/14 16:07
# @Author  : wangchongshi
# @Email   : wangchongshi.wcs@antgroup.com
# @FileName: chat_memory.py
from typing import Optional, List

from langchain.memory.chat_memory import BaseChatMemory

from agentuniverse.agent.memory.enum import MemoryTypeEnum
from agentuniverse.agent.memory.memory import Memory
from agentuniverse.agent.memory.message import Message
from agentuniverse.agent.memory.langchain_instance import AuConversationSummaryBufferMemory, \
    AuConversationTokenBufferMemory
from agentuniverse.base.config.component_configer.configers.memory_configer import MemoryConfiger
from agentuniverse.base.util.memory_util import get_memory_string
from agentuniverse.llm.llm import LLM


class ChatMemory(Memory):
    """The basic class for chat memory model.

    Attributes:
        llm (LLM): the LLM instance used by this memory.
        input_key (Optional[str]): The input key in the model input parameters is used to find the specific query in a
        round of conversations.
        output_key (Optional[str]): The output key in the model output parameters is used to find the specific result
        in a round of conversations.
        messages (Optional[List[Message]]): The list of conversation messages to send to the LLM memory.
    """

    llm: Optional[LLM] = None
    input_key: Optional[str] = 'input'
    output_key: Optional[str] = 'output'
    messages: Optional[List[Message]] = []
    prompt_version: Optional[str] = None

    def as_langchain(self) -> BaseChatMemory:
        """Convert the agentUniverse(aU) chat memory class to the langchain chat memory class."""
        if self.llm is None:
            raise ValueError("Must set `llm` when using langchain memory.")
        if self.type is None or self.type == MemoryTypeEnum.SHORT_TERM:
            return AuConversationTokenBufferMemory(llm=self.llm.as_langchain(), memory_key=self.memory_key,
                                                   input_key=self.input_key, output_key=self.output_key,
                                                   max_token_limit=self.max_tokens, messages=self.messages)
        elif self.type == MemoryTypeEnum.LONG_TERM:
            return AuConversationSummaryBufferMemory(llm=self.llm.as_langchain(), memory_key=self.memory_key,
                                                     input_key=self.input_key, output_key=self.output_key,
                                                     max_token_limit=self.max_tokens, messages=self.messages,
                                                     prompt_version=self.prompt_version)

    def set_by_agent_model(self, **kwargs):
        """ Assign values of parameters to the ChatMemory model in the agent configuration."""
        copied_obj = super().set_by_agent_model(**kwargs)
        if 'messages' in kwargs and kwargs['messages']:
            copied_obj.messages = kwargs['messages']
        if 'llm' in kwargs and kwargs['llm']:
            copied_obj.llm = kwargs['llm']
        if 'input_key' in kwargs and kwargs['input_key']:
            copied_obj.input_key = kwargs['input_key']
        if 'output_key' in kwargs and kwargs['output_key']:
            copied_obj.output_key = kwargs['output_key']
        return copied_obj

    def initialize_by_component_configer(self, component_configer: MemoryConfiger) -> 'ChatMemory':
        """Initialize the chat memory by the ComponentConfiger object.
        Args:
            component_configer(MemoryConfiger): the ComponentConfiger object
        Returns:
            ChatMemory: the ChatMemory object
        """
        super().initialize_by_component_configer(component_configer)
        if hasattr(component_configer, 'input_key') and component_configer.input_key:
            self.input_key = component_configer.input_key
        if hasattr(component_configer, 'output_key') and component_configer.output_key:
            self.output_key = component_configer.output_key
        if hasattr(component_configer, 'prompt_version') and component_configer.prompt_version:
            self.prompt_version = component_configer.prompt_version
        return self

    def add(self, message_list: List[Message], **kwargs) -> None:
        """Add messages to the chat memory."""
        if len(message_list) < 1:
            return
        self.messages.extend(message_list)

    def get(self, **kwargs) -> List[Message]:
        """Get messages from the memory."""
        return self.prune(self.messages, **kwargs)

    def clear(self, **kwargs) -> None:
        """Clear memory."""
        self.messages.clear()

    def prune(self, message_list: List[Message], **kwargs) -> List[Message]:
        """Prune messages from the memory due to memory max token limitation."""
        if len(message_list) < 1:
            return []
        # truncate the memory if it exceeds the maximum number of tokens
        prune_messages = message_list[:]
        if self.llm:
            session_message_str = get_memory_string(message_list)
            message_tokens = self.llm.get_num_tokens(session_message_str)
            if message_tokens > self.max_tokens:
                while message_tokens > self.max_tokens:
                    prune_messages.pop(0)
                    message_tokens = self.llm.get_num_tokens(get_memory_string(prune_messages))
        return prune_messages
