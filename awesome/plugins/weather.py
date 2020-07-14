import re
import arrow
from nonebot import (
    on_command,
    CommandSession,
    RequestSession,
    get_bot,
)
from nonebot.permission import SUPERUSER
from nonebot.typing import Context_T
from nonebot.helpers import send
from nonebot.log import logger
from client import (
    redis_client
)

from eve_api import (
    get_user_info,
    search_price
)

bot = get_bot()


@on_command('test', only_to_me=False)
async def add(session: RequestSession):
    print(session)
    await session.send('test')


@on_command("add", only_to_me=False)
async def add(session: CommandSession):
    stripped_arg = session.current_arg_text.strip()
    if len(stripped_arg.split()) < 2:
        await session.send("输入错误")
    else:
        keyword, sentence = stripped_arg.split()[0], ''.join(
            str(i) for i in stripped_arg.split()[1:])
        redis_client.sadd(keyword, sentence)
        await session.send(f"你说: {keyword}, 我说: {sentence}")
    logger.debug(stripped_arg)


@on_command("list", only_to_me=False)
async def list_key(session: CommandSession):
    stripped_arg = session.current_arg_text.strip()
    if stripped_arg and len(stripped_arg.split()) == 1:
        res = redis_client.smembers(stripped_arg)
        await session.send(f"{res}")


@on_command("del", only_to_me=False)
async def del_key(session: CommandSession):
    stripped_arg = session.current_arg_text.strip()
    if len(stripped_arg.split()) < 2:
        await session.send("看不懂啦！")
    else:
        key, word = stripped_arg.split()[0], stripped_arg.split()[1:]
        res = redis_client.srem(key, word)
        if res == 1:
            await session.send("如果你不想听我就不说了")
        else:
            await session.send("我可不想忘记[CQ:face,id=14]")


@on_command('jita', only_to_me=False)
async def _(session: CommandSession):
    stripped_arg = session.current_arg_text.strip()
    result = await search_price(stripped_arg)
    await session.send(result)


@on_command('info', only_to_me=False)
async def _(session: CommandSession):
    # user_name = session.ctx['sender']['card'].split('-')[-1]

    stripped_arg = session.current_arg_text.strip()
    if stripped_arg.strip() != '':
        user_name = stripped_arg.strip()
    else:
        user_name = re.split('[-~—=]', session.ctx['sender']['card'])[-1]

    print(f'{user_name}, {session.ctx}')
    user_info, feedback = await get_user_info(user_name)
    if user_info is not None:
        result = str(user_info)
        if feedback:
            result += f'\n{feedback}'
        await session.send(result)
    else:
        await session.send(f'不知道出啥问题了,咕咕')


@on_command('签到', only_to_me=False)
async def _(session: CommandSession):
    # user_name = session.ctx['sender']['card'].split('-')[-1]
    user_account = session.ctx['user_id']

    if redis_client.get(user_account):
        await session.send('都签到过了还想签, 羊毛怪')
        return

    redis_client.set(user_account, 1)
    expire = arrow.now().shift(days=1).floor('days') - arrow.now()
    redis_client.expire(user_account, expire)

    redis_client.hincrby('coin', user_account, 1)

    ad = '10积分可以兑换 星捷快运 运费券一张!详情咨询 mosike'

    user_coin = redis_client.hget('coin', user_account)

    await session.send(f'''
    当前积分为{user_coin}
    ______________________
    {ad}
    ''', at_sender=True)


@on_command('兑换', only_to_me=False, permission=SUPERUSER)
async def _(session: CommandSession):
    operating_account = session.current_arg_text.strip()

    user_account = session.ctx['user_id']

    if operating_account == '':
        await session.send('告诉咕咕鸟对方账号啦')
        return
    user_coin = redis_client.hget('coin', operating_account)
    if user_coin and int(user_coin) > 5:
        redis_client.hincrby('coin', operating_account, -5)
        await session.send('兑换成功, 星捷快运, 贴心服务')
    else:
        await session.send('没有那么多积分, 还想薅羊毛你')
        return

    ad = '5积分可以兑换 星捷快运 运费券一张!详情咨询 mosike'

    user_coin = redis_client.hget('coin', operating_account)

    await session.send(f'''
    当前积分为{user_coin}
    ______________________
    {ad}
    ''', at_sender=True)


@on_command("help", only_to_me=False)
async def help(session: CommandSession):
    await session.send(f"add 触发字 触发内容  添加一条 \n\
del 触发字 触发内容  删除一条 \n\
list 触发字  列出该触发字下的所有条目 \n\
jita 触发字 查询物品吉他价格    \n\
info 查询群名称个人信息\n\
没有其他的了...")


@bot.on_message('group')
async def _(ctx: Context_T) -> None:
    sentence = str(ctx['message'])
    logger.debug(sentence)
    if sentence.split()[0] in ['add', 'list', 'del', 'help', 'info', 'jita', '签到']:
        return

    keywords = redis_client.keys()
    for index, i in enumerate(keywords):
        sub = sentence.find(i)
        if sub != -1:
            word = redis_client.srandmember(keywords[index])
            await send(bot, ctx, word)
            return
