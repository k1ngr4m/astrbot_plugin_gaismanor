AstrMessageEvent
AstrBot 事件, AstrBot 运行的核心, AstrBot 所有操作的运行都是事件驱动的。 在插件中, 你声明的每一个async def函数都是一个 Handler, 它应当是一个异步协程(无 yield 返回)或异步生成器(存在一个或多个 yield)， 所有 Handler 都需要在 AstrBot 事件进入消息管道后, 被调度器触发, 在相应的阶段交由 Handler 处理。因此, 几乎所有操作都依赖于该事件, 你定义的大部分 Handler 都需要传入event: AstrMessageEvent参数。


@filter.command("helloworld")
async def helloworld(self, event: AstrMessageEvent):
    pass
这是一个接受helloworld指令, 触发对应操作的示例, 它应当被定义在插件类下, 一般而言, 想要 AstrBot 进行消息之类操作, 都需要依赖event参数。

属性
消息
message_str(str): 纯文本消息, 例如收到消息事件"你好", event.message_str将会是"你好"
message_obj(AstrBotMessage): 消息对象, 参考: AstrBotMessage
is_at_or_wake_command(bool): 是否@了机器人/消息带有唤醒词/为私聊(插件注册的事件监听器会让 is_wake 设为 True, 但是不会让这个属性置为 True)
消息来源
role(str): 用户是否为管理员, 两个可选选项:"member" or "admin"
platform_meta(PlatformMetadata): 消息平台的信息, 参考: PlatformMetadata
session_id(str): 不包含平台的会话 id, 以 qq 平台为例, 在私聊中它是对方 qq 号, 在群聊中它是群号, 它无法标记具体平台, 建议直接使用 9 中的unified_msg_origin作为代替
session(MessageSession): 会话对象, 用于唯一识别一个会话, unified_msg_origin是它的字符串表示, session_id等价于session.session_id
unified_msg_origin(str): 会话 id, 格式为: platform_name:message_type:session_id, 建议使用
事件控制
is_wake(bool): 机器人是否唤醒(通过 WakingStage, 详见: [WakingStage(施工中)]), 如果机器人未唤醒, 将不会触发后面的阶段
call_llm(bool): 是否在此消息事件中禁止默认的 LLM 请求, 对于每个消息事件, AstrBot 会默认调用一次 LLM 进行回复
方法
消息相关
get_message_str

get_message_str() -> str
# 等同于self.message_str
该方法用于获取该事件的文本消息字符串。

get_message_outline

get_message_outline() -> str
该方法用于获取消息概要, 不同于 2, 它不会忽略其他消息类型(如图片), 而是会将其他消息类型转换为对应的占位符, 例如图片会被转换为"[图片]"

get_messages

get_messages() -> List[BaseMessageComponent]
该方法返回一个消息列表，包含该事件中的所有消息组件。该列表中的每个组件都可以是文本、图片或其他类型的消息。组件参考: [BaseMessageComponent(施工中)]

get_message_type

get_message_type() -> MessageType
该方法用于获取消息类型, 消息类型参考: MessageType

is_private_chat

is_private_chat() -> bool
该方法用于判断该事件是否由私聊触发

is_admin

is_admin()
# 等同于self.role == "admin"
该方法用于判断该事件是否为管理员发出

消息平台相关
get_platform_name

get_platform_name() -> str
# 等同于self.platform_meta.name
该方法用于获取该事件的平台名称, 例如"aiocqhttp"。 如果你的插件想只对某个平台的消息事件进行处理, 可以通过该方法获取平台名称进行判断。

ID 相关
get_self_id

get_self_id() -> str
该方法用于获取 Bot 自身 id(自身 qq 号)

get_sender_id

get_sender_id() -> str
该方法用于获取该消息发送者 id(发送者 qq 号)

get_sender_name

get_sender_name() -> str
该方法用于获取消息发送者的昵称(可能为空)

get_group_id

get_group_id() -> str
该方法用于获取群组 id(qq 群群号), 如果不是群组消息将放回 None

会话控制相关
get_session_id

get_session_id() -> str
# 等同于self.session_id或self.session.session_id
该方法用于获取当前会话 id, 格式为 platform_name:message_type:session_id

get_group

get_group(group_id: str = None, **kwargs) -> Optional[Group]
该方法用于获取一个群聊的数据, 如果不填写group_id, 默认返回当前群聊消息, 在私聊中如果不填写该参数将返回 None

仅适配 gewechat 与 aiocqhttp

事件状态
is_wake_up

is_wake_up() -> bool
# 等同于self.is_wake
该方法用于判断该事件是否唤醒 Bot

stop_event

stop_event()
该方法用于终止事件传播, 调用该方法后, 该事件将停止后续处理

continue_event

continue_event()
该方法用于继续事件传播, 调用该方法后, 该事件将继续后续处理

is_stopped

is_stopped() -> bool
该方法用于判断该事件是否已经停止传播

事件结果
set_result

set_result(result: Union[MessageEventResult, str])
该方法用于设置该消息事件的结果, 该结果是 Bot 发送的内容 它接受一个参数:

result: MessageEventResult(参考:[MessageEventResult(施工中)]) 或字符串, 若为字符串, Bot 会发送该字符串消息
get_result

get_result() -> MessageEventResult
该方法用于获取消息事件的结果, 该结果类型参考: [MessageEventResult(施工中)]

clear_result

clear_result()
该方法用于清除消息事件的结果

LLM 相关
should_call_llm

should_call_llm(call_llm: bool)
该方法用于设置是否在此消息事件中禁止默认的 LLM 请求 只会阻止 AstrBot 默认的 LLM 请求(即收到消息->请求 LLM 进行回复)，不会阻止插件中的 LLM 请求

request_llm

request_llm(prompt: str,
        func_tool_manager=None,
        session_id: str = None,
        image_urls: List[str] = [],
        contexts: List = [],
        system_prompt: str = "",
        conversation: Conversation = None,
        ) -> ProviderRequest
该方法用于创建一个 LLM 请求

接受 7 个参数:

prompt(str): 提示词
func_tool_manager(FuncCall): 函数工具管理器, 参考: [FuncCall(施工中)]
session_id(str): 已经过时, 留空即可
image_urls(List(str)): 发送给 LLM 的图片, 可以为 base64 格式/网络链接/本地图片路径
contexts(List): 当指定 contexts 时, 将使用其中的内容作为该次请求的上下文(而不是聊天记录)
system_prompt(str): 系统提示词
conversation(Conversation): 可选, 在指定的对话中进行 LLM 请求, 将使用该对话的所有设置(包括人格), 结果也会被保存到对应的对话中
发送消息相关
一般作为生成器返回, 让调度器执行相应操作:


yield event.func()
make_result

make_result() -> MessageEventResult
该方法用于创建一个空的消息事件结果

plain_result

plain_result(text: str) -> MessageEventResult
该方法用于创建一个空的消息事件结果, 包含文本消息:text

image_result

image_result(url_or_path: str) -> MessageEventResult
该方法用于创建一个空的消息事件结果, 包含一个图片消息, 其中参数url_or_path可以为图片网址或本地图片路径

chain_result

chain_result(chain: List[BaseMessageComponent]) -> MessageEventResult
该方法用于创建一个空的消息事件结果, 包含整个消息链, 消息链是一个列表, 按顺序包含各个消息组件, 消息组件参考: [BaseMessageComponent(施工中)]

send

send(message: MessageChain)
注意这个方法不需要使用 yield 方式作为生成器返回来调用, 请直接使用await event.send(message) 该方法用于发送消息到该事件的当前对话中

接受 1 个参数:

message(MessageChain): 消息链, 参考: [MessageChain(施工中)]
其他
set_extra

set_extra(key, value)
该方法用于设置事件的额外信息, 如果你的插件需要分几个阶段处理事件, 你可以在这里将额外需要传递的信息存储入事件 接受两个参数:

key(str): 键名
value(any): 值
需要和 12 一起使用

get_extra

get_extra(key=None) -> any
该方法用于获取 11 中设置的额外信息, 如果没有提供键名将返回所有额外信息, 它是一个字典。

clear_extra

clear_extra()
该方法用于清除该事件的所有额外信息


AstrBotMessage
AstrBot 消息对象, 它是一个消息的容器, 所有平台的消息在接收时都被转换为该类型的对象, 以实现不同平台的统一处理。

对于每个事件, 一定都有一个驱动该事件的 AstrBotMessage 对象。


平台发来的消息 --> AstrBotMessage --> AstrBot 事件
属性
type(MessageType): 消息类型, 参考: MessageType
self_id(str): 机器人自身 id, 例如在 aiocqhttp 平台, 它是机器人自身的 qq 号
session_id(str): 不包含平台的会话 id, 以 qq 平台为例, 在私聊中它是对方 qq 号, 在群聊中它是群号
message_id(str): 消息 id, 消息的唯一标识符, 用于引用或获取某一条消息
group_id(str): 群组 id, 如果为私聊, 则为空字符串
sender(MessageMember): 消息发送者, 参考: MessageMember
message(List[BaseMessageComponent]): 消息链(Nakuru 格式), 包含该事件中的所有消息内容, 参考: [BaseMessageComponent(施工中)]
message_str(str): 纯文本消息字符串, 相当于把消息链转换为纯文本(会丢失信息!)
raw_message(object): 原始消息对象, 包含所有消息的原始数据(平台适配器发来的)
timestamp(int): 消息的时间戳(会自动初始化)


MessageType
消息类型, 用于区分消息是私聊还是群聊消息, 继承自Enum枚举类型

使用方法如下:


from astrbot.api import MessageType
print(MessageType.GROUP_MESSAGE)
内容
GROUP_MESSAGE: 群聊消息
FRIEND_MESSAGE: 私聊消息
OTHER_MESSAGE: 其他消息, 例如系统消息等


MessageMember
消息发送者对象, 用于标记一个消息发送者的最基本信息

属性
user_id(str): 消息发送者 id, 唯一, 例如在 aiocqhttp 平台, 它是发送者的 qq 号
nickname(str): 昵称, 例如在 aiocqhttp 平台, 它是发送者的 qq 昵称, 它会被自动初始化

Context
暴露给插件的上下文, 该类的作用就是为插件提供接口和数据。

属性:
provider_manager: 供应商管理器对象
platform_manager: 平台管理器对象
方法:
插件相关
get_registered_star

get_registered_star(star_name: str) -> StarMetadata
该方法根据输入的插件名获取插件的元数据对象, 该对象包含了插件的基本信息, 例如插件的名称、版本、作者等。 该方法可以获取其他插件的元数据。 StarMetadata 详情见StarMetadata

get_all_stars

get_all_stars() -> List[StarMetadata]
该方法获取所有已注册的插件的元数据对象列表, 该列表包含了所有插件的基本信息。 StarMetadata 详情见StarMetadata

函数工具相关
get_llm_tool_manager

get_llm_tool_manager() -> FuncCall
该方法获取 FuncCall 对象, 该对象用于管理注册的所有函数调用工具。

activate_llm_tool

activate_llm_tool(name: str) -> bool
该方法用于激活指定名称的已经注册的函数调用工具, 已注册的函数调用工具默认为激活状态, 不需要手动激活。 如果没能找到指定的函数调用工具, 则返回False。

deactivate_llm_tool

deactivate_llm_tool(name: str) -> bool
该方法用于停用指定名称的已经注册的函数调用工具。 如果没能找到指定的函数调用工具, 则返回False。

供应商相关
register_provider

register_provider(provider: Provider)
该方法用于注册一个新用于文本生成的的供应商对象, 该对象必须是 Provider 类。 用于文本生成的的 Provider 类型为 Chat_Completion, 后面将不再重复。

get_provider_by_id

get_provider_by_id(provider_id: str) -> Provider
该方法根据输入的供应商 ID 获取供应商对象。

get_all_providers

get_all_providers() -> List[Provider]
该方法获取所有已注册的用于文本生成的供应商对象列表。

get_all_tts_providers

get_all_tts_providers() -> List[TTSProvider]
该方法获取所有已注册的文本到语音供应商对象列表。

get_all_stt_providers

get_all_stt_providers() -> List[STTProvider]
该方法获取所有已注册的语音到文本供应商对象列表。

get_using_provider

get_using_provider() -> Provider
该方法获取当前使用的用于文本生成的供应商对象。

get_using_tts_provider

get_using_tts_provider() -> TTSProvider
该方法获取当前使用的文本到语音供应商对象。

get_using_stt_provider

get_using_stt_provider() -> STTProvider
该方法获取当前使用的语音到文本供应商对象。

其他
get_config

get_config() -> AstrBotConfig
该方法获取当前 AstrBot 的配置对象, 该对象包含了插件的所有配置项与 AstrBot Core 的所有配置项(谨慎修改!)。

get_db

get_db() -> BaseDatabase
该方法获取 AstrBot 的数据库对象, 该对象用于访问数据库, 该对象是 BaseDatabase 类的实例。

get_event_queue

get_event_queue() -> Queue
该方法用于获取 AstrBot 的事件队列, 这是一个异步队列, 其中的每一项都是一个 AstrMessageEvent 对象。

get_platform

get_platform(platform_type: Union[PlatformAdapterType, str]) -> Platform
该方法用于获取指定类型的平台适配器对象。

send_message

send_message(session: Union[str, MessageSesion], message_chain: MessageChain) -> bool
该方法可以根据会话的唯一标识符-session(unified_msg_origin)主动发送消息。

它接受两个参数：

session: 会话的唯一标识符, 可以是字符串或 MessageSesion 对象， 获取该标识符参考：[获取会话的 session]。
message_chain: 消息链对象, 该对象包含了要发送的消息内容, 该对象是 MessageChain 类的实例。
该方法返回一个布尔值, 表示是否找到对应的消息平台。

注意: 该方法不支持 qq_official 平台!!


Star
插件的基类, 所有插件都继承于该类, 拥有该类的所有属性和方法。

属性:
context: 暴露给插件的上下文, 参考: Context
方法:
文转图
text_to_image

text_to_image(text: str, return_url=True) -> str
该方法用于将文本转换为图片, 如果你的插件想实现类似功能, 优先考虑使用该方法。

它接受两个参数:

text: 你想转换为图片的文本信息, 它是一个字符串, 推荐使用多行字符串的形式。
return_url: 返回图片链接(True)或文件路径(False)。
html 渲染
html_render

async def html_render(self, tmpl: str, data: dict, return_url: bool = True, options: dict = None) -> str:
该方法用于将 Jinja2 模板渲染为图片。

参数说明:

tmpl: str (必选)
描述：HTML Jinja2 模板的文件路径。
data: dict (必选)
描述：用于渲染模板的数据字典。
return_url: bool (可选, 默认为 True)
描述：决定返回值是图片的 URL (True) 还是本地文件路径 (False)。
options: dict (可选)
描述：一个包含截图详细选项的字典。
timeout: float: 截图超时时间（秒）。
type: str: 图片类型，"jpeg" 或 "png"。
quality: int: 图片质量 (0-100)，仅用于 jpeg。
omit_background: bool: 是否使用透明背景，仅用于 png。
full_page: bool: 是否截取整个页面，默认为 True。
clip: dict: 裁剪区域，包含 x, y, width, height。
animations: str: CSS 动画，"allow" 或 "disabled"。
caret: str: 文本光标，"hide" 或 "initial"。
scale: str: 页面缩放，"css" 或 "device"。
mask: list: 需要遮盖的 Playwright Locator 列表。
如果你不知道如何构造模板, 请参考: Jinja2 文档

该功能由 CampuxUtility 提供支持

终止
terminate(Abstract)
该方法为基类提供的抽象方法, 你需要在自己的插件中实现该方法!!

该方法用于插件禁用、重载, 或关闭 AstrBot 时触发, 用于释放插件资源, 如果你的插件对 AstrBot 本体做了某些更改(例如修改了 System Prompt), 强烈建议在该方法中恢复对应的修改!! 如果你的插件使用了外部进程, 强烈建议在该方法中进行销毁!!

你需要在你的插件类中如此实现该方法:


async def terminate(self):
    """
    此处实现你的对应逻辑, 例如销毁, 释放某些资源, 回滚某些修改。
    """

StarMetadata
插件的元数据。

属性:
基础属性
name(str): 插件名称
author(str): 插件作者
desc(str): 插件简介
version(str): 插件版本
repo(str): 插件仓库地址
插件类, 模块属性
star_cls_type(type): 插件类对象类型, 例如你的插件类名为HelloWorld, 该属性就是<type 'HelloWorld'>
star_cls(object): 插件的类对象, 它是一个实例, 你可以使用它调用插件的方法和属性
module_path(str): 插件模块的路径
module(ModuleType): 插件的模块对象
root_dir_name(str): 插件的目录名称
插件身份&状态属性
reserved(bool): 是否为 AstrBot 保留插件
activated(bool): 是否被激活
插件配置
config(AstrBotConfig): 插件配置对象
注册的 Handler 全名列表
star_handler_full_names(List(str)): 注册的 Handler 全名列表, Handler 相关请见核心代码解释->插件注册(施工中)
其它
该类实现了__str__方法, 因此你可以打印插件信息。

PlatformMetadata
平台元数据, 包含了平台的基本信息, 例如平台名称, 平台类型等.

属性
name(str): 平台的名称
description(str): 平台的描述
id(str): 平台的唯一标识符, 用于区分不同的平台
default_config_tmpl(dict): 平台的默认配置模板, 用于生成平台的默认配置文件
adapter_display_name(str): 显示在 WebUI 中的平台名称, 默认为 name(可以更改)
