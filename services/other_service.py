from typing import List, Optional
from astrbot.api.event import AstrMessageEvent
from ..dao.fishing_dao import FishingDAO
from ..dao.user_dao import UserDAO
from ..models.user import User
from ..models.fishing import FishTemplate
from ..models.database import DatabaseManager
from ..dao.other_dao import OtherDAO
from .fishing_service import FishingService
from .achievement_service import AchievementService
from .technology_service import TechnologyService
from ..enums.messages import Messages
import time
import threading
from datetime import datetime

class OtherService:
    def __init__(self, db_manager: DatabaseManager):
        self.db = db_manager
        self.user_dao = UserDAO(db_manager)
        self.fishing_dao = FishingDAO(db_manager)
        self.other_dao = OtherDAO(db_manager)
        self.fishing_service = FishingService(db_manager)
        self.achievement_service = AchievementService(db_manager)
        self.technology_service = TechnologyService(db_manager)
        # 启动自动钓鱼检查线程
        self.auto_fishing_thread = threading.Thread(target=self._auto_fishing_loop, daemon=True)
        self.auto_fishing_thread.start()

    async def auto_fishing_command(self, event: AstrMessageEvent):
        """自动钓鱼命令"""
        user_id = event.get_sender_id()

        # 获取用户信息
        user = self.user_dao.get_user_by_id(user_id)
        if not user:
            yield event.plain_result(Messages.NOT_REGISTERED.value)
            return

        # 检查用户是否已解锁自动钓鱼科技
        if not self.technology_service.is_auto_fishing_unlocked(user_id, '自动钓鱼'):
            yield event.plain_result(Messages.AUTO_FISHING_NOT_UNLOCKED.value)
            return

        # 切换自动钓鱼状态
        new_auto_fishing = not user.auto_fishing

        if not self.fishing_dao.update_user_auto_fishing(user_id, new_auto_fishing):
            yield event.plain_result(Messages.AUTO_FISHING_TOGGLE_FAILED.value)
            return

        status = "开启" if new_auto_fishing else "关闭"
        if new_auto_fishing:
            yield event.plain_result(Messages.AUTO_FISHING_ENABLED.value)
        else:
            yield event.plain_result(Messages.AUTO_FISHING_DISABLED.value)

    def _auto_fishing_loop(self):
        """自动钓鱼检查循环"""
        while True:
            try:
                # 获取所有开启自动钓鱼的用户
                auto_fishing_users = self.fishing_dao.get_auto_fishing_users()

                for user_data in auto_fishing_users:
                    # 创建 User 对象
                    user = User(
                        user_id=user_data['user_id'],
                        platform=user_data['platform'],
                        nickname=user_data['nickname'],
                        gold=user_data['gold'],
                        exp=user_data['exp'],
                        level=user_data['level'],
                        fishing_count=user_data['fishing_count'],
                        total_fish_weight=user_data['total_fish_weight'],
                        total_income=user_data['total_income'],
                        last_fishing_time=user_data['last_fishing_time'],
                        auto_fishing=user_data['auto_fishing'],
                        created_at=user_data['created_at'],
                        updated_at=user_data['updated_at']
                    )

                    # 检查是否可以钓鱼
                    can_fish, _ = self.fishing_service.can_fish(user)
                    if can_fish:
                        # 执行钓鱼
                        result = self.fishing_service.fish(user)

                        # 更新用户数据
                        self.user_dao.update_user(user)

                # 每15秒检查一次
                time.sleep(10)
            except Exception as e:
                print(f"自动钓鱼循环出错: {e}")
                time.sleep(10)

    async def leaderboard_command(self, event: AstrMessageEvent):
        """排行榜命令"""
        from ..draw.rank import draw_fishing_ranking
        import os

        # 获取当前群聊ID
        group_id = event.get_group_id()

        # 获取综合排行榜 (前10名) - 综合考虑金币、钓鱼次数和总收益
        # 根据群聊ID进行排行
        comprehensive_leaderboard = self.other_dao.get_comprehensive_leaderboard(group_id, 10)

        if not comprehensive_leaderboard:
            yield event.plain_result(Messages.LEADERBOARD_NO_DATA.value)
            return

        # 转换为绘图函数需要的格式
        user_data = []
        for user in comprehensive_leaderboard:
            user_data.append({
                "nickname": user['nickname'] or "未知用户",
                "title": user['title_name'] or "无称号",
                "coins": user['gold'] or 0,
                "fish_count": user['fishing_count'] or 0,
                "fishing_rod": user['rod_name'] or "无鱼竿",
                "accessory": user['accessory_name'] or "无饰品"
            })

        # 生成排行榜图片
        output_path = "data/plugins/astrbot_plugin_gaismanor/cache/fishing_ranking.png"
        # 确保缓存目录存在
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        try:
            draw_fishing_ranking(user_data, output_path)
            if os.path.exists(output_path):
                yield event.image_result(output_path)
            else:
                yield event.plain_result(Messages.LEADERBOARD_GENERATION_FAILED.value)
        except Exception as e:
            yield event.plain_result(f"{Messages.LEADERBOARD_IMAGE_ERROR.value}: {str(e)}")

    async def fish_gallery_command(self, event: AstrMessageEvent):
        """鱼类图鉴命令"""
        # 获取所有鱼类模板
        fish_templates = self.fishing_dao.get_fish_templates()

        if not fish_templates:
            yield event.plain_result(Messages.FISH_GALLERY_NO_DATA.value)
            return

        # 构造鱼类图鉴信息
        gallery_info = f"{Messages.FISH_GALLERY.value}\n\n"

        # 按稀有度分组显示
        current_rarity = None
        for fish in fish_templates:
            if current_rarity != fish['rarity']:
                current_rarity = fish['rarity']
                stars = "★" * current_rarity
                gallery_info += f"{stars} ({current_rarity}星鱼类):\n"

            gallery_info += f"  · {fish['name']}\n"
            gallery_info += f"    描述: {fish['description']}\n"
            gallery_info += f"    基础价值: {fish['base_value']}金币\n\n"

        yield event.plain_result(gallery_info)

    async def fishing_log_command(self, event: AstrMessageEvent):
        """钓鱼记录命令"""
        user_id = event.get_sender_id()

        # 检查用户是否已注册
        user = self.user_dao.get_user_by_id(user_id)
        if not user:
            yield event.plain_result(Messages.NOT_REGISTERED.value)
            return

        # 获取用户的钓鱼记录（最近20条）
        fishing_logs = self.fishing_dao.get_fishing_logs(user_id, 20)

        if not fishing_logs:
            yield event.plain_result(Messages.FISHING_LOG_NO_DATA.value)
            return

        # 构造钓鱼记录信息
        log_info = f"{Messages.FISHING_LOG.value}\n\n"

        for log in fishing_logs:
            # 格式化时间到秒
            log_time = datetime.fromtimestamp(log['timestamp']).strftime('%Y-%m-%d %H:%M:%S')

            # 钓鱼结果
            if log['success']:
                if log['fish_name']:
                    stars = "★" * log['fish_rarity']
                    log_info += f"[{log_time}] 钓鱼成功\n"
                    log_info += f"  钓到: {log['fish_name']} {stars}\n"
                    log_info += f"  重量: {log['fish_weight']:.2f}kg\n"
                    log_info += f"  价值: {log['fish_value']}金币\n"
                else:
                    log_info += f"[{log_time}] 钓鱼成功\n"
                    log_info += f"  钓到: 未知鱼类\n"
            else:
                log_info += f"[{log_time}] 钓鱼失败\n"

            # 使用的装备
            if log['rod_name']:
                log_info += f"  鱼竿: {log['rod_name']}\n"
            if log['bait_name']:
                log_info += f"  鱼饵: {log['bait_name']}\n"

            log_info += "\n"

        yield event.plain_result(log_info)

    async def view_achievements_command(self, event: AstrMessageEvent):
        """查看成就命令"""
        user_id = event.get_sender_id()

        # 检查用户是否已注册
        user = self.user_dao.get_user_basic_info(user_id)
        if not user:
            yield event.plain_result(Messages.NOT_REGISTERED.value)
            return

        # 获取用户成就
        achievements = self.achievement_service.get_user_achievements(user_id)

        if not achievements:
            yield event.plain_result(Messages.ACHIEVEMENT_NO_DATA.value)
            return

        # 构造成就信息
        completed_count = sum(1 for a in achievements if a['completed'])
        total_count = len(achievements)

        achievement_info = f"{Messages.ACHIEVEMENT_SYSTEM.value}\n\n"
        achievement_info += f"成就完成度: {completed_count}/{total_count}\n\n"

        # 按完成状态分组显示
        completed_achievements = [a for a in achievements if a['completed']]
        in_progress_achievements = [a for a in achievements if not a['completed']]

        if completed_achievements:
            achievement_info += "✅ 已完成:\n"
            for achievement in completed_achievements:
                completed_time = datetime.fromtimestamp(achievement['completed_at']).strftime('%Y-%m-%d %H:%M')
                achievement_info += f"  · {achievement['name']}: {achievement['description']}\n"
                achievement_info += f"    完成时间: {completed_time}\n\n"

        if in_progress_achievements:
            achievement_info += "🔄 进行中:\n"
            for achievement in in_progress_achievements:
                # 处理不同的目标值类型
                if isinstance(achievement['target_value'], (int, float)):
                    progress_text = f"{achievement['progress']}/{achievement['target_value']}"
                else:
                    progress_text = f"{achievement['progress']}/1" if achievement['target_value'] else "0/1"

                achievement_info += f"  · {achievement['name']}: {achievement['description']}\n"
                achievement_info += f"    进度: {progress_text}\n\n"

        yield event.plain_result(achievement_info)

    async def view_titles_command(self, event: AstrMessageEvent):
        """查看称号命令"""
        user_id = event.get_sender_id()

        # 检查用户是否已注册
        user = self.user_dao.get_user_basic_info(user_id)
        if not user:
            yield event.plain_result(Messages.NOT_REGISTERED.value)
            return

        # 获取用户称号
        titles = self.achievement_service.get_user_titles(user_id)

        if not titles:
            yield event.plain_result(Messages.TITLE_NO_DATA.value)
            return

        # 构造称号信息
        title_info = f"{Messages.TITLE_SYSTEM.value}\n\n"

        active_title = None
        inactive_titles = []

        for title in titles:
            if title['is_active']:
                active_title = title
            else:
                inactive_titles.append(title)

        if active_title:
            acquired_time = datetime.fromtimestamp(active_title['acquired_at']).strftime('%Y-%m-%d %H:%M')
            title_info += f"👑 当前称号: {active_title['name']}\n"
            title_info += f"  描述: {active_title['description']}\n"
            title_info += f"  获得时间: {acquired_time}\n\n"

        if inactive_titles:
            title_info += "📦 其他称号:\n"
            for title in inactive_titles:
                acquired_time = datetime.fromtimestamp(title['acquired_at']).strftime('%Y-%m-%d %H:%M')
                title_info += f"  · {title['name']}: {title['description']}\n"
                title_info += f"    获得时间: {acquired_time}\n\n"

        yield event.plain_result(title_info)

    async def state_command(self, event: AstrMessageEvent):
        """状态命令 - 以图片形式展示用户状态"""
        from ..draw.state import draw_state_image
        import os

        user_id = event.get_sender_id()

        # 检查用户是否已注册
        user = self.user_dao.get_user_by_id(user_id)
        if not user:
            yield event.plain_result(Messages.NOT_REGISTERED.value)
            return

        # 获取用户装备的鱼竿
        equipped_rod = self.fishing_dao.get_equipped_rod(user_id)
        # 获取用户装备的饰品
        equipped_accessory = self.fishing_dao.get_equipped_accessory(user_id)
        # 获取用户使用的鱼饵
        current_bait = self.fishing_dao.get_user_current_bait(user_id)
        # 获取用户当前称号
        current_title = self.other_dao.get_user_current_title(user_id)
        # 获取用户钓鱼区域信息
        fishing_zone = None

        # 获取鱼塘信息
        pond_info = self.fishing_dao.get_user_pond_info(user_id)
        # 获取擦弹剩余次数
        today = datetime.now().date()
        today_start = int(datetime.combine(today, datetime.min.time()).timestamp())
        today_end = int(datetime.combine(today, datetime.max.time()).timestamp())
        wipe_bomb_count = self.other_dao.get_user_wipe_bomb_count(user_id, today_start, today_end)

        wipe_bomb_remaining = 3 - (wipe_bomb_count['count'] if wipe_bomb_count else 0)

        # 构造用户状态数据
        # 将装备对象转换为字典格式
        current_rod_dict = None
        if equipped_rod:
            current_rod_dict = {
                'name': equipped_rod.name,
                'rarity': equipped_rod.rarity,
                'refine_level': getattr(equipped_rod, 'refine_level', 1)
            }

        current_accessory_dict = None
        if equipped_accessory:
            current_accessory_dict = {
                'name': equipped_accessory.name,
                'rarity': equipped_accessory.rarity
            }

        user_data = {
            'user_id': user_id,
            'nickname': user.nickname or "未知用户",
            'coins': user.gold,
            'current_rod': current_rod_dict,
            'current_accessory': current_accessory_dict,
            'current_bait': current_bait,
            'auto_fishing_enabled': user.auto_fishing,
            'steal_cooldown_remaining': 0,  # 简化处理
            'fishing_zone': fishing_zone or {'name': '新手池', 'daily_rare_fish_quota': 0, 'rare_fish_caught_today': 0},
            'current_title': current_title,
            'total_fishing_count': user.fishing_count,
            'steal_total_value': 0,  # 简化处理
            'signed_in_today': True,  # 简化处理
            'wipe_bomb_remaining': max(0, wipe_bomb_remaining),
            'pond_info': pond_info or {'total_count': 0, 'total_value': 0}
        }

        # 生成状态图片
        # 清理用户ID中的特殊字符，只保留字母、数字和下划线
        import re
        safe_user_id = re.sub(r'[^a-zA-Z0-9_]', '_', user_id)
        output_path = f"data/plugins/astrbot_plugin_gaismanor/cache/user_state_{safe_user_id}.png"
        # 确保缓存目录存在
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        try:
            image = draw_state_image(user_data)
            image.save(output_path)
            if os.path.exists(output_path):
                yield event.image_result(output_path)
            else:
                yield event.plain_result(Messages.STATE_IMAGE_GENERATION_FAILED.value)
        except Exception as e:
            yield event.plain_result(f"{Messages.STATE_IMAGE_ERROR.value}: {str(e)}")

    async def wipe_bomb_command(self, event: AstrMessageEvent, amount: str):
        """擦弹命令 - 投入金币获得随机倍数回报"""
        import random
        from datetime import datetime

        user_id = event.get_sender_id()

        # 检查用户是否已注册
        user = self.user_dao.get_user_by_id(user_id)
        if not user:
            yield event.plain_result(Messages.NOT_REGISTERED.value)
            return

        # 解析投入的金币数
        gold_to_bet = 0
        if amount.lower() in ['梭哈', 'allin']:
            gold_to_bet = user.gold
        elif amount.lower() in ['梭一半', 'halfin']:
            gold_to_bet = user.gold // 2
        else:
            try:
                gold_to_bet = int(amount)
            except ValueError:
                yield event.plain_result(Messages.WIPE_BOMB_INVALID_AMOUNT.value)
                return

        # 检查金币是否足够
        if gold_to_bet <= 0:
            yield event.plain_result(Messages.WIPE_BOMB_INVALID_BET.value)
            return

        if user.gold < gold_to_bet:
            yield event.plain_result(Messages.WIPE_BOMB_NOT_ENOUGH_GOLD.value)
            return

        # 检查今日擦弹次数限制（每天最多3次）
        today = datetime.now().date()
        today_start = int(datetime.combine(today, datetime.min.time()).timestamp())
        today_end = int(datetime.combine(today, datetime.max.time()).timestamp())
        wipe_bomb_count = self.other_dao.get_user_wipe_bomb_count(user_id, today_start, today_end)

        used_attempts = wipe_bomb_count['count'] if wipe_bomb_count else 0
        if used_attempts >= 3:
            yield event.plain_result(Messages.WIPE_BOMB_DAILY_LIMIT.value)
            return

        # 扣除用户金币
        if not self.user_dao.deduct_gold(user_id, gold_to_bet):
            yield event.plain_result(Messages.WIPE_BOMB_DEDUCT_FAILED.value)
            return

        # 生成随机倍数 - 调整后的加权随机，数值合理
        # 倍数及其概率：
        # 0.1x (15%) - 15% 概率
        # 0.5x (15%) - 15% 概率
        # 1x (20%) - 20% 概率
        # 2x (25%) - 25% 概率
        # 3x (12%) - 12% 概率
        # 5x (9%) - 9% 概率
        # 10x (4%) - 4% 概率
        multipliers = [0.1, 0.5, 1, 2, 3, 5, 10]
        base_weights = [15, 15, 20, 25, 12, 9, 4]

        # 获取用户擦弹历史记录，用于实现保底机制和递增概率
        wipe_history = self.other_dao.get_wipe_bomb_logs(user_id, 10)

        # 计算连续失败次数（获得0.1x或0.5x的次数）
        consecutive_failures = 0
        for record in wipe_history:
            if record['multiplier'] <= 0.5:
                consecutive_failures += 1
            else:
                break

        # 保底机制：连续多次擦弹失败后，下一次必然不会得到0.1x
        weights = base_weights[:]
        if consecutive_failures >= 2:
            weights[0] = 0  # 0.1x概率设为0
            # 将概率转移到0.5x上
            weights[1] += base_weights[0]

        # 递增概率机制：每次失败后，高奖励概率略微提升
        bonus_factor = min(consecutive_failures * 0.1, 0.5)  # 最多增加50%的概率
        if bonus_factor > 0:
            # 将增加的概率从低倍数转移到高倍数
            weights[0] -= int(base_weights[0] * bonus_factor)
            weights[5] += int(base_weights[5] * bonus_factor / 2)  # 5x
            weights[6] += int(base_weights[6] * bonus_factor / 2)  # 10x

        # 动态调整概率机制：根据玩家金币数量调整
        # 当玩家金币较多时，降低高收益概率；当玩家金币较少时，略微提高高收益概率
        gold_ratio = user.gold / 10000  # 假设10000金币为基准
        if gold_ratio > 2:  # 金币是基准的2倍以上
            # 降低高收益概率
            weights[5] -= 2  # 5x
            weights[6] -= 1  # 10x
            # 增加低收益概率
            weights[0] += 1  # 0.1x
            weights[1] += 1  # 0.5x
            weights[2] += 1  # 1x
        elif gold_ratio < 0.5:  # 金币不到基准的一半
            # 提高高收益概率
            weights[5] += 1  # 5x
            weights[6] += 1  # 10x
            # 降低低收益概率
            weights[0] -= 1  # 0.1x
            weights[1] -= 1  # 0.5x

        # 确保权重不为负数
        weights = [max(0, w) for w in weights]

        # 如果所有权重都为0，则使用基础权重
        if sum(weights) == 0:
            weights = base_weights

        multiplier = random.choices(multipliers, weights=weights)[0]

        # 计算获得的金币
        earned_gold = int(gold_to_bet * multiplier)

        # 增加用户金币
        if not self.user_dao.add_gold(user_id, earned_gold):
            yield event.plain_result(Messages.WIPE_BOMB_ADD_GOLD_FAILED.value)
            return

        # 记录擦弹日志
        if not self.other_dao.add_wipe_bomb_log(user_id, gold_to_bet, multiplier, earned_gold, int(datetime.now().timestamp())):
            yield event.plain_result(Messages.WIPE_BOMB_LOG_FAILED.value)
            return

        # 构造返回消息
        if multiplier >= 5:
            result_msg = f"{Messages.WIPE_BOMB_SUCCESS_HIGH.value}\n"
        elif multiplier >= 2:
            result_msg = f"{Messages.WIPE_BOMB_SUCCESS_MEDIUM.value}\n"
        elif multiplier >= 1:
            result_msg = f"{Messages.WIPE_BOMB_SUCCESS_LOW.value}\n"
        else:
            result_msg = f"{Messages.WIPE_BOMB_FAILURE.value}\n"

        result_msg += f"投入金币: {gold_to_bet}\n"
        result_msg += f"获得倍数: {multiplier}x\n"
        result_msg += f"获得金币: {earned_gold}\n"
        result_msg += f"剩余次数: {2 - used_attempts}次"

        yield event.plain_result(result_msg)

    async def wipe_bomb_log_command(self, event: AstrMessageEvent):
        """擦弹记录命令"""
        user_id = event.get_sender_id()

        # 检查用户是否已注册
        user = self.user_dao.get_user_basic_info(user_id)
        if not user:
            yield event.plain_result(Messages.NOT_REGISTERED.value)
            return

        # 获取用户的擦弹记录（最近20条）
        wipe_bomb_logs = self.other_dao.get_wipe_bomb_logs(user_id, 20)

        if not wipe_bomb_logs:
            yield event.plain_result(Messages.WIPE_BOMB_LOG_NO_DATA.value)
            return

        # 构造擦弹记录信息
        log_info = f"{Messages.WIPE_BOMB_LOG.value}\n\n"

        for log in wipe_bomb_logs:
            # 格式化时间到秒
            log_time = datetime.fromtimestamp(log['timestamp']).strftime('%Y-%m-%d %H:%M:%S')

            log_info += f"[{log_time}]\n"
            log_info += f"  投入金币: {log['bet_amount']}\n"
            log_info += f"  获得倍数: {log['multiplier']}x\n"
            log_info += f"  获得金币: {log['earned_amount']}\n"

            # 计算净收益（获得金币 - 投入金币）
            net_profit = log['earned_amount'] - log['bet_amount']
            profit_indicator = "+" if net_profit > 0 else ""
            log_info += f"  净收益: {profit_indicator}{net_profit}\n\n"

        yield event.plain_result(log_info)