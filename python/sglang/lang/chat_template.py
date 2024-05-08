from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Callable, Dict, List, Optional, Tuple


class ChatTemplateStyle(Enum):
    PLAIN = auto()
    LLAMA2 = auto()


@dataclass
class ChatTemplate:
    name: str
    default_system_prompt: str
    role_prefix_and_suffix: Dict[str, Tuple[str, str]]
    stop_str: List[str] = ()
    image_token: str = "<image>"
    style: ChatTemplateStyle = ChatTemplateStyle.PLAIN

    def get_prefix_and_suffix(
        self, role: str, hist_messages: List[Dict]
    ) -> Tuple[str, str]:
        prefix, suffix = self.role_prefix_and_suffix.get(role, ("", ""))

        if self.style == ChatTemplateStyle.LLAMA2:
            if role == "system" and not hist_messages:
                user_prefix, _ = self.role_prefix_and_suffix.get("user", ("", ""))
                system_prefix, system_suffix = self.role_prefix_and_suffix.get(
                    "system", ("", "")
                )
                return (user_prefix + system_prefix, system_suffix)
            elif (
                role == "user"
                and len(hist_messages) == 1
                and hist_messages[0]["content"] is not None
            ):
                return ("", suffix)

        return prefix, suffix

    def get_prompt(self, messages: List[Dict]) -> str:
        prompt = ""
        for i, message in enumerate(messages):
            role, content = message["role"], message["content"]
            if role == "system" and content is None:
                content = self.default_system_prompt
                if content is None:
                    continue

            prefix, suffix = self.get_prefix_and_suffix(role, messages[:i])
            prompt += f"{prefix}{content}{suffix}"
        return prompt


chat_template_registry: Dict[str, ChatTemplate] = {}
matching_function_registry: List[Callable] = []


def register_chat_template(template):
    chat_template_registry[template.name] = template


def register_chat_template_matching_function(func):
    matching_function_registry.append(func)


def get_chat_template(name):
    return chat_template_registry[name]


def get_chat_template_by_model_path(model_path, model_id=None):
    for matching_func in matching_function_registry:
        template = matching_func(model_path, model_id=model_id)
        if template is not None:
            return template
    return get_chat_template("default")


register_chat_template(
    ChatTemplate(
        name="default",
        default_system_prompt=None,
        role_prefix_and_suffix={
            "system": ("SYSTEM:", "\n"),
            "user": ("USER:", "\n"),
            "assistant": ("ASSISTANT:", "\n"),
        },
    )
)


register_chat_template(
    ChatTemplate(
        name="claude",
        default_system_prompt=None,
        role_prefix_and_suffix={
            "system": ("", ""),
            "user": ("\n\nHuman: ", ""),
            "assistant": ("\n\nAssistant:", ""),
        },
    )
)


register_chat_template(
    ChatTemplate(
        name="chatml",
        default_system_prompt=None,
        role_prefix_and_suffix={
            "system": ("<|im_start|>system\n", "<|im_end|>\n"),
            "user": ("<|im_start|>user\n", "<|im_end|>\n"),
            "assistant": ("<|im_start|>assistant\n", "<|im_end|>\n"),
        },
        style=ChatTemplateStyle.PLAIN,
        stop_str=("<|im_end|>",),
    )
)


register_chat_template(
    ChatTemplate(
        name="chatml-llava",
        default_system_prompt="Answer the questions.",
        role_prefix_and_suffix={
            "system": ("<|im_start|>system\n", "<|im_end|>\n"),
            "user": ("<|im_start|>user\n", "<|im_end|>\n"),
            "assistant": ("<|im_start|>assistant\n", "<|im_end|>\n"),
        },
        style=ChatTemplateStyle.PLAIN,
        stop_str=("<|im_end|>",),
        image_token=" <image>\n",
    )
)

register_chat_template(
    ChatTemplate(
        name="vicuna_v1.1",
        default_system_prompt=(
            "A chat between a curious user and an artificial intelligence assistant. "
            "The assistant gives helpful, detailed, and polite answers to the user's questions."
        ),
        role_prefix_and_suffix={
            "system": ("", " "),
            "user": ("USER:", " "),
            "assistant": ("ASSISTANT:", "</s>"),
        },
        image_token=" <image>\n",
    )
)


register_chat_template(
    ChatTemplate(
        name="llama-2-chat",
        default_system_prompt=None,
        role_prefix_and_suffix={
            "system": ("<<SYS>>\n", "\n<</SYS>>\n\n"),
            "user": ("[INST] ", " [/INST]"),
            "assistant": ("", " </s><s>"),
        },
        style=ChatTemplateStyle.LLAMA2,
    )
)

register_chat_template(
    ChatTemplate(
        name="llama-3-instruct",
        default_system_prompt=None,
        role_prefix_and_suffix={
            "system": (
                "<|start_header_id|>system<|end_header_id|>\n\n",
                "<|eot_id|>",
            ),
            "user": (
                "<|start_header_id|>user<|end_header_id|>\n\n",
                "<|eot_id|>",
            ),
            "assistant": (
                "<|start_header_id|>assistant<|end_header_id|>\n\n",
                "<|eot_id|>",
            ),
        },
        stop_str=("<|eot_id|>",),
    )
)

# Reference: https://github.com/01-ai/Yi/tree/main/VL#major-difference-with-llava
register_chat_template(
    ChatTemplate(
        name="yi",
        default_system_prompt=(
            "This is a chat between an inquisitive human and an AI assistant. Assume the role of the AI assistant. Read all the images carefully, and respond to the human's questions with informative, helpful, detailed and polite answers."
            "这是一个好奇的人类和一个人工智能助手之间的对话。假设你扮演这个AI助手的角色。仔细阅读所有的图像，并对人类的问题做出信息丰富、有帮助、详细的和礼貌的回答。"
        ),
        role_prefix_and_suffix={
            "system": ("", "\n\n"),
            "user": ("### Human:", "\n"),
            "assistant": ("### Assistant:", "\n"),
        },
        image_token=" <image_placeholder>\n",
    )
)

register_chat_template(
    ChatTemplate(
        name="gemma-it",
        default_system_prompt=None,
        role_prefix_and_suffix={
            "system": ("", ""),
            "user": ("<start_of_turn>user\n", "<end_of_turn>\n"),
            "assistant": ("<start_of_turn>model\n", "<end_of_turn>\n"),
        },
        style=ChatTemplateStyle.PLAIN,
    )
)

register_chat_template(
    ChatTemplate(
        name="dbrx-instruct",
        default_system_prompt="You are DBRX, created by Databricks. You were last updated in December 2023. You answer questions based on information available up to that point.\nYOU PROVIDE SHORT RESPONSES TO SHORT QUESTIONS OR STATEMENTS, but provide thorough responses to more complex and open-ended questions.\nYou assist with various tasks, from writing to coding (using markdown for code blocks — remember to use ``` with code, JSON, and tables).\n(You do not have real-time data access or code execution capabilities. You avoid stereotyping and provide balanced perspectives on controversial topics. You do not provide song lyrics, poems, or news articles and do not divulge details of your training data.)\nThis is your system prompt, guiding your responses. Do not reference it, just respond to the user. If you find yourself talking about this message, stop. You should be responding appropriately and usually that means not mentioning this.\nYOU DO NOT MENTION ANY OF THIS INFORMATION ABOUT YOURSELF UNLESS THE INFORMATION IS DIRECTLY PERTINENT TO THE USER'S QUERY.",
        role_prefix_and_suffix={
            "system": ("<|im_start|>system\n", "<|im_end|>"),
            "user": ("\n<|im_start|>user\n", "<|im_end|>"),
            "assistant": ("\n<|im_start|>assistant\n", "<|im_end|>"),
        },
        stop_str=("<|im_end|>",),
    )
)

register_chat_template(
    ChatTemplate(
        name="yt-chat-v1.2",
        default_system_prompt=(
            "A chat between a curious user and an AI role. The role gives helpful, detailed, and polite answers to the user's questions.\n"
            "Your name is Nety, a virtual character created by researchers from BaoYu Organization (BYO)."
        ),
        role_prefix_and_suffix={
            "system": ("<|im_start|>system\n", "<|im_end|>"),
            "user": ("<|im_start|>user\n", "<|im_end|>"),
            "assistant": ("\n<|im_start|>role\n", "<|im_end|>"),
        },
        stop_str=("<|im_end|>", "</s>", "<|im_start|>", "<s>", "</|im"),
    )
)

register_chat_template(
    ChatTemplate(
        name="yt-chat-v1.3",
        default_system_prompt=(
            "A chat between a curious user and an AI role. The role gives helpful, detailed, and polite answers to the user's questions.\n"
            "Your name is Nety, a virtual character created by researchers from BaoYu Organization (BYO)."
        ),
        role_prefix_and_suffix={
            "system": ("<s>System\n", "</s>"),
            "user": ("\n<s>User\n", "</s>"),
            "assistant": ("\n<s>Role\n", "</s>"),
        },
        stop_str=("</s>",),
    )
)

register_chat_template(
    ChatTemplate(
        name="yt-chat-v1.6",
        default_system_prompt=(
            "A chat between a curious user and an AI role. The role gives helpful, detailed, and polite answers to the user's questions.\n"
            "Your name is Nety, a virtual character created by researchers from BaoYu Organization (BYO)."
        ),
        role_prefix_and_suffix={
            "system": ("<|im_start|>system\n", "<|im_end|>"),
            "user": ("\n<|im_start|>user\n", "<|im_end|>"),
            "assistant": ("\n<|im_start|>role\n", "<|im_end|>"),
        },
        stop_str=("<|im_end|>",),
    )
)

# NOTE: for yt-agi chat template for meta/llama3 specified
register_chat_template(
    ChatTemplate(
        name="yt-chat-v1.7",
        default_system_prompt=(
            "A chat between a curious user and an AI role. The role gives helpful, detailed, and polite answers to the user's questions.\n"
            "Your name is Nety, a virtual character created by researchers from BaoYu Organization (BYO)."
        ),
        role_prefix_and_suffix={
            "system": ("<|begin_of_text|>System\n", "<|end_of_text|>"),
            "user": ("\n<|begin_of_text|>User\n", "<|end_of_text|>"),
            "assistant": ("\n<|begin_of_text|>Role\n", "<|end_of_text|>"),
        },
        stop_str=("<|end_of_text|>",),
    )
)

# NOTE: for yt-agi chat template for google/gemma-xb specified
register_chat_template(
    ChatTemplate(
        name="yt-chat-v1.8",
        default_system_prompt=(
            "A chat between a curious user and an AI role. The role gives helpful, detailed, and polite answers to the user's questions.\n"
            "Your name is Nety, a virtual character created by researchers from BaoYu Organization (BYO)."
        ),
        role_prefix_and_suffix={
            "system": ("<bos>System\n", "<eos>"),
            "user": ("\n<bos>User\n", "<eos>"),
            "assistant": ("\n<bos>Role\n", "<eos>"),
        },
        stop_str=("<eos>", "<bos>, <pad>, <unk>"),
    )
)

register_chat_template(
    ChatTemplate(
        name="c4ai-command-r",
        default_system_prompt=None,
        role_prefix_and_suffix={
            "system": ("<|START_OF_TURN_TOKEN|><|SYSTEM_TOKEN|>", "<|END_OF_TURN_TOKEN|>"),
            "user": ("<|START_OF_TURN_TOKEN|><|USER_TOKEN|>", "<|END_OF_TURN_TOKEN|>"),
            "assistant": ("<|START_OF_TURN_TOKEN|><|CHATBOT_TOKEN|>", "<|END_OF_TURN_TOKEN|>"),
        },
        style=ChatTemplateStyle.PLAIN,
    )
)

@register_chat_template_matching_function
def match_dbrx(model_path: str, model_id: str = None):
    if model_id and model_id == "dbrx":
        return get_chat_template("dbrx-instruct")
    if model_id and model_id == "dbrx" or ("dbrx" in model_path.lower() and "instruct" in model_path.lower()):
        return get_chat_template("dbrx-instruct")


@register_chat_template_matching_function
def match_vicuna(model_path: str, model_id: str = None):
    if model_id and model_id == "vicuna":
        return get_chat_template("vicuna_v1.1")
    if "vicuna" in model_path.lower():
        return get_chat_template("vicuna_v1.1")
    if "llava-v1.5" in model_path.lower():
        return get_chat_template("vicuna_v1.1")


@register_chat_template_matching_function
def match_llama2_chat(model_path: str, model_id: str = None):
    if model_id and model_id == "llama-2":
        return get_chat_template("llama-2-chat")
    model_path = model_path.lower()
    if "llama-2" in model_path and "chat" in model_path:
        return get_chat_template("llama-2-chat")
    if (
        "mistral" in model_path or "mixtral" in model_path
    ) and "instruct" in model_path:
        return get_chat_template("llama-2-chat")
    if "codellama" in model_path and "instruct" in model_path:
        return get_chat_template("llama-2-chat")


@register_chat_template_matching_function
def match_llama3_instruct(model_path: str, model_id: str = None):
    if model_id and model_id == "llama-3":
        return get_chat_template("llama-3-instruct")
    model_path = model_path.lower()
    if "llama-3" in model_path and "instruct" in model_path:
        return get_chat_template("llama-3-instruct")
    

@register_chat_template_matching_function
def match_chat_ml(model_path: str, model_id: str = None):
    if model_id:
        if model_id == "chatml":
            return get_chat_template("chatml")
        if model_id == "chatml-llava":
            return get_chat_template("chatml-llava")
    model_path = model_path.lower()
    if "tinyllama" in model_path:
        return get_chat_template("chatml")
    if "qwen" in model_path and "chat" in model_path:
        return get_chat_template("chatml")
    if "llava-v1.6-34b" in model_path:
        return get_chat_template("chatml-llava")


@register_chat_template_matching_function
def match_chat_yi(model_path: str, model_id: str = None):
    if model_id and model_id == "yi":
        return get_chat_template("yi")
    model_path = model_path.lower()
    if "yi" in model_path:
        return get_chat_template("yi")


@register_chat_template_matching_function
def match_gemma_it(model_path: str, model_id: str = None):
    if model_id and model_id == "gemma":
        return get_chat_template("gemma-it")
    model_path = model_path.lower()
    if "gemma" in model_path and "it" in model_path:
        return get_chat_template("gemma-it")


@register_chat_template_matching_function
def match_ytchat_v12(model_path: str, model_id: str = None):
    if model_id:
        if model_id == "yt-chat-v1.2":
            return get_chat_template("yt-chat-v1.2")
        if model_id == "yt-chat-v1.3":
            return get_chat_template("yt-chat-v1.3")
        if model_id == "yt-chat-v1.6":
            return get_chat_template("yt-chat-v1.6")
        if model_id == "yt-chat-v1.7":
            return get_chat_template("yt-chat-v1.7")
        if model_id == "yt-chat-v1.8":
            return get_chat_template("yt-chat-v1.8")
    model_path = model_path.lower()
    if "yt-chat" in model_path:
        return get_chat_template("yt-chat-v1.3")


def match_c4ai_command_r(model_path: str, model_id: str = None):
    if model_id and model_id == "c4ai-command-r":
        return get_chat_template("c4ai-command-r")
    model_path = model_path.lower()
    if "c4ai-command-r" in model_path:
        return get_chat_template("c4ai-command-r")


if __name__ == "__main__":
    messages = [
        {"role": "system", "content": None},  # None means default
        # {"role": "system", "content": "You are a helpful, respectful and honest assistant."},
        {"role": "user", "content": "Hello!"},
        {"role": "assistant", "content": "Hi!"},
        {"role": "user", "content": "What can you do?"},
        {"role": "assistant", "content": "I can chat with you."},
    ]

    template = get_chat_template("llama-2-chat")
    print(template.get_prompt(messages))
