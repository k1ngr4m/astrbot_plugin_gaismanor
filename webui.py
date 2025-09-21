from flask import Flask, render_template, jsonify, request, redirect, url_for, session, flash
from .models.database import DatabaseManager
import threading
import webbrowser
import time
import os
import hashlib

app = Flask(__name__)
db_manager = None
secret_key = "SecretKey"  # 默认密钥

def init_webui(db_mgr, sec_key):
    """初始化WebUI"""
    global db_manager, secret_key
    db_manager = db_mgr
    secret_key = sec_key
    app.secret_key = hashlib.sha256(sec_key.encode()).hexdigest()

# 登录页面路由
@app.route('/login', methods=['GET', 'POST'])
def login():
    """登录页面"""
    if request.method == 'POST':
        key = request.form['key']
        if key == secret_key:
            session['logged_in'] = True
            return redirect(url_for('index'))
        else:
            flash('密钥错误，请重新输入')
    return render_template('login.html')

# 登出路由
@app.route('/logout')
def logout():
    """登出"""
    session.pop('logged_in', None)
    return redirect(url_for('login'))

# 验证登录装饰器
def login_required(f):
    def wrapper(*args, **kwargs):
        if not session.get('logged_in'):
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    wrapper.__name__ = f.__name__
    return wrapper

# 首页路由
@app.route('/')
@login_required
def index():
    """首页"""
    return render_template('index.html')

# 用户管理路由
@app.route('/users')
@login_required
def user_management():
    """用户管理页面"""
    return render_template('user_management.html')

@app.route('/api/users', methods=['GET'])
@login_required
def get_users():
    """获取所有用户数据"""
    if not db_manager:
        return jsonify({'error': 'Database not initialized'}), 500

    users = db_manager.fetch_all("SELECT * FROM users ORDER BY level DESC, exp DESC")
    user_list = []
    for user in users:
        user_list.append({
            'user_id': user['user_id'],
            'platform': user['platform'],
            'nickname': user['nickname'],
            'gold': user['gold'],
            'exp': user['exp'],
            'level': user['level'],
            'fishing_count': user['fishing_count'],
            'total_fish_weight': user['total_fish_weight'],
            'total_income': user['total_income'],
            'auto_fishing': user['auto_fishing'],
            'last_fishing_time': user['last_fishing_time'],
            'created_at': user['created_at'],
            'updated_at': user['updated_at']
        })
    return jsonify(user_list)

@app.route('/api/users', methods=['POST'])
@login_required
def add_user():
    """添加用户"""
    if not db_manager:
        return jsonify({'error': 'Database not initialized'}), 500

    try:
        data = request.get_json()
        user_id = data.get('user_id')
        nickname = data.get('nickname')
        gold = data.get('gold', 100)
        exp = data.get('exp', 0)
        level = data.get('level', 1)

        if not all([user_id, nickname]):
            return jsonify({'error': 'Missing required fields'}), 400

        # 检查用户是否已存在
        existing_user = db_manager.fetch_one("SELECT user_id FROM users WHERE user_id = ?", (user_id,))
        if existing_user:
            return jsonify({'error': 'User already exists'}), 400

        current_time = int(time.time())
        db_manager.execute_query(
            """INSERT INTO users
               (user_id, platform, nickname, gold, exp, level, fishing_count, total_fish_weight, total_income,
                auto_fishing, last_fishing_time, created_at, updated_at)
               VALUES (?, 'unknown', ?, ?, ?, ?, 0, 0, 0, FALSE, 0, ?, ?)""",
            (user_id, nickname, gold, exp, level, current_time, current_time)
        )

        return jsonify({'message': 'User added successfully'}), 201
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/users/<user_id>', methods=['PUT'])
@login_required
def update_user(user_id):
    """更新用户"""
    if not db_manager:
        return jsonify({'error': 'Database not initialized'}), 500

    try:
        data = request.get_json()
        nickname = data.get('nickname')
        gold = data.get('gold')
        exp = data.get('exp')
        level = data.get('level')
        auto_fishing = data.get('auto_fishing', False)

        if not all([nickname, gold, exp, level]):
            return jsonify({'error': 'Missing required fields'}), 400

        updated_at = int(time.time())
        db_manager.execute_query(
            """UPDATE users SET
               nickname=?, gold=?, exp=?, level=?, auto_fishing=?, updated_at=?
               WHERE user_id=?""",
            (nickname, gold, exp, level, auto_fishing, updated_at, user_id)
        )

        return jsonify({'message': 'User updated successfully'}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/users/<user_id>', methods=['DELETE'])
@login_required
def delete_user(user_id):
    """删除用户"""
    if not db_manager:
        return jsonify({'error': 'Database not initialized'}), 500

    try:
        # 删除用户的关联数据
        db_manager.execute_query("DELETE FROM user_fish_inventory WHERE user_id=?", (user_id,))
        db_manager.execute_query("DELETE FROM user_rod_instances WHERE user_id=?", (user_id,))
        db_manager.execute_query("DELETE FROM user_accessory_instances WHERE user_id=?", (user_id,))
        db_manager.execute_query("DELETE FROM user_bait_inventory WHERE user_id=?", (user_id,))
        db_manager.execute_query("DELETE FROM fishing_logs WHERE user_id=?", (user_id,))
        db_manager.execute_query("DELETE FROM gacha_logs WHERE user_id=?", (user_id,))
        db_manager.execute_query("DELETE FROM market_listings WHERE seller_user_id=?", (user_id,))
        db_manager.execute_query("DELETE FROM user_achievements WHERE user_id=?", (user_id,))
        db_manager.execute_query("DELETE FROM user_titles WHERE user_id=?", (user_id,))
        db_manager.execute_query("DELETE FROM tax_logs WHERE user_id=?", (user_id,))
        db_manager.execute_query("DELETE FROM sign_in_logs WHERE user_id=?", (user_id,))

        # 删除用户
        db_manager.execute_query("DELETE FROM users WHERE user_id=?", (user_id,))

        return jsonify({'message': 'User deleted successfully'}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# 鱼类数据路由
@app.route('/fish')
@login_required
def fish_data():
    """鱼类数据页面"""
    return render_template('fish_data.html')

@app.route('/api/fish', methods=['GET'])
@login_required
def get_fish_data():
    """获取所有鱼类数据"""
    if not db_manager:
        return jsonify({'error': 'Database not initialized'}), 500

    fish_templates = db_manager.fetch_all("SELECT * FROM fish_templates ORDER BY rarity, id")
    fish_list = []
    for fish in fish_templates:
        # 解析JSON字段
        narration = None
        active_time = None
        preferred_bait = None

        if fish['narration']:
            try:
                narration = json.loads(fish['narration'])
            except json.JSONDecodeError:
                narration = None

        if fish['active_time']:
            try:
                active_time = json.loads(fish['active_time'])
            except json.JSONDecodeError:
                active_time = None

        if fish['preferred_bait']:
            try:
                preferred_bait = json.loads(fish['preferred_bait'])
            except json.JSONDecodeError:
                preferred_bait = None

        fish_list.append({
            'id': fish['id'],
            'name': fish['name'],
            'description': fish['description'],
            'rarity': fish['rarity'],
            'base_value': fish['base_value'],
            'min_weight': fish['min_weight'],
            'max_weight': fish['max_weight'],
            'element': fish['element'],
            'narration': narration,
            'active_time': active_time,
            'preferred_bait': preferred_bait,
            'icon_url': fish['icon_url']
        })
    return jsonify(fish_list)

@app.route('/api/fish', methods=['POST'])
@login_required
def add_fish():
    """添加鱼类"""
    if not db_manager:
        return jsonify({'error': 'Database not initialized'}), 500

    try:
        data = request.get_json()
        name = data.get('name')
        description = data.get('description', '')
        rarity = data.get('rarity')
        base_value = data.get('base_value')
        min_weight = data.get('min_weight')
        max_weight = data.get('max_weight')
        element = data.get('element')
        narration = data.get('narration')
        active_time = data.get('active_time')
        preferred_bait = data.get('preferred_bait')

        if not all([name, rarity, base_value, min_weight, max_weight]):
            return jsonify({'error': 'Missing required fields'}), 400

        # 将列表转换为JSON字符串存储
        narration_json = json.dumps(narration) if narration else None
        active_time_json = json.dumps(active_time) if active_time else None
        preferred_bait_json = json.dumps(preferred_bait) if preferred_bait else None

        db_manager.execute_query(
            """INSERT INTO fish_templates
               (name, description, rarity, base_value, min_weight, max_weight, element, narration, active_time, preferred_bait)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (name, description, rarity, base_value, min_weight, max_weight, element, narration_json, active_time_json, preferred_bait_json)
        )

        return jsonify({'message': 'Fish added successfully'}), 201
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/fish/<int:fish_id>', methods=['PUT'])
@login_required
def update_fish(fish_id):
    """更新鱼类"""
    if not db_manager:
        return jsonify({'error': 'Database not initialized'}), 500

    try:
        data = request.get_json()
        name = data.get('name')
        description = data.get('description', '')
        rarity = data.get('rarity')
        base_value = data.get('base_value')
        min_weight = data.get('min_weight')
        max_weight = data.get('max_weight')
        element = data.get('element')
        narration = data.get('narration')
        active_time = data.get('active_time')
        preferred_bait = data.get('preferred_bait')

        if not all([name, rarity, base_value, min_weight, max_weight]):
            return jsonify({'error': 'Missing required fields'}), 400

        # 将列表转换为JSON字符串存储
        narration_json = json.dumps(narration) if narration else None
        active_time_json = json.dumps(active_time) if active_time else None
        preferred_bait_json = json.dumps(preferred_bait) if preferred_bait else None

        db_manager.execute_query(
            """UPDATE fish_templates SET
               name=?, description=?, rarity=?, base_value=?, min_weight=?, max_weight=?, element=?, narration=?, active_time=?, preferred_bait=?
               WHERE id=?""",
            (name, description, rarity, base_value, min_weight, max_weight, element, narration_json, active_time_json, preferred_bait_json, fish_id)
        )

        return jsonify({'message': 'Fish updated successfully'}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/fish/<int:fish_id>', methods=['DELETE'])
@login_required
def delete_fish(fish_id):
    """删除鱼类"""
    if not db_manager:
        return jsonify({'error': 'Database not initialized'}), 500

    try:
        db_manager.execute_query("DELETE FROM fish_templates WHERE id=?", (fish_id,))
        return jsonify({'message': 'Fish deleted successfully'}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/fish/<int:fish_id>')
@login_required
def get_fish_detail(fish_id):
    """获取特定鱼类详情"""
    if not db_manager:
        return jsonify({'error': 'Database not initialized'}), 500

    fish = db_manager.fetch_one("SELECT * FROM fish_templates WHERE id = ?", (fish_id,))
    if fish:
        return jsonify({
            'id': fish['id'],
            'name': fish['name'],
            'description': fish['description'],
            'rarity': fish['rarity'],
            'base_value': fish['base_value'],
            'min_weight': fish['min_weight'],
            'max_weight': fish['max_weight'],
            'icon_url': fish['icon_url']
        })
    return jsonify({'error': 'Fish not found'}), 404

# 鱼竿数据路由
@app.route('/rods')
@login_required
def rod_data():
    """鱼竿数据页面"""
    return render_template('rod_data.html')

@app.route('/api/rods')
@login_required
def get_rod_data():
    """获取所有鱼竿数据"""
    if not db_manager:
        return jsonify({'error': 'Database not initialized'}), 500

    rod_templates = db_manager.fetch_all("SELECT * FROM rod_templates ORDER BY rarity, id")
    rod_list = []
    for rod in rod_templates:
        # 解析JSON字段
        bonus_effect = None
        narration = None

        if rod['bonus_effect']:
            try:
                bonus_effect = json.loads(rod['bonus_effect'])
            except json.JSONDecodeError:
                bonus_effect = None

        if rod['narration']:
            try:
                narration = json.loads(rod['narration'])
            except json.JSONDecodeError:
                narration = None

        rod_list.append({
            'id': rod['id'],
            'name': rod['name'],
            'description': rod['description'],
            'rarity': rod['rarity'],
            'source': rod['source'],
            'purchase_cost': rod['purchase_cost'],
            'quality_mod': rod['quality_mod'],
            'quantity_mod': rod['quantity_mod'],
            'rare_mod': rod['rare_mod'],
            'durability': rod['durability'],
            'element': rod['element'],
            'bonus_effect': bonus_effect,
            'narration': narration,
            'icon_url': rod['icon_url']
        })
    return jsonify(rod_list)

@app.route('/api/rods', methods=['POST'])
@login_required
def add_rod():
    """添加鱼竿"""
    if not db_manager:
        return jsonify({'error': 'Database not initialized'}), 500

    try:
        data = request.get_json()
        name = data.get('name')
        description = data.get('description', '')
        rarity = data.get('rarity')
        source = data.get('source')
        purchase_cost = data.get('purchase_cost')
        quality_mod = data.get('quality_mod', 1.0)
        quantity_mod = data.get('quantity_mod', 1.0)
        rare_mod = data.get('rare_mod', 0.0)
        durability = data.get('durability')
        element = data.get('element')
        bonus_effect = data.get('bonus_effect')
        narration = data.get('narration')

        if not all([name, rarity, source]):
            return jsonify({'error': 'Missing required fields'}), 400

        # 将字典转换为JSON字符串存储
        bonus_effect_json = json.dumps(bonus_effect) if bonus_effect else None
        narration_json = json.dumps(narration) if narration else None

        db_manager.execute_query(
            """INSERT INTO rod_templates
               (name, description, rarity, source, purchase_cost, quality_mod, quantity_mod, rare_mod, durability, element, bonus_effect, narration)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (name, description, rarity, source, purchase_cost, quality_mod, quantity_mod, rare_mod, durability, element, bonus_effect_json, narration_json)
        )

        return jsonify({'message': 'Rod added successfully'}), 201
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# 饰品数据路由
@app.route('/accessories')
@login_required
def accessory_data():
    """饰品数据页面"""
    return render_template('accessory_data.html')

@app.route('/api/accessories')
@login_required
def get_accessory_data():
    """获取所有饰品数据"""
    if not db_manager:
        return jsonify({'error': 'Database not initialized'}), 500

    accessory_templates = db_manager.fetch_all("SELECT * FROM accessory_templates ORDER BY rarity, id")
    accessory_list = []
    for accessory in accessory_templates:
        accessory_list.append({
            'id': accessory['id'],
            'name': accessory['name'],
            'description': accessory['description'],
            'rarity': accessory['rarity'],
            'slot_type': accessory['slot_type'],
            'quality_mod': accessory['quality_mod'],
            'quantity_mod': accessory['quantity_mod'],
            'rare_mod': accessory['rare_mod'],
            'coin_mod': accessory['coin_mod'],
            'other_desc': accessory['other_desc'],
            'icon_url': accessory['icon_url']
        })
    return jsonify(accessory_list)

# 鱼饵数据路由
@app.route('/baits')
@login_required
def bait_data():
    """鱼饵数据页面"""
    return render_template('bait_data.html')

@app.route('/api/baits')
@login_required
def get_bait_data():
    """获取所有鱼饵数据"""
    if not db_manager:
        return jsonify({'error': 'Database not initialized'}), 500

    bait_templates = db_manager.fetch_all("SELECT * FROM bait_templates ORDER BY rarity, id")
    bait_list = []
    for bait in bait_templates:
        bait_list.append({
            'id': bait['id'],
            'name': bait['name'],
            'description': bait['description'],
            'rarity': bait['rarity'],
            'effect_description': bait['effect_description'],
            'duration_minutes': bait['duration_minutes'],
            'cost': bait['cost'],
            'required_rod_rarity': bait['required_rod_rarity'],
            'success_rate_modifier': bait['success_rate_modifier'],
            'rare_chance_modifier': bait['rare_chance_modifier'],
            'garbage_reduction_modifier': bait['garbage_reduction_modifier'],
            'value_modifier': bait['value_modifier'],
            'quantity_modifier': bait['quantity_modifier'],
            'is_consumable': bait['is_consumable']
        })
    return jsonify(bait_list)

# 商店管理路由
@app.route('/shop')
@login_required
def shop_management():
    """商店管理页面"""
    return render_template('shop_management.html')

@app.route('/api/shop/rods', methods=['GET'])
@login_required
def get_shop_rods():
    """获取商店鱼竿商品"""
    if not db_manager:
        return jsonify({'error': 'Database not initialized'}), 500

    try:
        # 获取商店中所有上架的鱼竿
        shop_rods = db_manager.fetch_all("""
            SELECT rt.*,
                   COALESCE(srt.purchase_cost, rt.purchase_cost) as purchase_cost,
                   srt.stock,
                   srt.enabled
            FROM rod_templates rt
            LEFT JOIN shop_rod_templates srt ON rt.id = srt.rod_template_id
            WHERE rt.source = 'shop'
            ORDER BY rt.rarity, rt.id
        """)

        rod_list = []
        for rod in shop_rods:
            rod_list.append({
                'id': rod['id'],
                'name': rod['name'],
                'description': rod['description'],
                'rarity': rod['rarity'],
                'source': rod['source'],
                'purchase_cost': rod['purchase_cost'],
                'quality_mod': rod['quality_mod'],
                'quantity_mod': rod['quantity_mod'],
                'rare_mod': rod['rare_mod'],
                'durability': rod['durability'],
                'icon_url': rod['icon_url'],
                'stock': rod['stock'],
                'enabled': bool(rod['enabled']) if rod['enabled'] is not None else True
            })

        return jsonify(rod_list)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/shop/rods', methods=['POST'])
@login_required
def add_rod_to_shop():
    """添加鱼竿到商店"""
    if not db_manager:
        return jsonify({'error': 'Database not initialized'}), 500

    try:
        data = request.get_json()
        rod_id = data.get('rod_id')
        purchase_cost = data.get('purchase_cost', 0)
        stock = data.get('stock', 0)
        enabled = data.get('enabled', True)

        if not rod_id:
            return jsonify({'error': 'Missing rod_id'}), 400

        # 检查鱼竿是否存在
        rod = db_manager.fetch_one("SELECT id FROM rod_templates WHERE id = ?", (rod_id,))
        if not rod:
            return jsonify({'error': 'Rod not found'}), 404

        # 检查是否已存在于商店中
        existing = db_manager.fetch_one("SELECT rod_template_id FROM shop_rod_templates WHERE rod_template_id = ?", (rod_id,))
        if existing:
            return jsonify({'error': 'Rod already in shop'}), 400

        # 添加到商店
        db_manager.execute_query(
            """INSERT INTO shop_rod_templates
               (rod_template_id, purchase_cost, stock, enabled, created_at, updated_at)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (rod_id, purchase_cost, stock, enabled, int(time.time()), int(time.time()))
        )

        return jsonify({'message': 'Rod added to shop successfully'}), 201
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/shop/rods/<int:rod_id>', methods=['PUT'])
@login_required
def update_shop_rod(rod_id):
    """更新商店鱼竿商品"""
    if not db_manager:
        return jsonify({'error': 'Database not initialized'}), 500

    try:
        data = request.get_json()
        purchase_cost = data.get('purchase_cost')
        stock = data.get('stock')
        enabled = data.get('enabled')

        # 检查鱼竿是否在商店中
        existing = db_manager.fetch_one("SELECT rod_template_id FROM shop_rod_templates WHERE rod_template_id = ?", (rod_id,))
        if not existing:
            return jsonify({'error': 'Rod not in shop'}), 404

        # 更新商店商品信息
        update_fields = []
        update_values = []

        if purchase_cost is not None:
            update_fields.append("purchase_cost = ?")
            update_values.append(purchase_cost)

        if stock is not None:
            update_fields.append("stock = ?")
            update_values.append(stock)

        if enabled is not None:
            update_fields.append("enabled = ?")
            update_values.append(enabled)

        if update_fields:
            update_fields.append("updated_at = ?")
            update_values.append(int(time.time()))
            update_values.append(rod_id)

            db_manager.execute_query(
                f"UPDATE shop_rod_templates SET {', '.join(update_fields)} WHERE rod_template_id = ?",
                update_values
            )

        return jsonify({'message': 'Shop rod updated successfully'}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/shop/rods/<int:rod_id>', methods=['DELETE'])
@login_required
def remove_rod_from_shop(rod_id):
    """从商店移除鱼竿"""
    if not db_manager:
        return jsonify({'error': 'Database not initialized'}), 500

    try:
        # 检查鱼竿是否在商店中
        existing = db_manager.fetch_one("SELECT rod_template_id FROM shop_rod_templates WHERE rod_template_id = ?", (rod_id,))
        if not existing:
            return jsonify({'error': 'Rod not in shop'}), 404

        # 从商店移除
        db_manager.execute_query("DELETE FROM shop_rod_templates WHERE rod_template_id = ?", (rod_id,))

        return jsonify({'message': 'Rod removed from shop successfully'}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/shop/baits', methods=['GET'])
@login_required
def get_shop_baits():
    """获取商店鱼饵商品"""
    if not db_manager:
        return jsonify({'error': 'Database not initialized'}), 500

    try:
        # 获取商店中所有上架的鱼饵
        shop_baits = db_manager.fetch_all("""
            SELECT bt.*,
                   COALESCE(sbt.cost, bt.cost) as cost,
                   sbt.stock,
                   sbt.enabled
            FROM bait_templates bt
            LEFT JOIN shop_bait_templates sbt ON bt.id = sbt.bait_template_id
            ORDER BY bt.rarity, bt.id
        """)

        bait_list = []
        for bait in shop_baits:
            bait_list.append({
                'id': bait['id'],
                'name': bait['name'],
                'description': bait['description'],
                'rarity': bait['rarity'],
                'effect_description': bait['effect_description'],
                'duration_minutes': bait['duration_minutes'],
                'cost': bait['cost'],
                'required_rod_rarity': bait['required_rod_rarity'],
                'success_rate_modifier': bait['success_rate_modifier'],
                'rare_chance_modifier': bait['rare_chance_modifier'],
                'garbage_reduction_modifier': bait['garbage_reduction_modifier'],
                'value_modifier': bait['value_modifier'],
                'quantity_modifier': bait['quantity_modifier'],
                'is_consumable': bait['is_consumable'],
                'stock': bait['stock'],
                'enabled': bool(bait['enabled']) if bait['enabled'] is not None else True
            })

        return jsonify(bait_list)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/shop/baits', methods=['POST'])
@login_required
def add_bait_to_shop():
    """添加鱼饵到商店"""
    if not db_manager:
        return jsonify({'error': 'Database not initialized'}), 500

    try:
        data = request.get_json()
        bait_id = data.get('bait_id')
        cost = data.get('cost', 0)
        stock = data.get('stock', 0)
        enabled = data.get('enabled', True)

        if not bait_id:
            return jsonify({'error': 'Missing bait_id'}), 400

        # 检查鱼饵是否存在
        bait = db_manager.fetch_one("SELECT id FROM bait_templates WHERE id = ?", (bait_id,))
        if not bait:
            return jsonify({'error': 'Bait not found'}), 404

        # 检查是否已存在于商店中
        existing = db_manager.fetch_one("SELECT bait_template_id FROM shop_bait_templates WHERE bait_template_id = ?", (bait_id,))
        if existing:
            return jsonify({'error': 'Bait already in shop'}), 400

        # 添加到商店
        db_manager.execute_query(
            """INSERT INTO shop_bait_templates
               (bait_template_id, cost, stock, enabled, created_at, updated_at)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (bait_id, cost, stock, enabled, int(time.time()), int(time.time()))
        )

        return jsonify({'message': 'Bait added to shop successfully'}), 201
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/shop/baits/<int:bait_id>', methods=['PUT'])
@login_required
def update_shop_bait(bait_id):
    """更新商店鱼饵商品"""
    if not db_manager:
        return jsonify({'error': 'Database not initialized'}), 500

    try:
        data = request.get_json()
        cost = data.get('cost')
        stock = data.get('stock')
        enabled = data.get('enabled')

        # 检查鱼饵是否在商店中
        existing = db_manager.fetch_one("SELECT bait_template_id FROM shop_bait_templates WHERE bait_template_id = ?", (bait_id,))
        if not existing:
            return jsonify({'error': 'Bait not in shop'}), 404

        # 更新商店商品信息
        update_fields = []
        update_values = []

        if cost is not None:
            update_fields.append("cost = ?")
            update_values.append(cost)

        if stock is not None:
            update_fields.append("stock = ?")
            update_values.append(stock)

        if enabled is not None:
            update_fields.append("enabled = ?")
            update_values.append(enabled)

        if update_fields:
            update_fields.append("updated_at = ?")
            update_values.append(int(time.time()))
            update_values.append(bait_id)

            db_manager.execute_query(
                f"UPDATE shop_bait_templates SET {', '.join(update_fields)} WHERE bait_template_id = ?",
                update_values
            )

        return jsonify({'message': 'Shop bait updated successfully'}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/shop/baits/<int:bait_id>', methods=['DELETE'])
@login_required
def remove_bait_from_shop(bait_id):
    """从商店移除鱼饵"""
    if not db_manager:
        return jsonify({'error': 'Database not initialized'}), 500

    try:
        # 检查鱼饵是否在商店中
        existing = db_manager.fetch_one("SELECT bait_template_id FROM shop_bait_templates WHERE bait_template_id = ?", (bait_id,))
        if not existing:
            return jsonify({'error': 'Bait not in shop'}), 404

        # 从商店移除
        db_manager.execute_query("DELETE FROM shop_bait_templates WHERE bait_template_id = ?", (bait_id,))

        return jsonify({'message': 'Bait removed from shop successfully'}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/rods/<int:rod_id>', methods=['PUT'])
@login_required
def update_rod(rod_id):
    """更新鱼竿"""
    if not db_manager:
        return jsonify({'error': 'Database not initialized'}), 500

    try:
        data = request.get_json()
        name = data.get('name')
        description = data.get('description', '')
        rarity = data.get('rarity')
        source = data.get('source')
        purchase_cost = data.get('purchase_cost')
        quality_mod = data.get('quality_mod', 1.0)
        quantity_mod = data.get('quantity_mod', 1.0)
        rare_mod = data.get('rare_mod', 0.0)
        durability = data.get('durability')
        element = data.get('element')
        bonus_effect = data.get('bonus_effect')
        narration = data.get('narration')

        if not all([name, rarity, source]):
            return jsonify({'error': 'Missing required fields'}), 400

        # 将字典转换为JSON字符串存储
        bonus_effect_json = json.dumps(bonus_effect) if bonus_effect else None
        narration_json = json.dumps(narration) if narration else None

        db_manager.execute_query(
            """UPDATE rod_templates SET
               name=?, description=?, rarity=?, source=?, purchase_cost=?, quality_mod=?, quantity_mod=?, rare_mod=?, durability=?, element=?, bonus_effect=?, narration=?
               WHERE id=?""",
            (name, description, rarity, source, purchase_cost, quality_mod, quantity_mod, rare_mod, durability, element, bonus_effect_json, narration_json, rod_id)
        )

        return jsonify({'message': 'Rod updated successfully'}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/rods/<int:rod_id>', methods=['DELETE'])
@login_required
def delete_rod(rod_id):
    """删除鱼竿"""
    if not db_manager:
        return jsonify({'error': 'Database not initialized'}), 500

    try:
        # 删除相关的商店商品
        db_manager.execute_query("DELETE FROM shop_rod_templates WHERE rod_template_id=?", (rod_id,))

        # 删除鱼竿模板
        db_manager.execute_query("DELETE FROM rod_templates WHERE id=?", (rod_id,))

        return jsonify({'message': 'Rod deleted successfully'}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# 卡池数据路由
@app.route('/gacha_pools')
@login_required
def gacha_pool_data():
    """卡池数据页面"""
    return render_template('gacha_pool_data.html')

@app.route('/api/gacha_pools', methods=['GET'])
@login_required
def get_gacha_pools():
    """获取所有卡池数据"""
    if not db_manager:
        return jsonify({'error': 'Database not initialized'}), 500

    # 从数据库获取卡池数据
    pools = db_manager.fetch_all("SELECT * FROM gacha_pools ORDER BY sort_order, id")
    pool_list = []

    for pool in pools:
        # 获取卡池稀有度权重
        rarity_weights = {}
        weights = db_manager.fetch_all(
            "SELECT rarity, weight FROM gacha_pool_rarity_weights WHERE pool_id = ?",
            (pool['id'],)
        )
        for weight in weights:
            rarity_weights[weight['rarity']] = weight['weight']

        # 获取卡池中的物品
        items = db_manager.fetch_all(
            "SELECT item_type, item_template_id, rarity FROM gacha_pool_items WHERE pool_id = ?",
            (pool['id'],)
        )

        # 按类型分组物品
        items_detail = {}
        for item in items:
            item_type = item['item_type']
            if item_type not in items_detail:
                items_detail[item_type] = []

            # 获取物品详情
            if item_type == "rod":
                item_detail = db_manager.fetch_one(
                    "SELECT id, name, rarity FROM rod_templates WHERE id = ?",
                    (item['item_template_id'],)
                )
            elif item_type == "accessory":
                item_detail = db_manager.fetch_one(
                    "SELECT id, name, rarity FROM accessory_templates WHERE id = ?",
                    (item['item_template_id'],)
                )
            elif item_type == "bait":
                item_detail = db_manager.fetch_one(
                    "SELECT id, name, rarity FROM bait_templates WHERE id = ?",
                    (item['item_template_id'],)
                )
            else:
                continue

            if item_detail:
                items_detail[item_type].append({
                    'id': item_detail['id'],
                    'name': item_detail['name'],
                    'rarity': item_detail['rarity']
                })

        pool_list.append({
            'id': pool['id'],
            'name': pool['name'],
            'description': pool['description'],
            'cost_coins': pool['cost_coins'],
            'cost_premium_currency': pool['cost_premium_currency'],
            'items': items_detail,
            'rarity_weights': rarity_weights
        })

    return jsonify(pool_list)

@app.route('/api/gacha_pools/<int:pool_id>', methods=['PUT'])
@login_required
def update_gacha_pool(pool_id):
    """更新卡池"""
    if not db_manager:
        return jsonify({'error': 'Database not initialized'}), 500

    try:
        data = request.get_json()
        name = data.get('name')
        description = data.get('description')
        rarity_weights = data.get('rarity_weights')
        items = data.get('items', {})

        # 更新卡池基本信息
        if name or description:
            update_fields = []
            update_values = []
            if name:
                update_fields.append("name = ?")
                update_values.append(name)
            if description:
                update_fields.append("description = ?")
                update_values.append(description)

            if update_fields:
                current_time = int(time.time())
                update_values.append(current_time)
                update_values.append(pool_id)
                db_manager.execute_query(
                    f"UPDATE gacha_pools SET {', '.join(update_fields)}, updated_at = ? WHERE id = ?",
                    update_values
                )

        # 更新稀有度权重
        if rarity_weights:
            # 先删除现有的权重配置
            db_manager.execute_query(
                "DELETE FROM gacha_pool_rarity_weights WHERE pool_id = ?",
                (pool_id,)
            )

            # 插入新的权重配置
            current_time = int(time.time())
            for rarity, weight in rarity_weights.items():
                db_manager.execute_query(
                    """INSERT INTO gacha_pool_rarity_weights
                       (pool_id, rarity, weight, created_at)
                       VALUES (?, ?, ?, ?)""",
                    (pool_id, int(rarity), int(weight), current_time)
                )

        # 更新物品配置
        if items:
            # 先删除现有的物品配置
            db_manager.execute_query(
                "DELETE FROM gacha_pool_items WHERE pool_id = ?",
                (pool_id,)
            )

            # 插入新的物品配置
            current_time = int(time.time())
            for item_type, item_ids in items.items():
                for item_id in item_ids:
                    # 获取物品的稀有度
                    rarity = 1
                    if item_type == "rod":
                        item = db_manager.fetch_one(
                            "SELECT rarity FROM rod_templates WHERE id = ?",
                            (item_id,)
                        )
                    elif item_type == "accessory":
                        item = db_manager.fetch_one(
                            "SELECT rarity FROM accessory_templates WHERE id = ?",
                            (item_id,)
                        )
                    elif item_type == "bait":
                        item = db_manager.fetch_one(
                            "SELECT rarity FROM bait_templates WHERE id = ?",
                            (item_id,)
                        )

                    if item:
                        rarity = item['rarity']

                    db_manager.execute_query(
                        """INSERT INTO gacha_pool_items
                           (pool_id, item_type, item_template_id, rarity, weight, created_at)
                           VALUES (?, ?, ?, ?, ?, ?)""",
                        (pool_id, item_type, item_id, rarity, 100, current_time)
                    )

        return jsonify({'message': '卡池更新成功'}), 200
    except Exception as e:
        print(f"更新卡池失败: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/gacha_pool_items', methods=['GET'])
@login_required
def get_all_items_for_gacha():
    """获取所有可用于卡池的物品"""
    if not db_manager:
        return jsonify({'error': 'Database not initialized'}), 500

    try:
        # 获取所有鱼竿
        rods = db_manager.fetch_all("SELECT id, name, rarity FROM rod_templates ORDER BY rarity, id")
        rod_list = [{'id': rod['id'], 'name': rod['name'], 'rarity': rod['rarity'], 'type': 'rod'} for rod in rods]

        # 获取所有饰品
        accessories = db_manager.fetch_all("SELECT id, name, rarity FROM accessory_templates ORDER BY rarity, id")
        accessory_list = [{'id': accessory['id'], 'name': accessory['name'], 'rarity': accessory['rarity'], 'type': 'accessory'} for accessory in accessories]

        # 获取所有鱼饵
        baits = db_manager.fetch_all("SELECT id, name, rarity FROM bait_templates ORDER BY rarity, id")
        bait_list = [{'id': bait['id'], 'name': bait['name'], 'rarity': bait['rarity'], 'type': 'bait'} for bait in baits]

        return jsonify({
            'rods': rod_list,
            'accessories': accessory_list,
            'baits': bait_list
        }), 200
    except Exception as e:
        print(f"获取物品列表失败: {e}")
        return jsonify({'error': str(e)}), 500

def start_webui(port):
    """启动WebUI"""
    app.run(host='0.0.0.0', port=port, debug=False, use_reloader=False)

if __name__ == '__main__':
    # 在单独的线程中启动Web服务器
    server_thread = threading.Thread(target=start_webui, args=(6200,))
    server_thread.daemon = True
    server_thread.start()

    # 等待服务器启动
    time.sleep(2)

    # 打开浏览器
    webbrowser.open('http://localhost:6200')

    # 保持主线程运行
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("服务器已关闭")