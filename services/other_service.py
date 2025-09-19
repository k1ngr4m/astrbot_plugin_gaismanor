from typing import List, Optional
from astrbot.api.event import AstrMessageEvent
from ..models.user import User
from ..models.fishing import FishTemplate
from ..models.database import DatabaseManager
from .fishing_service import FishingService
from .achievement_service import AchievementService
import time
import threading
from datetime import datetime

class OtherService:
    def __init__(self, db_manager: DatabaseManager):
        self.db = db_manager
        self.fishing_service = FishingService(db_manager)
        self.achievement_service = AchievementService(db_manager)
        # 启动自动钓鱼检查线程
        self.auto_fishing_thread = threading.Thread(target=self._auto_fishing_loop, daemon=True)
        self.auto_fishing_thread.start()

    async def auto_fishing_command(self, event: AstrMessageEvent):
        """自动钓鱼命令"""
        user_id = event.get_sender_id()

        # 获取用户信息
        user = self.db.fetch_one("SELECT * FROM users WHERE user_id = ?", (user_id,))
        if not user:
            yield event.plain_result("您还未注册，请先使用 /注册 命令注册账号")
            return

        # 切换自动钓鱼状态
        new_auto_fishing = not user['auto_fishing']

        self.db.execute_query(
            "UPDATE users SET auto_fishing = ? WHERE user_id = ?",
            (new_auto_fishing, user_id)
        )

        status = "开启" if new_auto_fishing else "关闭"
        yield event.plain_result(f"自动钓鱼功能已{status}！")

    def _auto_fishing_loop(self):
        """自动钓鱼检查循环"""
        while True:
            try:
                # 获取所有开启自动钓鱼的用户
                auto_fishing_users = self.db.fetch_all(
                    "SELECT * FROM users WHERE auto_fishing = TRUE"
                )

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
                        self.db.execute_query(
                            """UPDATE users SET
                               platform=?, gold=?, fishing_count=?, last_fishing_time=?, total_fish_weight=?, total_income=?
                               WHERE user_id=?""",
                            (user.platform, user.gold, user.fishing_count, user.last_fishing_time,
                             user.total_fish_weight, user.total_income, user.user_id)
                        )

                # 每30秒检查一次
                time.sleep(30)
            except Exception as e:
                print(f"自动钓鱼循环出错: {e}")
                time.sleep(30)

    async def leaderboard_command(self, event: AstrMessageEvent):
        """排行榜命令"""
        from ..draw.rank import draw_fishing_ranking
        import os

        # 获取综合排行榜 (前10名) - 综合考虑金币、钓鱼次数和总收益
        comprehensive_leaderboard = self.db.fetch_all("""
            SELECT u.nickname, u.gold, u.fishing_count, u.total_income,
                   uri.rod_template_id, rt.name as rod_name,
                   uai.accessory_template_id, at.name as accessory_name,
                   t.name as title_name
            FROM users u
            LEFT JOIN user_rod_instances uri ON u.user_id = uri.user_id AND uri.is_equipped = TRUE
            LEFT JOIN rod_templates rt ON uri.rod_template_id = rt.id
            LEFT JOIN user_accessory_instances uai ON u.user_id = uai.user_id AND uai.is_equipped = TRUE
            LEFT JOIN accessory_templates at ON uai.accessory_template_id = at.id
            LEFT JOIN user_titles ut ON u.user_id = ut.user_id AND ut.is_active = TRUE
            LEFT JOIN titles t ON ut.title_id = t.id
            ORDER BY (u.gold + u.fishing_count * 10 + u.total_income) DESC
            LIMIT 10
        """)

        if not comprehensive_leaderboard:
            yield event.plain_result("暂无排行榜数据！")
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
        output_path = "fishing_ranking.png"
        try:
            draw_fishing_ranking(user_data, output_path)
            if os.path.exists(output_path):
                yield event.image_result(output_path)
            else:
                yield event.plain_result("生成排行榜图片失败！")
        except Exception as e:
            yield event.plain_result(f"生成排行榜图片时出错: {str(e)}")

    async def fish_gallery_command(self, event: AstrMessageEvent):
        """鱼类图鉴命令"""
        # 获取所有鱼类模板
        fish_templates = self.db.fetch_all("""
            SELECT id, name, description, rarity, base_value
            FROM fish_templates
            ORDER BY rarity DESC, base_value DESC
        """)

        if not fish_templates:
            yield event.plain_result("暂无鱼类数据！")
            return

        # 构造鱼类图鉴信息
        gallery_info = "=== 鱼类图鉴 ===\n\n"

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
        user = self.db.fetch_one("SELECT * FROM users WHERE user_id = ?", (user_id,))
        if not user:
            yield event.plain_result("您还未注册，请先使用 /注册 命令注册账号")
            return

        # 获取用户的钓鱼记录（最近20条）
        fishing_logs = self.db.fetch_all("""
            SELECT fl.*, ft.name as fish_name, ft.rarity as fish_rarity,
                   uri.rod_template_id, rt.name as rod_name,
                   ubi.bait_template_id, bt.name as bait_name
            FROM fishing_logs fl
            LEFT JOIN fish_templates ft ON fl.fish_template_id = ft.id
            LEFT JOIN user_rod_instances uri ON fl.rod_id = uri.id
            LEFT JOIN rod_templates rt ON uri.rod_template_id = rt.id
            LEFT JOIN user_bait_inventory ubi ON fl.bait_id = ubi.id
            LEFT JOIN bait_templates bt ON ubi.bait_template_id = bt.id
            WHERE fl.user_id = ?
            ORDER BY fl.timestamp DESC
            LIMIT 20
        """, (user_id,))

        if not fishing_logs:
            yield event.plain_result("暂无钓鱼记录！")
            return

        # 构造钓鱼记录信息
        log_info = "=== 钓鱼记录 ===\n\n"

        for log in fishing_logs:
            # 格式化时间
            log_time = datetime.fromtimestamp(log['timestamp']).strftime('%Y-%m-%d %H:%M')

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
        user = self.db.fetch_one("SELECT * FROM users WHERE user_id = ?", (user_id,))
        if not user:
            yield event.plain_result("您还未注册，请先使用 /注册 命令注册账号")
            return

        # 获取用户成就
        achievements = self.achievement_service.get_user_achievements(user_id)

        if not achievements:
            yield event.plain_result("暂无成就数据！")
            return

        # 构造成就信息
        completed_count = sum(1 for a in achievements if a['completed'])
        total_count = len(achievements)

        achievement_info = f"=== 成就系统 ===\n\n"
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
        user = self.db.fetch_one("SELECT * FROM users WHERE user_id = ?", (user_id,))
        if not user:
            yield event.plain_result("您还未注册，请先使用 /注册 命令注册账号")
            return

        # 获取用户称号
        titles = self.achievement_service.get_user_titles(user_id)

        if not titles:
            yield event.plain_result("暂无称号数据！")
            return

        # 构造称号信息
        title_info = "=== 称号系统 ===\n\n"

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
        user = self.db.fetch_one("SELECT * FROM users WHERE user_id = ?", (user_id,))
        if not user:
            yield event.plain_result("您还未注册，请先使用 /注册 命令注册账号")
            return

        # 获取用户装备的鱼竿
        equipped_rod = self.db.fetch_one("""
            SELECT rt.name, rt.rarity, uri.level as refine_level
            FROM user_rod_instances uri
            JOIN rod_templates rt ON uri.rod_template_id = rt.id
            WHERE uri.user_id = ? AND uri.is_equipped = TRUE
        """, (user_id,))

        # 获取用户装备的饰品
        equipped_accessory = self.db.fetch_one("""
            SELECT at.name, at.rarity
            FROM user_accessory_instances uai
            JOIN accessory_templates at ON uai.accessory_template_id = at.id
            WHERE uai.user_id = ? AND uai.is_equipped = TRUE
        """, (user_id,))

        # 获取用户使用的鱼饵
        current_bait = self.db.fetch_one("""
            SELECT bt.name, bt.rarity, ubi.quantity
            FROM user_bait_inventory ubi
            JOIN bait_templates bt ON ubi.bait_template_id = bt.id
            WHERE ubi.user_id = ? AND ubi.id = (
                SELECT current_bait_id FROM users WHERE user_id = ?
            )
        """, (user_id, user_id))

        # 获取用户当前称号
        current_title = self.db.fetch_one("""
            SELECT t.name
            FROM user_titles ut
            JOIN titles t ON ut.title_id = t.id
            WHERE ut.user_id = ? AND ut.is_active = TRUE
        """, (user_id,))

        # 获取用户钓鱼区域信息
        fishing_zone = None

        # 获取鱼塘信息
        pond_info = self.db.fetch_one("""
            SELECT COUNT(*) as total_count, COALESCE(SUM(value), 0) as total_value
            FROM user_fish_inventory
            WHERE user_id = ?
        """, (user_id,))

        # 获取擦弹剩余次数
        today = datetime.now().date()
        today_str = today.strftime('%Y-%m-%d')
        wipe_bomb_count = self.db.fetch_one("""
            SELECT COUNT(*) as count
            FROM wipe_bomb_logs
            WHERE user_id = ? AND date(timestamp) = ?
        """, (user_id, today_str))

        wipe_bomb_remaining = 3 - (wipe_bomb_count['count'] if wipe_bomb_count else 0)

        # 构造用户状态数据
        user_data = {
            'user_id': user_id,
            'nickname': user['nickname'] or "未知用户",
            'coins': user['gold'],
            'current_rod': dict(equipped_rod) if equipped_rod else None,
            'current_accessory': dict(equipped_accessory) if equipped_accessory else None,
            'current_bait': dict(current_bait) if current_bait else None,
            'auto_fishing_enabled': bool(user['auto_fishing']),
            'steal_cooldown_remaining': 0,  # 简化处理
            'fishing_zone': dict(fishing_zone) if fishing_zone else {'name': '新手池', 'daily_rare_fish_quota': 0, 'rare_fish_caught_today': 0},
            'current_title': dict(current_title) if current_title else None,
            'total_fishing_count': user['fishing_count'],
            'steal_total_value': 0,  # 简化处理
            'signed_in_today': True,  # 简化处理
            'wipe_bomb_remaining': max(0, wipe_bomb_remaining),
            'pond_info': dict(pond_info) if pond_info else {'total_count': 0, 'total_value': 0}
        }

        # 生成状态图片
        output_path = f"user_state_{user_id}.png"
        try:
            image = draw_state_image(user_data)
            image.save(output_path)
            if os.path.exists(output_path):
                yield event.image_result(output_path)
            else:
                yield event.plain_result("生成状态图片失败！")
        except Exception as e:
            yield event.plain_result(f"生成状态图片时出错: {str(e)}")

    async def wipe_bomb_command(self, event: AstrMessageEvent, amount: str):
        """擦弹命令 - 投入金币获得随机倍数回报"""
        import random
        from datetime import datetime

        user_id = event.get_sender_id()

        # 检查用户是否已注册
        user = self.db.fetch_one("SELECT * FROM users WHERE user_id = ?", (user_id,))
        if not user:
            yield event.plain_result("您还未注册，请先使用 /注册 命令注册账号")
            return

        # 解析投入的金币数
        gold_to_bet = 0
        if amount.lower() in ['梭哈', 'allin']:
            gold_to_bet = user['gold']
        elif amount.lower() in ['梭一半', 'halfin']:
            gold_to_bet = user['gold'] // 2
        else:
            try:
                gold_to_bet = int(amount)
            except ValueError:
                yield event.plain_result("请输入有效的金币数量或 '梭哈'/'梭一半'/'allin'/'halfin'")
                return

        # 检查金币是否足够
        if gold_to_bet <= 0:
            yield event.plain_result("投入的金币数必须大于0！")
            return

        if user['gold'] < gold_to_bet:
            yield event.plain_result("您的金币不足！")
            return

        # 检查今日擦弹次数限制（每天最多3次）
        today = datetime.now().date()
        today_str = today.strftime('%Y-%m-%d')
        wipe_bomb_count = self.db.fetch_one("""
            SELECT COUNT(*) as count
            FROM wipe_bomb_logs
            WHERE user_id = ? AND date(timestamp) = ?
        """, (user_id, today_str))

        used_attempts = wipe_bomb_count['count'] if wipe_bomb_count else 0
        if used_attempts >= 3:
            yield event.plain_result("您今天的擦弹次数已用完！每天最多可擦弹3次。")
            return

        # 扣除用户金币
        self.db.execute_query(
            "UPDATE users SET gold = gold - ? WHERE user_id = ?",
            (gold_to_bet, user_id)
        )

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
        wipe_history = self.db.fetch_all("""
            SELECT multiplier, timestamp
            FROM wipe_bomb_logs
            WHERE user_id = ?
            ORDER BY timestamp DESC
            LIMIT 10
        """, (user_id,))

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
        gold_ratio = user['gold'] / 10000  # 假设10000金币为基准
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
        self.db.execute_query(
            "UPDATE users SET gold = gold + ? WHERE user_id = ?",
            (earned_gold, user_id)
        )

        # 记录擦弹日志
        self.db.execute_query(
            """INSERT INTO wipe_bomb_logs
               (user_id, bet_amount, multiplier, earned_amount, timestamp)
               VALUES (?, ?, ?, ?, ?)""",
            (user_id, gold_to_bet, multiplier, earned_gold, int(datetime.now().timestamp()))
        )

        # 构造返回消息
        if multiplier >= 5:
            result_msg = f"🎉 恭喜！擦弹成功！\n"
        elif multiplier >= 2:
            result_msg = f"😊 不错！擦弹成功！\n"
        elif multiplier >= 1:
            result_msg = f"🙂 还行！擦弹成功！\n"
        else:
            result_msg = f"😢 很遗憾，擦弹失败了...\n"

        result_msg += f"投入金币: {gold_to_bet}\n"
        result_msg += f"获得倍数: {multiplier}x\n"
        result_msg += f"获得金币: {earned_gold}\n"
        result_msg += f"剩余次数: {2 - used_attempts}次"

        yield event.plain_result(result_msg)