from enum import Enum



class Messages(Enum):
    # 通用
    NOT_REGISTERED = "您还未注册，请先使用 /注册 命令注册账号"
    ALREADY_REGISTERED = "您已经注册过了！"
    REGISTRATION_SUCCESS = "注册成功！欢迎来到大Gai庄园！"
    BALANCE_INFO = "当前金币余额"
    GOLD_UPDATE_FAILED = "金币更新失败，请稍后再试"
    SQL_FAILED = "数据库操作失败，请稍后再试"

    # 签到
    ALREADY_SIGNED_IN = "您今天已经签到过了！"
    SIGN_IN_SUCCESS = "签到成功！"
    SIGN_IN_GOLD = "获得金币"
    SIGN_IN_EXP = "获得经验"
    SIGN_IN_STREAK = "连续签到"

    # 等级相关
    LEVEL_INFO_HEADER = "📊 等级信息"
    LEVEL_CURRENT = "当前等级"
    LEVEL_EXP = "当前经验"
    LEVEL_PROGRESS = "升级进度"
    LEVEL_NEEDED = "距离升级还需"
    LEVEL_NEXT_REWARD = "下一等级奖励"
    LEVEL_MAX = "恭喜您已达到最高等级！"
    LEVEL_MAX_PRIVILEGE = "您已解锁所有等级特权！"

    # 升级/科技/成就
    LEVEL_UP_CONGRATS = "🎉 恭喜升级到 {new_level} 级！"
    LEVEL_UP_CONGRATS_MAX = "🎉 恭喜升级到 {new_level} 级！您已达到最高等级！"
    LEVEL_UP_REWARD = "获得金币奖励"
    LEVEL_UP_MAX = "您已达到最高等级！"
    TECH_UNLOCK = "🎉 成功解锁科技"
    ACHIEVEMENT_UNLOCK = "🎉 恭喜解锁新成就！"

    # 钓鱼消息
    COOLDOWN_NOT_EXPIRED = "还在冷却中，请等待 {remaining} 秒后再钓鱼"
    FISHING_SUCCESS = "钓鱼成功！"
    FISHING_FAILURE = "这次没有钓到鱼，再试试看吧！"
    AUTO_FISHING_ENABLED = "自动钓鱼功能已开启！"
    AUTO_FISHING_DISABLED = "自动钓鱼功能已关闭！"
    AUTO_FISHING_NOT_UNLOCKED = "您尚未解锁自动钓鱼功能！请先使用 /解锁科技 自动钓鱼 解锁自动钓鱼功能。"
    AUTO_FISHING_TOGGLE_FAILED = "设置自动钓鱼功能失败，请稍后再试。"
    FISHING_GOLD_NOT_ENOUGH = "金币不足，无法钓鱼"
    CAN_FISH = "您可以钓鱼了！"
    NO_ROD_EQUIPPED = "请先装备鱼竿再进行钓鱼！使用 /鱼竿 命令查看您的鱼竿，使用 /使用鱼竿 <ID> 来装备鱼竿。"
    FISHING_CAUGHT_FISH = "恭喜！你钓到了一条 {caught_fish_name} ({caught_fish_desc})"

    # 鱼类消息
    NO_FISH_TEMPLATES = "暂无鱼类数据"
    FISHING_FAILED_NO_FISH = "当前装备的鱼竿无法钓到任何鱼类，请使用更高级的鱼竿！"

    # 装备消息
    EQUIPMENT_NOT_OWNED = "您没有该装备"
    EQUIPMENT_ALREADY_EQUIPPED = "该装备已经装备中"
    EQUIPMENT_EQUIP_SUCCESS = "成功装备"
    EQUIPMENT_UNEQUIP_SUCCESS = "成功卸下"
    EQUIPMENT_REPAIR_SUCCESS = "成功修理"
    EQUIPMENT_REPAIR_FAILED = "修理失败"
    EQUIPMENT_REPAIR_NOT_NEEDED = "装备无需修理"
    EQUIPMENT_REFINE_SUCCESS = "成功精炼"
    EQUIPMENT_REFINE_FAILED = "精炼失败"
    EQUIPMENT_REFINE_MAX_LEVEL = "装备已达到最大精炼等级"
    EQUIPMENT_ROD_NOT_FOUND = "未找到指定的鱼竿"
    EQUIPMENT_ROD_EQUIP_SUCCESS = "成功装备鱼竿"
    EQUIPMENT_ROD_EQUIP_FAILED = "装备鱼竿失败"
    EQUIPMENT_ROD_NOT_EQUIPPED = "您当前没有装备任何鱼竿"
    EQUIPMENT_ROD_UNEQUIP_SUCCESS = "成功卸下鱼竿"
    EQUIPMENT_ROD_UNEQUIP_FAILED = "卸下鱼竿失败，可能鱼竿已被卸下或不存在"
    EQUIPMENT_ROD_REPAIR_NO_ID = "请指定要维修的鱼竿ID。使用 /鱼竿 命令查看您的鱼竿列表和对应的ID。"
    EQUIPMENT_ROD_REPAIR_NOT_FOUND = "未找到指定的鱼竿，请检查鱼竿ID是否正确"
    EQUIPMENT_ROD_REPAIR_NOT_DAMAGED = "鱼竿 [{rod_name}] 未损坏，无需维修"
    EQUIPMENT_ROD_REPAIR_NOT_NEEDED = "鱼竿 [{rod_name}] 无需维修"
    EQUIPMENT_ROD_REPAIR_NOT_ENOUGH_GOLD = "金币不足！维修需要 {repair_cost} 金币，您当前只有 {user_gold} 金币。"
    EQUIPMENT_ROD_REPAIR_SUCCESS = "鱼竿 [{rod_name}] 维修成功！"
    EQUIPMENT_ROD_BROKEN = "鱼竿已损坏，请先维修后再使用！"

    # 科技消息
    TECHNOLOGY_NOT_FOUND = "未找到指定的科技"
    TECHNOLOGY_UNLOCK_SUCCESS = "🎉 成功解锁科技"
    TECHNOLOGY_UNLOCK_FAILED = "解锁科技失败，请稍后再试"
    TECHNOLOGY_ALREADY_UNLOCKED = "您已解锁该科技"
    TECHNOLOGY_UNLOCK_FAILED_REQUIRED_LEVEL = "需要达到{required_level}级才能解锁此科技"
    TECHNOLOGY_UNLOCK_FAILED_GOLD_NOT_ENOUGH = "金币不足，无法解锁此科技，需要{required_gold}金币才能解锁"
    TECHNOLOGY_UNLOCK_FAILED_REQUIRED_TECH = "需要先解锁以下科技"
    TECHNOLOGY_CAN_UNLOCK = "您可以解锁此科技"

    # 商店消息
    SHOP_NO_ROD_ITEMS = "暂无鱼竿商品"
    SHOP_NO_BAIT_ITEMS = "暂无鱼饵商品"
    SHOP_NO_ACCESSORY_ITEMS = "暂无饰品商品"
    SHOP_BAIT_SYSTEM_NOT_UNLOCKED = "您尚未解锁鱼饵系统！请先升级以解锁鱼饵系统。"
    SHOP_BUY_BAIT_SUCCESS = "成功购买鱼饵"
    SHOP_BUY_BAIT_FAILED = "购买鱼饵失败，请检查金币是否足够、商品是否存在或您是否已解锁鱼饵系统"
    SHOP_BUY_ACCESSORY_SUCCESS = "成功购买饰品"
    SHOP_BUY_ACCESSORY_FAILED = "购买饰品失败，请检查金币是否足够或商品是否存在"
    SHOP_BUY_ROD_SUCCESS = "成功购买鱼竿"
    SHOP_BUY_ROD_FAILED = "购买鱼竿失败，请检查金币是否足够或商品是否存在"
    SHOP_USE_BAIT_NOT_OWNED = "您没有该鱼饵或数量不足"
    SHOP_USE_BAIT_FEATURE_COMING_SOON = "鱼饵使用功能正在开发中，敬请期待！"
    SHOP_EQUIP_ACCESSORY_NOT_OWNED = "您没有该饰品"
    SHOP_EQUIP_ACCESSORY_SUCCESS = "成功装备饰品"
    SHOP_EQUIP_ACCESSORY_FAILED = "装备饰品失败"
    SHOP_EQUIP_ROD_NOT_OWNED = "您没有该鱼竿"
    SHOP_EQUIP_ROD_SUCCESS = "成功装备鱼竿"
    SHOP_EQUIP_ROD_FAILED = "装备鱼竿失败"

    # 市场消息
    MARKET_NO_FISH_ITEMS = "市场上暂无鱼类商品"
    MARKET_NO_ROD_ITEMS = "市场上暂无鱼竿商品"
    MARKET_NO_ACCESSORY_ITEMS = "市场上暂无饰品商品"
    MARKET_NO_BAIT_ITEMS = "市场上暂无鱼饵商品"
    MARKET_LIST_FISH_NOT_OWNED = "未找到该鱼类或不属于您"
    MARKET_LIST_FISH_PRICE_TOO_LOW = "价格过低"
    MARKET_LIST_FISH_SUCCESS = "成功上架鱼类"
    MARKET_LIST_FISH_FAILED = "上架鱼类失败"
    MARKET_LIST_ROD_NOT_OWNED = "未找到该鱼竿或不属于您"
    MARKET_LIST_ROD_EQUIPPED = "装备中的鱼竿无法上架，请先卸下"
    MARKET_LIST_ROD_PRICE_TOO_LOW = "价格过低"
    MARKET_LIST_ROD_SUCCESS = "成功上架鱼竿"
    MARKET_LIST_ROD_FAILED = "上架鱼竿失败"
    MARKET_LIST_ACCESSORY_NOT_OWNED = "未找到该饰品或不属于您"
    MARKET_LIST_ACCESSORY_EQUIPPED = "装备中的饰品无法上架，请先卸下"
    MARKET_LIST_ACCESSORY_PRICE_TOO_LOW = "价格过低"
    MARKET_LIST_ACCESSORY_SUCCESS = "成功上架饰品"
    MARKET_LIST_ACCESSORY_FAILED = "上架饰品失败"
    MARKET_LIST_BAIT_NOT_OWNED = "未找到该鱼饵或数量不足"
    MARKET_LIST_BAIT_PRICE_TOO_LOW = "价格过低"
    MARKET_LIST_BAIT_SUCCESS = "成功上架鱼饵"
    MARKET_LIST_BAIT_FAILED = "上架鱼饵失败"
    MARKET_BUY_SUCCESS = "购买成功！"
    MARKET_BUY_FAILED = "购买失败，请检查金币是否足够或商品是否存在"

    # 出售消息
    SELL_NO_FISH = "您的鱼塘是空的，没有鱼可以卖出！"
    SELL_ALL_FISH_SUCCESS = "成功卖出所有鱼类！"
    SELL_RARITY_INVALID = "稀有度参数无效，请输入1-5之间的数字！"
    SELL_NO_FISH_OF_RARITY = "您的鱼塘中没有 {rarity} 星鱼类！"
    SELL_FISH_OF_RARITY_SUCCESS = "成功卖出所有 {rarity} 星鱼类！"
    SELL_ROD_NOT_OWNED = "找不到指定的鱼竿或该鱼竿不属于您！"
    SELL_ROD_EQUIPPED = "不能出售正在使用的鱼竿，请先卸下该鱼竿！"
    SELL_ROD_SUCCESS = "成功出售鱼竿"
    SELL_BAIT_NOT_OWNED = "找不到指定的鱼饵或该鱼饵不属于您！"
    SELL_BAIT_ZERO_QUANTITY = "该鱼饵数量为0，无法出售！"
    SELL_BAIT_SUCCESS = "成功出售鱼饵"
    SELL_NO_RODS_TO_SELL = "您没有可以出售的鱼竿（非五星且未装备的鱼竿）！"
    SELL_RODS_SUCCESS = "成功出售以下鱼竿："

    # 库存消息
    INVENTORY_NO_FISH = "您的鱼塘还是空的呢，快去钓鱼吧！"
    INVENTORY_NO_RODS = "您的鱼竿背包是空的，快去商店购买一些鱼竿吧！"
    INVENTORY_NO_ACCESSORIES = "您的饰品背包是空的"
    INVENTORY_NO_BAIT = "您的鱼饵背包是空的，快去商店购买一些鱼饵吧！"
    INVENTORY_FISH_INFO = "鱼塘信息"
    INVENTORY_ROD_INFO = "鱼竿信息"
    INVENTORY_ACCESSORY_INFO = "饰品信息"
    INVENTORY_BAIT_INFO = "鱼饵信息"
    INVENTORY_POND_FULL = "您的鱼塘已达到最高等级，无法继续升级！"
    INVENTORY_POND_UPGRADE_COST = "金币不足！升级需要 {upgrade_cost} 金币，您当前只有 {user_gold} 金币。"
    INVENTORY_POND_UPGRADE_DEDUCT_FAILED = "扣除金币失败，请稍后重试！"
    INVENTORY_POND_UPGRADE_FAILED = "升级鱼塘失败，请稍后重试！"
    INVENTORY_POND_UPGRADE_SUCCESS = "鱼塘升级成功！"

    # 抽卡消息
    GACHA_INVALID_POOL = "无效的卡池ID！请使用 1-3 之间的数字。"
    GACHA_NOT_ENOUGH_GOLD = "金币不足！单次抽卡需要100金币。"
    GACHA_DEDUCT_GOLD_FAILED = "扣除金币失败，请稍后再试。"
    GACHA_FAILED = "抽卡失败，请稍后再试。"
    GACHA_ADD_ITEM_FAILED = "抽卡成功，但添加物品到背包时出错。"
    GACHA_LOG_FAILED = "抽卡成功，但记录日志时出错。"
    GACHA_SUCCESS = "🎉 抽卡成功！"
    GACHA_TEN_NOT_ENOUGH_GOLD = "金币不足！十连抽卡需要900金币。"
    GACHA_NO_RECORDS = "您还没有抽卡记录。"
    GACHA_TEN_SUCCESS = "🎊 十连抽卡结果"

    # 成就消息
    ACHIEVEMENT_NO_DATA = "暂无成就数据！"
    ACHIEVEMENT_SYSTEM = "=== 成就系统 ==="

    # 称号消息
    TITLE_NO_DATA = "暂无称号数据！"
    TITLE_SYSTEM = "=== 称号系统 ==="
    TITLE_CURRENT = "👑 当前称号"
    TITLE_OTHERS = "📦 其他称号"

    # 鱼类图鉴消息
    FISH_GALLERY_NO_DATA = "暂无鱼类数据！"
    FISH_GALLERY = "=== 鱼类图鉴 ==="

    # 钓鱼记录消息
    FISHING_LOG_NO_DATA = "暂无钓鱼记录！"
    FISHING_LOG = "=== 钓鱼记录 ==="

    # 排行榜消息
    LEADERBOARD_NO_DATA = "暂无排行榜数据！"
    LEADERBOARD_GENERATION_FAILED = "生成排行榜图片失败！"
    LEADERBOARD_IMAGE_ERROR = "生成排行榜图片时出错"

    # 状态消息
    STATE_NOT_REGISTERED = "您还未注册，请先使用 /注册 命令注册账号"
    STATE_IMAGE_GENERATION_FAILED = "生成状态图片失败！"
    STATE_IMAGE_ERROR = "生成状态图片时出错"

    # 擦弹消息
    WIPE_BOMB_NOT_ENOUGH_GOLD = "您的金币不足！"
    WIPE_BOMB_INVALID_AMOUNT = "请输入有效的金币数量或 '梭哈'/'梭一半'/'allin'/'halfin'"
    WIPE_BOMB_INVALID_BET = "投入的金币数必须大于0！"
    WIPE_BOMB_DAILY_LIMIT = "您今天的擦弹次数已用完！每天最多可擦弹3次。"
    WIPE_BOMB_DEDUCT_FAILED = "扣除金币失败，请稍后再试。"
    WIPE_BOMB_ADD_GOLD_FAILED = "增加金币失败，请稍后再试。"
    WIPE_BOMB_LOG_FAILED = "记录擦弹日志失败，请稍后再试。"
    WIPE_BOMB_SUCCESS_HIGH = "🎉 恭喜！擦弹成功！"
    WIPE_BOMB_SUCCESS_MEDIUM = "😊 不错！擦弹成功！"
    WIPE_BOMB_SUCCESS_LOW = "🙂 还行！擦弹成功！"
    WIPE_BOMB_FAILURE = "😢 很遗憾，擦弹失败了..."

    # 擦弹记录消息
    WIPE_BOMB_LOG_NO_DATA = "暂无擦弹记录！"
    WIPE_BOMB_LOG = "=== 擦弹记录 ==="